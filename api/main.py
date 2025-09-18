# api/main.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
from datetime import datetime
try:
    from .match_flow import flow_matcher, Candidate
except ImportError:
    from match_flow import flow_matcher, Candidate

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


def extract_education_level(cv_text: str) -> str:
    """
    Extract education level from CV text

    Args:
        cv_text: CV text content

    Returns:
        Education level: 'undergraduate', 'postgraduate', or 'unknown'
    """
    import re

    cv_text_lower = cv_text.lower()

    # Postgraduate indicators (stronger signals)
    postgraduate_patterns = [
        r'\b(?:master|masters|master\'s|msc|ma|mba|phd|doctorate|graduate)\b',
        r'\b(?:postgraduate|post-graduate)\b',
        r'(?:硕士|研究生|博士|学士后)',
        r'\b(?:bachelor.*degree.*completed|graduated.*bachelor)\b',
        r'\b(?:university.*graduate|college.*graduate)\b.*(?:20\d{2}|19\d{2})',
        # Work experience patterns suggesting bachelor's completion
        r'(?:software engineer|developer|analyst|consultant).*(?:20\d{2}|experience)',
    ]

    # Undergraduate indicators
    undergraduate_patterns = [
        r'\b(?:high school|secondary school|a-level|ib|diploma)\b',
        r'\b(?:year 12|year 13|grade 12)\b',
        r'(?:高中|中学|高等中学|高级中学)',
        r'\b(?:currently.*bachelor|pursuing.*bachelor|studying.*bachelor)\b',
        r'\b(?:freshman|sophomore|junior|senior).*(?:student|year)\b',
    ]

    # Check for postgraduate indicators
    postgrad_score = 0
    for pattern in postgraduate_patterns:
        matches = len(re.findall(pattern, cv_text_lower))
        postgrad_score += matches

    # Check for undergraduate indicators
    undergrad_score = 0
    for pattern in undergraduate_patterns:
        matches = len(re.findall(pattern, cv_text_lower))
        undergrad_score += matches

    # Decision logic
    if postgrad_score > undergrad_score and postgrad_score > 0:
        return 'postgraduate'
    elif undergrad_score > 0:
        return 'undergraduate'
    else:
        return 'unknown'


def extract_work_experience_keywords(cv_text: str) -> str:
    """
    Extract work experience related keywords from CV text

    Args:
        cv_text: CV text content

    Returns:
        Extracted work experience keywords string
    """
    import re

    # Work experience related keyword patterns
    work_patterns = [
        # English keywords
        r'\b(?:work|working|worked|employment|employed|job|position|role|career)\b',
        r'\b(?:experience|experiences|professional|occupation|industry)\b',
        r'\b(?:company|corporation|firm|organization|startup|enterprise)\b',
        r'\b(?:manager|developer|engineer|analyst|consultant|specialist|director)\b',
        r'\b(?:intern|internship|volunteer|project|team|lead|senior|junior)\b',

        # Chinese keywords
        r'(?:工作|就业|职业|岗位|职位|角色|经历)',
        r'(?:公司|企业|机构|组织|团队|部门)',
        r'(?:经理|开发|工程师|分析师|顾问|专家|主管)',
        r'(?:实习|项目|负责|参与|管理|领导)',
    ]

    extracted_keywords = set()
    cv_text_lower = cv_text.lower()

    # Extract matching keywords
    for pattern in work_patterns:
        matches = re.findall(pattern, cv_text_lower, re.IGNORECASE)
        extracted_keywords.update(matches)

    # Extract additional work-related proper nouns (company names, tech stack, etc.)
    # Find possible company names (words starting with capital letters)
    company_pattern = r'\b[A-Z][a-zA-Z]{2,}\s*(?:Inc|Corp|Ltd|LLC|Technology|Tech|Software|Systems|Solutions|Group|Company)?\b'
    company_matches = re.findall(company_pattern, cv_text)

    # Technology-related keywords
    tech_patterns = [
        r'\b(?:Python|Java|JavaScript|C\+\+|React|Node\.js|SQL|AWS|Azure|Docker)\b',
        r'\b(?:machine learning|artificial intelligence|data science|backend|frontend)\b',
        r'\b(?:agile|scrum|git|github|database|API|microservices|cloud)\b'
    ]

    for pattern in tech_patterns:
        tech_matches = re.findall(pattern, cv_text, re.IGNORECASE)
        extracted_keywords.update([match.lower() for match in tech_matches])

    # Limit keyword count to avoid overly long queries
    keywords_list = list(extracted_keywords)[:10]  # Maximum 10 keywords

    return ' '.join(keywords_list)


