import os
import json
import re
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agents.monitoring import get_performance_tracker, timer, get_audit_logger, get_cost_tracker
import numpy as np
import pandas as pd


def make_json_safe(obj):
    """Recursively convert all objects to JSON-serializable types."""
    if isinstance(obj, dict):
        return {str(k): make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(x) for x in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, (np.bool_)):
        return bool(obj)
    elif isinstance(obj, (pd.Timestamp, np.datetime64, datetime)):
        return obj.isoformat()
    elif isinstance(obj, (pd.Timedelta)):
        return str(obj)
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif obj is None:
        return None
    else:
        try:
            return str(obj)
        except:
            return None


def extract_json_from_text(text):
    """Extract first JSON block from text safely, handling both // and # comments."""
    import re
    import json
    
    print(f"\n🔧 Cleaning JSON response (original length: {len(text)} chars)")
    
    # First, remove any comments (both // and #) from the text
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Check for // comments
        if '//' in line:
            parts = line.split('//')
            before_comment = parts[0].rstrip()
            if before_comment and before_comment[-1] in '0123456789"\'':  # Likely data with // in value
                cleaned_lines.append(line)  # Keep the whole line
            else:
                cleaned_lines.append(parts[0].rstrip())  # Remove comment
        # Check for # comments
        elif '#' in line:
            parts = line.split('#')
            before_comment = parts[0].rstrip()
            # Only remove if it's a real comment (not inside a string)
            if before_comment and before_comment[-1] not in '"\'0123456789':
                cleaned_lines.append(parts[0].rstrip())  # Remove comment
            else:
                cleaned_lines.append(line)  # Keep the whole line
        else:
            cleaned_lines.append(line)
    
    cleaned_text = '\n'.join(cleaned_lines)
    
    # Fix numbers with commas (e.g., "25,895.0" -> "25895.0")
    def fix_number_commas(match):
        """Remove commas from numbers"""
        num_str = match.group(0)
        return num_str.replace(',', '')
    
    cleaned_text = re.sub(r'\d+,\d+\.?\d*', fix_number_commas, cleaned_text)
    
    # Remove any remaining comments
    cleaned_text = re.sub(r'#.*$', '', cleaned_text, flags=re.MULTILINE)
    
    # Try to find JSON block
    match = re.search(r'\{.*\}', cleaned_text, flags=re.DOTALL)
    if not match:
        print("⚠️ No JSON pattern found in text")
        return {}

    json_text = match.group()
    
    # Remove trailing commas before } or ]
    json_text = re.sub(r',\s*([}\]])', r'\1', json_text)
    
    # Remove any remaining # comments inside the JSON
    json_text = re.sub(r'#.*?\n', '\n', json_text)
    
    # Remove any placeholder comments
    json_text = re.sub(r'\s*#.*$', '', json_text, flags=re.MULTILINE)
    
    # Remove blank lines
    json_text = re.sub(r'\n\s*\n', '\n', json_text)

    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"⚠️ First parse attempt failed: {e}")
        try:
            # Second try: fix unquoted keys
            json_text = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_text)
            return json.loads(json_text)
        except json.JSONDecodeError as e2:
            print(f"⚠️ Second parse attempt failed: {e2}")
            try:
                # Third try: fix unquoted string values
                json_text = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,}])', r':"\1"\2', json_text)
                return json.loads(json_text)
            except json.JSONDecodeError as e3:
                print(f"⚠️ Third parse attempt failed: {e3}")
                print(f"Problematic JSON text (first 500 chars): {json_text[:500]}...")
                
                # Last resort: try to extract just the answer field
                try:
                    answer_match = re.search(r'"answer"\s*:\s*"([^"]+)"', json_text)
                    summary_match = re.search(r'"human_readable_summary"\s*:\s*"([^"]+)"', json_text)
                    
                    result = {
                        "answer": answer_match.group(1) if answer_match else "Analysis complete.",
                        "supporting_insights": {},
                        "anomalies": {},
                        "recommended_metrics": {},
                        "human_readable_summary": summary_match.group(1) if summary_match else "See analysis results."
                    }
                    print("✅ Extracted basic fields using regex fallback")
                    return result
                except:
                    pass
                
                return {}


