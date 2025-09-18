"""
CV Analyzer using Prompt Flow LLM
Replaces keyword-based analysis with intelligent LLM analysis
"""

import os
import sys
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Add the current directory to sys.path to enable relative imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

logger = logging.getLogger(__name__)


class CVAnalyzer:
    def __init__(self):
        """Initialize CV Analyzer with Prompt Flow"""
        self.flow_path = os.path.join(
            os.path.dirname(__file__), "flows", "cv_analysis")
        self._flow = None

    def _get_flow(self):
        """Get or create the prompt flow instance"""
        if self._flow is None:
            try:
                from promptflow import load_flow
                self._flow = load_flow(self.flow_path)
                logger.info(f"CV Analysis flow loaded from: {self.flow_path}")
            except Exception as e:
                logger.error(f"Failed to load CV analysis flow: {e}")
                raise e
        return self._flow

    async def analyze_cv(self, cv_text: str, candidate_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze CV using LLM instead of keyword matching

        Args:
            cv_text: Full CV text content
            candidate_info: Additional candidate information from form

        Returns:
            Structured analysis results including education level, work experience, gaps, and questions
        """
        try:
            # Prepare inputs
            inputs = {
                "cv_text": cv_text,
                "candidate_info": candidate_info or {}
            }

            # Run the flow
            flow = self._get_flow()
            result = flow(**inputs)

            # Parse the result
            if isinstance(result, dict) and "cv_analysis_result" in result:
                analysis_result = result["cv_analysis_result"]

                # If result is a string (JSON), parse it
                if isinstance(analysis_result, str):
                    import json
                    try:
                        analysis_result = json.loads(analysis_result)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON result: {e}")
                        return self._get_fallback_analysis(cv_text)

                # Validate and return structured result
                return self._validate_analysis_result(analysis_result)
            else:
                logger.error(f"Unexpected flow result format: {result}")
                return self._get_fallback_analysis(cv_text)

        except Exception as e:
            logger.error(f"CV analysis failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return self._get_fallback_analysis(cv_text)

    def _validate_analysis_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize the analysis result"""
        validated_result = {
            "education_level": result.get("education_level", "unknown"),
            "education_details": result.get("education_details", {}),
            "work_experience": result.get("work_experience", {
                "has_experience": False,
                "years_of_experience": 0,
                "experience_level": "none",
                "relevant_industries": [],
                "key_skills": [],
                "job_titles": []
            }),
            "gaps_analysis": result.get("gaps_analysis", {
                "has_gaps": False,
                "gap_types": [],
                "gap_duration": "",
                "gap_explanation": ""
            }),
            "personalized_questions": result.get("personalized_questions", []),
            "analysis_summary": result.get("analysis_summary", "CV analysis completed"),
            "confidence_score": result.get("confidence_score", 0.8)
        }

        # Ensure personalized_questions has the right format
        questions = validated_result["personalized_questions"]
        if not isinstance(questions, list):
            questions = []

        # Format questions for the frontend
        formatted_questions = []
        for i, q in enumerate(questions[:2]):  # Limit to 2 questions
            if isinstance(q, dict):
                formatted_questions.append({
                    "id": q.get("id", f"llm_question_{i+1}"),
                    "question": q.get("question", "Please tell us more about your background"),
                    "placeholder": q.get("placeholder", "Please provide more details"),
                    "required": False,
                    "reason": q.get("reason", "Help us understand your profile better")
                })

        validated_result["personalized_questions"] = formatted_questions
        return validated_result

    def _get_fallback_analysis(self, cv_text: str) -> Dict[str, Any]:
        """Provide fallback analysis when LLM analysis fails"""
        # Simple keyword-based fallback
        cv_lower = cv_text.lower()

        # Basic education level detection
        if any(keyword in cv_lower for keyword in ["high school", "secondary school", "高中"]):
            education_level = "high_school"
        elif any(keyword in cv_lower for keyword in ["master", "phd", "硕士", "博士"]):
            education_level = "postgraduate"
        elif any(keyword in cv_lower for keyword in ["bachelor", "university", "college"]):
            education_level = "undergraduate"
        else:
            education_level = "unknown"

        # Basic work experience detection
        has_experience = any(keyword in cv_lower for keyword in [
                             "work", "job", "experience", "company", "工作"])

        return {
            "education_level": education_level,
            "education_details": {
                "highest_qualification": "Unknown",
                "institution": "Unknown",
                "graduation_year": None,
                "gpa_or_grades": None,
                "current_status": "unknown"
            },
            "work_experience": {
                "has_experience": has_experience,
                "years_of_experience": 1 if has_experience else 0,
                "experience_level": "entry" if has_experience else "none",
                "relevant_industries": [],
                "key_skills": [],
                "job_titles": []
            },
            "gaps_analysis": {
                "has_gaps": False,
                "gap_types": [],
                "gap_duration": "",
                "gap_explanation": "Analysis not available"
            },
            "personalized_questions": [
                {
                    "id": "fallback_question_1",
                    "question": "Could you tell us more about your educational background and goals?",
                    "placeholder": "Please describe your education and what you hope to achieve",
                    "required": False,
                    "reason": "Help us understand your academic journey"
                },
                {
                    "id": "fallback_question_2",
                    "question": "What specific field or area would you like to focus on in your studies?",
                    "placeholder": "Please describe your areas of interest and career goals",
                    "required": False,
                    "reason": "Help us match you with suitable programs"
                }
            ],
            "analysis_summary": "Basic analysis completed using fallback method. LLM analysis was not available.",
            "confidence_score": 0.3
        }


# Global CV analyzer instance
cv_analyzer = CVAnalyzer()
