import re
import hashlib
from typing import List, Dict


def estimate_tokens(text: str) -> int:
    """Simple token count estimation (大约4个characters=1个token)"""
    return len(text) // 4


def simple_chunk_by_tokens(text: str, max_tokens: int = 400, overlap_tokens: int = 50) -> List[Dict[str, str]]:
    """
    Simple chunking by fixed token count, no complex logic

    Args:
        text: Input text
        max_tokens: Maximum token count (默认400)
        overlap_tokens: Overlap token count (默认50)

    Returns:
        Chunk list
    """
    # Estimate character count
    max_chars = max_tokens * 4
    overlap_chars = overlap_tokens * 4

    # Clean text
    text = re.sub(r'\s+', ' ', text.strip())

    chunks = []
    start = 0
    chunk_id = 0

    while start < len(text):
        # Calculate end position
        end = min(start + max_chars, len(text))

        # Attempt to split at sentence boundaries
        if end < len(text):
            # Find the nearest period, newline or space ahead
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

        # Next chunk start position（Consider overlap）
        if end >= len(text):
            # Reach end of text, stop chunking
            break

        # Normal case: move forward, subtract overlap
        next_start = end - overlap_chars

        # Ensure minimum advance distance（Avoid generating almost identical chunks）
        min_advance = max_chars // 4  # At least advance 1/4 of chunk size
        if next_start <= start + min_advance:
            next_start = start + min_advance

        start = next_start

    return chunks


def get_relevant_chunks_simple(chunks: List[Dict[str, str]], query: str, top_k: int = 3) -> List[Dict[str, str]]:
    """
    Simple keyword matching to find relevant chunks

    Args:
        chunks: Chunk list
        query: Query keywords
        top_k: Return chunk count

    Returns:
        相关Chunk list
    """
    if not chunks or not query:
        return chunks[:top_k]

    query_words = query.lower().split()
    scored_chunks = []

    for chunk in chunks:
        text_lower = chunk['text'].lower()

        # Simple keyword matching scoring
        score = 0
        for word in query_words:
            score += text_lower.count(word)

        # Consider chunk length
        if chunk['length'] > 50:  # Prefer chunks with content
            score += 1

        chunk_with_score = chunk.copy()
        chunk_with_score['relevance_score'] = score
        scored_chunks.append(chunk_with_score)

    # Sort by score
    scored_chunks.sort(key=lambda x: x['relevance_score'], reverse=True)

    return scored_chunks[:top_k]


def format_chunks_for_llm(chunks: List[Dict[str, str]]) -> str:
    """
    Format chunks for LLM use

    Args:
        chunks: Chunk list

    Returns:
        Formatted text
    """
    if not chunks:
        return ""

    formatted = ""
    for i, chunk in enumerate(chunks, 1):
        formatted += f"\n--- CV segment {i} ---\n"
        formatted += f"Length: {chunk.get('length', 0)} characters\n"
        formatted += f"Estimated tokens: {chunk.get('estimated_tokens', 0)}\n"
        if 'relevance_score' in chunk:
            formatted += f"Relevance: {chunk['relevance_score']}\n"
        formatted += f"Content:\n{chunk['text']}\n"

    return formatted


if __name__ == "__main__":
    # Test
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

    print("=== 简单Token切块Test ===")
    chunks = simple_chunk_by_tokens(
        test_text, max_tokens=100, overlap_tokens=20)

    print(f"Generated {len(chunks)} chunks:")
    for chunk in chunks:
        print(
            f"- Chunk {chunk['id']}: {chunk['estimated_tokens']} tokens, {chunk['length']} characters")
        print(f"  Content preview: {chunk['text'][:50]}...")
        print()

    # Test检索
    relevant = get_relevant_chunks_simple(
        chunks, "work experience programming", top_k=2)
    print("相关Chunk:")
    for chunk in relevant:
        print(f"- {chunk['id']}: Score {chunk['relevance_score']}")

    # Test格式化
    formatted = format_chunks_for_llm(relevant)
    print("\n=== Formatted content for LLM ===")
    print(formatted[:200] + "...")
