from promptflow import tool
from typing import Dict, Any, List
import json
import os


@tool
def match_programs(query_embedding: Dict[str, Any], conversation_history: Dict[str, Any], cv_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    使用embedding向量匹配top3项目
    """
    try:
        # 检查是否在对话阶段（没有embedding数据）
        if not query_embedding or (isinstance(query_embedding, dict) and not query_embedding.get("embedding")):
            print("没有embedding数据，使用fallback匹配")
            fallback_programs = get_fallback_programs()
            return {
                "matched_programs": fallback_programs,
                "status": "fallback_used",
                "reason": "no_embedding",
                "programs_count": len(fallback_programs)
            }
        # 检查embedding状态
        embedding_data = query_embedding.get("embedding", []) if isinstance(
            query_embedding, dict) else query_embedding
        embedding_status = query_embedding.get("status", "unknown") if isinstance(
            query_embedding, dict) else "unknown"

        if not embedding_data or embedding_status != "success":
            print("没有有效的embedding，使用fallback匹配")
            fallback_programs = get_fallback_programs()
            return {
                "matched_programs": fallback_programs,
                "status": "fallback_used",
                "reason": "embedding_failed",
                "embedding_status": embedding_status,
                "programs_count": len(fallback_programs)
            }

        print(f"使用embedding匹配项目，向量维度: {len(embedding_data)}")

        # TODO: 这里应该使用Azure Search的向量搜索
        # 目前使用简化的本地搜索
        programs = load_local_programs()

        # 简化的匹配逻辑（基于对话内容）
        scored_programs = []
        user_text = extract_user_preferences(conversation_history)

        for program in programs:
            score = calculate_simple_match_score(
                program, user_text, cv_analysis)
            program["match_score"] = score
            scored_programs.append(program)

        # 排序并返回top3
        scored_programs.sort(key=lambda x: x.get(
            "match_score", 0), reverse=True)
        top3 = scored_programs[:3]

        print(f"匹配完成，返回{len(top3)}个项目")
        return {
            "matched_programs": top3,
            "status": "success",
            "embedding_status": embedding_status,
            "programs_count": len(top3),
            "user_text": user_text[:100] + "..." if len(user_text) > 100 else user_text
        }

    except Exception as e:
        print(f"RAG匹配失败: {e}")
        fallback_programs = get_fallback_programs()
        return {
            "matched_programs": fallback_programs,
            "status": "fallback_used",
            "reason": "matching_failed",
            "error": str(e),
            "programs_count": len(fallback_programs)
        }


def load_local_programs() -> List[Dict]:
    """加载本地项目数据"""
    try:
        programs_file = os.path.join(os.path.dirname(
            __file__), "..", "..", "..", "data", "curated", "programs.jsonl")
        programs = []

        with open(programs_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    programs.append(json.loads(line))

        return programs[:50]  # 取前50个程序进行匹配

    except Exception as e:
        print(f"加载本地数据失败: {e}")
        return get_fallback_programs()


def extract_user_preferences(conversation_history: Dict[str, Any]) -> str:
    """从对话历史提取用户偏好"""
    messages = conversation_history.get("messages", [])
    user_messages = [msg.get("content", "")
                     for msg in messages if msg.get("type") == "user"]
    return " ".join(user_messages).lower()


def calculate_simple_match_score(program: Dict, user_text: str, cv_analysis: Dict[str, Any]) -> float:
    """简单的匹配评分"""
    score = 0.0

    # 专业匹配
    program_fields = program.get("fields", [])
    if isinstance(program_fields, str):
        program_fields = [program_fields]

    program_text = " ".join(program_fields).lower()
    program_text += " " + program.get("program", "").lower()

    # 关键词匹配
    business_keywords = ["business", "商科", "管理",
                         "management", "finance", "金融", "marketing"]
    tech_keywords = ["technology", "技术",
                     "computer", "计算机", "engineering", "工程"]

    for keyword in business_keywords:
        if keyword in user_text and keyword in program_text:
            score += 0.3

    for keyword in tech_keywords:
        if keyword in user_text and keyword in program_text:
            score += 0.3

    # 级别匹配
    if "硕士" in user_text or "master" in user_text:
        if program.get("level") == "Postgraduate":
            score += 0.4

    return min(score, 1.0)


def get_fallback_programs() -> List[Dict]:
    """默认推荐项目"""
    return [
        {
            "id": "fallback_1",
            "university": "University of Auckland",
            "program": "Master of Business Administration",
            "fields": ["Business", "Management"],
            "level": "Postgraduate",
            "campus": "Auckland",
            "tuition_nzd_per_year": 45000,
            "duration_years": 1.5,
            "url": "https://www.auckland.ac.nz/",
            "match_score": 0.8
        },
        {
            "id": "fallback_2",
            "university": "Victoria University of Wellington",
            "program": "Master of Commerce",
            "fields": ["Business", "Commerce"],
            "level": "Postgraduate",
            "campus": "Wellington",
            "tuition_nzd_per_year": 35000,
            "duration_years": 1,
            "url": "https://www.wgtn.ac.nz/",
            "match_score": 0.7
        },
        {
            "id": "fallback_3",
            "university": "University of Canterbury",
            "program": "Master of Engineering Management",
            "fields": ["Engineering", "Management"],
            "level": "Postgraduate",
            "campus": "Christchurch",
            "tuition_nzd_per_year": 38000,
            "duration_years": 1.5,
            "url": "https://www.canterbury.ac.nz/",
            "match_score": 0.6
        }
    ]
