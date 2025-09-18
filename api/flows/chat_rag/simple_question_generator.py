import os
import json
from typing import Dict, Any, List
from openai import OpenAI

# Azure OpenAI Configuration
model_name = os.getenv("AZURE_OPENAI_MODEL", "gpt-4")
endpoint = os.getenv('AZURE_OPENAI_ENDPOINT').rstrip(
    '/')  # Remove trailing slash
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

client = OpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    base_url=f"{endpoint}/openai/deployments/{model_name}",
    default_query={"api-version": api_version}
)


def generate_questions_from_chunks(relevant_chunks: str, candidate_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate personalized questions based on relevant CV chunks

    Args:
        relevant_chunks: Formatted relevant CV chunks
        candidate_info: Candidate basic information

    Returns:
        Generated questions and analysis
    """

    prompt = f"""You are a professional education consultant. Based on the following CV segments and candidate information, generate 1-2 specific questions to help match suitable New Zealand study programs.

CV related segments:
{relevant_chunks}

Candidate basic information:
- Professional background: {candidate_info.get('bachelor_major', 'Unknown')}
- GPA: {candidate_info.get('gpa_value', 'Unknown')}/{candidate_info.get('gpa_scale', '4.0')}
- IELTS: {candidate_info.get('ielts_overall', 'Unknown')}
- Work experience: {candidate_info.get('work_years', 0)} years
- Interest areas: {', '.join(candidate_info.get('interests', []))}
- Preferred cities: {', '.join(candidate_info.get('city_pref', []))}
- Budget: ${candidate_info.get('budget_nzd_per_year', 'Unknown')} NZD/year

Generation requirements:
1. Questions should be specific and targeted
2. Focus on gaps in CV, skill transitions, career goals
3. Question answers will be directly used for course matching
4. Each question includes the reason for asking

Please return JSON format:
{{
  "questions": [
    {{
      "id": "q1",
      "question": "Specific question content",
      "placeholder": "Answer example",
      "required": false,
      "reason": "Reason for asking"
    }}
  ],
  "analysis_summary": "Brief summary based on CV analysis",
  "key_areas": ["Key areas1", "Key areas2"]
}}"""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3
        )

        result_text = response.choices[0].message.content.strip()

        # Clean possible markdown markers
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]

        result = json.loads(result_text.strip())
        return {
            "status": "success",
            "data": result
        }

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return {
            "status": "error",
            "error": "JSON parsing failed",
            "fallback_questions": get_fallback_questions()
        }
    except Exception as e:
        print(f"Question generation failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "fallback_questions": get_fallback_questions()
        }


def get_fallback_questions() -> Dict[str, Any]:
    """
    Fallback questions when AI generation fails
    """
    return {
        "questions": [
            {
                "id": "fallback_1",
                "question": "Please describe your career development goals and why you chose to study in New Zealand？",
                "placeholder": "For example: I hope to develop in the field of data science, New Zealand's education quality and job opportunities attract me...",
                "required": True,
                "reason": "Understand learning motivation and career planning"
            },
            {
                "id": "fallback_2",
                "question": "What skills or knowledge areas do you think you need to further improve?",
                "placeholder": "For example: I need to improve machine learning algorithms and big data processing skills...",
                "required": True,
                "reason": "Identify skill gaps to match suitable courses"
            }
        ],
        "analysis_summary": "Using general questions for information collection",
        "key_areas": ["Career planning", "Skill improvement"]
    }


if __name__ == "__main__":
    # Test
    test_chunks = """
--- CV segment 1 ---
Length: 200 characters
Content:
WORK EXPERIENCE
Software Engineer
Tech Company
2022-Present
Developed web applications
"""

    test_candidate = {
        "bachelor_major": "computer science",
        "gpa_value": 3.5,
        "ielts_overall": 7.0,
        "work_years": 2,
        "interests": ["machine learning"],
        "city_pref": ["Auckland"],
        "budget_nzd_per_year": 50000
    }

    result = generate_questions_from_chunks(test_chunks, test_candidate)
    print(json.dumps(result, indent=2, ensure_ascii=False))
