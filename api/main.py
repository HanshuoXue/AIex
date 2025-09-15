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

# CV 文本提取函数


def extract_cv_text(file_path: str) -> str:
    """
    从 PDF 或 Word 文档中提取文本内容
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
            # 对于 .doc 文件，需要更复杂的处理
            # 暂时返回错误信息
            raise Exception(
                "Unsupported .doc format. Please convert to .docx or .pdf")

        else:
            raise Exception(
                "Unsupported file type. Only PDF and Word documents are supported.")

        # 清理文本
        cleaned_text = os.linesep.join(
            [s for s in extracted_text.splitlines() if s.strip()])

        if not cleaned_text.strip():
            raise Exception("No text content found in the document")

        return cleaned_text

    except Exception as e:
        raise Exception(
            f"Error extracting text from {file_extension} file: {str(e)}")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://red-sand-0d1794703.2.azurestaticapps.net",  # Production URL
        "http://localhost:3000",  # Local development
        "http://127.0.0.1:3000",  # Alternative localhost
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
    return {"status": "healthy", "version": "1.2"}


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
        # Build search query
        q = " OR ".join((c.interests or ["Master"])) or "Master"

        # Extract Q&A and CV analysis from candidate data
        qa_answers = getattr(c, 'qa_answers', None) or {}
        cv_analysis = getattr(c, 'cv_analysis', None) or {}

        print(f"Received candidate data: {c}")
        print(f"Q&A answers: {qa_answers}")
        print(f"CV analysis: {cv_analysis}")

        # Use Prompt Flow for matching
        results = await flow_matcher.match_programs(
            candidate=c,
            query=q,
            top_k=1,  # Show top 3 by default
            level=None,
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
        q = " OR ".join((c.interests or ["Master"])) or "Master"

        # Extract Q&A and CV analysis from candidate data
        qa_answers = getattr(c, 'qa_answers', None) or {}
        cv_analysis = getattr(c, 'cv_analysis', None) or {}

        print(f"Detailed match - Received candidate data: {c}")
        print(f"Q&A answers: {qa_answers}")
        print(f"CV analysis: {cv_analysis}")

        results = await flow_matcher.match_programs_fixed_serial(
            candidate=c,
            query=q,
            top_k=3,
            level=None,
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
        q = " OR ".join((c.interests or ["Master"])) or "Master"

        # Extract Q&A and CV analysis from candidate data
        qa_answers = getattr(c, 'qa_answers', None) or {}
        cv_analysis = getattr(c, 'cv_analysis', None) or {}

        print(f"Complete analysis - Received candidate data: {c}")
        print(f"Q&A answers: {qa_answers}")
        print(f"CV analysis: {cv_analysis}")

        results = await flow_matcher.match_programs_with_rejected(
            candidate=c,
            query=q,
            top_k=5,
            level=None,
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
        # 验证文件类型
        allowed_types = ['application/pdf', 'application/msword',
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if cv.content_type not in allowed_types:
            return {
                "success": False,
                "error": "不支持的文件类型。请上传 PDF 或 Word 文档。"
            }

        # 验证文件大小 (5MB 限制)
        if cv.size > 5 * 1024 * 1024:
            return {
                "success": False,
                "error": "文件大小不能超过 5MB"
            }

        # 创建上传目录
        upload_dir = "uploads/cv"
        os.makedirs(upload_dir, exist_ok=True)

        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(cv.filename)[1]
        filename = f"{file_id}{file_extension}"
        file_path = os.path.join(upload_dir, filename)

        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await cv.read()
            buffer.write(content)

        # 解析候选人数据
        import json
        candidate = json.loads(candidate_data)

        # 只进行文本提取，不做AI分析
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

        # 记录上传信息
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
            "message": "CV 上传成功",
            "file_id": file_id,
            "upload_info": upload_info
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"上传失败: {str(e)}"
        }


@app.post("/analyze-cv")
async def analyze_cv(
    file_id: str = Form(...),
    candidate_data: str = Form(...)
):
    """
    对已上传的CV进行AI分析
    """
    try:
        # 解析候选人数据
        import json
        candidate = json.loads(candidate_data)

        # 构建文件路径
        upload_dir = "uploads/cv"
        # 这里需要根据file_id找到文件，简化处理，假设文件路径可以重构
        import glob
        files = glob.glob(f"{upload_dir}/{file_id}.*")
        if not files:
            return {
                "success": False,
                "error": "找不到上传的文件"
            }

        file_path = files[0]

        # 重新提取文本（可以缓存优化）
        extracted_text = extract_cv_text(file_path)

        # 使用 Prompt Flow 进行 AI 分析
        try:
            # 检查环境变量
            print(
                f"AZURE_OPENAI_KEY exists: {bool(os.getenv('AZURE_OPENAI_KEY'))}")
            print(
                f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")

            from promptflow.client import PFClient
            pf_client = PFClient()

            # 运行 CV 分析流程
            cv_flow_path = os.path.join(
                os.path.dirname(__file__), "flows", "chat_rag")
            result = pf_client.test(
                flow=cv_flow_path,
                inputs={
                    "extracted_text": extracted_text,
                    "candidate_data": candidate
                }
            )

            # 解析 AI 分析结果和生成的问题
            ai_analysis = result.get("extracted_info", {})
            generated_questions = result.get("generated_questions", {})

            print(f"Prompt Flow 结果: {result}")
            print(f"AI 分析结果: {ai_analysis}")
            print(f"生成的问题: {generated_questions}")

            return {
                "success": True,
                "ai_analysis": ai_analysis,
                "generated_questions": generated_questions,
                "file_id": file_id
            }

        except Exception as ai_error:
            print(f"AI analysis failed: {ai_error}")
            print(f"Error type: {type(ai_error)}")
            print(f"Error details: {str(ai_error)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")

            # 返回默认问题
            return {
                "success": True,
                "ai_analysis_error": f"AI analysis failed: {str(ai_error)}",
                "generated_questions": {
                    "questions": [
                        {
                            "id": "fallback_question_1",
                            "question": "请简单介绍一下您的职业背景和学习目标？",
                            "placeholder": "请描述您的工作经验、技能和学习目标",
                            "required": True,
                            "reason": "帮助了解您的基本情况"
                        },
                        {
                            "id": "fallback_question_2",
                            "question": "您希望在新西兰学习什么专业？为什么选择这个方向？",
                            "placeholder": "请说明您感兴趣的专业领域和原因",
                            "required": True,
                            "reason": "帮助匹配合适的课程"
                        }
                    ],
                    "analysis_summary": "由于 AI 分析暂时不可用，我们提供了一些通用问题来帮助匹配",
                    "priority_areas": ["职业背景", "学习目标"]
                },
                "file_id": file_id
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"分析失败: {str(e)}"
        }
