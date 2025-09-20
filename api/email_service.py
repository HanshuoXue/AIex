"""
邮件服务模块
用于发送密码重置邮件
支持SMTP方式（MailerSend/Gmail等）
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv

# 加载.env文件
import sys
from pathlib import Path

# 确保从项目根目录加载.env文件
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)


class EmailService:
    """邮件服务类"""

    def __init__(self):
        # SMTP配置（MailerSend）
        self.smtp_server = os.getenv('MAILSEND_Server', 'smtp.mailersend.net')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('MAILSEND_UserName')
        self.smtp_password = os.getenv('MAILSEND_PassWord')
        # 使用MailerSend的验证域名作为发件人
        self.from_email = self.smtp_username if self.smtp_username else os.getenv(
            'FROM_EMAIL', 'noreply@alex-system.com')

        # 调试信息（可选，生产环境可以注释掉）
        # print(f"📧 SMTP配置:")
        # print(f"  服务器: {self.smtp_server}")
        # print(f"  端口: {self.smtp_port}")
        # print(f"  用户名: {self.smtp_username[:10]}..." if self.smtp_username else "  用户名: 未设置")
        # print(f"  密码: {'已设置' if self.smtp_password else '未设置'}")
        # print(f"  发件人: {self.from_email}")

    def send_password_reset_email(self, to_email: str, reset_token: str, username: str) -> bool:
        """发送密码重置邮件"""
        try:
            # 生成重置链接
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
            reset_link = f"{frontend_url}/reset-password?token={reset_token}"

            # 创建邮件内容
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Alex系统 - 密码重置'
            msg['From'] = self.from_email
            msg['To'] = to_email

            # HTML邮件内容
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>密码重置</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 30px; background-color: #f9f9f9; }}
                    .button {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                    .warning {{ color: #dc2626; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎓 Alex系统</h1>
                        <p>New Zealand Study Program Smart Matching System</p>
                    </div>
                    
                    <div class="content">
                        <h2>密码重置请求</h2>
                        <p>亲爱的 {username}，</p>
                        <p>我们收到了您的密码重置请求。点击下面的按钮来重置您的密码：</p>
                        
                        <p style="text-align: center;">
                            <a href="{reset_link}" class="button">重置密码</a>
                        </p>
                        
                        <p>或者复制以下链接到浏览器中打开：</p>
                        <p style="word-break: break-all; color: #4F46E5;">{reset_link}</p>
                        
                        <div class="warning">
                            <p>⚠️ 重要提醒：</p>
                            <ul>
                                <li>此链接将在24小时后过期</li>
                                <li>如果您没有请求重置密码，请忽略此邮件</li>
                                <li>请勿将此链接分享给他人</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>此邮件由Alex系统自动发送，请勿直接回复。</p>
                        <p>如有疑问，请联系系统管理员。</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # 纯文本版本
            text_content = f"""
Alex系统 - 密码重置

亲爱的 {username}，

我们收到了您的密码重置请求。请复制以下链接到浏览器中打开来重置您的密码：

{reset_link}

重要提醒：
- 此链接将在24小时后过期
- 如果您没有请求重置密码，请忽略此邮件
- 请勿将此链接分享给他人

此邮件由Alex系统自动发送，请勿直接回复。
如有疑问，请联系系统管理员。
            """

            # 添加邮件内容
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')

            msg.attach(part1)
            msg.attach(part2)

            # 发送邮件：SMTP优先，否则开发模式
            if self.smtp_username and self.smtp_password:
                # 使用SMTP发送（MailerSend、Gmail等）
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)

                print(f"✅ SMTP邮件已发送到: {to_email}")
                return True

            # 开发模式：控制台输出
            print(f"=== 密码重置邮件 (开发模式) ===")
            print(f"收件人: {to_email}")
            print(f"重置链接: {reset_link}")
            print(f"=== 邮件内容结束 ===")
            return True

        except Exception as e:
            print(f"❌ 发送邮件失败: {e}")
            print(f"❌ 错误类型: {type(e).__name__}")
            import traceback
            print(f"❌ 详细错误信息:")
            traceback.print_exc()
            return False


# 创建全局邮件服务实例
email_service = EmailService()
