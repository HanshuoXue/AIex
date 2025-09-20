#!/usr/bin/env python3
"""
测试QA助手报告生成
"""
from api.qa_assistant import QAAssistant
import os
import sys
import asyncio
import json

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def test_qa_report():
    """测试QA助手报告生成"""
    try:
        print("🔍 初始化QA助手...")
        qa_assistant = QAAssistant()

        # 测试数据
        cv_analysis = {
            "education": "Bachelor's Degree in Computer Science",
            "experience": "2 years software development",
            "skills": ["Python", "JavaScript", "React"]
        }

        conversation_history = {
            "messages": [
                {"type": "user", "content": "I want to study computer science in New Zealand"},
                {"type": "user", "content": "I'm interested in AI and machine learning programs"}
            ]
        }

        user_id = "test-user-123"

        print("📝 开始生成报告...")
        result = await qa_assistant.generate_report(
            cv_analysis=cv_analysis,
            conversation_history=conversation_history,
            user_id=user_id
        )

        print("📊 报告生成结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get("success"):
            print("✅ 报告生成成功!")
            print(f"📄 报告URL: {result.get('report_url')}")
            print(f"🎯 匹配项目数: {result.get('programs_matched')}")
            print(f"⏰ 生成时间: {result.get('generation_time')}")
        else:
            print("❌ 报告生成失败!")
            print(f"错误: {result.get('error')}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_qa_report())
