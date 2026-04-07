import json
import logging
import os
from typing import Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        # SendGrid configuration
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.use_sendgrid = bool(self.sendgrid_api_key)
        
        # Common settings
        self.from_email = os.getenv("FROM_EMAIL", "alexkavanagh6@gmail.com")
        self.from_name = os.getenv("FROM_NAME", "Agentic Analyst")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

        # Initialize SendGrid
        self.sendgrid_client = None
        if self.use_sendgrid:
            try:
                from sendgrid import SendGridAPIClient
                self.sendgrid_client = SendGridAPIClient(self.sendgrid_api_key)
                print(f"✅ SendGrid email service initialized")
            except ImportError:
                print("⚠️ SendGrid package not installed. Install with: pip install sendgrid")
                self.use_sendgrid = False
            except Exception as e:
                print(f"⚠️ SendGrid initialization failed: {e}")
                self.use_sendgrid = False
        
        print(f"📧 Email service initialized (SendGrid: {self.use_sendgrid})")
        print(f"📧 From: {self.from_email}")
        print(f"📧 Frontend URL: {self.frontend_url}")

    async def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str) -> tuple:
        """Send email using SendGrid API"""
        if not self.sendgrid_client:
            return False, "SendGrid client not initialized"
        
        try:
            from sendgrid.helpers.mail import Mail
            
            print(f"📧 SendGrid - Sending to: {to_email}")
            print(f"📧 SendGrid - Subject: {subject}")
            
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject
            )
            message.html_content = html_content
            
            response = self.sendgrid_client.send(message)
            
            print(f"📧 SendGrid - Response status: {response.status_code}")
            
            if response.status_code == 202:
                print(f"✅ Email sent via SendGrid to {to_email}")
                return True, "Email sent successfully"
            else:
                print(f"❌ SendGrid returned {response.status_code}")
                return False, f"SendGrid error: {response.status_code}"
                
        except Exception as e:
            error_msg = f"SendGrid error: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg

    async def send_verification_email(self, to_email: str, username: str, token: str):
        """Send email verification link"""
        if not self.use_sendgrid:
            print("❌ SendGrid not configured. Cannot send email.")
            return False, "Email service not configured"
        
        verification_link = f"{self.frontend_url}/verification-success?token={token}"

        print(f"📧 Sending verification email to {to_email}")
        print(f"🔗 Verification link: {verification_link}")

        html = self._get_verification_html(username, verification_link)
        
        return await self._send_via_sendgrid(to_email, "Verify Your Email - Agentic Analyst", html)

    async def send_password_reset_email(self, to_email: str, username: str, token: str):
        """Send password reset email"""
        if not self.use_sendgrid:
            print("❌ SendGrid not configured. Cannot send email.")
            return False, "Email service not configured"
        
        reset_link = f"{self.frontend_url}/reset-password?token={token}"

        print(f"📧 Sending password reset email to {to_email}")
        print(f"🔗 Reset link: {reset_link}")

        html = self._get_password_reset_html(username, reset_link)
        
        return await self._send_via_sendgrid(to_email, "Reset Your Password - Agentic Analyst", html)

    async def send_analysis_results(self, to_email: str, question: str, results: dict[str, Any],
                                    charts: dict[str, str] | None = None):
        """Send analysis results via email"""
        if not self.use_sendgrid:
            print("❌ SendGrid not configured. Cannot send email.")
            return False, "Email service not configured"
        
        subject = f"📊 Agentic Analyst Results: {question[:50]}..."
        
        html = self._get_analysis_html(question, results)
        
        return await self._send_via_sendgrid(to_email, subject, html)

    def _get_verification_html(self, username: str, verification_link: str) -> str:
        """Generate verification email HTML"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Verify Your Email</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 30px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .button {{ display: inline-block; padding: 12px 24px; 
                          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white; text-decoration: none; border-radius: 5px; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 Agentic Analyst</h1>
                </div>
                <div class="content">
                    <h2>Welcome, {username}!</h2>
                    <p>Please verify your email address to start using Agentic Analyst.</p>
                    <div style="text-align: center;">
                        <a href="{verification_link}" class="button">Verify Email Address</a>
                    </div>
                    <p style="margin-top: 20px; font-size: 12px;">
                        Or copy this link: <br>
                        <small>{verification_link}</small>
                    </p>
                    <p><strong>🔒 This link expires in 24 hours.</strong></p>
                </div>
                <div class="footer">
                    <p>© 2025 Agentic Analyst. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_password_reset_html(self, username: str, reset_link: str) -> str:
        """Generate password reset email HTML"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Reset Your Password</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 30px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .button {{ display: inline-block; padding: 12px 24px; 
                          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white; text-decoration: none; border-radius: 5px; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset</h1>
                </div>
                <div class="content">
                    <h2>Hi {username},</h2>
                    <p>We received a request to reset your password.</p>
                    <div style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </div>
                    <p style="margin-top: 20px; font-size: 12px;">
                        Or copy this link: <br>
                        <small>{reset_link}</small>
                    </p>
                    <p><strong>🔒 This link expires in 24 hours.</strong></p>
                    <p>If you didn't request this, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Agentic Analyst. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_analysis_html(self, question: str, results: dict) -> str:
        """Generate analysis results email HTML"""
        insights = results.get("insights", "No insights available")
        if isinstance(insights, dict):
            insights = insights.get("human_readable_summary") or insights.get("answer") or str(insights)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Analysis Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 30px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .insights-box {{
                    background: #e3f2fd;
                    padding: 20px;
                    border-left: 4px solid #1976d2;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
                .question {{ font-style: italic; background: #f5f5f5; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 Agentic Analyst</h1>
                    <p>Your AI-Powered Business Intelligence Results</p>
                </div>
                <div class="content">
                    <div class="question">
                        <strong>Your Question:</strong><br>
                        "{question if question else 'General Business Overview'}"
                    </div>
                    <div class="insights-box">
                        <h3>💡 Key Insights</h3>
                        <p>{insights}</p>
                    </div>
                </div>
                <div class="footer">
                    <p>© 2025 Agentic Analyst. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """


__all__ = ['EmailService']