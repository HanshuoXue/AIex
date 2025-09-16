#!/usr/bin/env python3
"""
测试RAG-based CV分析功能
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


def test_cv_chunking():
    """测试CV分块功能"""
    print("🔍 Testing CV chunking...")

    try:
        from api.flows.chat_rag.cv_chunker import chunk_cv_text, analyze_chunk_relevance

        test_cv = """
        John Doe
        Senior Software Engineer
        Email: john.doe@email.com
        Phone: +1234567890
        Location: San Francisco, CA
        
        PROFESSIONAL SUMMARY
        Experienced software engineer with 5+ years in full-stack development.
        Specialized in React, Node.js, and cloud technologies.
        
        EDUCATION
        Bachelor of Computer Science
        Stanford University
        2018-2022
        GPA: 3.8/4.0
        
        Relevant Coursework: Data Structures, Algorithms, Machine Learning
        
        WORK EXPERIENCE
        Senior Software Engineer
        Tech Innovations Inc.
        June 2022 - Present
        • Developed scalable web applications serving 100K+ users
        • Led a team of 5 developers in agile environment
        • Implemented microservices architecture reducing latency by 40%
        • Technologies: React, Node.js, AWS, Docker, Kubernetes
        
        Software Developer
        StartUp Solutions
        January 2020 - May 2022
        • Built responsive web applications using React and Redux
        • Developed RESTful APIs with Node.js and Express
        • Integrated third-party services and payment gateways
        • Collaborated with cross-functional teams
        
        Intern Software Developer
        Code Academy
        June 2019 - December 2019
        • Assisted in developing educational platform features
        • Wrote unit tests and documentation
        • Learned best practices in software development
        
        TECHNICAL SKILLS
        Programming Languages: JavaScript, TypeScript, Python, Java
        Frontend: React, Redux, HTML5, CSS3, Bootstrap
        Backend: Node.js, Express, Django, Spring Boot
        Databases: PostgreSQL, MongoDB, Redis
        Cloud & DevOps: AWS, Docker, Kubernetes, CI/CD
        Tools: Git, Jira, Slack, VS Code
        
        PROJECTS
        E-commerce Platform
        Personal Project - 2023
        • Full-stack e-commerce solution with React frontend and Node.js backend
        • Implemented user authentication, product catalog, and payment processing
        • Used AWS for hosting and deployment
        • Technologies: React, Node.js, PostgreSQL, Stripe API, AWS
        
        Task Management Application
        Team Project - 2021
        • Collaborative task management tool for small teams
        • Real-time updates using WebSocket connections
        • Mobile-responsive design
        • Technologies: React, Socket.io, MongoDB
        
        CERTIFICATIONS
        AWS Certified Developer - Associate (2023)
        React Developer Certification (2022)
        
        LANGUAGES
        English: Native
        Spanish: Conversational
        Mandarin: Basic
        """

        # 测试不同的分块方法
        methods = ['sections', 'semantic', 'hybrid']

        for method in methods:
            print(f"\n--- Testing {method} chunking ---")
            chunks = chunk_cv_text(test_cv, method=method)
            analyzed_chunks = analyze_chunk_relevance(chunks)

            print(f"Generated {len(analyzed_chunks)} chunks")

            for i, chunk in enumerate(analyzed_chunks[:3]):  # 只显示前3个
                print(f"\nChunk {i+1}:")
                print(f"  Section: {chunk['section_type']}")
                print(f"  Relevance: {chunk['relevance_score']}")
                print(f"  Tags: {chunk['importance_tags']}")
                print(f"  Length: {chunk['text_length']}")
                print(f"  Text preview: {chunk['text'][:100]}...")

        print("✅ CV chunking test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ CV chunking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cv_embedding():
    """测试CV向量化功能"""
    print("\n🔍 Testing CV embedding...")

    try:
        from api.flows.chat_rag.cv_embedder import process_cv_with_rag, get_relevant_chunks

        test_cv = """
        John Doe
        Software Engineer
        
        EDUCATION
        Bachelor of Computer Science
        Stanford University
        2018-2022
        
        WORK EXPERIENCE
        Software Engineer
        Tech Company
        2022-Present
        Developed web applications using React
        """

        # 测试RAG处理
        result = process_cv_with_rag(test_cv, chunking_method='hybrid')

        print(f"Processing status: {result['status']}")
        print(
            f"Number of chunks: {result['processing_summary']['total_chunks']}")
        print(
            f"Has embeddings: {result['processing_summary']['has_embeddings']}")

        if result['status'] == 'success' and result['chunks']:
            # 测试相关性检索
            relevant_chunks = get_relevant_chunks(
                result['chunks'],
                "software engineering experience",
                top_k=3
            )

            print(f"\nMost relevant chunks for 'software engineering experience':")
            for chunk in relevant_chunks:
                similarity = chunk.get('similarity_score', 'N/A')
                print(f"  - {chunk['section_type']}: similarity={similarity}")

        print("✅ CV embedding test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ CV embedding test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_promptflow_functions():
    """测试PromptFlow函数"""
    print("\n🔍 Testing PromptFlow functions...")

    try:
        from api.flows.chat_rag.cv_chunker_flow import chunk_cv_for_analysis
        from api.flows.chat_rag.cv_embedder_flow import prepare_chunks_for_analysis

        test_cv = """
        John Doe
        Software Engineer
        
        EDUCATION
        Bachelor of Computer Science
        2018-2022
        
        WORK EXPERIENCE
        Software Engineer
        2022-Present
        """

        # 测试分块函数
        chunking_result = chunk_cv_for_analysis(test_cv, method="hybrid")
        print(f"Chunking status: {chunking_result['status']}")
        print(f"Number of chunks: {chunking_result['stats']['total_chunks']}")

        if chunking_result['status'] == 'success':
            # 测试准备函数
            prep_result = prepare_chunks_for_analysis(
                chunking_result['chunks'], top_k=5)
            print(f"Preparation status: {prep_result['status']}")
            print(
                f"Formatted chunks length: {len(prep_result['formatted_chunks'])}")
            print(f"Has embeddings: {prep_result['has_embeddings']}")

        print("✅ PromptFlow functions test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ PromptFlow functions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("🚀 Starting RAG CV Analysis Tests\n")

    results = []

    # 运行测试
    results.append(test_cv_chunking())
    results.append(test_cv_embedding())
    results.append(test_promptflow_functions())

    # 汇总结果
    print(f"\n{'='*50}")
    print("📊 Test Results Summary:")
    print(f"{'='*50}")

    test_names = ["CV Chunking", "CV Embedding", "PromptFlow Functions"]
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{i+1}. {name}: {status}")

    total_passed = sum(results)
    total_tests = len(results)

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("🎉 All tests passed! RAG CV analysis is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