def determine_program_level(candidate_data: dict, cv_text: str = None) -> str:
    """
    Determine the appropriate program level based on candidate data and CV analysis

    Args:
        candidate_data: Candidate information dictionary
        cv_text: CV text for analysis (optional)

    Returns:
        Program level: 'Undergraduate', 'Postgraduate', or None (for all levels)
    """
    # Check explicit preference first
    education_preference = candidate_data.get(
        'education_level_preference', 'auto')

    if education_preference == 'undergraduate':
        return 'Undergraduate'
    elif education_preference == 'postgraduate':
        return 'Postgraduate'
    elif education_preference == 'auto':
        # Auto-detect from CV if available
        if cv_text:
            detected_level = extract_education_level(cv_text)
            if detected_level == 'undergraduate':
                return 'Undergraduate'
            elif detected_level == 'postgraduate':
                return 'Postgraduate'

        # Fallback to bachelor_major logic
        bachelor_major = candidate_data.get('bachelor_major', '').strip()
        if not bachelor_major:  # No bachelor's degree mentioned
            return 'Undergraduate'
        else:  # Has bachelor's degree, recommend masters
            return 'Postgraduate'

    return None  # Return all levels


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://red-sand-0d1794703.2.azurestaticapps.net",  # Production URL
        "http://localhost:3000",  # Local development
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://172.23.102.158:3000",  # Network IP
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz():
    return {"ok": True}  # Health check endpoint


@app.get("/health")
def health():
    # Docker health check endpoint
    return {"status": "healthy", "version": "1.3"}


