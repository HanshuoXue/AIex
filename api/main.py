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
    Quick Match - Return top 3 programs (default view)
    """
    # Build search query
    q = " OR ".join((c.interests or ["Master"])) or "Master"

    # Use Prompt Flow for matching
    results = await flow_matcher.match_programs(
        candidate=c,
        query=q,
        top_k=1,  # Show top 3 by default
        level=None
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


@app.post("/match/detailed")
async def match_detailed(c: Candidate):
    """
    Detailed Analysis - Serial evaluation of top 3 programs, show eligible + rejected
    """
    q = " OR ".join((c.interests or ["Master"])) or "Master"

    results = await flow_matcher.match_programs_fixed_serial(
        candidate=c,
        query=q,
        top_k=3,
        level=None
    )

    return {
        "eligible_matches": results["eligible"],
        "rejected_matches": results["rejected"],
        "total_evaluated": len(results["eligible"]) + len(results["rejected"])
    }

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
