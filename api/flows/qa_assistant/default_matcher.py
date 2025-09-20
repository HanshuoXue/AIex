from promptflow import tool
from typing import Dict, Any
import os
import sys

# 添加当前目录到Python路径，以便导入rag_matcher
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from rag_matcher import match_programs
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


@tool
def default_match_programs(conversation_history: Dict[str, Any], cv_analysis: Dict[str, Any], query_embedding: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    默认匹配器，在对话阶段返回空结果，在报告生成阶段返回fallback结果
    """
    # 检查是否在报告生成阶段（通过conversation_history中的消息数量判断）
    messages = conversation_history.get("messages", [])
    user_messages = [msg for msg in messages if msg.get("type") == "user"]

    if len(user_messages) >= 2:
        # 报告生成阶段，尝试使用RAG匹配器
        print("报告生成阶段，尝试使用RAG匹配器")
        if RAG_AVAILABLE and query_embedding:
            try:
                # 调用RAG匹配器
                rag_result = match_programs(
                    query_embedding, conversation_history, cv_analysis)
                print(f"RAG匹配器返回: {rag_result.get('status', 'unknown')}")
                return rag_result
            except Exception as e:
                print(f"RAG匹配器失败: {e}")
                # 回退到fallback
                pass

        # 如果RAG不可用或失败，返回fallback项目
        print("使用fallback项目")
        fallback_programs = [
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
        return {
            "matched_programs": fallback_programs,
            "status": "fallback_used",
            "programs_count": len(fallback_programs)
        }
    else:
        # 对话阶段，返回空结果
        print("对话阶段，使用默认匹配器返回空结果")
        return {
            "matched_programs": [],
            "status": "conversation_mode",
            "programs_count": 0
        }