@app.get("/debug")
def debug_info():
    """
    Debug endpoint to check paths and environment
    Returns:
    {
      "current_dir": "/app/api",
      "project_root": "/app",
      "flow_path": "/app/api/flows/program_match",
      "flow_path_exists": false,
      "working_directory": "/app",
      "current_dir_contents": ["main.py", "flows"],
      "flows_exists": true,
      "flows_contents": ["program_match"],
      "root_contents": ["api", "requirements.txt"]
    }
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    flow_path = os.path.join(current_dir, "flows", "program_match")

    debug_info = {
        "current_dir": current_dir,
        "project_root": project_root,
        "flow_path": flow_path,
        "flow_path_exists": os.path.exists(flow_path),
        "working_directory": os.getcwd(),
        "current_dir_contents": [],
        "flows_exists": os.path.exists(os.path.join(current_dir, "flows")),
        "flows_contents": []
    }

    try:
        debug_info["current_dir_contents"] = os.listdir(current_dir)
    except Exception as e:
        debug_info["current_dir_error"] = str(e)

    try:
        flows_dir = os.path.join(current_dir, "flows")
        if os.path.exists(flows_dir):
            debug_info["flows_contents"] = os.listdir(flows_dir)
    except Exception as e:
        debug_info["flows_error"] = str(e)

    try:
        debug_info["root_contents"] = os.listdir(project_root)
    except Exception as e:
        debug_info["root_error"] = str(e)

    return debug_info


@app.get("/debug/search")
def debug_search():
    """Debug Azure Search connection"""
    try:
        programs = flow_matcher.fetch_programs(query="*", top=5)
        return {
            "status": "success",
            "programs_found": len(programs),
            "sample_programs": programs[:2] if programs else []
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }


@app.get("/debug/matcher")
def debug_matcher():
    """Get detailed debug info from PromptFlowMatcher"""
    try:
        try:
            from .match_flow import flow_matcher
        except ImportError:
            from match_flow import flow_matcher
        from datetime import datetime
        return {
            "status": "ok",
            "matcher_debug_info": getattr(flow_matcher, 'debug_info', {}),
            "current_time": str(datetime.now()),
            "environment_variables": {
                "AZURE_OPENAI_KEY": "SET" if os.environ.get("AZURE_OPENAI_KEY") else "NOT SET",
                "AZURE_OPENAI_ENDPOINT": os.environ.get("AZURE_OPENAI_ENDPOINT", "NOT SET")
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "type": type(e).__name__
        }


@app.post("/match")
async def match(c: Candidate):
    """
    Quick Match - Return top 3 programs (default view)
    """
    try:
        # Determine appropriate program level
        candidate_dict = c.dict() if hasattr(c, 'dict') else c.__dict__
        program_level = determine_program_level(candidate_dict)

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
            top_k=1,  # Show top 3 by default
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
async def match_detailed(c: Candidate):
    """
    Detailed Analysis - Serial evaluation of top 3 programs, show eligible + rejected
    """
    try:
        # Determine appropriate program level
        candidate_dict = c.dict() if hasattr(c, 'dict') else c.__dict__
        program_level = determine_program_level(candidate_dict)

        # Build search query based on interests
        q = " OR ".join((c.interests or [])) or "*"

        # Extract Q&A and CV analysis from candidate data
        qa_answers = getattr(c, 'qa_answers', None) or {}
        cv_analysis = getattr(c, 'cv_analysis', None) or {}

        print(f"Detailed match - Received candidate data: {c}")
        print(f"Determined program level: {program_level}")
        print(f"Q&A answers: {qa_answers}")
        print(f"CV analysis: {cv_analysis}")

        results = await flow_matcher.match_programs_fixed_serial(
            candidate=c,
            query=q,
            top_k=3,
            level=program_level,
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

    """
    More Programs - Return next batch of programs after initial results
    """
    q = " OR ".join((c.interests or ["Master"])) or "Master"

    # Get more results
    results = await flow_matcher.match_programs(
        candidate=c,
        query=q,
        top_k=skip + 3,  # Get skip + 3 more
        level=None
    )

    # Return only the "more" results (skip the first ones)
    more_results = results[skip:skip + 3] if len(results) > skip else []

    # Format output
    formatted_results = []
    for result in more_results:
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

    return {
        "programs": formatted_results,
        "has_more": len(results) > skip + 3
    }


@app.post("/match/all")
async def match_all(c: Candidate):
    """
    Complete Analysis - Parallel batch evaluation of top 5 programs, show eligible + rejected
    """
    try:
        # Determine appropriate program level
        candidate_dict = c.dict() if hasattr(c, 'dict') else c.__dict__
        program_level = determine_program_level(candidate_dict)

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
            top_k=5,
            level=program_level,
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
    candidate_data: str = Form(...)
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
    candidate_data: str = Form(...)
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

        # Use simplified RAG analysis
        try:
            print(f"Start simplified RAG analysis...")
            print(f"CV text length: {len(extracted_text)} characters")

            # Import simplified components
            import sys
            import os
            current_dir = os.path.dirname(__file__)
            chat_rag_path = os.path.join(current_dir, "flows", "chat_rag")
            sys.path.insert(0, chat_rag_path)

            from simple_chunker import simple_chunk_by_tokens, get_relevant_chunks_simple, format_chunks_for_llm
            from simple_question_generator import generate_questions_from_chunks

            # 1. Simple token chunking
            print("Step 1: Text chunking...")
            chunks = simple_chunk_by_tokens(
                extracted_text, max_tokens=300, overlap_tokens=50)
            print(f"Generated {len(chunks)} chunks")

            # 2. Extract work experience keywords from CV
            print("Step 2: Extract work experience keywords...")
            work_keywords = extract_work_experience_keywords(extracted_text)
            print(f"Extracted work keywords: {work_keywords}")

            # 2.5. Extract education level from CV
            print("Step 2.5: Extract education level...")
            detected_education_level = extract_education_level(extracted_text)
            print(f"Detected education level: {detected_education_level}")

            # 3. Build enhanced query
            print("Step 3: Build enhanced query...")
            base_query = f"{candidate.get('bachelor_major', '')} {' '.join(candidate.get('interests', []))}"
            query = f"{base_query} {work_keywords}".strip()
            print(f"Final query: {query}")

            # 4. Get relevant chunks
            relevant_chunks = get_relevant_chunks_simple(
                chunks, query, top_k=2)
            print(f"Selected {len(relevant_chunks)} relevant chunks")

            # 5. Format chunks
            formatted_chunks = format_chunks_for_llm(relevant_chunks)

            # 6. Generate questions
            print("Step 5: Generate personalized questions...")
            question_result = generate_questions_from_chunks(
                formatted_chunks, candidate)

            # Build return result
            if question_result.get("status") == "success":
                generated_questions = question_result["data"]
            else:
                generated_questions = question_result.get(
                    "fallback_questions", {})

            # Build analysis metadata
            analysis_metadata = {
                "analysis_method": "Simple RAG",
                "flow_used": "simple_rag_analysis",
                "chunking_method": "fixed_tokens",
                "text_length": len(extracted_text),
                "detected_education_level": detected_education_level,
                "query_info": {
                    "base_query": base_query,
                    "work_keywords_extracted": work_keywords,
                    "final_query": query,
                    "query_enhancement_ratio": len(query.split()) / len(base_query.split()) if base_query.strip() else 1
                },
                "chunk_info": {
                    "total_chunks": len(chunks),
                    "relevant_chunks_used": len(relevant_chunks),
                    "avg_chunk_tokens": sum(chunk['estimated_tokens'] for chunk in chunks) // len(chunks) if chunks else 0,
                    "chunking_successful": True
                },
                "chunk_details": {
                    "all_chunks_summary": [
                        {
                            "id": chunk["id"],
                            "text_preview": chunk["text"][:100] + "..." if len(chunk["text"]) > 100 else chunk["text"],
                            "length": chunk["length"],
                            "estimated_tokens": chunk["estimated_tokens"]
                        } for chunk in chunks[:10]  # Only show first 10 chunks
                    ],
                    "relevant_chunks": [
                        {
                            "id": chunk["id"],
                            "text_preview": chunk["text"][:150] + "..." if len(chunk["text"]) > 150 else chunk["text"],
                            "full_text": chunk["text"],  # Add full text
                            "length": chunk["length"],
                            "estimated_tokens": chunk["estimated_tokens"],
                            "relevance_score": chunk.get("relevance_score", 0),
                            "rank": i + 1
                        } for i, chunk in enumerate(relevant_chunks)
                    ]
                }
            }

            # No longer extract complex AI analysis, directly return basic information
            ai_analysis = {
                "analysis_type": "simple_rag",
                "chunks_analyzed": len(relevant_chunks),
                "text_processed": True
            }

            print(f"Analysis completed!")
            print(f"- Total chunks: {len(chunks)}")
            print(f"- Relevant chunks: {len(relevant_chunks)}")
            print(
                f"- Generated questions: {len(generated_questions.get('questions', []))}")

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
                            "required": True,
                            "reason": "Help understand your basic situation"
                        },
                        {
                            "id": "fallback_question_2",
                            "question": "What major do you want to study in New Zealand? Why did you choose this direction?",
                            "placeholder": "Please explain your areas of interest and reasons",
                            "required": True,
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
