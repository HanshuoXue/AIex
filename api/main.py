# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from .match_flow import flow_matcher, Candidate
except ImportError:
    from match_flow import flow_matcher, Candidate

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
    return {"status": "healthy"}  # Docker health check endpoint

@app.get("/debug")
def debug_info():
    """Debug endpoint to check paths and environment"""
    import os
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

@app.get("/debug/matcher")
def debug_matcher():
    """Get detailed debug info from PromptFlowMatcher"""
    try:
        try:
            from .match_flow import flow_matcher
        except ImportError:
            from match_flow import flow_matcher
        import os
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
    Use Prompt Flow for intelligent matching
    """
    # Build search query
    q = " OR ".join((c.interests or ["Master"])) or "Master"
    
    # Use Prompt Flow for matching
    results = await flow_matcher.match_programs(
        candidate=c,
        query=q,
        top_k=2,  # can return more results
        level=None  # can specify level as needed
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
            "url": result.get("program_url")  # Return program's official URL
        })
    
    return formatted_results[:2]  # Return top 2 results

@app.post("/match/detailed")
async def match_detailed(c: Candidate):
    """
    Return detailed match analysis including all scoring details
    """
    q = " OR ".join((c.interests or ["Master"])) or "Master"
    
    results = await flow_matcher.match_programs(
        candidate=c,
        query=q,
        top_k=5,
        level=None
    )
    
    return results  # Return complete evaluation results

@app.post("/match/all")
async def match_all(c: Candidate):
    """
    Return match analysis for all programs, including rejected programs and exclusion reasons
    """
    q = " OR ".join((c.interests or ["Master"])) or "Master"
    
    results = await flow_matcher.match_programs_with_rejected(
        candidate=c,
        query=q,
        top_k=5,
        level=None
    )
    
    return {
        "eligible_matches": results["eligible"],
        "rejected_matches": results["rejected"],
        "total_evaluated": len(results["eligible"]) + len(results["rejected"])
    }
