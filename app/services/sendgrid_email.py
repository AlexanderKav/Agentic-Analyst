import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class SendGridEmailService:
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "alexkavanagh6@gmail.com")
        self.from_name = os.getenv("FROM_NAME", "Agentic Analyst")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        if not self.api_key:
            print("⚠️ SENDGRID_API_KEY not set. Email sending will be disabled.")
        else:
            print("✅ SendGrid email service initialized")

    async def send_verification_email(self, to_email: str, username: str, token: str):
        """Send email verification link"""
        if not self.api_key:
            print("❌ Cannot send email: SendGrid API key not configured")
            return False
        
        verification_link = f"{self.frontend_url}/verification-success?token={token}"
        
        html_content = f"""
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
        
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject="Verify Your Email - Agentic Analyst"
            )
            message.html_content = html_content
            
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            
            if response.status_code == 202:
                print(f"✅ Verification email sent to {to_email}")
                return True
            else:
                print(f"❌ Failed to send email: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    async def send_password_reset_email(self, to_email: str, username: str, token: str):
        """Send password reset link"""
        if not self.api_key:
            print("❌ Cannot send email: SendGrid API key not configured")
            return False
        
        reset_link = f"{self.frontend_url}/reset-password?token={token}"
        
        html_content = f"""
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
        
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject="Reset Your Password - Agentic Analyst"
            )
            message.html_content = html_content
            
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            
            if response.status_code == 202:
                print(f"✅ Password reset email sent to {to_email}")
                return True
            else:
                print(f"❌ Failed to send email: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


# Singleton instance
_sendgrid_email_service = None

def get_sendgrid_email_service():
    global _sendgrid_email_service
    if _sendgrid_email_service is None:
        _sendgrid_email_service = SendGridEmailService()
    return _sendgrid_email_service