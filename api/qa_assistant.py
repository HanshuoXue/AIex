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
from io import BytesIO
import tempfile

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QAAssistant:
    def __init__(self):
        """初始化QA助手"""
        self.pf_client = PFClient()

        # QA助手flow路径 - 使用智能化Flow
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.flow_path = os.path.join(current_dir, "flows", "qa_assistant")
        self.intelligent_flow_config = os.path.join(
            self.flow_path, "intelligent_qa_flow.dag.yaml")

        # 确保flow路径存在
        if not os.path.exists(self.flow_path):
            logger.error(f"QA Assistant flow path not found: {self.flow_path}")

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

    async def generate_report(self, cv_analysis: Dict[str, Any], conversation_history: Dict[str, str], user_id: str, report_content: str = None, matched_programs: List[Dict] = None) -> Dict[str, Any]:
        """
        生成个性化留学建议报告
        """
        try:
            logger.info(f"Starting report generation for user {user_id}")

            # 如果已经有报告内容，直接生成PDF
            if report_content and matched_programs is not None:
                logger.info("Using provided report content for PDF generation")

                # 生成PDF报告
                report_filename = f"study_report_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                report_path = os.path.join(self.reports_dir, report_filename)

                pdf_success = await self.generate_pdf_from_content(
                    report_content=report_content,
                    programs=matched_programs,
                    conversation_history=conversation_history,
                    output_path=report_path
                )

                if pdf_success:
                    return {
                        "success": True,
                        "report_url": f"/api/reports/{report_filename}",
                        "report_path": report_path,
                        "programs_matched": len(matched_programs),
                        "generation_time": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": "PDF generation failed",
                        "report_content": report_content
                    }

            # 否则运行完整的flow生成报告
            else:
                logger.info(
                    "Running full QA Assistant flow for report generation")

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
                flow_result = self.pf_client.test(
                    flow=self.flow_path,
                    inputs={
                        "cv_analysis": cv_analysis or {},
                        "conversation_history": {"messages": []},
                        "user_profile": user_profile
                    }
                )

                logger.info("Flow execution completed")

                # 提取结果
                top_programs = flow_result.get("matched_programs", [])
                final_report_content = flow_result.get("final_report", "")

                # 生成PDF报告
                report_filename = f"study_report_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                report_path = os.path.join(self.reports_dir, report_filename)

                pdf_success = await self.generate_pdf_from_content(
                    report_content=final_report_content,
                    programs=top_programs,
                    conversation_history=conversation_history,
                    output_path=report_path
                )

            if pdf_success:
                # 返回成功结果
                return {
                    "success": True,
                    "report_url": f"/api/reports/{report_filename}",
                    "report_path": report_path,
                    "programs_matched": len(top_programs.get("matched_programs", [])),
                    "generation_time": datetime.now().isoformat(),
                    "flow_details": {
                        "matching_status": top_programs.get("status", "unknown"),
                        "matching_strategy": top_programs.get("matching_details", {}).get("matching_strategy", "default")
                    }
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

    async def generate_pdf_from_content(self, report_content: str, programs: list, conversation_history: Dict[str, str], output_path: str) -> bool:
        """
        从报告内容生成PDF
        """
        try:
            logger.info(f"Generating PDF from content: {output_path}")

            # 创建PDF文档
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # 标题
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                spaceAfter=20,
                textColor=colors.darkblue,
                alignment=1
            )

            story.append(Paragraph("新西兰留学个性化建议报告", title_style))
            story.append(Spacer(1, 20))
            story.append(
                Paragraph(f"生成时间: {datetime.now().strftime('%Y年%m月%d日')}", styles['Normal']))
            story.append(Spacer(1, 20))

            # 报告内容（转换Markdown为PDF）
            content_lines = report_content.split('\n')
            for line in content_lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 6))
                elif line.startswith('# '):
                    story.append(Paragraph(line[2:], styles['Heading1']))
                elif line.startswith('## '):
                    story.append(Paragraph(line[3:], styles['Heading2']))
                elif line.startswith('### '):
                    story.append(Paragraph(line[4:], styles['Heading3']))
                elif line.startswith('- '):
                    story.append(Paragraph(f"• {line[2:]}", styles['Normal']))
                else:
                    story.append(Paragraph(line, styles['Normal']))
                story.append(Spacer(1, 3))

            # 构建PDF
            doc.build(story)

            logger.info(f"PDF report generated successfully: {output_path}")
            return True

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return False

    async def generate_pdf_report(self, report_content: Dict[str, Any], programs: list, user_profile: Dict[str, Any], conversation_history: Dict[str, str], output_path: str) -> bool:
        """
        生成PDF报告
        """
        try:
            logger.info(f"Generating PDF report: {output_path}")

            # 创建PDF文档
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # 自定义样式
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.darkblue,
                alignment=1  # 居中
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.darkblue
            )

            # 1. 标题页
            story.append(Paragraph("新西兰留学个性化建议报告", title_style))
            story.append(Spacer(1, 20))
            story.append(
                Paragraph(f"生成时间: {datetime.now().strftime('%Y年%m月%d日')}", styles['Normal']))
            story.append(Spacer(1, 40))

            # 2. 执行摘要
            story.append(Paragraph("执行摘要", heading_style))

            # 基于对话生成摘要
            summary_text = self.generate_executive_summary(
                conversation_history, programs)
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(Spacer(1, 20))

            # 3. 用户背景分析
            story.append(Paragraph("用户背景分析", heading_style))

            background_analysis = self.generate_background_analysis(
                conversation_history)
            for section_title, content in background_analysis.items():
                story.append(
                    Paragraph(f"<b>{section_title}</b>", styles['Heading3']))
                story.append(Paragraph(content, styles['Normal']))
                story.append(Spacer(1, 12))

            # 4. 项目推荐详解
            story.append(Paragraph("项目推荐详解", heading_style))

            for i, program in enumerate(programs[:3], 1):
                story.append(Paragraph(
                    f"推荐项目 {i}: {program.get('program', 'Unknown Program')}", styles['Heading3']))

                # 项目基本信息表格
                program_data = [
                    ['大学', program.get('university', 'N/A')],
                    ['校区', program.get('campus', 'N/A')],
                    ['学制', f"{program.get('duration_years', 'N/A')} 年"],
                    ['年学费', f"NZ$ {program.get('tuition_nzd_per_year', 'N/A'):,}" if program.get(
                        'tuition_nzd_per_year') else 'N/A'],
                    ['匹配度', f"{(program.get('matching_score', 0) * 100):.1f}%"]
                ]

                program_table = Table(program_data, colWidths=[2*inch, 3*inch])
                program_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))

                story.append(program_table)
                story.append(Spacer(1, 12))

                # 匹配分析
                match_analysis = self.generate_program_match_analysis(
                    program, conversation_history)
                story.append(Paragraph("<b>匹配分析</b>", styles['Heading4']))
                story.append(Paragraph(match_analysis, styles['Normal']))
                story.append(Spacer(1, 20))

            # 5. 申请策略建议
            story.append(Paragraph("申请策略建议", heading_style))

            application_strategy = self.generate_application_strategy(
                conversation_history, programs)
            for section_title, content in application_strategy.items():
                story.append(
                    Paragraph(f"<b>{section_title}</b>", styles['Heading3']))
                story.append(Paragraph(content, styles['Normal']))
                story.append(Spacer(1, 12))

            # 6. 新西兰留学指南
            story.append(Paragraph("新西兰留学指南", heading_style))

            study_guide = self.generate_study_guide()
            for section_title, content in study_guide.items():
                story.append(
                    Paragraph(f"<b>{section_title}</b>", styles['Heading3']))
                story.append(Paragraph(content, styles['Normal']))
                story.append(Spacer(1, 12))

            # 7. 后续行动计划
            story.append(Paragraph("后续行动计划", heading_style))

            action_plan = self.generate_action_plan(conversation_history)
            for section_title, items in action_plan.items():
                story.append(
                    Paragraph(f"<b>{section_title}</b>", styles['Heading3']))
                for item in items:
                    story.append(Paragraph(f"• {item}", styles['Normal']))
                story.append(Spacer(1, 12))

            # 构建PDF
            doc.build(story)

            logger.info(f"PDF report generated successfully: {output_path}")
            return True

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return False

    def generate_executive_summary(self, conversation_history: Dict[str, str], programs: list) -> str:
        """生成执行摘要"""
        motivation = conversation_history.get("study_motivation", "提升个人能力")
        field = conversation_history.get("preferred_field", "商科")
        level = conversation_history.get("study_level", "研究生")

        summary = f"基于您的背景分析和详细对话，我们为您精选了{len(programs)}个最适合的新西兰留学项目。"
        summary += f"您希望通过{level}阶段的学习来{motivation}，专注于{field}相关领域。"
        summary += "我们的推荐充分考虑了您的学术背景、职业规划、预算限制和城市偏好，"
        summary += "旨在为您提供最具价值的留学体验和职业发展机会。"

        return summary

    def generate_background_analysis(self, conversation_history: Dict[str, str]) -> Dict[str, str]:
        """生成背景分析"""
        return {
            "学习动机": conversation_history.get("study_motivation", "未详细说明学习动机"),
            "专业兴趣": conversation_history.get("preferred_field", "未明确专业方向"),
            "职业规划": conversation_history.get("career_goals", "未详细说明职业目标"),
            "工作经验": conversation_history.get("work_experience", "工作经验信息不详"),
            "英语能力": conversation_history.get("english_proficiency", "英语水平信息不详"),
            "特殊要求": conversation_history.get("special_requirements", "无特殊要求") or "无特殊要求"
        }

    def generate_program_match_analysis(self, program: Dict[str, Any], conversation_history: Dict[str, str]) -> str:
        """生成项目匹配分析"""
        analysis = f"该项目非常适合您，主要原因包括："

        # 专业匹配
        preferred_field = conversation_history.get("preferred_field", "")
        if preferred_field:
            analysis += f"专业方向与您感兴趣的{preferred_field}领域高度吻合；"

        # 城市匹配
        location_pref = conversation_history.get("location_preference", "")
        campus = program.get("campus", "")
        if location_pref and campus:
            if any(city.lower() in location_pref.lower() for city in [campus]):
                analysis += f"校区位于您偏好的{campus}地区；"

        # 预算匹配
        budget = conversation_history.get("budget_range", "")
        tuition = program.get("tuition_nzd_per_year")
        if budget and tuition:
            analysis += f"年学费{tuition:,}新西兰元符合您的预算预期；"

        # 职业发展
        career_goals = conversation_history.get("career_goals", "")
        if career_goals:
            analysis += f"课程设置与您的职业发展目标{career_goals}密切相关。"

        return analysis

    def generate_application_strategy(self, conversation_history: Dict[str, str], programs: list) -> Dict[str, str]:
        """生成申请策略"""
        english_level = conversation_history.get("english_proficiency", "")

        return {
            "申请时间规划": "建议提前12-18个月开始准备申请，确保有充足时间准备材料和语言考试。主要申请季为每年2月和7月入学。",
            "材料准备清单": "学历证明及成绩单、英语成绩证明(IELTS/TOEFL)、个人陈述、推荐信、CV/简历、护照复印件等。",
            "语言考试建议": f"根据您目前的英语水平({english_level})，建议针对性准备IELTS考试，目标分数6.5-7.0分。",
            "背景提升建议": "可考虑参与相关实习、志愿活动、专业证书考试等来增强申请竞争力。"
        }

    def generate_study_guide(self) -> Dict[str, str]:
        """生成留学指南"""
        return {
            "签证申请": "学生签证申请需要提供录取通知书、资金证明、体检报告等材料。建议提前2-3个月申请。",
            "住宿安排": "可选择学校宿舍、寄宿家庭或自租公寓。学校宿舍相对安全便利，寄宿家庭有助于文化融入。",
            "生活费用": "新西兰生活费约15,000-20,000新西兰元/年，包括住宿、餐饮、交通、娱乐等费用。",
            "工作机会": "学生签证允许每周工作20小时，假期可全职工作。毕业后可申请工作签证。"
        }

    def generate_action_plan(self, conversation_history: Dict[str, str]) -> Dict[str, list]:
        """生成行动计划"""
        return {
            "短期行动项 (1-3个月)": [
                "完善个人陈述和申请材料",
                "准备并参加IELTS考试",
                "联系推荐人准备推荐信",
                "研究具体的申请要求和截止日期"
            ],
            "中期规划 (3-6个月)": [
                "提交正式申请",
                "准备签证申请材料",
                "安排住宿和接机服务",
                "了解目标城市的生活信息"
            ],
            "长期目标 (6个月以上)": [
                "获得录取通知书",
                "完成签证申请",
                "安排行前准备",
                "制定学习和职业发展规划"
            ]
        }


# 全局实例
qa_assistant = QAAssistant()
