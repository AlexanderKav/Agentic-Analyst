import os
from typing import Any

class EmailService:
    def __init__(self):
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = "alexkavanagh6@gmail.com"
        self.frontend_url = os.getenv("FRONTEND_URL", "https://agentic-analyst.vercel.app")
        
        if self.sendgrid_api_key:
            print("✅ Email service ready")
        else:
            print("⚠️ No SendGrid API key")

    async def send_password_reset_email(self, to_email: str, username: str, token: str):
        """Send password reset email"""
        reset_link = f"{self.frontend_url}/reset-password?token={token}"
        
        print(f"📧 Sending to: {to_email}")
        print(f"🔗 Link: {reset_link}")
        
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            sg = SendGridAPIClient(self.sendgrid_api_key)
            
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject="Reset Your Password"
            )
            message.plain_text_content = f"""
Password Reset

Hi {username},

Click the link below to reset your password:

{reset_link}

This link expires in 24 hours.

If you didn't request this, please ignore this email.

Agentic Analyst Team
"""
            
            response = sg.send(message)
            print(f"✅ Sent! Status: {response.status_code}")
            return True, "Email sent"
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if hasattr(e, 'body'):
                print(f"Body: {e.body}")
            return False, str(e)

    async def send_verification_email(self, to_email: str, username: str, token: str):
        """Send verification email"""
        verification_link = f"{self.frontend_url}/verification-success?token={token}"
        
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            sg = SendGridAPIClient(self.sendgrid_api_key)
            
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject="Verify Your Email"
            )
            message.plain_text_content = f"""
Verify Your Email

Hi {username},

Click the link below to verify your email:

{verification_link}

This link expires in 24 hours.

Agentic Analyst Team
"""
            
            response = sg.send(message)
            print(f"✅ Verification sent! Status: {response.status_code}")
            return True, "Email sent"
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False, str(e)

    async def send_analysis_results(self, to_email: str, question: str, results: dict, charts: dict = None):
        """Send analysis results"""
        insights = results.get("insights", "No insights available")
        if isinstance(insights, dict):
            insights = insights.get("human_readable_summary", str(insights))
        
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            sg = SendGridAPIClient(self.sendgrid_api_key)
            
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=f"Analysis Results: {question[:30]}"
            )
            message.plain_text_content = f"""
Analysis Results

Question: {question}

Key Insights:
{insights}

Agentic Analyst Team
"""
            
            response = sg.send(message)
            print(f"✅ Analysis sent! Status: {response.status_code}")
            return True, "Email sent"
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False, str(e)