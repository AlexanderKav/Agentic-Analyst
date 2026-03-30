import os
import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


class PlannerAgent:

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.6,
            api_key=os.getenv("OPENAI_API_KEY")
        )

        self.prompt = ChatPromptTemplate.from_template("""
You are an AI data analyst planner.

Given a user question, select **only the tools necessary to answer it**.
Map question intent to available tools. Do NOT include tools unrelated to the question.

Available tools:

1. compute_kpis            -> overall revenue, profit, margins
2. revenue_by_customer     -> top customers by revenue/spending trends
3. revenue_by_product      -> top products by revenue/sales trends
4. monthly_growth          -> month-over-month revenue/profit changes
5. monthly_profit          -> monthly profit totals
6. detect_revenue_spikes   -> detect sudden revenue changes
7. forecast_revenue        -> basic ARIMA forecast (requires 12+ months)
8. forecast_revenue_with_explanation -> ARIMA forecast with plain English explanation (requires 12+ months)
9. forecast_with_confidence -> ARIMA forecast with confidence intervals (requires 12+ months)
10. forecast_ensemble      -> compare multiple forecasting methods (requires 12+ months)
11. detect_seasonality     -> find seasonal patterns (REQUIRES 24+ months of data)
12. visualization          -> generate charts from results
13. monthly_revenue_by_customer -> monthly revenue trends for customers
14. monthly_revenue_by_product -> monthly revenue trends for products
15. forecast_revenue_by_product  -> forecast revenue for each product individually

CRITICAL DATA REQUIREMENTS:
- `detect_seasonality` requires AT LEAST 24 months of data (2 years)
- `forecast_*` tools require AT LEAST 12 months of data
- If data requirements aren't met, do NOT include those tools

User Question:
{question}

Instructions:
- Identify the intent and pick only the tools that directly answer it.
- Return a JSON object with a list of tools in order.
- Include `visualization` last if charts are useful.

If the question contains:
- "forecast" or "predict" → add "forecast_revenue_with_explanation" (if data available)
- "confidence" or "likely" → add "forecast_with_confidence" (if data available)
- "seasonal" or "pattern" → add "detect_seasonality" (ONLY if 24+ months data available)

Important:
- **For questions about specific time periods (Q1 2025, next quarter, next month), pass that as context**
- **Use `forecast_revenue_by_product` when asked about product success in future periods**
- **If the question contains a specific time period (e.g., "Q1 2025", "first quarter of 2025"), extract that period and add it to the plan as a context parameter**

**Return format:**
{{
  "plan": ["tool1", "tool2", ...],
  "period": "Q1 2025"  // Include this if a specific period is mentioned
}}

Return ONLY valid JSON:
{{
  "plan": [ ...tools to run... ],
  "period": "period_string_if_mentioned"
}}
""")
    def create_plan(self, question):
        messages = self.prompt.format_messages(question=question)
        response = self.llm.invoke(messages)

        raw = response.content
        print("RAW RESPONSE:", raw)

        # Extract JSON safely
        match = re.search(r'\{.*\}', raw, flags=re.DOTALL)
        if match:
            parsed_json = json.loads(match.group())
        else:
            raise ValueError("LLM did not return valid JSON:\n" + raw)

        # Extract period if present
        period = parsed_json.get("period")
        plan = parsed_json.get("plan", [])
        
        return raw, {"plan": plan, "period": period}
    
