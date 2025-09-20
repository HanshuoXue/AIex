from promptflow import tool
from typing import Dict, Any, List
import json
import os
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def try_azure_vector_search(embedding_data: List[float], conversation_history: Dict[str, Any], cv_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    尝试使用Azure Search进行向量搜索
    """
    try:
        # 初始化Azure Search客户端
        search_endpoint = os.environ.get("SEARCH_ENDPOINT")
        search_key = os.environ.get("SEARCH_KEY")

        if not search_endpoint or not search_key:
            return {
                "matched_programs": [],
                "status": "failed",
                "error": "Azure Search credentials not configured",
                "programs_count": 0
            }

        search_client = SearchClient(
            endpoint=search_endpoint,
            index_name="nz-programs",
            credential=AzureKeyCredential(search_key)
        )

        print(f"开始Azure Search向量搜索，向量维度: {len(embedding_data)}")

        # 尝试向量搜索
        user_text = extract_user_preferences(conversation_history)

        try:
            # 首先尝试向量搜索
            search_results = search_client.search(
                search_text="",  # 空文本，只使用向量搜索
                vector_queries=[{
                    "kind": "vector",
                    "vector": embedding_data,
                    "k_nearest_neighbors": 3,
                    "fields": "content_vector"
                }],
                select=["*"],
                top=3
            )
            print("🔍 搜索方式: Azure Search 向量搜索 (Vector Search)")
            search_method = "azure_vector_search"
        except Exception as vector_error:
            print(f"❌ 向量搜索失败: {vector_error}")
            print("🔄 回退到: Azure Search 文本搜索 (Text Search)")
            # 如果向量搜索失败，回退到文本搜索
            search_results = search_client.search(
                search_text=user_text,
                select=["*"],
                top=3
            )
            search_method = "azure_text_search"

        matched_programs = []
        for result in search_results:
            program_data = dict(result)
            # 添加匹配分数（Azure Search返回的相关性分数）
            program_data["match_score"] = result.get(
                "@search.score", 0.0) / 100.0  # 标准化到0-1
            matched_programs.append(program_data)

        print(f"✅ Azure Search返回 {len(matched_programs)} 个结果")
        print(f"📊 搜索方式: {search_method}")

        return {
            "matched_programs": matched_programs,
            "status": "success",
            "search_method": search_method,
            "programs_count": len(matched_programs)
        }

    except Exception as e:
        print(f"Azure Search向量搜索失败: {e}")
        return {
            "matched_programs": [],
            "status": "failed",
            "error": str(e),
            "programs_count": 0
        }


def try_local_fallback_match(conversation_history: Dict[str, Any], cv_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    本地fallback匹配（原有的关键词匹配逻辑）
    """
    try:
        programs = load_local_programs()
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

        print(f"✅ 本地关键词匹配返回 {len(top3)} 个结果")
        print(f"📊 搜索方式: 本地关键词匹配 (Local Keyword Match)")

        return {
            "matched_programs": top3,
            "status": "success",
            "search_method": "local_keyword_match",
            "programs_count": len(top3)
        }
    except Exception as e:
        print(f"本地fallback匹配失败: {e}")
        fallback_programs = get_fallback_programs()
        return {
            "matched_programs": fallback_programs,
            "status": "fallback_used",
            "error": str(e),
            "programs_count": len(fallback_programs)
        }


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

        # 尝试使用Azure Search向量搜索
        azure_search_result = try_azure_vector_search(
            embedding_data, conversation_history, cv_analysis)

        if azure_search_result["status"] == "success":
            search_method = azure_search_result.get("search_method", "unknown")
            print(
                f"✅ Azure Search搜索成功，匹配到 {len(azure_search_result['matched_programs'])} 个项目")
            print(f"🔍 搜索方式: {search_method}")
            return azure_search_result
        else:
            print(
                f"❌ Azure Search失败: {azure_search_result.get('error', 'unknown')}")
            print("🔄 回退到: 本地关键词匹配 (Local Fallback)")
            # 使用本地fallback
            return try_local_fallback_match(conversation_history, cv_analysis)

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
