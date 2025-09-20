#!/usr/bin/env python3
"""
直接测试QA助手的对话功能，绕过认证
"""

from api.qa_assistant import QAAssistant
import asyncio
import sys
import os

# 添加api目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))


async def test_conversation():
    """测试对话功能"""
    print("🧪 开始测试QA助手对话功能...")
    print("=" * 50)

    # 初始化QA助手
    qa_assistant = QAAssistant()

    # 测试数据
    conversation_history = {
        "messages": [
            {
                "id": "1",
                "type": "user",
                "content": "I want to study computer science in New Zealand",
                "timestamp": "2025-09-21T02:00:00Z"
            }
        ]
    }

    cv_analysis = {
        "education_details": "Bachelor Degree in Computer Science",
        "skills": ["Python", "JavaScript", "React", "Machine Learning"],
        "experience": "2 years software development"
    }

    user_message = "I want to study computer science in New Zealand"
    question_count = 1

    try:
        print("1️⃣ 测试对话处理...")
        result = await qa_assistant.process_conversation(
            conversation_history=conversation_history,
            cv_analysis=cv_analysis,
            user_message=user_message
        )

        print("✅ 对话处理成功")
        print(f"📝 响应类型: {result.get('response_type', 'unknown')}")
        print(f"🎯 动作: {result.get('action', 'unknown')}")
        print(f"💬 内容: {result.get('content', '')[:200]}...")
        print(f"🔄 对话完成: {result.get('conversation_complete', False)}")

        return True

    except Exception as e:
        print(f"❌ 对话处理失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_conversation())

    if success:
        print("\n🎊 对话功能测试通过！")
    else:
        print("\n💥 对话功能测试失败！")
