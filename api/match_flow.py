import json
import asyncio
from typing import List, Dict, Any, Optional
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from promptflow.client import PFClient
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path="../.env")

# ---- Candidate Definition ----
class Candidate(BaseModel):
    bachelor_major: str
    gpa_scale: str = "4.0"
    gpa_value: float
    ielts_overall: float
    ielts_subscores: Optional[Dict[str, float]] = None
    work_years: Optional[int] = 0
    interests: List[str] = []
    city_pref: List[str] = []
    budget_nzd_per_year: Optional[float] = None

class PromptFlowMatcher:
    def __init__(self):
        # Initialize Azure Search client (with fallback for missing env vars)
        search_endpoint = os.environ.get("SEARCH_ENDPOINT")
        search_key = os.environ.get("SEARCH_KEY")
        
        if not search_endpoint or not search_key:
            print("Warning: SEARCH_ENDPOINT and SEARCH_KEY environment variables are not set")
            print("Please set these variables for Azure Search functionality")
            self.search_client = None
        else:
            self.search_client = SearchClient(
                endpoint=search_endpoint,
                index_name="nz-programs",
                credential=AzureKeyCredential(search_key)
            )
        
        # Initialize Prompt Flow client
        self.pf_client = PFClient()
        # Use absolute path to ensure correct path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # In production, flows/ is at the same level as api/
        # So we need to go up from api/ to find flows/
        if current_dir.endswith('/api') or 'api' in current_dir:
            # In deployment, api/ and flows/ are siblings
            project_root = os.path.dirname(current_dir) if current_dir.endswith('/api') else current_dir
            self.flow_path = os.path.join(project_root, "flows", "program_match")
        else:
            # Fallback for other environments
            project_root = os.path.dirname(current_dir)
            self.flow_path = os.path.join(project_root, "flows", "program_match")
        
        # Debug: print path information
        print(f"Current dir: {current_dir}")
        print(f"Project root: {project_root}")
        print(f"Flow path: {self.flow_path}")
        print(f"Flow path exists: {os.path.exists(self.flow_path)}")
        
        # Fallback: try different path strategies
        if not os.path.exists(self.flow_path):
            # Try relative from current working directory
            fallback_path = os.path.join(os.getcwd(), "flows", "program_match")
            print(f"Trying fallback path: {fallback_path}")
            if os.path.exists(fallback_path):
                self.flow_path = fallback_path
                print(f"Using fallback path: {self.flow_path}")
            else:
                print(f"WARNING: Flow path not found! Current working directory: {os.getcwd()}")
                # List available directories for debugging
                try:
                    print(f"Available in current dir: {os.listdir('.')}")
                    if os.path.exists('flows'):
                        print(f"Available in flows/: {os.listdir('flows')}")
                except Exception as e:
                    print(f"Error listing directories: {e}")
    
    def fetch_programs(self, query: str = "*", top: int = 50, level: str = None) -> List[Dict]:
        """Get program list"""
        if not self.search_client:
            print("Warning: Azure Search client not initialized. Returning empty results.")
            return []
            
        filt = f"level eq '{level}'" if level else None
        select = ",".join([
            "id","university","program","fields","type","campus","intakes",
            "tuition_nzd_per_year",
            "english_ielts","english_no_band_below",
            "duration_years","level","academic_reqs","other_reqs",
            "url","source_updated"
        ])
        results = self.search_client.search(search_text=query, top=top, filter=filt, select=select)
        return [dict(r) for r in results]
    
    async def evaluate_match(self, candidate: Candidate, program: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use Prompt Flow to evaluate a single candidate-program match
        """
        try:
            # Prepare candidate data
            candidate_data = {
                "bachelor_major": candidate.bachelor_major,
                "gpa_scale": candidate.gpa_scale,
                "gpa_value": candidate.gpa_value,
                "ielts_overall": candidate.ielts_overall,
                "ielts_subscores": candidate.ielts_subscores,
                "work_years": candidate.work_years,
                "interests": candidate.interests,
                "city_pref": candidate.city_pref,
                "budget_nzd_per_year": candidate.budget_nzd_per_year
            }
            
            # Prepare program data
            program_data = {
                "id": program.get("id"),
                "university": program.get("university"),
                "program": program.get("program"),
                "fields": program.get("fields", []),
                "type": program.get("type"),
                "campus": program.get("campus"),
                "tuition_nzd_per_year": program.get("tuition_nzd_per_year"),
                "english_ielts": program.get("english_ielts"),
                "english_no_band_below": program.get("english_no_band_below"),
                "duration_years": program.get("duration_years"),
                "level": program.get("level"),
                "academic_reqs": program.get("academic_reqs", []),
                "other_reqs": program.get("other_reqs", []),
                "url": program.get("url")
            }
            
            # Run the flow using test method
            result = self.pf_client.test(
                flow=self.flow_path,
                inputs={
                    "candidate_profile": json.dumps(candidate_data),
                    "program_details": json.dumps(program_data)
                }
            )
            
            # Extract the match_result from the flow output
            if isinstance(result, dict) and 'match_result' in result:
                return result['match_result']
            else:
                # If result format is unexpected, return the whole result
                return result
            
        except Exception as e:
            # Fallback error response
            return {
                "eligible": False,
                "overall_score": 0,
                "detailed_scores": {
                    "academic_fit": 0,
                    "english_proficiency": 0,
                    "field_alignment": 0,
                    "location_preference": 0,
                    "budget_compatibility": 0
                },
                "reasoning": {
                    "overall_assessment": f"Error during evaluation: {str(e)}"
                },
                "red_flags": [f"Evaluation error: {str(e)}"],
                "strengths": [],
                "error": str(e),
                "program_id": program.get("id"),
                "program_name": program.get("program"),
                "university": program.get("university")
            }
    
    async def match_programs(self, candidate: Candidate, query: str = "*", top_k: int = 2, level: str = None) -> List[Dict[str, Any]]:
        """
        Find and evaluate top matching programs for a candidate
        """
        # Get candidate programs from search
        programs = self.fetch_programs(query=query, top=100, level=level)
        
        # Evaluate each program using Prompt Flow
        evaluations = []
        for program in programs:
            evaluation = await self.evaluate_match(candidate, program)
            if evaluation.get("eligible", False):  # Only include eligible matches
                evaluations.append(evaluation)
        
        # Sort by overall score and return top K
        evaluations.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
        return evaluations[:top_k]
    
    async def match_programs_with_rejected(self, candidate: Candidate, query: str = "*", top_k: int = 5, level: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find and evaluate all programs, returning both eligible and rejected matches
        """
        # Get candidate programs from search
        programs = self.fetch_programs(query=query, top=100, level=level)
        
        # Evaluate each program using Prompt Flow
        eligible_matches = []
        rejected_matches = []
        
        for program in programs:
            evaluation = await self.evaluate_match(candidate, program)
            if evaluation.get("eligible", False):
                eligible_matches.append(evaluation)
            else:
                # Add rejection reason for rejected matches
                evaluation["rejection_reason"] = evaluation.get("reasoning", {}).get("overall_assessment", "Failed AI evaluation screening")
                rejected_matches.append(evaluation)
        
        # Sort both lists by overall score
        eligible_matches.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
        rejected_matches.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
        
        return {
            "eligible": eligible_matches[:top_k],
            "rejected": rejected_matches
        }

# Global instance
flow_matcher = PromptFlowMatcher()
