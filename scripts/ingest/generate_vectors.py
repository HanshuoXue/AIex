#!/usr/bin/env python3
"""
为项目数据生成向量并更新到Azure Search
"""
import os
import json
import sys
from typing import List, Dict, Any
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def generate_embedding(text: str) -> List[float]:
    """生成文本的embedding向量"""
    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_KEY"],
        api_version="2024-02-01"
    )

    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )

    return response.data[0].embedding


def create_content_text(program: Dict[str, Any]) -> str:
    """为项目创建用于embedding的文本内容"""
    content_parts = []

    # 基本信息
    content_parts.append(f"Program: {program.get('program', '')}")
    content_parts.append(f"University: {program.get('university', '')}")
    content_parts.append(f"Type: {program.get('type', '')}")
    content_parts.append(f"Level: {program.get('level', '')}")
    content_parts.append(f"Campus: {program.get('campus', '')}")

    # 字段和兴趣
    if program.get('fields'):
        content_parts.append(f"Fields: {', '.join(program['fields'])}")

    # 学术要求
    if program.get('academic_reqs'):
        content_parts.append(
            f"Academic Requirements: {', '.join(program['academic_reqs'])}")

    # 其他要求
    if program.get('other_reqs'):
        content_parts.append(
            f"Other Requirements: {', '.join(program['other_reqs'])}")

    # 学费和时长
    if program.get('tuition_nzd_per_year'):
        content_parts.append(
            f"Tuition: NZ$ {program['tuition_nzd_per_year']} per year")

    if program.get('duration_years'):
        content_parts.append(f"Duration: {program['duration_years']} years")

    # 英语要求
    if program.get('english_ielts'):
        content_parts.append(f"IELTS: {program['english_ielts']}")

    # 入学时间
    if program.get('intakes'):
        content_parts.append(f"Intakes: {', '.join(program['intakes'])}")

    return " | ".join(content_parts)


def process_programs_with_vectors(input_file: str, search_endpoint: str, search_key: str, index_name: str):
    """处理项目数据并生成向量"""

    # 初始化Azure Search客户端
    search_client = SearchClient(
        endpoint=search_endpoint,
        index_name=index_name,
        credential=AzureKeyCredential(search_key)
    )

    # 读取项目数据
    programs = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                programs.append(json.loads(line))

    print(f"处理 {len(programs)} 个项目...")

    # 批量处理并更新
    batch_size = 10
    for i in range(0, len(programs), batch_size):
        batch = programs[i:i + batch_size]
        updated_docs = []

        for program in batch:
            try:
                # 创建用于embedding的文本
                content_text = create_content_text(program)

                # 生成向量
                print(f"为项目 '{program.get('program', '')}' 生成向量...")
                vector = generate_embedding(content_text)

                # 更新文档
                updated_program = program.copy()
                updated_program['content_vector'] = vector
                updated_docs.append(updated_program)

            except Exception as e:
                print(f"处理项目 {program.get('program', '')} 时出错: {e}")
                continue

        # 批量上传到Azure Search
        if updated_docs:
            try:
                result = search_client.upload_documents(updated_docs)
                successful = sum(1 for r in result if r.succeeded)
                failed = sum(1 for r in result if not r.succeeded)
                print(f"批次 {i//batch_size + 1}: 成功 {successful}, 失败 {failed}")

                if failed > 0:
                    for r in result:
                        if not r.succeeded:
                            print(f"错误: {r.error_message}")

            except Exception as e:
                print(f"上传批次 {i//batch_size + 1} 时出错: {e}")


def main():
    if len(sys.argv) != 2:
        print("用法: python generate_vectors.py <programs.jsonl>")
        sys.exit(1)

    input_file = sys.argv[1]

    # 检查环境变量
    search_endpoint = os.environ.get("SEARCH_ENDPOINT")
    search_key = os.environ.get("SEARCH_KEY")

    if not search_endpoint or not search_key:
        print("错误: 请设置 SEARCH_ENDPOINT 和 SEARCH_KEY 环境变量")
        sys.exit(1)

    # 处理项目数据
    process_programs_with_vectors(
        input_file=input_file,
        search_endpoint=search_endpoint,
        search_key=search_key,
        index_name="nz-programs"
    )

    print("向量生成完成！")


if __name__ == "__main__":
    main()
