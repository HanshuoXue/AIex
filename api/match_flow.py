import json
import asyncio
from typing import List, Dict, Any, Optional
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from promptflow.client import PFClient
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            print(
                "Warning: SEARCH_ENDPOINT and SEARCH_KEY environment variables are not set")
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

        # Super simple path - flows is now in api directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.flow_path = os.path.join(current_dir, "flows", "program_match")

        # Initialize debug info storage
        self.debug_info = {
            "init_time": str(datetime.now()),
            "env_vars": {
                "AZURE_OPENAI_KEY": "SET" if os.environ.get("AZURE_OPENAI_KEY") else "NOT SET",
                "AZURE_OPENAI_ENDPOINT": os.environ.get("AZURE_OPENAI_ENDPOINT", "NOT SET"),
                "SEARCH_ENDPOINT": "SET" if search_endpoint else "NOT SET",
                "SEARCH_KEY": "SET" if search_key else "NOT SET"
            },
            "paths": {
                "current_dir": current_dir,
                "flow_path": self.flow_path,
                "flow_path_exists": os.path.exists(self.flow_path),
                "working_dir": os.getcwd()
            },
            "connection_attempts": [],
            "errors": []
        }

        # Debug: print path and environment information
        logger.info("=== PROMPT FLOW MATCHER INITIALIZATION ===")
        logger.info(f"Current dir: {current_dir}")
        logger.info(f"Flow path: {self.flow_path}")
        logger.info(f"Flow path exists: {os.path.exists(self.flow_path)}")
        logger.info(f"Environment variables: {self.debug_info['env_vars']}")

        # Auto-create Azure OpenAI connection if it doesn't exist
        self._ensure_connection()

        # Final verification
        if not os.path.exists(self.flow_path):
            print(f"ERROR: Flow path not found at {self.flow_path}")
            # List directories for debugging
            try:
                print(f"Current dir contents: {os.listdir(current_dir)}")
                flows_dir = os.path.join(current_dir, "flows")
                if os.path.exists(flows_dir):
                    print(f"flows/ contents: {os.listdir(flows_dir)}")
            except Exception as e:
                print(f"Error listing directories: {e}")

    def _ensure_connection(self):
        """Ensure Azure OpenAI connection exists, create if not (lean version)"""
        # lean version: assume environment variables are set
        from promptflow.entities import AzureOpenAIConnection
        import os
        from pathlib import Path
        import yaml
        from datetime import datetime

        # ensure debug_info won't report KeyError (keep minimal recording ability)
        self.debug_info = getattr(self, "debug_info", {}) or {}
        self.debug_info.setdefault("errors", [])
        self.debug_info.setdefault("connection_attempts", [])

        attempt = {
            "timestamp": str(datetime.now()),
            "success": False,
            "details": {},
            "error": None
        }

        logger.info("=== CONNECTION CHECK START (lean) ===")

        # 1) check existing connections
        connections = self.pf_client.connections.list()
        names = [getattr(c, "name", None) for c in connections]
        attempt["details"]["existing_connections"] = names

        target = "azure_openai_connection"
        if target in names:
            logger.info("✅ Azure OpenAI connection already exists")
            attempt["success"] = True
            attempt["details"]["status"] = "already_exists"
            self.debug_info["connection_attempts"].append(attempt)
            logger.info("=== CONNECTION CHECK END (lean, already_exists) ===")
            return

        logger.info("Azure OpenAI connection NOT found, creating...")

        # 2) create directly by environment variables (no more existence check)
        api_key = os.environ["AZURE_OPENAI_KEY"]
        api_base = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
        api_ver = os.environ.get(
            "AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

        conn = AzureOpenAIConnection(
            name=target,
            api_key=api_key,
            api_base=api_base,
            api_version=api_ver,
        )

        try:
            # 3) first: use SDK create/update
            self.pf_client.connections.create_or_update(conn)
            logger.info("✅ Azure OpenAI connection created via SDK")
            attempt["success"] = True
            attempt["details"]["method"] = "create_or_update"

        except Exception as e:
            # 4) minimal fallback: file method (adapt to no keyring/CI)
            logger.warning(
                f"SDK create_or_update failed, fallback to file: {e}")
            try:
                dir_ = Path.home() / ".promptflow" / "connections"
                dir_.mkdir(parents=True, exist_ok=True)
                file_ = dir_ / f"{target}.yaml"
                data = {
                    "name": target,
                    "type": "azure_open_ai",
                    "configs": {
                        "api_key": api_key,
                        "api_base": api_base,
                        "api_version": api_ver
                    }
                }
                with open(file_, "w", encoding="utf-8") as f:
                    yaml.safe_dump(data, f, sort_keys=False,
                                   allow_unicode=True)
                logger.info(
                    f"✅ Azure OpenAI connection created via file -> {file_}")
                attempt["success"] = True
                attempt["details"]["method"] = "file_method"
                attempt["details"]["file_path"] = str(file_)
            except Exception as fe:
                # keep minimal error recording, but no further checks
                msg = f"create_or_update and file fallback both failed: {fe}"
                logger.error(f"❌ {msg}")
                attempt["error"] = msg

        self.debug_info["connection_attempts"].append(attempt)
        logger.info(
            f"=== CONNECTION CHECK END (lean, success={attempt['success']}) ===")

    def fetch_programs(self, query: str = "*", top: int = 50, level: str = None) -> List[Dict]:
        """Get program list :
        match all programs by default
        default 50 programs
        filter by level if provided
        return list of programs
        """
        if not self.search_client:
            print(
                "Warning: Azure Search client not initialized. Returning empty results.")
            return []

        filt = f"level eq '{level}'" if level else None
        select = ",".join([
            "id", "university", "program", "fields", "type", "campus", "intakes",
            "tuition_nzd_per_year",
            "english_ielts", "english_no_band_below",
            "duration_years", "level", "academic_reqs", "other_reqs",
            "url", "source_updated"
        ])
        results = self.search_client.search(
            search_text=query, top=top, filter=filt, select=select)
        return [dict(r) for r in results]

    async def evaluate_match(self, candidate: Candidate, program: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use Prompt Flow to evaluate a single candidate vs a single program match 1v1
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

            # Try to ensure connection, but don't fail if it doesn't work
            try:
                self._ensure_connection()
            except Exception as conn_error:
                logger.warning(
                    f"Connection setup failed, but continuing: {conn_error}")

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
        QUICK MATCH
        Find and evaluate top matching programs for a candidate (ELIGIBLE ONLY)
        Serial evaluation until finding enough eligible matches
        """
        # Get candidate programs from search
        programs = self.fetch_programs(query=query, top=100, level=level)

        # Evaluate each program using Prompt Flow until we find enough eligible ones
        evaluations = []
        for program in programs:
            evaluation = await self.evaluate_match(candidate, program)
            if evaluation.get("eligible", False):  # Only include eligible matches
                evaluations.append(evaluation)
                # Stop when we have enough eligible matches
                if len(evaluations) >= top_k:
                    break

        # Sort by overall score and return top K
        evaluations.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
        return evaluations[:top_k]

    async def match_programs_fixed_serial(self, candidate: Candidate, query: str = "*", top_k: int = 3, level: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        DETAILED MATCH
        Evaluate fixed number of programs serially, return both eligible and rejected
        For Detailed Analysis - evaluate exactly top_k programs
        """
        # Get candidate programs from search
        programs = self.fetch_programs(query=query, top=100, level=level)

        # Take only the first top_k programs
        programs = programs[:top_k]

        # Evaluate each program serially
        eligible_matches = []
        rejected_matches = []

        for program in programs:
            evaluation = await self.evaluate_match(candidate, program)
            if evaluation.get("eligible", False):
                eligible_matches.append(evaluation)
            else:
                evaluation["rejection_reason"] = evaluation.get("reasoning", {}).get(
                    "overall_assessment", "Failed AI evaluation screening")
                rejected_matches.append(evaluation)

        # Sort both lists by overall score
        eligible_matches.sort(key=lambda x: x.get(
            "overall_score", 0), reverse=True)
        rejected_matches.sort(key=lambda x: x.get(
            "overall_score", 0), reverse=True)

        return {
            "eligible": eligible_matches,
            "rejected": rejected_matches
        }

    async def evaluate_batch_match(self, candidate: Candidate, programs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        BATCH MATCH
        Batch evaluate multiple programs with a single LLM call for better performance
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

            # Prepare programs data with essential info only
            programs_data = []
            for program in programs:
                programs_data.append({
                    "id": program.get("id"),
                    "university": program.get("university"),
                    "program": program.get("program"),
                    "fields": program.get("fields", []),
                    "campus": program.get("campus"),
                    "tuition_nzd_per_year": program.get("tuition_nzd_per_year"),
                    "english_ielts": program.get("english_ielts"),
                    "duration_years": program.get("duration_years"),
                    "level": program.get("level"),
                    "url": program.get("url")
                })

            # Ensure connection
            try:
                self._ensure_connection()
            except Exception as conn_error:
                logger.warning(
                    f"Connection setup failed, but continuing: {conn_error}")

            # Use batch prompt for efficiency
            result = self.pf_client.test(
                flow=self.flow_path,
                inputs={
                    "candidate_profile": json.dumps(candidate_data),
                    "programs_batch": json.dumps(programs_data),
                    "use_batch": "true"  # Flag to use batch processing
                }
            )

            # Parse batch result
            if isinstance(result, dict) and 'batch_evaluations' in result:
                return result['batch_evaluations']
            elif isinstance(result, list):
                return result
            else:
                # Fallback to individual evaluation if batch fails
                logger.warning(
                    "Batch evaluation failed, falling back to individual processing")
                return await self._fallback_individual_evaluation(candidate, programs)

        except Exception as e:
            logger.error(f"Batch evaluation error: {e}")
            # Fallback to individual evaluation
            return await self._fallback_individual_evaluation(candidate, programs)

    async def _fallback_individual_evaluation(self, candidate: Candidate, programs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback to individual evaluation if batch processing fails"""
        evaluations = []
        for program in programs:
            evaluation = await self.evaluate_match(candidate, program)
            evaluations.append(evaluation)
        return evaluations

    async def match_programs_with_rejected(self, candidate: Candidate, query: str = "*", top_k: int = 5, level: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Complete Analysis - Parallel batch evaluation of top programs
        Uses batch processing for maximum speed
        """
        # Get candidate programs from search
        programs = self.fetch_programs(query=query, top=100, level=level)

        # Take exactly top_k programs for batch processing
        programs = programs[:top_k]

        # Use batch evaluation for parallel processing (faster)
        try:
            evaluations = await self.evaluate_batch_match(candidate, programs)
        except Exception as e:
            logger.warning(
                f"Batch evaluation failed, falling back to serial: {e}")
            # Fallback to individual evaluation if batch fails
            evaluations = await self._fallback_individual_evaluation(candidate, programs)

        # Separate eligible and rejected matches
        eligible_matches = []
        rejected_matches = []

        for evaluation in evaluations:
            if evaluation.get("eligible", False):
                eligible_matches.append(evaluation)
            else:
                # Add rejection reason for rejected matches
                evaluation["rejection_reason"] = evaluation.get("reasoning", {}).get(
                    "overall_assessment", "Failed AI evaluation screening")
                rejected_matches.append(evaluation)

        # Sort both lists by overall score
        eligible_matches.sort(key=lambda x: x.get(
            "overall_score", 0), reverse=True)
        rejected_matches.sort(key=lambda x: x.get(
            "overall_score", 0), reverse=True)

        return {
            "eligible": eligible_matches[:top_k],
            "rejected": rejected_matches
        }


# Global instance
flow_matcher = PromptFlowMatcher()
