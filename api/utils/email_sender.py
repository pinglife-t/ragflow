import json
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from datetime import datetime

from api.utils import get_base_config


class EmailSender:
    """Utility class for sending emails"""
    
    def __init__(self):
        """Initialize EmailSender with SMTP configuration"""
        
        smtp_config = get_base_config("smtp", {})
        self.smtp_server = smtp_config.get("server")
        self.smtp_port = int(smtp_config.get("port")) if smtp_config.get("port") else None
        self.sender_email = smtp_config.get("email")
        self.sender_password = smtp_config.get("password")
        self.sender_name = smtp_config.get("sender_name")
    
    def send_verification_code(self, to_email: str, code: str) -> bool:
        """Send verification code email"""
        subject = "验证码"
        current_year = datetime.now().year
        html_content = f"""
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2>您的验证码是：{code}</h2>
            <p>验证码有效期为10分钟，请尽快使用。</p>
            <p>如果这不是您的操作，请忽略此邮件。</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                此邮件由系统自动发送，请勿回复。
                <br>© {current_year} {self.sender_name}
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
        if not self.smtp_server or not self.smtp_port or not self.sender_email or not self.sender_password:
            logging.error("Cannot send email: Missing SMTP configuration")
            return False
        
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
                        
            # Login
            server.login(self.sender_email, self.sender_password)
            
            # Send email
            recipients = [email_data["to_email"]]
            if "cc_email" in email_data and email_data["cc_email"]:
                recipients.extend(email_data["cc_email"].split(','))
            
            server.send_message(msg, self.sender_email, recipients)            
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