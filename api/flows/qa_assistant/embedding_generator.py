from promptflow import tool
from typing import Dict, Any, List
import os
from openai import AzureOpenAI


@tool
def generate_embedding(conversation_history: Dict[str, Any], cv_analysis: Dict[str, Any]) -> List[float]:
    """
    使用Azure OpenAI生成embedding向量
    """
    try:
        # 构建查询文本
        query_parts = []

        # 从对话历史提取用户回答
        messages = conversation_history.get("messages", [])
        user_messages = [msg.get("content", "")
                         for msg in messages if msg.get("type") == "user"]

        if user_messages:
            # 合并所有用户回答
            user_text = " ".join(user_messages)
            query_parts.append(user_text)

        # 从CV分析提取关键信息
        if cv_analysis:
            if cv_analysis.get("education_details"):
                query_parts.append(str(cv_analysis["education_details"]))
            if cv_analysis.get("skills"):
                query_parts.extend(cv_analysis["skills"][:5])

        # 构建最终查询文本
        query_text = " ".join(query_parts)
        if not query_text.strip():
            query_text = "business management education new zealand study"

        print(f"生成embedding查询文本: {query_text[:200]}...")

        # 调用Azure OpenAI embedding API
        client = AzureOpenAI(
            api_version="2024-02-01",
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            api_key=os.environ.get("AZURE_OPENAI_KEY")
        )

        response = client.embeddings.create(
            input=query_text,
            model="text-embedding-3-large"
        )

        embedding = response.data[0].embedding
        print(f"生成embedding成功，维度: {len(embedding)}")

        return embedding

    except Exception as e:
        print(f"Embedding生成失败: {e}")
        return []