def ensure_insight_format(insight_data):
    """
    Ensure insight data has the correct structure with string fields.
    This is the central sanitizer for all insight outputs.
    """
    result = {
        "answer": "",
        "supporting_insights": {},
        "anomalies": {},
        "recommended_metrics": {},
        "human_readable_summary": ""
    }
    
    if not isinstance(insight_data, dict):
        result["answer"] = str(insight_data) if insight_data else "Analysis complete."
        result["human_readable_summary"] = result["answer"][:200]
        return result
    
    # Extract and sanitize answer
    answer = insight_data.get('answer', '')
    if isinstance(answer, dict):
        # If answer is a dict, try to get the actual answer field
        answer = answer.get('answer', str(answer))
    result["answer"] = str(answer) if answer else "Analysis complete."
    
    # Extract and sanitize human_readable_summary
    summary = insight_data.get('human_readable_summary', '')
    if isinstance(summary, dict):
        summary = summary.get('human_readable_summary', str(summary))
    result["human_readable_summary"] = str(summary) if summary else result["answer"][:200]
    
    # Ensure supporting_insights is a dict
    supporting = insight_data.get('supporting_insights', {})
    if isinstance(supporting, dict):
        result["supporting_insights"] = make_json_safe(supporting)
    elif isinstance(supporting, list):
        result["supporting_insights"] = {"items": make_json_safe(supporting)}
    else:
        result["supporting_insights"] = {}
    
    # Ensure anomalies is a dict
    anomalies = insight_data.get('anomalies', {})
    if isinstance(anomalies, dict):
        result["anomalies"] = make_json_safe(anomalies)
    elif isinstance(anomalies, list):
        result["anomalies"] = {"detected": make_json_safe(anomalies)}
    else:
        result["anomalies"] = {}
    
    # Ensure recommended_metrics is a dict
    metrics = insight_data.get('recommended_metrics', {})
    if isinstance(metrics, dict):
        result["recommended_metrics"] = make_json_safe(metrics)
    elif isinstance(metrics, list):
        result["recommended_metrics"] = {"suggestions": make_json_safe(metrics)}
    else:
        result["recommended_metrics"] = {}
    
    return result


