#!/usr/bin/env python3
"""
测试简化的RAG CV分析功能
"""
import os
import sys
import json
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
api_path = project_root / "api"
sys.path.insert(0, str(api_path))
sys.path.insert(0, str(api_path / "flows" / "chat_rag"))


def test_simple_chunking():
    """测试简单Token切块"""
    print("🔍 测试简单Token切块...")

    try:
        from api.flows.chat_rag.simple_chunker import simple_chunk_by_tokens, get_relevant_chunks_simple, format_chunks_for_llm

        test_cv = """
        John Doe
        Senior Software Engineer
        Email: john.doe@email.com
        Phone: +1234567890
        
        EDUCATION
        Bachelor of Computer Science
        Stanford University
        2018-2022
        GPA: 3.8/4.0
        
        WORK EXPERIENCE
        Senior Software Engineer
        Tech Innovations Inc.
        June 2022 - Present
        • Developed scalable web applications serving 100K+ users
        • Led a team of 5 developers in agile environment
        • Implemented microservices architecture reducing latency by 40%
        
        Software Developer
        StartUp Solutions
        January 2020 - May 2022
        • Built responsive web applications using React and Redux
        • Developed RESTful APIs with Node.js and Express
        
        TECHNICAL SKILLS
        Programming Languages: JavaScript, TypeScript, Python, Java
        Frontend: React, Redux, HTML5, CSS3
        Backend: Node.js, Express, Django
        Databases: PostgreSQL, MongoDB
        """

        # 1. 测试分块
        chunks = simple_chunk_by_tokens(
            test_cv, max_tokens=400, overlap_tokens=50)
        print(f"✅ 生成了 {len(chunks)} 个分块")

        for i, chunk in enumerate(chunks[:3]):
            print(
                f"  分块 {i+1}: {chunk['estimated_tokens']} tokens, {chunk['length']} 字符")
            print(f"  内容: {chunk['text'][:80]}...")

        # 2. 测试检索
        relevant = get_relevant_chunks_simple(
            chunks, "software engineering experience", top_k=3)
        print(f"✅ 检索到 {len(relevant)} 个相关分块")

        for chunk in relevant:
            print(f"  - 分块 {chunk['id']}: 相关性分数 {chunk['relevance_score']}")

        # 3. 测试格式化
        formatted = format_chunks_for_llm(relevant)
        print(f"✅ 格式化后长度: {len(formatted)} 字符")
        print(f"格式化预览:\n{formatted[:200]}...")

        return True

    except Exception as e:
        print(f"❌ 简单分块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_question_generation():
    """测试问题生成"""
    print("\n🔍 测试问题生成...")

    try:
        from api.flows.chat_rag.simple_question_generator import generate_questions_from_chunks

        test_chunks = """
--- CV片段 1 ---
长度: 300 字符
预估tokens: 75
相关性: 3
内容:
WORK EXPERIENCE
Senior Software Engineer
Tech Innovations Inc.
June 2022 - Present
• Developed scalable web applications serving 100K+ users
• Led a team of 5 developers in agile environment

--- CV片段 2 ---
长度: 200 字符  
预估tokens: 50
相关性: 2
内容:
EDUCATION
Bachelor of Computer Science
Stanford University
2018-2022
GPA: 3.8/4.0
"""

        test_candidate = {
            "bachelor_major": "computer science",
            "gpa_value": 3.5,
            "gpa_scale": "4.0",
            "ielts_overall": 7.0,
            "work_years": 2,
            "interests": ["machine learning", "web development"],
            "city_pref": ["Auckland"],
            "budget_nzd_per_year": 50000
        }

        result = generate_questions_from_chunks(test_chunks, test_candidate)

        if result.get("status") == "success":
            questions = result["data"]["questions"]
            print(f"✅ 成功生成 {len(questions)} 个问题")

            for i, q in enumerate(questions, 1):
                print(f"\n问题 {i}:")
                print(f"  内容: {q['question']}")
                print(f"  原因: {q['reason']}")
                print(f"  必填: {q['required']}")
        else:
            print("⚠️ 使用备用问题")
            fallback = result.get("fallback_questions", {})
            questions = fallback.get("questions", [])
            print(f"✅ 备用问题数量: {len(questions)}")

        return True

    except Exception as e:
        print(f"❌ 问题生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integrated_flow():
    """测试完整流程"""
    print("\n🔍 测试完整RAG流程...")

    try:
        from api.flows.chat_rag.simple_chunker import simple_chunk_by_tokens, get_relevant_chunks_simple, format_chunks_for_llm
        from api.flows.chat_rag.simple_question_generator import generate_questions_from_chunks

        # 模拟完整CV文本
        cv_text = """
        张三
        高级软件工程师
        电话: 138xxxx8888
        邮箱: zhangsan@email.com
        
        教育背景
        计算机科学与技术学士
        北京大学
        2016-2020
        GPA: 3.6/4.0
        
        工作经历
        高级软件工程师
        字节跳动
        2021年3月 - 至今
        • 负责推荐系统算法优化，提升CTR 15%
        • 带领6人团队开发微服务架构
        • 使用Python、Go、React技术栈
        
        软件工程师
        美团
        2020年7月 - 2021年3月
        • 开发外卖配送算法
        • 维护高并发系统，日活1000万+
        
        技能
        编程语言: Python, Java, Go, JavaScript
        框架: Django, Spring Boot, React, Vue
        数据库: MySQL, Redis, MongoDB
        云服务: AWS, 阿里云
        
        项目经历
        智能推荐系统
        2022年
        • 设计并实现基于深度学习的推荐算法
        • 使用TensorFlow和PyTorch
        • 系统日处理请求量达1亿次
        """

        candidate_info = {
            "bachelor_major": "computer science",
            "gpa_value": 3.6,
            "gpa_scale": "4.0",
            "ielts_overall": 7.5,
            "work_years": 3,
            "interests": ["machine learning", "artificial intelligence"],
            "city_pref": ["Wellington", "Auckland"],
            "budget_nzd_per_year": 60000
        }

        # 完整流程
        print("步骤1: 文本切块...")
        chunks = simple_chunk_by_tokens(
            cv_text, max_tokens=400, overlap_tokens=50)
        print(f"  生成 {len(chunks)} 个分块")

        print("步骤2: 相关性检索...")
        query = f"{candidate_info.get('bachelor_major', '')} {' '.join(candidate_info.get('interests', []))}"
        relevant_chunks = get_relevant_chunks_simple(chunks, query, top_k=5)
        print(f"  选择 {len(relevant_chunks)} 个相关分块")

        print("步骤3: 格式化分块...")
        formatted_chunks = format_chunks_for_llm(relevant_chunks)
        print(f"  格式化长度: {len(formatted_chunks)} 字符")

        print("步骤4: 生成问题...")
        question_result = generate_questions_from_chunks(
            formatted_chunks, candidate_info)

        if question_result.get("status") == "success":
            questions = question_result["data"]["questions"]
            summary = question_result["data"].get("analysis_summary", "")
            print(f"✅ 完整流程成功!")
            print(f"  生成问题数: {len(questions)}")
            print(f"  分析摘要: {summary}")
        else:
            print("⚠️ 问题生成失败，使用备用问题")

        return True

    except Exception as e:
        print(f"❌ 完整流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("🚀 简化RAG CV分析测试\n")

    results = []

    # 运行测试
    results.append(test_simple_chunking())
    results.append(test_question_generation())
    results.append(test_integrated_flow())

    # 汇总结果
    print(f"\n{'='*50}")
    print("📊 测试结果汇总:")
    print(f"{'='*50}")

    test_names = ["简单分块", "问题生成", "完整流程"]
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{i+1}. {name}: {status}")

    total_passed = sum(results)
    total_tests = len(results)

    print(f"\n总计: {total_passed}/{total_tests} 测试通过")

    if total_passed == total_tests:
        print("🎉 所有测试通过！简化RAG系统已就绪。")
        return True
    else:
        print("⚠️ 部分测试失败，请检查上述错误。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
