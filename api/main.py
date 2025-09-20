# api/main.py
from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import os
import uuid
from datetime import datetime
try:
    from .match_flow import flow_matcher, Candidate
    from .user_routes import router as user_router
    from .auth import get_current_active_user, get_current_user
except ImportError:
    try:
        from match_flow import flow_matcher, Candidate
        from user_routes import router as user_router
        from auth import get_current_active_user, get_current_user
    except ImportError:
        # 如果所有导入都失败，尝试从当前目录导入
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from match_flow import flow_matcher, Candidate
        from user_routes import router as user_router
        from auth import get_current_active_user, get_current_user

# 延迟导入QA助手，避免启动时错误
qa_assistant = None

# CV text extraction functions


def extract_cv_text(file_path: str) -> str:
    """
    Extract text content from PDF or Word documents
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    extracted_text = ""

    try:
        if file_extension == ".pdf":
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted_text += page.extract_text() + "\n"

        elif file_extension == ".docx":
            from docx import Document
            doc = Document(file_path)
            for para in doc.paragraphs:
                extracted_text += para.text + "\n"

        elif file_extension == ".doc":
            # For .doc files, more complex processing is needed
            # Temporarily return error message
            raise Exception(
                "Unsupported .doc format. Please convert to .docx or .pdf")

        else:
            raise Exception(
                "Unsupported file type. Only PDF and Word documents are supported.")

        # Clean text
        cleaned_text = os.linesep.join(
            [s for s in extracted_text.splitlines() if s.strip()])

        if not cleaned_text.strip():
            raise Exception("No text content found in the document")

        return cleaned_text

    except Exception as e:
        raise Exception(
            f"Error extracting text from {file_extension} file: {str(e)}")


def determine_program_level(candidate_data: dict, cv_analysis: dict = None, cv_text: str = None) -> str:
    """
    Determine the appropriate program level based on candidate data and CV analysis

    Priority order:
    1. User explicit preference (undergraduate/postgraduate)  
    2. LLM CV analysis results (education_level)
    3. Academic background field logic (bachelor_major field - legacy name)

    Args:
        candidate_data: Candidate info including education_level_preference and academic background
        cv_analysis: LLM CV analysis results (preferred method)
        cv_text: CV text for fallback analysis (deprecated, not used)

    Returns:
        Program level: 'Undergraduate', 'Postgraduate', or None (for all levels)
    """
    # Check explicit preference first
    education_preference = candidate_data.get(
        'education_level_preference', 'auto')

    print(f"DEBUG: education_level_preference = '{education_preference}'")
    print(f"DEBUG: candidate_data keys = {list(candidate_data.keys())}")

    if education_preference == 'undergraduate':
        print("DEBUG: Returning 'Undergraduate'")
        return 'Undergraduate'
    elif education_preference == 'postgraduate':
        print("DEBUG: Returning 'Postgraduate'")
        return 'Postgraduate'
    elif education_preference == 'auto':
        # Use LLM analysis if available
        if cv_analysis and cv_analysis.get('education_level'):
            detected_level = cv_analysis.get('education_level')
            if detected_level == 'high_school':
                return 'Undergraduate'
            elif detected_level == 'undergraduate':
                return 'Undergraduate'
            elif detected_level == 'postgraduate':
                return 'Postgraduate'

        # Note: Old keyword-based extraction removed - relying on LLM analysis

        # Final fallback: academic background logic
        academic_background = candidate_data.get('bachelor_major', '').strip()
        if not academic_background:  # No academic background specified
            return 'Undergraduate'  # Default to undergraduate
        else:  # Has academic background, may suggest postgraduate
            return 'Postgraduate'

    return None  # Return all levels


app = FastAPI(title="Alex Study Program Matching System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 临时允许所有来源，解决CORS问题
    allow_credentials=False,  # 当allow_origins为*时，credentials必须为False
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册用户管理路由
app.include_router(user_router)


@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests"""
    return Response(status_code=200)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/match")
