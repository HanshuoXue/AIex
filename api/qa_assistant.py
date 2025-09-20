import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from promptflow.client import PFClient
from datetime import datetime
import logging
import uuid
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import tempfile

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 注册中文字体


def register_chinese_fonts():
    """注册中文字体"""
    try:
        # 尝试注册系统中文字体
        import platform
        system = platform.system()

        if system == "Darwin":  # macOS
            font_paths = [
                "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
                "/System/Library/Fonts/HelveticaNeue.ttc",
                "/System/Library/Fonts/Supplemental/Arial.ttf"
            ]
        elif system == "Windows":
            font_paths = [
                "C:/Windows/Fonts/simsun.ttc",
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simhei.ttf"
            ]
        else:  # Linux
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
            ]

        # 尝试注册字体
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    logger.info(
                        f"Successfully registered Chinese font: {font_path}")
                    return True
            except Exception as e:
                logger.warning(f"Failed to register font {font_path}: {e}")
                continue

        # 如果都失败了，使用默认字体
        logger.warning("No Chinese fonts found, using default font")
        return False

    except Exception as e:
        logger.error(f"Error registering Chinese fonts: {e}")
        return False


# 初始化时注册字体
register_chinese_fonts()


class QAAssistant:
    def __init__(self):
        """初始化QA助手"""
        self.pf_client = PFClient()

        # QA助手flow路径 - 使用智能化Flow
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.flow_path = os.path.join(current_dir, "flows", "qa_assistant")
        self.flow_config = os.path.join(self.flow_path, "flow.dag.yaml")

        # 确保flow路径存在
        if not os.path.exists(self.flow_path):
            logger.error(f"QA Assistant flow path not found: {self.flow_path}")
        if not os.path.exists(self.flow_config):
            logger.error(
                f"QA Assistant flow config not found: {self.flow_config}")

        # 报告存储目录
        self.reports_dir = os.path.join(current_dir, "..", "reports")
        os.makedirs(self.reports_dir, exist_ok=True)

        logger.info(
            f"QA Assistant initialized with flow path: {self.flow_path}")

    async def process_conversation(self, conversation_history: Dict[str, Any], user_message: str, cv_analysis: Dict[str, Any] = None, session_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        使用智能Flow处理对话
        """
        try:
            logger.info("Processing conversation with intelligent QA flow...")

            # 准备输入数据
            flow_inputs = {
                "conversation_history": conversation_history or {"messages": []},
                "user_message": user_message or "",
                "cv_analysis": cv_analysis or {},
                "session_state": session_state or {}
            }

            # 运行智能QA Flow
            flow_result = self.pf_client.test(
                flow=self.flow_path,  # 使用flow目录而不是specific config文件
                inputs=flow_inputs
            )

            logger.info("Intelligent QA flow completed successfully")

            # 提取结果
            action = flow_result.get("action", "ask_question")
            next_question = flow_result.get("next_question", "")
            final_report = flow_result.get("final_report", "")
            matched_programs = flow_result.get("matched_programs", [])

            # 构建响应
            if action == "generate_report" and final_report:
                response = {
                    "response_type": "final_report",
                    "content": final_report,
                    "action": "show_report",
                    "conversation_complete": True,
                    "matched_programs": matched_programs
                }
            elif action == "generate_report":
                response = {
                    "response_type": "generating_report",
                    "content": "太好了！我已经收集到足够信息。现在正在为您匹配最适合的项目并生成个性化报告...",
                    "action": "generate_report",
                    "conversation_complete": False
                }
            else:
                response = {
                    "response_type": "question",
                    "content": next_question or "请告诉我更多关于您的留学需求。",
                    "action": "continue_conversation",
                    "conversation_complete": False
                }

            return {
                "success": True,
                "response": response,
                "session_update": {
                    "action": action,
                    "question_count": len([msg for msg in conversation_history.get("messages", []) if msg.get("type") == "user"])
                },
                "flow_result": flow_result
            }

        except Exception as e:
            logger.error(f"Intelligent conversation processing failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")

            # 返回fallback响应
            return {
                "success": False,
                "error": str(e),
                "response": {
                    "response_type": "fallback",
                    "content": "抱歉，我在处理您的消息时遇到了问题。请告诉我您对新西兰留学最关心的是什么？",
                    "action": "continue_conversation",
                    "conversation_complete": False
                },
                "session_update": {
                    "updated_session_state": session_state or {},
                    "updated_conversation_history": conversation_history or {"messages": []}
                }
            }

    async def generate_report(self, cv_analysis: Dict[str, Any], conversation_history: Dict[str, str], user_id: str) -> Dict[str, Any]:
        """
        生成个性化留学建议报告 - 完整模式
        结合CV分析、聊天历史和项目匹配，生成个性化报告
        """
        try:
            logger.info(f"Starting report generation for user {user_id}")
            logger.info(
                "🔄 FULL MODE: Running complete QA Assistant flow for report generation")
            print("🔄 FULL MODE: Running complete QA Assistant flow for report generation")

            # 准备用户画像
            user_profile = {
                "user_id": user_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "basic_info": {
                    "has_cv": bool(cv_analysis),
                    "conversation_completed": len(conversation_history) >= 8
                }
            }

            # 运行QA助手flow
            logger.info("🔄 开始执行PromptFlow...")
            print("🔄 开始执行PromptFlow...")

            flow_result = self.pf_client.test(
                flow=self.flow_config,
                inputs={
                    "cv_analysis": cv_analysis or {},
                    "conversation_history": conversation_history,
                    "user_message": "Generate personalized study abroad report",
                    "question_count": 2  # 表示已经问够问题，可以生成报告
                }
            )

            logger.info("✅ Flow execution completed")
            print("✅ Flow execution completed")
            logger.info(
                f"📊 Flow result keys: {list(flow_result.keys()) if flow_result else 'None'}")
            print(
                f"📊 Flow result keys: {list(flow_result.keys()) if flow_result else 'None'}")

            # 提取结果
            top_programs = flow_result.get("matched_programs", [])
            final_report_content = flow_result.get("final_report", "")

            # 详细调试信息
            debug_info = {
                "flow_result_keys": list(flow_result.keys()) if flow_result else [],
                "matched_programs_count": len(top_programs) if isinstance(top_programs, list) else 0,
                "final_report_length": len(final_report_content) if final_report_content else 0,
                "embedding_status": "unknown",  # 将在下面更新
                "rag_matching_status": "unknown"  # 将在下面更新
            }

            # 检查embedding和RAG状态
            embedding_result = flow_result.get("embedding_generator", {})
            rag_result = flow_result.get("rag_matcher", {})

            if embedding_result.get("status") == "success":
                debug_info["embedding_status"] = "success"
                debug_info["embedding_dimension"] = embedding_result.get(
                    "dimension", 0)
            else:
                debug_info["embedding_status"] = "fallback_used"
                debug_info["embedding_error"] = embedding_result.get(
                    "error", "unknown")

            if rag_result.get("status") == "success":
                debug_info["rag_matching_status"] = "success"
                debug_info["rag_programs_count"] = rag_result.get(
                    "programs_count", 0)
            else:
                debug_info["rag_matching_status"] = "fallback_used"
                debug_info["rag_reason"] = rag_result.get("reason", "unknown")

            logger.info(f"🔍 Debug info: {debug_info}")
            print(f"🔍 Debug info: {debug_info}")

            # 生成PDF报告
            report_filename = f"study_report_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            report_path = os.path.join(self.reports_dir, report_filename)

            pdf_success = await self.generate_pdf_report(
                cv_analysis=cv_analysis,
                matched_programs=top_programs,
                conversation_history=conversation_history,
                user_profile=user_profile,
                final_report_content=final_report_content,
                output_path=report_path
            )

            if pdf_success:
                # 返回成功结果
                return {
                    "success": True,
                    "report_url": f"/api/reports/{report_filename}",
                    "report_path": report_path,
                    "programs_matched": len(top_programs) if isinstance(top_programs, list) else 0,
                    "generation_time": datetime.now().isoformat(),
                    "generation_mode": "FULL_MODE",
                    "flow_details": {
                        "matching_status": "completed",
                        "matching_strategy": "full_llm_analysis"
                    },
                    "debug_info": debug_info,
                    "flow_result": flow_result  # 包含完整的flow结果
                }
            else:
                return {
                    "success": False,
                    "error": "PDF report generation failed",
                    "flow_result": flow_result
                }

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")

            return {
                "success": False,
                "error": f"Report generation failed: {str(e)}",
                "details": str(e)
            }

    async def generate_pdf_report(self, cv_analysis: Dict[str, Any], matched_programs: list, conversation_history: Dict[str, str], user_profile: Dict[str, Any], final_report_content: str, output_path: str) -> bool:
        """
        生成PDF报告 - 使用LLM模板生成英文内容
        """
        try:
            logger.info(f"Generating PDF report: {output_path}")

            # 使用已经生成的报告内容
            report_content = final_report_content

            # 创建PDF文档
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # 强制使用Helvetica字体，避免编码问题
            base_font = 'Helvetica'
            logger.info(
                f"Using font: {base_font} (forced to avoid encoding issues)")
            print(
                f"PDF Generation - Using font: {base_font} (forced to avoid encoding issues)")

            # 更新默认样式以使用Helvetica
            for style_name in ['Normal', 'Heading1', 'Heading2', 'Heading3', 'Heading4']:
                if style_name in styles:
                    styles[style_name].fontName = base_font

            # 标题
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=base_font,
                fontSize=20,
                spaceAfter=20,
                textColor=colors.darkblue,
                alignment=1
            )

            story.append(Paragraph(
                "New Zealand Study Abroad Personalized Recommendation Report", title_style))
            story.append(Spacer(1, 20))
            story.append(
                Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            story.append(Spacer(1, 20))

            # 使用LLM生成的内容
            content_lines = report_content.split('\n')
            for line in content_lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 6))
                else:
                    # 过滤非ASCII字符，确保只有英文
                    filtered_line = ''.join(
                        char for char in line if ord(char) < 128)

                    if filtered_line.startswith('# '):
                        story.append(
                            Paragraph(filtered_line[2:], styles['Heading1']))
                    elif filtered_line.startswith('## '):
                        story.append(
                            Paragraph(filtered_line[3:], styles['Heading2']))
                    elif filtered_line.startswith('### '):
                        story.append(
                            Paragraph(filtered_line[4:], styles['Heading3']))
                    elif filtered_line.startswith('- '):
                        story.append(
                            Paragraph(f"• {filtered_line[2:]}", styles['Normal']))
                    else:
                        story.append(
                            Paragraph(filtered_line, styles['Normal']))
                    story.append(Spacer(1, 3))

            # 构建PDF
            doc.build(story)

            # 验证PDF文件
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(
                    f"PDF report generated successfully: {output_path} (size: {os.path.getsize(output_path)} bytes)")
                return True
            else:
                logger.error(f"PDF file not created or empty: {output_path}")
                return False

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    async def generate_llm_report_content(self, cv_analysis: Dict[str, Any], matched_programs: list, conversation_history: Dict[str, str], user_profile: Dict[str, Any]) -> str:
        """
        使用LLM生成英文报告内容 - 完全个性化，无预填写模板
        """
        try:
            logger.info(
                "Generating personalized report content using PromptFlow LLM")

            # 调用PromptFlow生成完全个性化的报告内容
            logger.info(
                f"Calling PromptFlow with inputs: cv_analysis={bool(cv_analysis)}, conversation_history={len(conversation_history)}")

            response = self.pf_client.test(
                flow=self.flow_config,
                inputs={
                    "cv_analysis": cv_analysis,
                    "conversation_history": conversation_history,
                    "user_message": "Generate personalized study abroad report",
                    "question_count": 2  # 表示已经问够问题，可以生成报告
                }
            )

            logger.info(
                f"PromptFlow response keys: {list(response.keys()) if response else 'None'}")
            logger.info(f"PromptFlow response: {response}")

            # 提取生成的报告内容
            report_content = response.get("final_report", "")

            if not report_content:
                logger.warning(
                    "LLM did not return report content, using fallback")
                logger.warning(f"Response was: {response}")
                report_content = self.generate_fallback_report(
                    cv_analysis, matched_programs, conversation_history)
            else:
                logger.info(
                    "Successfully generated personalized report content from LLM")
                logger.info(f"Report content length: {len(report_content)}")

            return report_content

        except Exception as e:
            logger.error(f"LLM report generation failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # 使用备用模板
            return self.generate_fallback_report(cv_analysis, matched_programs, conversation_history)

    def generate_fallback_report(self, cv_analysis: Dict[str, Any], matched_programs: list, conversation_history: Dict[str, str]) -> str:
        """
        备用报告模板（当LLM失败时使用）
        """
        return """# Study Abroad Report Generation Failed

We apologize, but we were unable to generate your personalized study abroad report at this time. 

Please try again or contact support if the issue persists.

## Error Information
- CV Analysis: Available
- Conversation History: Available  
- Matched Programs: Available
- Report Generation: Failed

Please retry the report generation process.
"""


# 全局实例
qa_assistant = QAAssistant()
