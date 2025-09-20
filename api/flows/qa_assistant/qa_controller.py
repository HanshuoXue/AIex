from promptflow import tool
from typing import Dict, Any


@tool
def control_qa_flow(conversation_history: Dict[str, Any], user_message: str, cv_analysis: Dict[str, Any], question_count: int) -> str:
    """
    线性控制QA流程
    1. 上传简历/开始对话
    2. 问10个问题
    3. 生成报告
    """
    try:
        # 获取用户消息数量
        messages = conversation_history.get("messages", [])
        user_messages = [msg for msg in messages if msg.get("type") == "user"]
        current_question_count = len(user_messages)

        print(f"当前问题数量: {current_question_count}")
        print(f"用户消息: {user_message}")
        print(f"是否有CV: {bool(cv_analysis)}")

        # 阶段1: 如果问题少于10个，继续提问
        if current_question_count < 2:
            print(f"继续提问 (第{current_question_count + 1}个问题)")
            return "ask_question"

        # 阶段2: 问够10个问题，生成报告
        else:
            print("问题收集完成，开始生成报告")
            return "generate_report"

    except Exception as e:
        print(f"QA控制器错误: {e}")
        return "ask_question"  # 默认继续提问