async def match(c: Candidate, current_user: dict = Depends(get_current_active_user)):
    """
    Quick Match - Return top 3 programs (default view)
    """
    try:
        # Determine appropriate program level
        candidate_dict = c.dict() if hasattr(c, 'dict') else c.__dict__
        cv_analysis = getattr(c, 'cv_analysis', None) or {}
        program_level = determine_program_level(candidate_dict, cv_analysis)

        # Build search query based on interests
        q = " OR ".join((c.interests or [])) or "*"

        # Extract Q&A and CV analysis from candidate data
        qa_answers = getattr(c, 'qa_answers', None) or {}
        cv_analysis = getattr(c, 'cv_analysis', None) or {}

        print(f"Received candidate data: {c}")
        print(f"Determined program level: {program_level}")
        print(f"Q&A answers: {qa_answers}")
        print(f"CV analysis: {cv_analysis}")

        # Use Prompt Flow for matching
        results = await flow_matcher.match_programs(
            candidate=c,
            query=q,
            top_k=1,  # Quick match shows top 3 eligible programs
            level=program_level,
            qa_answers=qa_answers,
            cv_analysis=cv_analysis
        )

        # Format output
        formatted_results = []
        for result in results:
            formatted_results.append({
                "program": result.get("program_name"),
                "university": result.get("university"),
                "score": result.get("overall_score"),
                "detailed_scores": result.get("detailed_scores"),
                "reasoning": result.get("reasoning", {}).get("overall_assessment", ""),
                "strengths": result.get("strengths", []),
                "red_flags": result.get("red_flags", []),
                "url": result.get("program_url")
            })

        return formatted_results[:3]

    except Exception as e:
        print(f"Error in /match endpoint: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/match/detailed")
async def match_detailed(c: Candidate, current_user: dict = Depends(get_current_active_user)):
    """
    Detailed Analysis - Comprehensive evaluation of all programs in appropriate level, show eligible + rejected
    """
    try:
        # Determine appropriate program level
        candidate_dict = c.dict() if hasattr(c, 'dict') else c.__dict__
        cv_analysis = getattr(c, 'cv_analysis', None) or {}
        program_level = determine_program_level(candidate_dict, cv_analysis)

        # Build search query based on interests
        q = " OR ".join((c.interests or [])) or "*"

        # Extract Q&A and CV analysis from candidate data
        qa_answers = getattr(c, 'qa_answers', None) or {}
        cv_analysis = getattr(c, 'cv_analysis', None) or {}

        print(f"Detailed match - Received candidate data: {c}")
        print(f"Determined program level: {program_level}")
        print(f"Q&A answers: {qa_answers}")
        print(f"CV analysis: {cv_analysis}")

        results = await flow_matcher.match_programs_with_rejected(
            candidate=c,
            query=q,
            top_k=11,  # 评估所有相关级别的项目
            level=program_level,  # 保持级别过滤
            qa_answers=qa_answers,
            cv_analysis=cv_analysis
        )

        return {
            "eligible_matches": results["eligible"],
            "rejected_matches": results["rejected"],
            "total_evaluated": len(results["eligible"]) + len(results["rejected"])
        }

    except Exception as e:
        print(f"Error in /match/detailed endpoint: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/match/all")
async def match_all(c: Candidate, current_user: dict = Depends(get_current_active_user)):
    """
    Complete Analysis - Random selection of 6 programs from all levels, show eligible + rejected
    """
    try:
        # Determine appropriate program level
        candidate_dict = c.dict() if hasattr(c, 'dict') else c.__dict__
        cv_analysis = getattr(c, 'cv_analysis', None) or {}
        program_level = determine_program_level(candidate_dict, cv_analysis)

        # Build search query based on interests
        q = " OR ".join((c.interests or [])) or "*"

        # Extract Q&A and CV analysis from candidate data
        qa_answers = getattr(c, 'qa_answers', None) or {}
        cv_analysis = getattr(c, 'cv_analysis', None) or {}

        print(f"Complete analysis - Received candidate data: {c}")
        print(f"Determined program level: {program_level}")
        print(f"Q&A answers: {qa_answers}")
        print(f"CV analysis: {cv_analysis}")

        results = await flow_matcher.match_programs_with_rejected(
            candidate=c,
            query=q,
            top_k=6,  # 随机取6个项目进行分析
            level=None,  # Complete Analysis评估所有级别的项目
            qa_answers=qa_answers,
            cv_analysis=cv_analysis
        )

        return {
            "eligible_matches": results["eligible"],
            "rejected_matches": results["rejected"],
            "total_evaluated": len(results["eligible"]) + len(results["rejected"])
        }

    except Exception as e:
        print(f"Error in /match/all endpoint: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/upload-cv")
