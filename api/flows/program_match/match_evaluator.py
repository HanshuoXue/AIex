import json
import re
from typing import Dict, Any

try:
    from promptflow.core import tool
except ImportError:
    # Fallback decorator if promptflow is not available
    def tool(func):
        return func

@tool
def match_evaluator(llm_response: str, candidate_data: str, program_data: str) -> Dict[str, Any]:
    """
    Process LLM response and return structured match evaluation
    """
    try:
        # Parse input data
        candidate = json.loads(candidate_data)
        program = json.loads(program_data)
        
        # Extract JSON from LLM response
        json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
        if json_match:
            evaluation = json.loads(json_match.group(1))
        else:
            # Fallback: try to parse the entire response as JSON
            evaluation = json.loads(llm_response)
        
        # Validate and ensure required fields
        required_fields = ['eligible', 'overall_score', 'detailed_scores', 'reasoning']
        for field in required_fields:
            if field not in evaluation:
                raise ValueError(f"Missing required field: {field}")
        
        # Add metadata
        result = {
            **evaluation,
            "program_id": program.get("id"),
            "program_name": program.get("program"),
            "university": program.get("university"),
            "program_url": program.get("url"),
            "candidate_id": candidate.get("id", "unknown"),
            "evaluation_timestamp": None  # Could add timestamp if needed
        }
        
        # Validate score ranges
        if not (0 <= result["overall_score"] <= 100):
            result["overall_score"] = max(0, min(100, result["overall_score"]))
        
        return result
        
    except json.JSONDecodeError as e:
        # Fallback for invalid JSON
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
                "overall_assessment": f"Error parsing LLM response: {str(e)}"
            },
            "red_flags": ["Failed to evaluate match due to parsing error"],
            "strengths": [],
            "error": str(e),
            "raw_response": llm_response
        }
    except Exception as e:
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
            "error": str(e)
        }
