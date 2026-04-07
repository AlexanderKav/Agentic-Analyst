import os
import json
import base64
from typing import Any

class EmailService:
    def __init__(self):
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.use_sendgrid = bool(self.sendgrid_api_key)
        self.from_email = os.getenv("FROM_EMAIL", "alexkavanagh6@gmail.com")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

        if self.use_sendgrid:
            print(f"✅ SendGrid email service initialized")
        print(f"📧 Email service ready (SendGrid: {self.use_sendgrid})")

    async def _send_via_sendgrid(self, to_email: str, subject: str, content: str, charts: dict = None, json_results: bytes = None) -> tuple:
        """Send email using SendGrid API by constructing the raw JSON payload."""
        if not self.use_sendgrid or not self.sendgrid_api_key:
            return False, "SendGrid not configured"
        
        try:
            from sendgrid import SendGridAPIClient
            
            # 1. Build the base email payload as a dictionary
            payload = {
                "personalizations": [
                    {
                        "to": [{"email": to_email}],
                        "subject": subject,
                    }
                ],
                "from": {"email": self.from_email},
                "content": [{"type": "text/plain", "value": content}],
            }
            
            # 2. Add JSON attachment if provided
            if json_results and len(json_results) > 0:
                encoded_content = base64.b64encode(json_results).decode()
                attachment = {
                    "content": encoded_content,
                    "filename": "analysis_results.json",
                    "type": "application/json",
                    "disposition": "attachment"
                }
                payload.setdefault("attachments", []).append(attachment)
                print(f"📎 Added JSON attachment to payload")
            
            # 3. Add chart attachments if provided
            if charts:
                for chart_name, chart_path in charts.items():
                    if chart_path and os.path.exists(chart_path):
                        with open(chart_path, 'rb') as f:
                            file_data = f.read()
                            if file_data:
                                encoded_content = base64.b64encode(file_data).decode()
                                attachment = {
                                    "content": encoded_content,
                                    "filename": f"{chart_name}.png",
                                    "type": "image/png",
                                    "disposition": "attachment"
                                }
                                payload.setdefault("attachments", []).append(attachment)
                                print(f"📎 Added chart: {chart_name}.png ({len(file_data)} bytes)")
                    else:
                        print(f"⚠️ Chart file not found: {chart_path}")
            
            # 4. Send the email using the low-level API method
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.client.mail.send.post(request_body=payload)
            
            if response.status_code == 202:
                print(f"✅ Email sent to {to_email}")
                return True, "Email sent"
            else:
                print(f"❌ SendGrid returned {response.status_code}")
                print(f"Response body: {response.body}")
                return False, f"Error: {response.status_code}"
                
        except Exception as e:
            print(f"❌ SendGrid error: {e}")
            if hasattr(e, 'body'):
                print(f"Error body: {e.body}")
            return False, str(e)

    async def send_verification_email(self, to_email: str, username: str, token: str):
        """Send verification email"""
        if not self.use_sendgrid:
            return False, "Not configured"
        
        verification_link = f"{self.frontend_url}/verification-success?token={token}"
        
        content = f"""
Verify Your Email

Hi {username},

Click the link below to verify your email:

{verification_link}

This link expires in 24 hours.

If you didn't create an account, please ignore this email.

Agentic Analyst Team
"""
        return await self._send_via_sendgrid(to_email, "Verify Your Email - Agentic Analyst", content)

    async def send_password_reset_email(self, to_email: str, username: str, token: str):
        """Send password reset email"""
        if not self.use_sendgrid:
            return False, "Not configured"
        
        reset_link = f"{self.frontend_url}/reset-password?token={token}"
        
        content = f"""
Password Reset Request

Hi {username},

We received a request to reset your password. Click the link below to reset it:

{reset_link}

This link expires in 24 hours.

If you didn't request this, please ignore this email.

Agentic Analyst Team
"""
        return await self._send_via_sendgrid(to_email, "Reset Your Password - Agentic Analyst", content)

    async def send_analysis_results(self, to_email: str, question: str, results: dict, charts: dict = None):
        """Send analysis results email with chart attachments"""
        subject = f"Agentic Analyst Results: {question[:40]}..."
        
        # Extract insights safely
        insights = results.get("insights", "No insights available")
        if isinstance(insights, dict):
            insights = insights.get("human_readable_summary") or insights.get("answer") or str(insights)
        
        # Extract raw insights safely (handle None)
        raw_insights = results.get("raw_insights")
        if raw_insights is None:
            raw_insights = {}
        
        supporting_insights = raw_insights.get("supporting_insights", {}) if isinstance(raw_insights, dict) else {}
        key_findings = supporting_insights.get("key_findings", []) if isinstance(supporting_insights, dict) else []
        
        anomalies_dict = raw_insights.get("anomalies", {}) if isinstance(raw_insights, dict) else {}
        anomalies = anomalies_dict.get("identified", []) if isinstance(anomalies_dict, dict) else []
        
        recommendations_dict = raw_insights.get("recommended_metrics", {}) if isinstance(raw_insights, dict) else {}
        recommendations = recommendations_dict.get("next_steps", []) if isinstance(recommendations_dict, dict) else []
        
        # Get KPIs safely
        results_dict = results.get("results", {}) if isinstance(results.get("results"), dict) else {}
        kpis = results_dict.get("kpis", {}) if isinstance(results_dict, dict) else {}
        if not kpis:
            kpis = results.get("kpis", {}) if isinstance(results.get("kpis"), dict) else {}
        
        # Get forecast details safely
        forecast_details = ""
        if isinstance(supporting_insights, dict):
            metrics = supporting_insights.get("metrics", {})
            if isinstance(metrics, dict):
                forecast_details = metrics.get("forecast_details", "")
        
        # Get data summary
        data_summary = results.get("data_summary", {})
        
        # Build Key Findings section
        findings_text = ""
        if key_findings:
            findings_text = "\n\nKey Findings:\n"
            for finding in key_findings:
                findings_text += f"  • {finding}\n"
        
        # Build KPIs text
        kpi_text = ""
        if kpis:
            kpi_text = "\n\nKey Metrics:\n"
            for key, value in kpis.items():
                if isinstance(value, (int, float)):
                    if "margin" in key:
                        formatted = f"{value:.1%}"
                    elif "revenue" in key or "profit" in key or "cost" in key:
                        formatted = f"${value:,.0f}"
                    else:
                        formatted = f"{value:,.0f}"
                else:
                    formatted = str(value)
                label = key.replace('_', ' ').title()
                kpi_text += f"  • {label}: {formatted}\n"
        
        # Add forecast details if available
        if forecast_details:
            kpi_text += f"  • Forecast Details: {forecast_details}\n"
        
        # Build Anomalies section
        anomalies_text = ""
        if anomalies:
            anomalies_text = "\n\n⚠️ Detected Anomalies:\n"
            for anomaly in anomalies:
                anomalies_text += f"  • {anomaly}\n"
        
        # Build Recommendations section
        recommendations_text = ""
        if recommendations:
            recommendations_text = "\n\n📊 Recommended Next Steps:\n"
            for i, step in enumerate(recommendations, 1):
                recommendations_text += f"  {i}. {step}\n"
        
        # Add data summary
        summary_text = ""
        if data_summary:
            summary_text = f"\n\n📋 Data Summary: {data_summary.get('rows', 0):,} rows | {len(data_summary.get('columns', []))} columns\n"
        
        # Convert relative chart paths to absolute paths
        abs_charts = {}
        if charts:
            possible_base_dirs = [
                "/app/agents/charts",  # Docker path
                os.path.join(os.path.dirname(__file__), "../../agents/charts"),  # Relative to this file
                "agents/charts",  # Relative to cwd
                os.path.abspath("agents/charts"),
            ]
            
            for name, filename in charts.items():
                # If filename is already a full path and exists
                if filename and os.path.exists(filename):
                    abs_charts[name] = filename
                    print(f"✅ Chart '{name}' found at: {filename}")
                    continue
                
                # Try to find the file in possible directories
                found = False
                for base_dir in possible_base_dirs:
                    if filename and not os.path.isabs(filename):
                        full_path = os.path.join(base_dir, filename)
                    else:
                        full_path = os.path.join(base_dir, os.path.basename(filename) if filename else f"{name}.png")
                    
                    if os.path.exists(full_path):
                        abs_charts[name] = full_path
                        print(f"✅ Chart '{name}' found at: {full_path}")
                        found = True
                        break
                
                if not found:
                    print(f"⚠️ Chart '{name}' not found. Tried in: {possible_base_dirs}")
        
        # Charts notice
        charts_text = ""
        if abs_charts:
            charts_text = f"\n\n📎 {len(abs_charts)} chart(s) attached to this email.\n"
        
        # Create JSON attachment (without charts data to save space)
        json_results = None
        if results:
            try:
                clean_results = results.copy()
                if 'results' in clean_results and isinstance(clean_results['results'], dict):
                    clean_results['results'].pop('charts', None)
                json_str = json.dumps(clean_results, indent=2, default=str)
                json_results = json_str.encode('utf-8')
                print(f"📝 Created JSON attachment: {len(json_results)} bytes")
            except Exception as e:
                print(f"⚠️ Could not create JSON attachment: {e}")
        
        # Create the full email content
        content = f"""
{'='*60}
🤖 AGENTIC ANALYST - ANALYSIS RESULTS
{'='*60}

Your Question: "{question}"

Analysis Summary:
{insights}
{findings_text}
{kpi_text}
{anomalies_text}
{recommendations_text}
{summary_text}
{charts_text}
{'='*60}
📎 Complete analysis results attached as JSON file.

Agentic Analyst Team
"""
        
        return await self._send_via_sendgrid(to_email, subject, content, abs_charts, json_results)


__all__ = ['EmailService']