class InsightAgent:

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.6,
            api_key=os.getenv("OPENAI_API_KEY")
        )

        self.prompt = ChatPromptTemplate.from_template("""
You are a senior AI business analyst specializing in data-driven insights.

**USER QUESTION:** {question}

**BUSINESS DATA:** {data}

---

## YOUR ROLE
Provide a comprehensive, data-driven analysis that directly answers the user's question. If exact data isn't available, provide the closest relevant insights with specific numbers and actionable recommendations.

---

## RESPONSE RULES

### 1. ANSWER QUALITY
- **ALWAYS use actual numbers from the data** - never make up values
- **If exact data isn't available**, acknowledge the limitation briefly, THEN provide the most relevant available metrics
- **NEVER just say "I cannot answer"** without providing useful alternative insights
- **Include specific percentages, dollar amounts, and timeframes** in your answer

### 2. QUESTION TYPE HANDLING

**Forecast Questions** (e.g., "What will revenue look like in 2025?")
- Include: recent revenue trends, growth patterns, seasonal patterns, forecast methodology
- Exclude: payment status, missing customers, operational metrics
- State forecast period clearly (e.g., "next 3 months", "Jan-Mar 2025")
- Explain limitations if forecasting beyond available data range

**Customer Analysis Questions** (e.g., "Which customers are declining?")
- If customer-level monthly data available: provide specific customer trends
- If only product-level data available: provide product trends and explain how they relate to customers
- Include: top customers by total revenue, product-level anomalies, actionable next steps

**Product Analysis Questions** (e.g., "What are our top products?")
- Aggregate revenue across ALL customers for each product
- Show monthly trends with month names (e.g., "January: $18,986")
- Include peak and low months with specific values

**Risk Questions** (e.g., "Are there any risks?")
- Include: failed payments, pending revenue, missing data, refunds, customer concentration
- Quantify risks with dollar amounts and percentages
- Provide specific recommendations to mitigate risks

**Performance/Overview Questions** (e.g., "How is the business performing?")
- Include: total revenue, profit margin, top products, top customers, regional breakdown
- Highlight both strengths and areas of concern
- Provide balanced assessment with specific metrics

**General Questions** (e.g., "Show me revenue trends")
- Focus on the specific metrics requested
- Include relevant supporting data
- Avoid adding unrelated metrics

### 3. DATA FORMATTING
- **Monthly trends**: Always specify months (e.g., "January: $18,986, February: $18,030")
- **Percentages**: Round to 1 decimal place (e.g., "23.4% increase")
- **Currency**: Format with $ and commas (e.g., "$18,986")
- **Large numbers**: Use commas for readability (e.g., "221,819")

### 4. CONTENT RULES
- **Do NOT include comments** (// or #) in JSON
- **Only include insights relevant to the question** - filter out unrelated metrics
- **If a tool returned "insufficient_data"**, acknowledge it and suggest what data would help
- **Be specific** - avoid vague statements like "some products are doing well"
- **Be actionable** - provide specific recommendations when appropriate

---

## RESPONSE FORMAT

Return ONLY valid JSON in this exact structure:

{{
  "answer": "A direct, data-driven answer to the user's question. Include specific numbers and, if exact data unavailable, provide the closest relevant insights.",
  "supporting_insights": {{
    "key_findings": ["Specific finding with numbers (e.g., 'Enterprise Plan dropped 36% in May')", "Specific finding with numbers"],
    "relevant_trends": ["Trend with numbers and timeframe", "Trend with numbers and timeframe"],
    "additional_context": "Optional: Additional context that supports the answer"
  }},
  "anomalies": {{
    "identified": ["Anomaly with specific numbers and impact (e.g., 'Enterprise Plan: May revenue $11,898 vs $18,485 average')"],
    "severity": "Brief assessment of anomaly significance (optional)"
  }},
  "recommended_metrics": {{
    "next_steps": ["Actionable recommendation 1", "Actionable recommendation 2"],
    "data_needed": "If applicable: What additional data would enable better analysis"
  }},
  "human_readable_summary": "A concise 1-2 sentence summary of the most important insight for the user"
}}

---

## EXAMPLES

### Example 1: Customer Question with Product Data Only
**Question:** "Which customers show declining revenue?"
**Good Response:**
{{
  "answer": "Customer-level monthly data isn't available, but product analysis shows the Enterprise Plan dropped 36% in May ($11,898 vs $18,485 average), suggesting potential issues with Enterprise customers. Top customers by total revenue: Acme Corp ($50,000+), BetaCo ($40,000+).",
  "supporting_insights": {{
    "key_findings": [
      "Enterprise Plan: 36% decline in May ($11,898 vs $18,485 average)",
      "Premium Plan: 23% spike in December ($6,917 vs $5,627 average)",
      "Enterprise Plan accounts for 69% of total revenue"
    ],
    "relevant_trends": [
      "Enterprise Plan revenue volatile, May lowest month",
      "Premium Plan shows consistent growth"
    ]
  }},
  "anomalies": {{
    "identified": [
      "Enterprise Plan: May revenue $11,898 (36% below $18,485 average)",
      "Premium Plan: December revenue $6,917 (23% above $5,627 average)"
    ]
  }},
  "recommended_metrics": {{
    "next_steps": [
      "Investigate Enterprise customers active in May",
      "Add transaction dates to enable customer-level trend analysis",
      "Analyze what drove Premium Plan December spike"
    ],
    "data_needed": "Customer-month revenue data would enable precise customer decline analysis"
  }},
  "human_readable_summary": "Enterprise Plan revenue dropped 36% in May, suggesting potential issues with Enterprise customers. Top customers are Acme Corp and BetaCo."
}}

### Example 2: Forecast Question
**Question:** "What will revenue look like in 2025?"
**Good Response:**
{{
  "answer": "Based on 12 months of data, revenue shows volatile growth with May decline (-27%) and December growth (+11%). Without seasonal patterns, a precise 2025 forecast requires more historical data. Current trend suggests potential growth if December patterns continue.",
  "supporting_insights": {{
    "key_findings": [
      "Revenue: $319,925 total, average $26,660/month",
      "Growth: 4 months positive, 8 months negative",
      "Best month: December (+11% growth)",
      "Worst month: May (-27% decline)"
    ],
    "trends": [
      "Negative growth months: Feb, Apr, May, Jul, Sep, Nov",
      "Positive growth months: Mar, Jun, Aug, Oct, Dec"
    ]
  }},
  "anomalies": {{
    "identified": [
      "May: -27% growth (significant decline)",
      "December: +11% growth (strong recovery)"
    ]
  }},
  "recommended_metrics": {{
    "next_steps": [
      "Collect 24+ months data for seasonal forecasting",
      "Analyze factors driving May decline",
      "Monitor if December growth trend continues"
    ],
    "data_needed": "2+ years of monthly data for reliable forecasting"
  }},
  "human_readable_summary": "Revenue shows volatile growth with a concerning May decline (-27%) and strong December recovery (+11%). More historical data needed for accurate 2025 forecast."
}}

### Example 3: Performance Overview
**Question:** "How is the business performing?"
**Good Response:**
{{
  "answer": "Your business generated $319,925 in revenue with a 49% profit margin ($158,539 profit). Enterprise Plan leads with 69% of revenue, followed by Premium Plan (21%) and Basic Plan (10%). Top customers: Acme Corp ($50,000+), BetaCo ($40,000+).",
  "supporting_insights": {{
    "key_findings": [
      "Total revenue: $319,925",
      "Profit margin: 49% ($158,539 profit)",
      "Enterprise Plan: 69% of revenue ($221,819)",
      "Top 2 customers account for 28% of revenue"
    ],
    "trends": [
      "Revenue volatile: May decline (-27%), December growth (+11%)",
      "Enterprise Plan May dip ($11,898 vs $18,485 avg)"
    ]
  }},
  "anomalies": {{
    "identified": [
      "Enterprise Plan: May revenue $11,898 (36% below average)",
      "Premium Plan: December spike $6,917 (23% above average)"
    ]
  }},
  "recommended_metrics": {{
    "next_steps": [
      "Investigate May decline in Enterprise Plan",
      "Analyze December Premium Plan spike for repeatable strategies",
      "Reduce customer concentration risk"
    ]
  }},
  "human_readable_summary": "Strong overall performance ($319,925 revenue, 49% margin) but Enterprise Plan shows concerning May decline (-36%) and customer concentration poses risk."
}}

---

Return ONLY valid JSON, no explanations outside the JSON structure.
""")
    
    @timer(operation='generate_insights')
    def generate_insights(self, data, question="General business insights"):
        try:
            # Convert tool results to JSON-safe dict
            if hasattr(data, "to_dict"):
                data_dict = data.to_dict(orient="records")
            else:
                data_dict = make_json_safe(data)

            data_dict = make_json_safe(data_dict)
            
            # Check if there's a skipped tools note
            skipped_note = data_dict.pop("_skipped_tools_note", None)
            if skipped_note:
                # Add a note to the data that the AI can see
                data_dict["_note"] = skipped_note["message"]
                print(f"📝 Adding note for insight agent: {skipped_note['message']}")
            
            data_json = json.dumps(data_dict, indent=2, default=str)

            messages = self.prompt.format_messages(data=data_json, question=question)
            response = self.llm.invoke(messages)
            raw = response.content

            print("\n" + "="*60)
            print("RAW INSIGHT RESPONSE:")
            print("="*60)
            print(raw)
            print("="*60 + "\n")

            # Extract JSON safely
            parsed_json = extract_json_from_text(raw)
            
            # === CRITICAL: Sanitize the output to ensure strings ===
            sanitized_insights = ensure_insight_format(parsed_json)
            
            # Check if the parsed JSON itself contains a nested JSON string
            if parsed_json and 'answer' in parsed_json:
                answer = parsed_json['answer']
                if isinstance(answer, str) and answer.strip().startswith('{'):
                    try:
                        nested = json.loads(answer)
                        if isinstance(nested, dict) and 'answer' in nested:
                            sanitized_insights = ensure_insight_format(nested)
                    except:
                        pass
            
            # If parsing failed but we have raw text, create a simple response
            if not parsed_json and raw:
                sanitized_insights = ensure_insight_format({
                    "answer": raw[:500] if isinstance(raw, str) else str(raw)[:500],
                    "human_readable_summary": raw[:200] if isinstance(raw, str) else str(raw)[:200]
                })
            
            print(f"✅ Final answer type: {type(sanitized_insights.get('answer', ''))}")
            print(f"✅ Answer preview: {str(sanitized_insights.get('answer', ''))[:150]}...")
            print(f"✅ Summary type: {type(sanitized_insights.get('human_readable_summary', ''))}")
            
            return raw, sanitized_insights

        except Exception as e:
            print("❌ Error in InsightAgent.generate_insights:", e)
            import traceback
            traceback.print_exc()
            
            # Return a safe error response
            error_insights = ensure_insight_format({
                "answer": f"Error generating insights: {str(e)}",
                "human_readable_summary": "An error occurred during analysis. Please try again or rephrase your question."
            })
            return "", error_insights