async def upload_cv(
    cv: UploadFile = File(...),
    candidate_data: str = Form(...),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Upload CV file and store it for processing
    """
    try:
        # Validate file type
        allowed_types = ['application/pdf', 'application/msword',
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if cv.content_type not in allowed_types:
            return {
                "success": False,
                "error": "Unsupported file type. Please upload PDF or Word documents."
            }

        # Validate file size (5MB limit)
        if cv.size > 5 * 1024 * 1024:
            return {
                "success": False,
                "error": "File size cannot exceed 5MB"
            }

        # Create upload directory
        upload_dir = "uploads/cv"
        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(cv.filename)[1]
        filename = f"{file_id}{file_extension}"
        file_path = os.path.join(upload_dir, filename)

        # Save file
        with open(file_path, "wb") as buffer:
            content = await cv.read()
            buffer.write(content)

        # Parse candidate data
        import json
        candidate = json.loads(candidate_data)

        # Only perform text extraction, no AI analysis
        try:
            extracted_text = extract_cv_text(file_path)

            extracted_info = {
                "status": "text_extracted",
                "extracted_text": extracted_text,
                "text_length": len(extracted_text),
                "file_path": file_path
            }

        except Exception as e:
            print(f"CV text extraction failed: {e}")
            extracted_info = {
                "status": "error",
                "error": f"CV text extraction failed: {str(e)}",
                "file_path": file_path
            }

        # Record upload information
        upload_info = {
            "file_id": file_id,
            "original_filename": cv.filename,
            "file_path": file_path,
            "file_size": cv.size,
            "content_type": cv.content_type,
            "upload_time": datetime.now().isoformat(),
            "candidate_info": {
                "bachelor_major": candidate.get("bachelor_major"),
                "interests": candidate.get("interests", []),
                "city_pref": candidate.get("city_pref", [])
            },
            "extracted_cv_info": extracted_info
        }

        return {
            "success": True,
            "message": "CV upload successful",
            "file_id": file_id,
            "upload_info": upload_info
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Upload failed: {str(e)}"
        }


@app.post("/analyze-cv")
async def analyze_cv(
    file_id: str = Form(...),
    candidate_data: str = Form(...),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Perform AI analysis on uploaded CV
    """
    try:
        # Parse candidate data
        import json
        candidate = json.loads(candidate_data)

        # Build file path
        upload_dir = "uploads/cv"
        # Need to find file based on file_id, simplified processing, assume file path can be reconstructed
        import glob
        files = glob.glob(f"{upload_dir}/{file_id}.*")
        if not files:
            return {
                "success": False,
                "error": "Uploaded file not found"
            }

        file_path = files[0]

        # Re-extract text (can be optimized with caching)
        extracted_text = extract_cv_text(file_path)

        # Use advanced LLM-based CV analysis
        try:
            print(f"Starting LLM-based CV analysis...")
            print(f"CV text length: {len(extracted_text)} characters")

            # Import the new CV analyzer
            from cv_analyzer import cv_analyzer

            # Run LLM analysis on the full CV text
            print("Running comprehensive LLM analysis...")
            analysis_result = await cv_analyzer.analyze_cv(
                cv_text=extracted_text,
                candidate_info=candidate
            )

            print(f"LLM analysis completed!")
            print(
                f"- Education level: {analysis_result.get('education_level')}")
            print(
                f"- Work experience: {analysis_result.get('work_experience', {}).get('has_experience')}")
            print(
                f"- Questions generated: {len(analysis_result.get('personalized_questions', []))}")
            print(
                f"- Confidence score: {analysis_result.get('confidence_score')}")

            # Build analysis metadata for frontend
            analysis_metadata = {
                "analysis_method": "LLM Analysis",
                "flow_used": "cv_analysis_flow",
                "text_length": len(extracted_text),
                "confidence_score": analysis_result.get('confidence_score', 0.8),
                "detected_education_level": analysis_result.get('education_level'),
                "work_experience_detected": analysis_result.get('work_experience', {}).get('has_experience', False),
                "gaps_detected": analysis_result.get('gaps_analysis', {}).get('has_gaps', False)
            }

            # Format the questions for frontend compatibility
            generated_questions = {
                "questions": analysis_result.get('personalized_questions', []),
                "analysis_summary": analysis_result.get('analysis_summary', 'CV analysis completed'),
                "analysis_type": "llm_comprehensive"
            }

            # Comprehensive AI analysis result
            ai_analysis = {
                "analysis_type": "llm_comprehensive",
                "education_analysis": analysis_result.get('education_details', {}),
                "work_experience_analysis": analysis_result.get('work_experience', {}),
                "gaps_analysis": analysis_result.get('gaps_analysis', {}),
                "confidence_score": analysis_result.get('confidence_score', 0.8),
                "text_processed": True
            }

            return {
                "success": True,
                "ai_analysis": ai_analysis,
                "generated_questions": generated_questions,
                "analysis_metadata": analysis_metadata,
                "file_id": file_id
            }

        except Exception as ai_error:
            print(f"AI analysis failed: {ai_error}")
            print(f"Error type: {type(ai_error)}")
            print(f"Error details: {str(ai_error)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")

            # Return default questions
            return {
                "success": True,
                "ai_analysis_error": f"AI analysis failed: {str(ai_error)}",
                "generated_questions": {
                    "questions": [
                        {
                            "id": "fallback_question_1",
                            "question": "Please briefly introduce your professional background and learning goals?",
                            "placeholder": "Please describe your work experience, skills and learning goals",
                            "required": False,
                            "reason": "Help understand your basic situation"
                        },
                        {
                            "id": "fallback_question_2",
                            "question": "What major do you want to study in New Zealand? Why did you choose this direction?",
                            "placeholder": "Please explain your areas of interest and reasons",
                            "required": False,
                            "reason": "Help match suitable courses"
                        }
                    ],
                    "analysis_summary": "Since AI analysis is temporarily unavailable, we provide some general questions to help with matching",
                    "priority_areas": ["Professional background", "Learning goals"]
                },
                "file_id": file_id
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }


@app.post("/api/qa-assistant/conversation")
async def qa_conversation(
    request_data: dict,
    current_user: dict = Depends(get_current_active_user)
):
    """
    QA助手智能对话处理
    """
    try:
        # 延迟导入QA助手
        global qa_assistant
        if qa_assistant is None:
            try:
                from qa_assistant import QAAssistant
                qa_assistant = QAAssistant()
            except Exception as import_error:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=500,
                    detail=f"QA Assistant not available: {str(import_error)}"
                )

        conversation_history = request_data.get(
            "conversation_history", {"messages": []})
        user_message = request_data.get("user_message", "")
        cv_analysis = request_data.get("cv_analysis", {})
        session_state = request_data.get("session_state", {})

        # 调用智能QA助手处理对话
        result = await qa_assistant.process_conversation(
            conversation_history=conversation_history,
            user_message=user_message,
            cv_analysis=cv_analysis,
            session_state=session_state
        )

        return result

    except Exception as e:
        print(f"Error in QA conversation processing: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"Conversation processing failed: {str(e)}"
        )


