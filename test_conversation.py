#!/usr/bin/env python3
"""
测试QA助手的对话功能
"""

import asyncio
import json
import requests
import time

# 测试数据
TEST_CV_ANALYSIS = {
    "education_details": "Bachelor's Degree in Computer Science",
    "skills": ["Python", "JavaScript", "React", "Machine Learning"],
    "experience": "2 years software development",
    "summary": "Experienced software developer with interest in AI/ML"
}

TEST_CONVERSATION = {
    "messages": [
        {
            "id": "1",
            "type": "user",
            "content": "I want to study computer science in New Zealand",
            "timestamp": "2025-09-21T01:00:00Z"
        },
        {
            "id": "2",
            "type": "user",
            "content": "I'm interested in AI and machine learning programs",
            "timestamp": "2025-09-21T01:01:00Z"
        }
    ]
}


def test_conversation_flow():
    """测试完整的对话流程"""
    base_url = "http://localhost:8000"

    print("🧪 开始测试QA助手对话功能...")
    print("=" * 50)

    # 1. 测试对话接口
    print("1️⃣ 测试对话接口...")
    try:
        response = requests.post(
            f"{base_url}/api/qa-assistant/conversation",
            json={
                "conversation_history": TEST_CONVERSATION,
                "cv_analysis": TEST_CV_ANALYSIS,
                "user_message": "I want to study computer science in New Zealand",
                "question_count": 2
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ 对话接口测试成功")
            print(f"📝 响应类型: {result.get('response_type', 'unknown')}")
            print(f"🎯 动作: {result.get('action', 'unknown')}")
            print(f"💬 内容: {result.get('content', '')[:200]}...")
            print(f"🔄 对话完成: {result.get('conversation_complete', False)}")
        else:
            print(f"❌ 对话接口测试失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 对话接口测试异常: {e}")
        return False

    print("\n" + "=" * 50)

    # 2. 测试报告生成接口
    print("2️⃣ 测试报告生成接口...")
    try:
        response = requests.post(
            f"{base_url}/api/qa-assistant/generate-report",
            json={
                "cv_analysis": TEST_CV_ANALYSIS,
                "conversation_history": TEST_CONVERSATION,
                "user_id": "test-user-123"
            },
            headers={"Content-Type": "application/json"},
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ 报告生成接口测试成功")
            print(f"📊 成功: {result.get('success', False)}")
            print(f"📄 报告URL: {result.get('report_url', 'N/A')}")
            print(f"🎯 匹配项目数: {result.get('programs_matched', 0)}")
            print(f"⏰ 生成模式: {result.get('generation_mode', 'unknown')}")

            # 显示调试信息
            debug_info = result.get('debug_info', {})
            if debug_info:
                print("\n🔍 调试信息:")
                print(
                    f"  - Embedding状态: {debug_info.get('embedding_status', 'unknown')}")
                print(
                    f"  - RAG匹配状态: {debug_info.get('rag_matching_status', 'unknown')}")
                print(
                    f"  - 报告长度: {debug_info.get('final_report_length', 0)} 字符")
                print(f"  - Flow结果键: {debug_info.get('flow_result_keys', [])}")
        else:
            print(f"❌ 报告生成接口测试失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 报告生成接口测试异常: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 对话功能测试完成！")
    return True


def test_server_health():
    """测试服务器健康状态"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            return True
        else:
            print(f"⚠️ 服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 服务器连接失败: {e}")
        return False


if __name__ == "__main__":
    print("🚀 启动QA助手对话功能测试")
    print("=" * 60)

    # 检查服务器状态
    if not test_server_health():
        print("请先启动服务器: python start_server.py")
        exit(1)

    # 运行对话测试
    success = test_conversation_flow()

    if success:
        print("\n🎊 所有测试通过！对话功能正常工作。")
    else:
        print("\n💥 测试失败，请检查服务器日志。")
