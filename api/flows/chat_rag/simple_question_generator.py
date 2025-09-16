import os
import json
from typing import Dict, Any, List
from openai import OpenAI

# Azure OpenAI 配置
model_name = os.getenv("AZURE_OPENAI_MODEL", "gpt-4")
endpoint = os.getenv('AZURE_OPENAI_ENDPOINT').rstrip('/')  # 移除末尾斜杠
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

client = OpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    base_url=f"{endpoint}/openai/deployments/{model_name}",
    default_query={"api-version": api_version}
)


def generate_questions_from_chunks(relevant_chunks: str, candidate_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    基于相关CV分块生成个性化问题

    Args:
        relevant_chunks: 格式化的相关CV分块
        candidate_info: 候选人基本信息

    Returns:
        生成的问题和分析
    """

    prompt = f"""你是一个专业的教育顾问。基于以下CV片段和候选人信息，生成2-3个具体的问题来帮助匹配合适的新西兰学习项目。

CV相关片段:
{relevant_chunks}

候选人基本信息:
- 专业背景: {candidate_info.get('bachelor_major', 'Unknown')}
- GPA: {candidate_info.get('gpa_value', 'Unknown')}/{candidate_info.get('gpa_scale', '4.0')}
- 雅思: {candidate_info.get('ielts_overall', 'Unknown')}
- 工作经验: {candidate_info.get('work_years', 0)} 年
- 兴趣领域: {', '.join(candidate_info.get('interests', []))}
- 偏好城市: {', '.join(candidate_info.get('city_pref', []))}
- 预算: ${candidate_info.get('budget_nzd_per_year', 'Unknown')} NZD/年

生成要求:
1. 问题要具体且有针对性
2. 关注CV中的空白期、技能转换、职业目标
3. 问题答案将直接用于课程匹配
4. 每个问题包含提问原因

请返回JSON格式:
{{
  "questions": [
    {{
      "id": "q1",
      "question": "具体问题内容",
      "placeholder": "回答示例",
      "required": true,
      "reason": "提问原因"
    }}
  ],
  "analysis_summary": "基于CV分析的简要总结",
  "key_areas": ["关键领域1", "关键领域2"]
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

        # 清理可能的markdown标记
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
        print(f"JSON解析错误: {e}")
        return {
            "status": "error",
            "error": "JSON parsing failed",
            "fallback_questions": get_fallback_questions()
        }
    except Exception as e:
        print(f"问题生成失败: {e}")
        return {
            "status": "error",
            "error": str(e),
            "fallback_questions": get_fallback_questions()
        }


def get_fallback_questions() -> Dict[str, Any]:
    """
    当AI生成失败时的备用问题
    """
    return {
        "questions": [
            {
                "id": "fallback_1",
                "question": "请描述您的职业发展目标和为什么选择在新西兰学习？",
                "placeholder": "例如：我希望在数据科学领域发展，新西兰的教育质量和工作机会吸引我...",
                "required": True,
                "reason": "了解学习动机和职业规划"
            },
            {
                "id": "fallback_2",
                "question": "您觉得自己在哪些技能或知识领域需要进一步提升？",
                "placeholder": "例如：我需要提升机器学习算法和大数据处理技能...",
                "required": True,
                "reason": "识别技能空白以匹配合适课程"
            }
        ],
        "analysis_summary": "使用通用问题进行信息收集",
        "key_areas": ["职业规划", "技能提升"]
    }


if __name__ == "__main__":
    # 测试
    test_chunks = """
--- CV片段 1 ---
长度: 200 字符
内容:
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
