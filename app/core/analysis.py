import re
import time
from typing import Any

import pandas as pd

from agents.analytics_agent import AnalyticsAgent
from agents.autonomous_analyst import AutonomousAnalyst
from agents.insight_agent import InsightAgent
from agents.planner_agent import PlannerAgent
from agents.schema_mapper import SchemaMapper
from agents.visualization_agent import VisualizationAgent
from connectors.data_loader import DataLoader

# Constants for validation
MAX_ROWS = 100000
MINIMUM_REQUIRED_COLUMNS = ['date', 'revenue']
MAX_STRING_LENGTH = 10000


class AnalysisOrchestrator:
    def __init__(self, data_loader: DataLoader | None = None, user_id: int | None = None):
        self.data_loader = data_loader or DataLoader()
        self.planner = PlannerAgent()
        self.insight = InsightAgent(user_id=user_id, prompt_version=None)
        self.viz = VisualizationAgent()

    def validate_dataframe(self, df: pd.DataFrame) -> bool:
        """Validate dataframe has minimum required columns and is safe"""
        missing = [col for col in MINIMUM_REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}. Your data must contain at least 'date' and 'revenue' columns.")

        if len(df) > MAX_ROWS:
            raise ValueError(f"Too many rows. Maximum allowed is {MAX_ROWS:,} rows.")

        for col in df.columns:
            if df[col].dtype == 'object':
                max_len = df[col].astype(str).str.len().max()
                if max_len > MAX_STRING_LENGTH:
                    raise ValueError(
                        f"Column '{col}' contains suspiciously long strings "
                        f"(max length: {max_len:,} chars). Limit is {MAX_STRING_LENGTH:,} chars."
                    )

        return True

    def _is_url(self, text: str) -> bool:
        """Check if text looks like a URL."""
        url_patterns = [
            r'https?://',           # http:// or https://
            r'www\.',               # www.
            r'\.com\b',             # .com
            r'\.ie\b',              # .ie
            r'\.net\b',             # .net
            r'\.org\b',             # .org
            r'\.io\b',              # .io
            r'google\.com',         # google.com
            r'docs\.google\.com',   # docs.google.com
            r'spreadsheets/d/',     # Google Sheets URL pattern
            r'edit\?gid=',          # Sheet edit URL pattern
            r'/d/e/',               # Another Google Sheets pattern
            r'github\.com',         # GitHub URLs
            r'bit\.ly',             # Shortened URLs
            r'tinyurl\.com',        # Shortened URLs
            r'cloudflare\.com',     # Cloudflare
            r'amazonaws\.com',      # AWS URLs
        ]
        for pattern in url_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _is_gibberish(self, text: str) -> bool:
        """Check if text looks like gibberish."""
        # Remove spaces for checking
        no_spaces = text.replace(' ', '')
        
        # Long string with no spaces is suspicious
        if len(no_spaces) > 20 and ' ' not in text:
            return True
        
        # Check for random keyboard mash patterns
        gibberish_patterns = [
            r'^[a-z]{15,}$',        # 15+ random letters with no spaces
            r'^[0-9]{10,}$',        # 10+ numbers
            r'^[a-z0-9]{15,}$',     # 15+ alphanumeric with no spaces
            r'[^\w\s]{5,}',         # 5+ special characters in a row
            r'^[a-z]{1,3}$',        # Single letters or very short words
            r'^[0-9]+$',            # Only numbers
            r'^[!@#$%^&*()]+$',     # Only special characters
        ]
        
        for pattern in gibberish_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        # Check common keyboard mashes
        keyboard_mashes = [
            'asdf', 'qwerty', 'zxcv', 'test123', '123456', 
            'password', 'abc123', 'qwerty123', 'aaaaaaaa', 
            'bbbbbbbb', 'abcdefgh', 'qwertyuiop'
        ]
        if text.lower() in keyboard_mashes:
            return True
        
        return False

    def _check_question_relevance(self, question: str, df: pd.DataFrame) -> tuple[bool, str]:
        """
        Check if question is relevant to the business data.
        This is a PRE-filter before any analysis.
        """
        if not question or not question.strip():
            return True, "No question provided (using default overview)"

        question_lower = question.lower().strip()
        
        # 🔥 FIRST: Check for URLs (BEFORE any other checks)
        if self._is_url(question_lower):
            print(f"❌ URL detected: {question_lower[:100]}...")
            return False, "URL detected. Please ask a business question about your data."
        
        # 🔥 SECOND: Check for gibberish
        if self._is_gibberish(question_lower):
            print(f"❌ Gibberish detected: {question_lower}")
            return False, "I couldn't understand that question. Please ask a business-related question about your data."
        
        # Quick filter for very short/meaningless questions
        if len(question_lower) < 3:
            return False, "Question is too short or meaningless. Please ask a specific business question."
        
        # Get data columns for context
        columns = [col.lower() for col in df.columns]
        
        # Business keywords - removed 'do' to avoid false positives with URLs
        business_keywords = [
            # Revenue/Financial
            'revenue', 'sales', 'profit', 'income', 'earnings', 'turnover',
            'cost', 'expense', 'margin', 'price', 'value', 'amount',
            'total', 'sum', 'average', 'mean', 'median', 'kpi', 'metric',

            # Customer related
            'customer', 'client', 'buyer', 'account', 'user', 'subscription',
            'retention', 'churn', 'acquisition', 'lifetime', 'ltv',

            # Product related
            'product', 'item', 'service', 'plan', 'sku', 'category',
            'inventory', 'stock', 'demand', 'popular', 'best', 'top',
            'worst', 'ranking', 'rank',

            # Trends/Time
            'trend', 'growth', 'decline', 'increase', 'decrease', 'change',
            'month', 'year', 'quarter', 'weekly', 'daily', 'time', 'period',
            'seasonal', 'forecast', 'predict', 'future',

            # Regional
            'region', 'market', 'geo', 'location', 'country', 'city',
            'area', 'territory', 'zone',

            # Performance
            'performance', 'performing', 'efficiency', 'conversion', 'rate', 'ratio',
            'percentage', 'share', 'market share', 'health', 'healthy',

            # Risks
            'risk', 'risks', 'danger', 'threat', 'issue', 'problem', 'concern',
            'warning', 'alert', 'vulnerability', 'exposure',

            # Status
            'paid', 'pending', 'overdue', 'refunded', 'status', 'payment',
            'order', 'transaction', 'invoice', 'subscription', 'failed',

            # Business health
            'well', 'good', 'bad', 'improve', 'improving', 'declining',
            'stable', 'volatile', 'outlook', 'overview', 'summary', 'dashboard',
            
            # Question starters (removed 'do' to avoid false positives)
            'show', 'tell', 'what', 'how', 'which', 'when', 'where', 'why',
            'is', 'are', 'does', 'can', 'could', 'would', 'should',
            'compare', 'analyze', 'calculate', 'compute', 'find', 'get'
        ]

        # Check against column names (most specific matching)
        column_matches = []
        for col in columns:
            if col in question_lower:
                column_matches.append(col)
            col_words = col.split('_')
            for word in col_words:
                if word in question_lower and len(word) > 2:
                    column_matches.append(word)
        
        column_matches = list(set(column_matches))

        # Strong signal: question mentions actual data columns
        if column_matches:
            print(f"✅ Column matches: {column_matches[:5]}")
            return True, f"Question relates to data column(s): {', '.join(column_matches[:3])}"

        # Check for business keyword matches
        matches = [kw for kw in business_keywords if kw in question_lower]
        
        if matches:
            print(f"✅ Keyword matches: {matches[:5]}")
            return True, f"Question is relevant (matched: {', '.join(matches[:3])})"

        # Check for business phrase patterns
        business_phrases = [
            r'how\s+is\s+the\s+business',
            r'how\s+are\s+we\s+doing',
            r'business\s+performance',
            r'company\s+performance',
            r'overall\s+performance',
            r'what\'s\s+the\s+state\s+of\s+the\s+business',
            r'give\s+me\s+an\s+overview',
            r'show\s+me\s+the\s+business\s+health',
            r'is\s+the\s+business\s+doing\s+well',
            r'are\s+there\s+any\s+risks',
            r'what\s+are\s+the\s+risks',
            r'business\s+risks',
            r'what\s+should\s+we\s+be\s+concerned\s+about',
            r'how\s+are\s+things\s+looking',
            r'business\s+health',
            r'company\s+health',
            r'performance\s+review'
        ]

        for pattern in business_phrases:
            if re.search(pattern, question_lower):
                print(f"✅ Business phrase matched: {pattern}")
                return True, "Question is relevant (business performance inquiry)"

        # If question contains business-related terms, be permissive
        business_terms = ['business', 'company', 'performance', 'risk', 'overview', 'summary']
        if any(term in question_lower for term in business_terms):
            print("✅ Question contains business terms, marking as relevant")
            return True, "Question is relevant (business inquiry)"

        # Check for obvious off-topic patterns (only if no business indicators)
        off_topic_patterns = [
            r'\bhappiest\b', r'\bsaddest\b', r'\bweather\b', r'\bclimate\b',
            r'\bpolitics\b', r'\belection\b', r'\bpresident\b', r'\bprime\s+minister\b',
            r'\bfamous\b', r'\bcelebrity\b', r'\bactor\b', r'\bactress\b',
            r'\bsports\b', r'\bfootball\b', r'\bsoccer\b', r'\bbasketball\b',
            r'\bmovie\b', r'\bfilm\b', r'\bmusic\b', r'\bsong\b',
            r'\bworld\s+record\b', r'\bguinness\b',
            r'\bwho\s+is\b', r'\bmeaning\s+of\b',
            r'\bhistory\b', r'\binventor\b', r'\bdiscovery\b',
            r'\brecipe\b', r'\bcooking\b', r'\bfood\b',
            r'\btravel\b', r'\bvacation\b', r'\bholiday\b',
            r'\bhow\s+to\s+make\b', r'\bhow\s+to\s+build\b',
            r'\bspaghetti\b', r'\bpasta\b', r'\bpizza\b',
            r'\bhello\b', r'\bhi\b', r'\bhey\b', r'\bgreetings\b',
        ]

        for pattern in off_topic_patterns:
            if re.search(pattern, question_lower):
                print(f"❌ Off-topic pattern matched: {pattern}")
                return False, "This question appears to be off-topic for business data analysis."

        # If we have data columns and the question isn't obviously off-topic, assume it's relevant
        if columns:
            print("⚠️ No clear match but data exists. Defaulting to relevant.")
            return True, "Question is potentially relevant to business data."

        return False, "Question doesn't seem related to your business data. Try asking about revenue, customers, products, or trends."

    def _get_irrelevant_response(self, question: str, df: pd.DataFrame, execution_time: float = 0.0) -> tuple[dict, float]:
        """Generate a friendly response for irrelevant questions."""
        columns = list(df.columns)[:8]
        
        # Check if it's a URL for a slightly different message
        is_url = self._is_url(question)
        
        if is_url:
            response_text = (
                "I noticed you pasted a URL or link.\n\n"
                "I'm a business analytics assistant. I can only answer questions about your business data.\n\n"
                f"Your dataset contains columns like: {', '.join(columns)}{'...' if len(df.columns) > 8 else ''}\n\n"
                "Here are some examples of questions I can help with:\n"
                "  • 'What are our top products by revenue?'\n"
                "  • 'Show me revenue trends over time'\n"
                "  • 'Who are our top customers?'\n"
                "  • 'What's our profit margin?'\n"
                "  • 'Which region has the highest sales?'\n\n"
                "Please ask a business question about your data, not a URL."
            )
        else:
            response_text = (
                "I'm a business analytics assistant. I can only answer questions about your business data.\n\n"
                f"Your dataset contains columns like: {', '.join(columns)}{'...' if len(df.columns) > 8 else ''}\n\n"
                "Here are some examples of questions I can help with:\n"
                "  • 'What are our top products by revenue?'\n"
                "  • 'Show me revenue trends over time'\n"
                "  • 'Who are our top customers?'\n"
                "  • 'What's our profit margin?'\n"
                "  • 'Which region has the highest sales?'\n"
                "  • 'How has revenue grown month-over-month?'\n"
                "  • 'Are there any anomalies in the data?'\n"
                "  • 'What's the forecast for next quarter?'\n\n"
                "Please ask a business question about your data."
            )
        
        response = {
            "success": True,
            "insights": response_text,
            "raw_insights": {
                "answer": "Please ask a business-related question about your data.",
                "human_readable_summary": "This question is not related to business data analysis.",
                "supporting_insights": {},
                "anomalies": {},
                "recommended_metrics": {}
            },
            "results": {},
            "plan": {"plan": []},
            "warnings": ["Question not related to business data"],
            "mapping": {},
            "data_summary": {
                "rows": len(df),
                "columns": list(df.columns)
            },
            "execution_time": execution_time,
            "is_generic_overview": False
        }
        
        return response, execution_time

    async def analyze_dataframe(self, df: pd.DataFrame, question: str) -> tuple[dict[str, Any], float]:
        """
        Analyze a pandas DataFrame directly (used by both file upload and database)
        """
        start_time = time.time()

        try:
            # 🔐 VALIDATE THE DATAFRAME FIRST
            self.validate_dataframe(df)

            # 🔥 CHECK QUESTION RELEVANCE BEFORE ANY ANALYSIS
            if question and question.strip():
                is_relevant, relevance_message = self._check_question_relevance(question, df)
                print(f"🔍 Relevance check: {relevance_message}")

                if not is_relevant:
                    execution_time = time.time() - start_time
                    return self._get_irrelevant_response(question, df, execution_time)

            print("🧹 Cleaning and mapping schema...")
            mapper = SchemaMapper(df)
            clean_df, mapping, warnings = mapper.map_schema()
            print(f"✅ Schema mapped. Shape: {clean_df.shape}")

            analytics = AnalyticsAgent(clean_df)
            
            analyst = AutonomousAnalyst(
                planner=self.planner,
                analytics=analytics,
                insight_agent=self.insight,
                viz_agent=self.viz,
            )

            if not question or question.strip() == "":
                # Generic overview
                print("📊 Generating generic overview")

                # Compute KPIs
                kpis = analytics.compute_kpis()

                # Get top customers
                customer_data = analytics.revenue_by_customer()
                if isinstance(customer_data, dict):
                    sorted_customers = sorted(customer_data.items(), key=lambda x: x[1], reverse=True)[:5]
                    top_customers = dict(sorted_customers)
                else:
                    top_customers = {}

                # Get top products
                product_data = analytics.revenue_by_product()
                if isinstance(product_data, dict):
                    sorted_products = sorted(product_data.items(), key=lambda x: x[1], reverse=True)[:5]
                    top_products = dict(sorted_products)
                else:
                    top_products = {}

                # Get monthly trend
                monthly_data = analytics.monthly_revenue()
                if hasattr(monthly_data, 'to_dict'):
                    monthly_trend = monthly_data.to_dict()
                elif isinstance(monthly_data, dict):
                    monthly_trend = monthly_data
                else:
                    monthly_trend = {}

                # Get anomalies
                spikes_data = analytics.detect_revenue_spikes()
                if hasattr(spikes_data, 'to_dict'):
                    anomalies = spikes_data.to_dict()
                elif isinstance(spikes_data, dict):
                    anomalies = spikes_data
                else:
                    anomalies = {}

                overview = {
                    "answer": "Here's a comprehensive overview of your business data:",
                    "supporting_insights": {
                        "key_metrics": kpis,
                        "top_customers": top_customers,
                        "top_products": top_products,
                        "monthly_trend": monthly_trend,
                        "anomalies_detected": len(anomalies) > 0
                    },
                    "anomalies": anomalies if anomalies else {"note": "No significant anomalies detected"},
                    "recommended_metrics": {
                        "customer_retention": "Analyze customer retention rates",
                        "profit_margin_trend": "Track profit margin over time",
                        "seasonal_patterns": "Look for seasonal patterns in your data"
                    },
                    "human_readable_summary": self._generate_overview_summary(
                        kpis, top_customers, top_products, anomalies
                    )
                }

                results = {
                    "kpis": kpis,
                    "top_customers": top_customers,
                    "top_products": top_products,
                    "monthly_trend": monthly_trend
                }

                insights = overview["human_readable_summary"]
                plan = {"plan": ["compute_kpis", "revenue_by_customer", "revenue_by_product", "monthly_revenue", "detect_revenue_spikes"]}
                raw_insights = None

            else:
                print(f"❓ Question: {question}")
                raw_plan, plan, results, raw_insights, insights = analyst.run(question)

            execution_time = time.time() - start_time

            return {
                "success": True,
                "insights": insights,
                "raw_insights": raw_insights,
                "results": results,
                "plan": plan,
                "warnings": warnings,
                "mapping": mapping,
                "data_summary": {
                    "rows": len(clean_df),
                    "columns": list(clean_df.columns)
                },
                "execution_time": execution_time,
                "is_generic_overview": not question or question.strip() == ""
            }, execution_time

        except ValueError as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "insights": f"Validation Error: {str(e)}",
                "results": {},
                "plan": {"plan": []},
                "warnings": [],
                "data_summary": {
                    "rows": len(df) if 'df' in locals() else 0,
                    "columns": list(df.columns) if 'df' in locals() else []
                },
                "execution_time": execution_time,
                "is_generic_overview": False
            }, execution_time

        except Exception as e:
            import traceback
            traceback.print_exc()
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "insights": f"Analysis Error: {str(e)}",
                "results": {},
                "plan": {"plan": []},
                "warnings": [],
                "data_summary": {
                    "rows": len(df) if 'df' in locals() else 0,
                    "columns": list(df.columns) if 'df' in locals() else []
                },
                "execution_time": execution_time,
                "is_generic_overview": False
            }, execution_time

    async def analyze(
        self,
        question: str,
        source_type: str,
        source_config: dict[str, Any]
    ) -> tuple[dict[str, Any], float]:
        """
        Run complete analysis pipeline
        
        If question is empty, provides a generic business overview
        """
        start_time = time.time()

        try:
            print(f"📂 Loading data from {source_type}...")
            df = self._load_data(source_type, source_config)
            print(f"✅ Loaded {len(df)} rows")

            return await self.analyze_dataframe(df, question)

        except Exception as e:
            import traceback
            traceback.print_exc()
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "insights": f"Error: {str(e)}",
                "results": {},
                "plan": {"plan": []},
                "warnings": [],
                "data_summary": {
                    "rows": 0,
                    "columns": []
                },
                "execution_time": execution_time,
                "is_generic_overview": False
            }, execution_time

    def _generate_overview_summary(self, kpis: dict, top_customers: dict, top_products: dict, anomalies: dict) -> str:
        """Generate a human-readable overview summary"""
        summary = f"Your business has generated ${kpis.get('total_revenue', 0):,.0f} in revenue "
        summary += f"with a {kpis.get('profit_margin', 0)*100:.1f}% profit margin. "

        if top_customers:
            top_cust = list(top_customers.keys())[0] if top_customers else "N/A"
            top_cust_value = list(top_customers.values())[0] if top_customers else 0
            summary += f"Your top customer is {top_cust} "
            summary += f"contributing ${top_cust_value:,.0f}. "

        if top_products:
            top_prod = list(top_products.keys())[0] if top_products else "N/A"
            top_prod_value = list(top_products.values())[0] if top_products else 0
            summary += f"The best-selling product is {top_prod} "
            summary += f"with ${top_prod_value:,.0f} in revenue. "

        if anomalies:
            summary += f"We detected {len(anomalies)} revenue anomalies that may need investigation."
        else:
            summary += "No significant revenue anomalies were detected."

        return summary

    def _load_data(self, source_type: str, config: dict[str, Any]) -> pd.DataFrame:
        """Load data based on source type"""
        print(f"📂 Loading data from {source_type}...")

        if source_type == "database":
            return self.data_loader.load('database', config)

        elif source_type in ["csv", "excel"]:
            file_path = config.get('path')
            if not file_path:
                raise ValueError("No file path provided")

            print(f"📁 File path: {file_path}")
            return self.data_loader.load(source_type, file_path)

        elif source_type == "google_sheets":
            return self.data_loader.load('google_sheets', {
                'sheet_id': config.get('sheet_id'),
                'range': config.get('range', 'A1:Z1000')
            })

        else:
            raise ValueError(f"Unsupported source type: {source_type}")