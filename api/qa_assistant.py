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
                logger.info(
                    "🚀 FAST MODE: Using provided report content for PDF generation")
                print("🚀 FAST MODE: Using provided report content for PDF generation")

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
                        "generation_time": datetime.now().isoformat(),
                        "generation_mode": "FAST_MODE"
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
                    "🔄 FULL MODE: Running complete QA Assistant flow for report generation")
                print(
                    "🔄 FULL MODE: Running complete QA Assistant flow for report generation")

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
                    "generation_mode": "FULL_MODE",
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

            # 强制使用Helvetica字体，避免编码问题
            base_font = 'Helvetica'
            logger.info(f"generate_pdf_from_content - Using font: {base_font}")
            print(f"generate_pdf_from_content - Using font: {base_font}")

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

            # 报告内容（转换Markdown为PDF）
            content_lines = report_content.split('\n')
            for line in content_lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 6))
                else:
                    # 过滤中文字符，只保留ASCII字符
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

            # 强制使用Helvetica字体，避免编码问题
            base_font = 'Helvetica'

            logger.info(
                f"Using font: {base_font} (forced to avoid encoding issues)")
            print(
                f"PDF Generation - Using font: {base_font} (forced to avoid encoding issues)")

            # 自定义样式
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=base_font,
                fontSize=24,
                spaceAfter=30,
                textColor=colors.darkblue,
                alignment=1  # 居中
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName=base_font,
                fontSize=16,
                spaceAfter=12,
                textColor=colors.darkblue
            )

            # 更新默认样式以支持中文
            for style_name in ['Normal', 'Heading1', 'Heading2', 'Heading3', 'Heading4']:
                if style_name in styles:
                    styles[style_name].fontName = base_font

            # 1. Title Page
            story.append(Paragraph(
                "New Zealand Study Abroad Personalized Recommendation Report", title_style))
            story.append(Spacer(1, 20))
            story.append(
                Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            story.append(Spacer(1, 40))

            # 2. Executive Summary
            story.append(Paragraph("Executive Summary", heading_style))

            # 基于对话生成摘要
            summary_text = self.generate_executive_summary(
                conversation_history, programs)
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(Spacer(1, 20))

            # 3. Background Analysis
            story.append(Paragraph("Background Analysis", heading_style))

            background_analysis = self.generate_background_analysis(
                conversation_history)
            for section_title, content in background_analysis.items():
                story.append(
                    Paragraph(f"<b>{section_title}</b>", styles['Heading3']))
                story.append(Paragraph(content, styles['Normal']))
                story.append(Spacer(1, 12))

            # 4. Program Recommendations
            story.append(Paragraph("Program Recommendations", heading_style))

            for i, program in enumerate(programs[:3], 1):
                story.append(Paragraph(
                    f"Recommended Program {i}: {program.get('program', 'Unknown Program')}", styles['Heading3']))

                # Program basic information table
                program_data = [
                    ['University', program.get('university', 'N/A')],
                    ['Campus', program.get('campus', 'N/A')],
                    ['Duration',
                        f"{program.get('duration_years', 'N/A')} years"],
                    ['Annual Tuition', f"NZ$ {program.get('tuition_nzd_per_year', 'N/A'):,}" if program.get(
                        'tuition_nzd_per_year') else 'N/A'],
                    ['Match Score',
                        f"{(program.get('matching_score', 0) * 100):.1f}%"]
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

                # Match Analysis
                match_analysis = self.generate_program_match_analysis(
                    program, conversation_history)
                story.append(
                    Paragraph("<b>Match Analysis</b>", styles['Heading4']))
                story.append(Paragraph(match_analysis, styles['Normal']))
                story.append(Spacer(1, 20))

            # 5. Application Strategy
            story.append(Paragraph("Application Strategy", heading_style))

            application_strategy = self.generate_application_strategy(
                conversation_history, programs)
            for section_title, content in application_strategy.items():
                story.append(
                    Paragraph(f"<b>{section_title}</b>", styles['Heading3']))
                story.append(Paragraph(content, styles['Normal']))
                story.append(Spacer(1, 12))

            # 6. New Zealand Study Guide
            story.append(Paragraph("New Zealand Study Guide", heading_style))

            study_guide = self.generate_study_guide()
            for section_title, content in study_guide.items():
                story.append(
                    Paragraph(f"<b>{section_title}</b>", styles['Heading3']))
                story.append(Paragraph(content, styles['Normal']))
                story.append(Spacer(1, 12))

            # 7. Action Plan
            story.append(Paragraph("Action Plan", heading_style))

            action_plan = self.generate_action_plan(conversation_history)
            for section_title, items in action_plan.items():
                story.append(
                    Paragraph(f"<b>{section_title}</b>", styles['Heading3']))
                for item in items:
                    story.append(Paragraph(f"• {item}", styles['Normal']))
                story.append(Spacer(1, 12))

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

    def generate_executive_summary(self, conversation_history: Dict[str, str], programs: list) -> str:
        """Generate executive summary"""
        motivation = conversation_history.get(
            "study_motivation", "enhance personal capabilities")
        field = conversation_history.get("preferred_field", "business")
        level = conversation_history.get("study_level", "postgraduate")

        summary = f"Based on your background analysis and detailed conversation, we have carefully selected {len(programs)} most suitable study abroad programs in New Zealand for you. "
        summary += f"You aim to {motivation} through {level} level studies, focusing on {field} related fields. "
        summary += "Our recommendations fully consider your academic background, career planning, budget constraints, and city preferences, "
        summary += "aiming to provide you with the most valuable study abroad experience and career development opportunities."

        return summary

    def generate_background_analysis(self, conversation_history: Dict[str, str]) -> Dict[str, str]:
        """Generate background analysis"""
        return {
            "Study Motivation": conversation_history.get("study_motivation", "Not clearly specified"),
            "Field Interest": conversation_history.get("preferred_field", "Not clearly specified"),
            "Career Goals": conversation_history.get("career_goals", "Not clearly specified"),
            "Work Experience": conversation_history.get("work_experience", "Not clearly specified"),
            "English Proficiency": conversation_history.get("english_proficiency", "Not clearly specified"),
            "Special Requirements": conversation_history.get("special_requirements", "No special requirements") or "No special requirements"
        }

    def generate_program_match_analysis(self, program: Dict[str, Any], conversation_history: Dict[str, str]) -> str:
        """Generate program match analysis"""
        analysis = f"This program is highly suitable for you, with the following key reasons: "

        # Field match
        preferred_field = conversation_history.get("preferred_field", "")
        if preferred_field:
            analysis += f"Field alignment - the program's focus aligns perfectly with your interest in {preferred_field}; "

        # Location match
        location_pref = conversation_history.get("location_preference", "")
        campus = program.get("campus", "")
        if location_pref and campus:
            if any(city.lower() in location_pref.lower() for city in [campus]):
                analysis += f"Campus location - the {campus} campus is in your preferred area; "

        # Budget match
        budget = conversation_history.get("budget_range", "")
        tuition = program.get("tuition_nzd_per_year")
        if budget and tuition:
            analysis += f"Tuition affordability - annual tuition NZ${tuition:,} fits your budget expectations; "

        # Career development
        career_goals = conversation_history.get("career_goals", "")
        if career_goals:
            analysis += f"Career alignment - the curriculum closely relates to your career development goals: {career_goals}."

        return analysis

    def generate_application_strategy(self, conversation_history: Dict[str, str], programs: list) -> Dict[str, str]:
        """生成申请策略"""
        english_level = conversation_history.get("english_proficiency", "")

        return {
            "Application Timeline": "Recommend starting application preparation 12-18 months in advance to ensure sufficient time for document preparation and language tests. Main intake periods are February and July each year.",
            "Document Checklist": "Academic transcripts, English test scores (IELTS/TOEFL), personal statement, recommendation letters, CV/resume, passport copy, etc.",
            "Language Test Advice": f"Based on your current English level ({english_level}), recommend targeted IELTS preparation with target score 6.5-7.0.",
            "Background Enhancement": "Consider participating in relevant internships, volunteer activities, professional certifications to enhance application competitiveness."
        }

    def generate_study_guide(self) -> Dict[str, str]:
        """Generate study guide"""
        return {
            "Visa Application": "Student visa application requires offer letter, financial proof, medical examination report, etc. Recommend applying 2-3 months in advance.",
            "Accommodation Options": "Choose from university dormitories, homestay, or private rental. University dorms are safer and convenient, homestay helps with cultural integration.",
            "Living Costs": "New Zealand living expenses approximately NZ$15,000-20,000/year, including accommodation, meals, transportation, entertainment, etc.",
            "Work Opportunities": "Student visa allows 20 hours work per week, full-time during holidays. Can apply for work visa after graduation."
        }

    def generate_action_plan(self, conversation_history: Dict[str, str]) -> Dict[str, list]:
        """生成行动计划"""
        return {
            "Short-term Actions (1-3 months)": [
                "Complete personal statement and application materials",
                "Prepare and take IELTS exam",
                "Contact recommenders for recommendation letters",
                "Research specific application requirements and deadlines"
            ],
            "Medium-term Planning (3-6 months)": [
                "Submit formal applications",
                "Prepare visa application materials",
                "Arrange accommodation and airport pickup",
                "Learn about target city living information"
            ],
            "Long-term Goals (6+ months)": [
                "Receive offer letters",
                "Complete visa application",
                "Arrange pre-departure preparations",
                "Develop study and career development plans"
            ]
        }


# 全局实例
qa_assistant = QAAssistant()