@app.post("/api/qa-assistant/generate-report")
async def generate_qa_report(
    request_data: dict,
    current_user: dict = Depends(get_current_active_user)
):
    """
    QA助手生成个性化留学报告
    """
    try:
        # 延迟导入QA助手
        global qa_assistant
        if qa_assistant is None:
            try:
                from qa_assistant import QAAssistant
                qa_assistant = QAAssistant()
            except Exception as import_error:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=500,
                    detail=f"QA Assistant not available: {str(import_error)}"
                )

        cv_analysis = request_data.get("cv_analysis", {})
        conversation_history = request_data.get("conversation_history", {})
        user_id = request_data.get(
            "user_id", current_user.get("id", "unknown"))
        report_content = request_data.get("report_content", None)
        matched_programs = request_data.get("matched_programs", None)

        # 调用QA助手生成报告
        result = await qa_assistant.generate_report(
            cv_analysis=cv_analysis,
            conversation_history=conversation_history,
            user_id=str(user_id),
            report_content=report_content,
            matched_programs=matched_programs
        )

        return result

    except Exception as e:
        print(f"Error in QA assistant report generation: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )


@app.get("/api/reports/{filename}")
async def serve_report(filename: str):
    """
    提供PDF报告下载服务
    """
    try:
        reports_dir = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "..", "reports")
        file_path = os.path.join(reports_dir, filename)

        if not os.path.exists(file_path):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Report not found")

        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/pdf'
        )

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"Error serving report: {str(e)}"
        )
