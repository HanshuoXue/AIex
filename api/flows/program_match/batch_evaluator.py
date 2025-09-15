import json
import re
from typing import Dict, Any, List
from promptflow import tool


@tool
def batch_evaluator(llm_response: str, candidate_data: str, programs_data: str) -> List[Dict[str, Any]]:
    """
    Parse LLM response for batch evaluation of multiple programs
    """
    try:
        # Parse candidate and programs data for context
        candidate = json.loads(candidate_data)
        programs = json.loads(programs_data)

        # Try to extract JSON from LLM response
        llm_response = llm_response.strip()

        # Remove markdown code blocks if present
        if llm_response.startswith("```json"):
            llm_response = llm_response[7:]
        if llm_response.startswith("```"):
            llm_response = llm_response[3:]
        if llm_response.endswith("```"):
            llm_response = llm_response[:-3]

        llm_response = llm_response.strip()

        # Parse the JSON response
        parsed_response = json.loads(llm_response)

        # Extract evaluations array
        if "evaluations" in parsed_response:
            evaluations = parsed_response["evaluations"]
        elif isinstance(parsed_response, list):
            evaluations = parsed_response
        else:
            # Single evaluation wrapped in array
            evaluations = [parsed_response]

        # Ensure all required fields and add program metadata
        processed_evaluations = []
        for i, evaluation in enumerate(evaluations):
            # Get corresponding program data
            program = programs[i] if i < len(programs) else {}

            # Ensure required fields exist with defaults
            processed_eval = {
                "program_id": evaluation.get("program_id", program.get("id", f"program_{i}")),
                "program_name": evaluation.get("program_name", program.get("program", "Unknown Program")),
                "university": evaluation.get("university", program.get("university", "Unknown University")),
                "program_url": program.get("url", ""),
                "eligible": evaluation.get("eligible", False),
                "overall_score": max(0, min(100, evaluation.get("overall_score", 0))),
                "detailed_scores": {
                    "academic_fit": max(0, min(35, evaluation.get("detailed_scores", {}).get("academic_fit", 0))),
                    "english_proficiency": max(0, min(25, evaluation.get("detailed_scores", {}).get("english_proficiency", 0))),
                    "field_alignment": max(0, min(20, evaluation.get("detailed_scores", {}).get("field_alignment", 0))),
                    "location_preference": max(0, min(10, evaluation.get("detailed_scores", {}).get("location_preference", 0))),
                    "budget_compatibility": max(0, min(10, evaluation.get("detailed_scores", {}).get("budget_compatibility", 0)))
                },
                "reasoning": evaluation.get("reasoning", {
                    "overall_assessment": "AI evaluation completed"
                }),
                "red_flags": evaluation.get("red_flags", []),
                "strengths": evaluation.get("strengths", [])
            }

            processed_evaluations.append(processed_eval)

        return processed_evaluations

    except json.JSONDecodeError as e:
        print(f"JSON parsing error in batch evaluator: {e}")
        print(f"LLM Response: {llm_response}")

        # Return fallback evaluations for all programs
        try:
            programs = json.loads(programs_data)
            fallback_evals = []
            for i, program in enumerate(programs):
                fallback_evals.append({
                    "program_id": program.get("id", f"program_{i}"),
                    "program_name": program.get("program", "Unknown Program"),
                    "university": program.get("university", "Unknown University"),
                    "program_url": program.get("url", ""),
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
                        "overall_assessment": f"Batch evaluation parsing error: {str(e)}"
                    },
                    "red_flags": ["Evaluation error"],
                    "strengths": []
                })
            return fallback_evals
        except:
            return []

    except Exception as e:
        print(f"Unexpected error in batch evaluator: {e}")
        return []
