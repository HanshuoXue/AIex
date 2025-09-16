import re
import hashlib
from typing import List, Dict


def estimate_tokens(text: str) -> int:
    """简单估算token数量 (大约4个字符=1个token)"""
    return len(text) // 4


def simple_chunk_by_tokens(text: str, max_tokens: int = 400, overlap_tokens: int = 50) -> List[Dict[str, str]]:
    """
    按固定token数简单切块，没有复杂逻辑

    Args:
        text: 输入文本
        max_tokens: 最大token数 (默认400)
        overlap_tokens: 重叠token数 (默认50)

    Returns:
        分块列表
    """
    # 估算字符数
    max_chars = max_tokens * 4
    overlap_chars = overlap_tokens * 4

    # 清理文本
    text = re.sub(r'\s+', ' ', text.strip())

    chunks = []
    start = 0
    chunk_id = 0

    while start < len(text):
        # 计算结束位置
        end = min(start + max_chars, len(text))

        # 尝试在句子边界分割
        if end < len(text):
            # 往前找最近的句号、换行或空格
            for i in range(end, max(start, end - 100), -1):
                if text[i] in '.。\n ':
                    end = i + 1
                    break

        chunk_text = text[start:end].strip()

        if chunk_text:
            chunk_id += 1
            chunks.append({
                'id': f"chunk_{chunk_id}",
                'text': chunk_text,
                'start_pos': start,
                'end_pos': end,
                'estimated_tokens': estimate_tokens(chunk_text),
                'length': len(chunk_text)
            })

        # 下一个分块的起始位置（考虑重叠）
        start = max(start + 1, end - overlap_chars)

        # 避免无限循环
        if start >= end:
            break

    return chunks


def get_relevant_chunks_simple(chunks: List[Dict[str, str]], query: str, top_k: int = 3) -> List[Dict[str, str]]:
    """
    简单的关键词匹配找相关分块

    Args:
        chunks: 分块列表
        query: 查询关键词
        top_k: 返回分块数

    Returns:
        相关分块列表
    """
    if not chunks or not query:
        return chunks[:top_k]

    query_words = query.lower().split()
    scored_chunks = []

    for chunk in chunks:
        text_lower = chunk['text'].lower()

        # 简单关键词匹配评分
        score = 0
        for word in query_words:
            score += text_lower.count(word)

        # 考虑分块长度
        if chunk['length'] > 50:  # 偏好有内容的分块
            score += 1

        chunk_with_score = chunk.copy()
        chunk_with_score['relevance_score'] = score
        scored_chunks.append(chunk_with_score)

    # 按分数排序
    scored_chunks.sort(key=lambda x: x['relevance_score'], reverse=True)

    return scored_chunks[:top_k]


def format_chunks_for_llm(chunks: List[Dict[str, str]]) -> str:
    """
    格式化分块给LLM使用

    Args:
        chunks: 分块列表

    Returns:
        格式化的文本
    """
    if not chunks:
        return ""

    formatted = ""
    for i, chunk in enumerate(chunks, 1):
        formatted += f"\n--- CV片段 {i} ---\n"
        formatted += f"长度: {chunk.get('length', 0)} 字符\n"
        formatted += f"预估tokens: {chunk.get('estimated_tokens', 0)}\n"
        if 'relevance_score' in chunk:
            formatted += f"相关性: {chunk['relevance_score']}\n"
        formatted += f"内容:\n{chunk['text']}\n"

    return formatted


if __name__ == "__main__":
    # 测试
    test_text = """
    John Doe
    Software Engineer
    Email: john@example.com
    
    EDUCATION
    Bachelor of Computer Science
    University of Technology
    2018-2022
    GPA: 3.5/4.0
    
    WORK EXPERIENCE
    Software Engineer
    Tech Company Inc.
    2022-Present
    Developed web applications using React and Node.js
    Led team of 5 developers
    
    SKILLS
    Programming: Python, JavaScript, Java
    Frameworks: React, Django, Express
    """

    print("=== 简单Token切块测试 ===")
    chunks = simple_chunk_by_tokens(
        test_text, max_tokens=100, overlap_tokens=20)

    print(f"生成了 {len(chunks)} 个分块:")
    for chunk in chunks:
        print(
            f"- 分块 {chunk['id']}: {chunk['estimated_tokens']} tokens, {chunk['length']} 字符")
        print(f"  内容预览: {chunk['text'][:50]}...")
        print()

    # 测试检索
    relevant = get_relevant_chunks_simple(
        chunks, "work experience programming", top_k=2)
    print("相关分块:")
    for chunk in relevant:
        print(f"- {chunk['id']}: 分数 {chunk['relevance_score']}")

    # 测试格式化
    formatted = format_chunks_for_llm(relevant)
    print("\n=== 格式化给LLM的内容 ===")
    print(formatted[:200] + "...")
