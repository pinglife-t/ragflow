import json
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from typing import Optional

import settings


class EmailSender:
    """Utility class for sending emails"""
    
    def __init__(
        self,
        smtp_server: str = None,
        smtp_port: int = None,
        sender_email: str = None,
        sender_password: str = None,
        sender_name: str = None
    ):
        """Initialize EmailSender with SMTP configuration"""
        # 使用硬编码的默认值
        self.smtp_server = smtp_server or settings.SMTP_SERVER or "smtp.163.com"
        self.smtp_port = smtp_port or settings.SMTP_PORT or 465
        self.sender_email = sender_email or settings.SMTP_EMAIL or "stop_loss@163.com"
        self.sender_password = sender_password or settings.SMTP_PASSWORD or "Lab4man1"
        self.sender_name = sender_name or settings.SMTP_SENDER_NAME or "DOES.AI"
        
        logging.info(f"EmailSender initialized with server: {self.smtp_server}:{self.smtp_port}")
    
    def send_verification_code(self, to_email: str, code: str) -> bool:
        """Send verification code email"""
        subject = "验证码"
        html_content = f"""
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2>您的验证码是：{code}</h2>
            <p>验证码有效期为10分钟，请尽快使用。</p>
            <p>如果这不是您的操作，请忽略此邮件。</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                此邮件由系统自动发送，请勿回复。
                <br>© {settings.CURRENT_YEAR} {self.sender_name}
            </p>
        </div>
        """
        
        return self.send_email({
            "to_email": to_email,
            "subject": subject,
            "html_content": html_content
        })
    
    def send_email(self, email_data: dict) -> bool:
        """Send email with the given data"""
        try:
            msg = MIMEMultipart()
            msg['From'] = formataddr((str(Header(self.sender_name, 'utf-8')), self.sender_email))
            msg['To'] = email_data["to_email"]
            msg['Subject'] = Header(email_data["subject"], 'utf-8')
            
            # Add HTML content
            msg.attach(MIMEText(email_data["html_content"], 'html', 'utf-8'))
            
            # Connect to SMTP server
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            
            logging.info(f"Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
            
            # Login
            server.login(self.sender_email, self.sender_password)
            logging.info(f"Logged in as {self.sender_email}")
            
            # Send email
            recipients = [email_data["to_email"]]
            if "cc_email" in email_data and email_data["cc_email"]:
                recipients.extend(email_data["cc_email"].split(','))
            
            server.send_message(msg, self.sender_email, recipients)
            logging.info(f"Email sent successfully to {recipients}")
            
            server.quit()
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logging.error(f"SMTP Authentication failed: {str(e)}")
            return False
            
        except smtplib.SMTPConnectError as e:
            logging.error(f"Failed to connect to SMTP server: {str(e)}")
            return False
            
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return False 