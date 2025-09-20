#!/usr/bin/env python3
"""
测试不同的搜索方式：向量搜索 vs 文本搜索 vs 本地匹配
"""
import asyncio
import os
from dotenv import load_dotenv
from api.qa_assistant import QAAssistant

# 加载环境变量
load_dotenv()


async def test_search_methods():
    """测试不同的搜索方式"""
    print("🔍 测试不同的搜索方式...")
    print("=" * 50)

    # 初始化QA助手
    qa_assistant = QAAssistant()

    # 测试数据
    cv_analysis = {
        "education": "Bachelor's Degree in Computer Science",
        "experience": "2 years software development",
        "skills": ["Python", "JavaScript", "React"],
        "interests": ["AI", "Machine Learning", "Data Science"]
    }

    conversation_history = {
        "messages": [
            {"type": "user", "content": "I want to study computer science in New Zealand"},
            {"type": "user", "content": "I'm interested in AI and machine learning programs"}
        ]
    }

    print("📊 测试场景：")
    print("- 用户背景：计算机科学学士，2年开发经验")
    print("- 兴趣：AI、机器学习、数据科学")
    print("- 目标：新西兰留学")
    print()

    try:
        # 生成报告
        result = await qa_assistant.generate_report(
            cv_analysis=cv_analysis,
            conversation_history=conversation_history,
            user_id="test-search-methods"
        )

        print("✅ 报告生成成功！")
        print(f"📄 报告URL: {result.get('report_url', 'N/A')}")
        print(f"🎯 匹配项目数: {result.get('programs_matched', 0)}")
        print(f"⏰ 生成模式: {result.get('generation_mode', 'N/A')}")

        # 显示搜索方式信息
        debug_info = result.get('debug_info', {})
        flow_result = result.get('flow_result', {})

        print("\n🔍 搜索方式详情：")
        print("-" * 30)

        # Embedding状态
        embedding_status = debug_info.get('embedding_status', 'unknown')
        if embedding_status == 'success':
            print("✅ Embedding生成: 成功")
            print(f"   - 维度: {debug_info.get('embedding_dimension', 'N/A')}")
        else:
            print("⚠️ Embedding生成: 使用备用方案")
            print(f"   - 错误: {debug_info.get('embedding_error', 'N/A')}")

        # RAG匹配状态
        rag_status = debug_info.get('rag_matching_status', 'unknown')
        if rag_status == 'success':
            print("✅ RAG匹配: 成功")
            print(f"   - 匹配项目数: {debug_info.get('rag_programs_count', 0)}")
        else:
            print("⚠️ RAG匹配: 使用备用方案")
            print(f"   - 原因: {debug_info.get('rag_reason', 'N/A')}")

        # 搜索方式
        search_method = flow_result.get('search_method', 'unknown')
        search_method_map = {
            'azure_vector_search': '🔍 Azure Search 向量搜索',
            'azure_text_search': '📝 Azure Search 文本搜索',
            'local_keyword_match': '🏠 本地关键词匹配'
        }

        print(
            f"🔍 实际搜索方式: {search_method_map.get(search_method, search_method)}")

        # 显示匹配的项目
        matched_programs = flow_result.get('matched_programs', [])
        if matched_programs:
            print(f"\n📋 匹配的项目 ({len(matched_programs)} 个):")
            print("-" * 30)
            for i, program in enumerate(matched_programs[:3], 1):
                print(f"{i}. {program.get('program', 'N/A')}")
                print(f"   - 大学: {program.get('university', 'N/A')}")
                print(
                    f"   - 学费: NZ$ {program.get('tuition_nzd_per_year', 'N/A')}")
                print(
                    f"   - 匹配度: {((program.get('match_score', 0)) * 100):.1f}%")
                print()

        print("=" * 50)
        print("🎉 测试完成！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search_methods())
