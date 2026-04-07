import json
import logging
import os
from typing import Any

from dotenv import load_dotenv

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

    async def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str, plain_text_content: str = None) -> tuple:
        """Send email using SendGrid API"""
        if not self.sendgrid_client:
            return False, "SendGrid client not initialized"
        
        try:
            from sendgrid.helpers.mail import Mail
            
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject
            )
            message.html_content = html_content
            
            if plain_text_content:
                message.plain_text_content = plain_text_content
            
            print(f"📧 SendGrid Request:")
            print(f"   From: {self.from_email}")
            print(f"   To: {to_email}")
            print(f"   Subject: {subject}")
            
            response = self.sendgrid_client.send(message)
            
            if response.status_code == 202:
                print(f"✅ Email sent via SendGrid to {to_email}")
                return True, "Email sent successfully"
            else:
                print(f"❌ SendGrid returned {response.status_code}")
                return False, f"SendGrid error: {response.status_code}"
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ SendGrid error: {error_msg}")
            
            if hasattr(e, 'body'):
                print(f"Error body: {e.body}")
            if hasattr(e, 'headers'):
                print(f"Error headers: {e.headers}")
            
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
        plain_text = self._get_verification_plain_text(username, verification_link)
        
        return await self._send_via_sendgrid(to_email, "Verify Your Email - Agentic Analyst", html, plain_text)

    async def send_password_reset_email(self, to_email: str, username: str, token: str):
        """Send password reset email"""
        if not self.use_sendgrid:
            print("❌ SendGrid not configured. Cannot send email.")
            return False, "Email service not configured"
        
        reset_link = f"{self.frontend_url}/reset-password?token={token}"

        print(f"📧 Sending password reset email to {to_email}")
        print(f"🔗 Reset link: {reset_link}")

        html = self._get_password_reset_html(username, reset_link)
        plain_text = self._get_password_reset_plain_text(username, reset_link)
        
        return await self._send_via_sendgrid(to_email, "Reset Your Password - Agentic Analyst", html, plain_text)

    async def send_analysis_results(self, to_email: str, question: str, results: dict, charts: dict = None):
        """Send analysis results email - ENHANCED VERSION"""
        subject = f"📊 Agentic Analyst: Your Analysis Results"
        
        # Extract insights and format nicely
        insights = results.get("insights", "No insights available")
        if isinstance(insights, dict):
            insights = insights.get("human_readable_summary") or insights.get("answer") or str(insights)
        
        # Get KPIs if available
        kpis = results.get("results", {}).get("kpis", {})
        if not kpis:
            kpis = results.get("kpis", {})
        
        # Get charts if any
        has_charts = charts and len(charts) > 0
        
        # Get data summary
        data_summary = results.get("data_summary", {})
        
        # Format KPIs nicely
        kpi_html = ""
        kpi_text = ""
        if kpis:
            kpi_html = """
            <div style="margin: 20px 0;">
                <h3 style="color: #2c3e50; margin-bottom: 15px;">📊 Key Metrics</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
            """
            kpi_text = "\n📊 KEY METRICS:\n"
            for key, value in kpis.items():
                if isinstance(value, (int, float)):
                    if "revenue" in key or "profit" in key or "cost" in key:
                        formatted = f"${value:,.0f}"
                    elif "margin" in key:
                        formatted = f"{value:.1%}"
                    else:
                        formatted = f"{value:,.0f}"
                else:
                    formatted = str(value)
                
                label = key.replace('_', ' ').title()
                kpi_html += f"""
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 14px; color: #666;">{label}</div>
                        <div style="font-size: 24px; font-weight: bold; color: #1976d2;">{formatted}</div>
                    </div>
                """
                kpi_text += f"  {label}: {formatted}\n"
            kpi_html += "</div></div>"
        
        # Format data summary
        summary_html = ""
        summary_text = ""
        if data_summary:
            summary_html = f"""
            <div style="margin: 20px 0; padding: 15px; background: #e3f2fd; border-radius: 8px;">
                <strong>📋 Data Summary:</strong> {data_summary.get('rows', 0):,} rows | {len(data_summary.get('columns', []))} columns
            </div>
            """
            summary_text = f"\n📋 DATA SUMMARY: {data_summary.get('rows', 0):,} rows | {len(data_summary.get('columns', []))} columns\n"
        
        # Charts notice
        charts_html = ""
        charts_text = ""
        if has_charts:
            charts_html = f"""
            <div style="margin: 20px 0; padding: 15px; background: #e8f5e9; border-radius: 8px;">
                📎 <strong>{len(charts)} chart(s)</strong> attached to this email
            </div>
            """
            charts_text = f"\n📎 {len(charts)} chart(s) attached to this email.\n"
        
        # Create full HTML email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Analysis Results</title>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #fff; padding: 30px; }}
                .question-box {{ background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0; font-style: italic; }}
                .insights-box {{ background: #e3f2fd; padding: 20px; border-left: 4px solid #1976d2; border-radius: 8px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; border-top: 1px solid #eee; }}
                h1 {{ margin: 0; }}
                h2 {{ color: #1976d2; }}
                h3 {{ color: #2c3e50; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">🤖 Agentic Analyst</h1>
                    <p style="margin: 5px 0 0;">Your AI Business Intelligence Assistant</p>
                </div>
                <div class="content">
                    <div class="question-box">
                        <strong>📝 Your Question:</strong><br>
                        "{question if question else 'General Business Overview'}"
                    </div>
                    
                    <div class="insights-box">
                        <h3 style="margin-top: 0;">💡 Key Insights</h3>
                        <p style="margin-bottom: 0;">{insights}</p>
                    </div>
                    
                    {kpi_html}
                    
                    {summary_html}
                    
                    {charts_html}
                    
                    <div style="margin-top: 30px; padding: 15px; background: #f9f9f9; border-radius: 8px; font-size: 12px; color: #666;">
                        <strong>📎 Attachment:</strong> Complete analysis results in JSON format attached.
                    </div>
                </div>
                <div class="footer">
                    <p>Sent by Agentic Analyst - Your AI Business Intelligence Assistant</p>
                    <p>© 2025 Agentic Analyst. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version
        plain_text = f"""
🤖 AGENTIC ANALYST - ANALYSIS RESULTS
{'=' * 50}

Your Question: "{question if question else 'General Business Overview'}"

💡 KEY INSIGHTS:
{insights}

{kpi_text}
{summary_text}
{charts_text}
📎 Attachment: Complete analysis results in JSON format attached.

---
Sent by Agentic Analyst - Your AI Business Intelligence Assistant
"""
        
        return await self._send_via_sendgrid(to_email, subject, html_content, plain_text)

    def _get_verification_html(self, username: str, verification_link: str) -> str:
        """Generate verification email HTML"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Verify Your Email</title>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #fff; padding: 30px; }}
                .button {{ display: inline-block; padding: 12px 24px; 
                          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; border-top: 1px solid #eee; }}
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
                    <p>If you didn't create an account, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Agentic Analyst. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_verification_plain_text(self, username: str, verification_link: str) -> str:
        """Generate verification email plain text"""
        return f"""
Welcome to Agentic Analyst!

Hi {username},

Please verify your email address by clicking the link below:

{verification_link}

This link expires in 24 hours.

If you didn't create an account, please ignore this email.

Agentic Analyst Team
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
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #fff; padding: 30px; }}
                .button {{ display: inline-block; padding: 12px 24px; 
                          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; border-top: 1px solid #eee; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset</h1>
                </div>
                <div class="content">
                    <h2>Hi {username},</h2>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
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

    def _get_password_reset_plain_text(self, username: str, reset_link: str) -> str:
        """Generate password reset email plain text"""
        return f"""
Password Reset Request

Hi {username},

We received a request to reset your password. Click the link below to reset it:

{reset_link}

This link expires in 24 hours.

If you didn't request this, please ignore this email.

Agentic Analyst Team
"""


__all__ = ['EmailService']