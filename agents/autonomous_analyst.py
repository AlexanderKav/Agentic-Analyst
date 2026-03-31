import pandas as pd
import numpy as np
from datetime import datetime
from agents.insight_agent import make_json_safe
from agents.monitoring import get_performance_tracker, timer, get_audit_logger, get_cost_tracker
from agents.self_healing import get_healing_agent

class AutonomousAnalyst:
    def __init__(self, planner, analytics, insight_agent, viz_agent, user_id=None):
        self.planner = planner
        self.analytics = analytics
        self.insight_agent = insight_agent
        self.viz_agent = viz_agent
        self.analytics_cache = {}
        
        # Initialize monitoring
        self.perf_tracker = get_performance_tracker()
        self.audit_logger = get_audit_logger()
        self.cost_tracker = get_cost_tracker()
        self.healer = get_healing_agent()
        self.session_id = id(self)
        
        # Audit log initialization
        self.audit_logger.log_action(
            action_type='autonomous_init',
            agent='autonomous',
            details={
                'has_planner': planner is not None,
                'has_analytics': analytics is not None,
                'has_insight': insight_agent is not None,
                'has_viz': viz_agent is not None
            },
            session_id=self.session_id
        )
    
    def detect_question_type(self, question):
        """Detect the type of question to filter relevant data"""
        if not question:
            return "overview"
        
        question_lower = question.lower()
        
        # Forecast keywords - expanded
        forecast_keywords = [
            'forecast', 'predict', 'future', '2025', '2026', '2027',
            'next year', 'coming year', 'will be', 'will look',
            'projection', 'estimate', 'expected', 'anticipate',
            'first quarter', 'q1', 'second quarter', 'q2', 
            'third quarter', 'q3', 'fourth quarter', 'q4',
            'most likely', 'likely to be', 'most successful',
            'q1 2025', 'q2 2025', 'q3 2025', 'q4 2025',
            'next quarter', 'next month', 'upcoming'
        ]
        
        # Risk keywords
        risk_keywords = [
            'risk', 'risks', 'concern', 'threat', 'vulnerability',
            'danger', 'issue', 'problem', 'challenge', 'exposure',
            'downside', 'warning', 'alert'
        ]
        
        # Performance keywords
        performance_keywords = [
            'performance', 'overview', 'dashboard', 'summary',
            'how is', 'how are', 'doing', 'health', 'status'
        ]
        
        # Revenue/product specific keywords
        revenue_keywords = [
            'revenue', 'sales', 'profit', 'income', 'earnings',
            'product', 'customer', 'region', 'top', 'best', 'worst'
        ]
        
        if any(kw in question_lower for kw in forecast_keywords):
            return "forecast"
        elif any(kw in question_lower for kw in risk_keywords):
            return "risk"
        elif any(kw in question_lower for kw in performance_keywords):
            return "performance"
        elif any(kw in question_lower for kw in revenue_keywords):
            return "revenue_analysis"
        else:
            return "general"
    
    @staticmethod
    def make_json_safe(obj):
        """Recursively convert all objects to JSON-serializable types."""
        if isinstance(obj, dict):
            return {str(k): AutonomousAnalyst.make_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [AutonomousAnalyst.make_json_safe(x) for x in obj]
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
        elif obj is None:
            return None
        else:
            try:
                return str(obj)
            except:
                return None

    @timer(operation='cached_run')
    def cached_run(self, tool_name):
        """Cache tool results to avoid repeated computation."""
        try:
            if tool_name in self.analytics_cache:
                self.audit_logger.log_action(
                    action_type='cache_hit',
                    agent='autonomous',
                    details={'tool': tool_name},
                    session_id=self.session_id
                )
                return self.analytics_cache[tool_name]
                
            result = self.analytics.run_tool(tool_name)
            self.analytics_cache[tool_name] = result
            
            self.audit_logger.log_action(
                action_type='cache_miss',
                agent='autonomous',
                details={'tool': tool_name},
                session_id=self.session_id
            )
            
            return result
            
        except Exception as e:
            self.healer.analyze_failure(e, {
                'tool': 'cached_run',
                'tool_name': tool_name,
                'cache_keys': list(self.analytics_cache.keys())
            })
            raise

    @timer(operation='autonomous_run')
    def run(self, question=None):
        """
        Run analysis based on a question.
        - Returns: JSON-safe raw_plan, plan, results, raw_insights, insights
        """
        try:
            # Audit log start
            self.audit_logger.log_action(
                action_type='run_start',
                agent='autonomous',
                details={'question': question, 'has_question': question is not None},
                session_id=self.session_id
            )
            
            # Step 1: Determine tools
            plan_period = None  # Initialize plan_period

            if question:
                raw_plan, plan_data = self.planner.create_plan(question)
                
                # Debug: print what we got
                print("RAW PLAN:", raw_plan)
                print("PLAN DATA:", plan_data)
                
                # Handle plan_data correctly
                if isinstance(plan_data, dict):
                    # If it's a dictionary with 'plan' key
                    if "plan" in plan_data:
                        plan = plan_data["plan"]
                        plan_period = plan_data.get("period")  # Capture the period from planner
                    else:
                        # Assume the dict itself is the plan
                        plan = plan_data
                elif isinstance(plan_data, list):
                    # If it's a list, use it as the plan
                    plan = plan_data
                else:
                    # Fallback
                    plan = []
                
                # Ensure plan is a list
                if not isinstance(plan, list):
                    plan = []
                
                # Print the captured period if available
                if plan_period:
                    print(f"📅 Plan period detected: {plan_period}")
                
                # Detect question type and add necessary tools
                question_type = self.detect_question_type(question)
                print(f"🔍 Detected question type: {question_type}")
                
                # For forecast questions, ensure we have monthly product data
                if question_type == "forecast":
                    if "monthly_revenue_by_product" not in plan:
                        print("📊 Adding monthly_revenue_by_product to plan for forecast question")
                        plan.append("monthly_revenue_by_product")
                    
                    if "monthly_growth" not in plan:
                        plan.append("monthly_growth")
                    
                    if "revenue_by_product" not in plan:
                        plan.append("revenue_by_product")
                    
                    # Also ensure forecast_revenue_by_product is in the plan
                    if "forecast_revenue_by_product" not in plan:
                        print("📈 Adding forecast_revenue_by_product to plan for forecast question")
                        plan.append("forecast_revenue_by_product")
                
                # Track LLM cost for planner
                self.cost_tracker.track_call(
                    model='gpt-4o-mini',
                    input_tokens=len(question.split()),
                    output_tokens=len(str(plan).split()),
                    agent='planner',
                    user='system',
                    session_id=self.session_id
                )
                self.audit_logger.log_action(
                    action_type='plan_created',
                    agent='autonomous',
                    details={
                        'question': question,
                        'plan': plan,
                        'period': plan_period,
                        'num_tools': len(plan)
                    },
                    session_id=self.session_id
                )
            else:
                # No question - default overview plan
                # Check if we have enough data for seasonality
                monthly_revenue = self.analytics.monthly_revenue()
                has_enough_for_seasonality = len(monthly_revenue) >= 24 if not monthly_revenue.empty else False
                
                plan = [
                    "compute_kpis",
                    "monthly_profit",
                    "monthly_growth",
                    "detect_revenue_spikes",
                    "monthly_revenue_by_product",
                    "forecast_revenue_with_explanation",
                    "forecast_with_confidence",            
                    "forecast_ensemble",                   
                    "visualization",
                    "revenue_by_customer",
                    "revenue_by_product",
                    "monthly_revenue_by_customer",
                    "forecast_revenue_by_product",
                ]
                
                # Only add seasonality if we have enough data
                if has_enough_for_seasonality:
                    plan.insert(4, "detect_seasonality")
                    self.audit_logger.log_action(
                        action_type='seasonality_included',
                        agent='autonomous',
                        details={'months_available': len(monthly_revenue)},
                        session_id=self.session_id
                    )
                else:
                    self.audit_logger.log_action(
                        action_type='seasonality_skipped',
                        agent='autonomous',
                        details={'reason': 'insufficient_data', 'months_available': len(monthly_revenue)},
                        session_id=self.session_id
                    )
                
                raw_plan = "Default general analysis plan applied."
                plan_period = None
                self.audit_logger.log_action(
                    action_type='default_plan_used',
                    agent='autonomous',
                    details={'num_tools': len(plan)},
                    session_id=self.session_id
                )
            # Step 2: Run tools
            results = {}
            raw_results = {}
            failed_tools = []
            skipped_tools = []

            for tool in plan:
                if tool == "visualization":
                    continue

                try:
                    # List of tools that can accept a period parameter
                    period_tools = [
                        "forecast_revenue_by_product",
                        "forecast_revenue_with_explanation",
                        "forecast_with_confidence",
                        "forecast_ensemble"
                    ]
                    
                    # Check if this tool needs period parameter
                    if tool in period_tools and plan_period:
                        # Call tool with period parameter
                        tool_func = getattr(self.analytics, tool, None)
                        if tool_func:
                            print(f"🔮 Calling {tool} with period: {plan_period}")
                            tool_result = tool_func(period_label=plan_period)
                        else:
                            # Fallback to cached run if method doesn't exist
                            tool_result = self.cached_run(tool)
                    else:
                        # Regular tool call without parameters
                        tool_result = self.cached_run(tool)
                    
                    raw_results[tool] = tool_result

                    # Check if tool returned "insufficient_data"
                    if isinstance(tool_result, dict) and tool_result.get("error") == "insufficient_data":
                        skipped_tools.append(tool)
                        print(f"⚠️ Skipping {tool} - insufficient data")
                        results[tool] = tool_result
                    else:
                        # Convert pandas → JSON-compatible
                        if isinstance(tool_result, pd.DataFrame):
                            tool_result = tool_result.copy()
                            for col in tool_result.select_dtypes(include=["datetime64[ns]"]):
                                tool_result[col] = tool_result[col].astype(str)
                            tool_result = tool_result.to_dict(orient="records")
                        elif isinstance(tool_result, pd.Series):
                            if pd.api.types.is_datetime64_any_dtype(tool_result.index):
                                tool_result.index = tool_result.index.astype(str)
                            tool_result = tool_result.to_dict()

                        # Make JSON-safe
                        results[tool] = make_json_safe(tool_result)
                        
                except Exception as e:
                    failed_tools.append(tool)
                    self.healer.analyze_failure(e, {
                        'tool': tool,
                        'phase': 'tool_execution',
                        'question': question
                    })
                    results[tool] = {"error": str(e), "status": "failed"}

            # Step 3: Generate charts
            charts = {}
            if raw_results:
                try:
                    charts = self.viz_agent.generate_from_results(raw_results)
                    
                    if "forecast_revenue_by_product" in raw_results:
                        forecast_data = raw_results["forecast_revenue_by_product"]
                        if isinstance(forecast_data, dict) and "forecasts" in forecast_data:
                            period_label = forecast_data.get("period", "Next Quarter")
                            forecast_chart = self.viz_agent.plot_product_forecast(
                                forecast_data, 
                                period_label
                            )
                            if forecast_chart:
                                charts["product_forecast"] = forecast_chart
                                print(f"📊 Added product forecast chart for {period_label}")
                    
                    if charts:
                        results["charts"] = make_json_safe(charts)
                        self.audit_logger.log_action(
                            action_type='charts_generated',
                            agent='autonomous',
                            details={'num_charts': len(charts)},
                            session_id=self.session_id
                        )
                except Exception as e:
                    self.healer.analyze_failure(e, {'tool': 'visualization'})
                    results["charts"] = {"error": str(e), "status": "failed"}

            # Add note about skipped tools
            if skipped_tools:
                results["_skipped_tools_note"] = {
                    "message": f"The following tools were skipped due to insufficient data: {', '.join(skipped_tools)}",
                    "skipped_tools": skipped_tools
                }

            # Step 3.5: Prepare combined data for insight agent
            combined_data = {}

            # Add KPIs
            if "compute_kpis" in results:
                kpis = results["compute_kpis"]
                if not isinstance(kpis, dict) or "error" not in kpis:
                    combined_data["total_revenue"] = kpis.get("total_revenue", 0)
                    combined_data["total_cost"] = kpis.get("total_cost", 0)
                    combined_data["total_profit"] = kpis.get("total_profit", 0)
                    combined_data["profit_margin"] = kpis.get("profit_margin", 0)
                    combined_data["avg_order_value"] = kpis.get("avg_order_value", 0)
                    combined_data["total_transactions"] = kpis.get("total_transactions", 0)

            # Add monthly growth
            if "monthly_growth" in results:
                monthly_growth = results["monthly_growth"]
                if isinstance(monthly_growth, dict) and "error" not in monthly_growth:
                    combined_data["monthly_growth"] = monthly_growth

            # Add monthly profit
            if "monthly_profit" in results:
                monthly_profit = results["monthly_profit"]
                if isinstance(monthly_profit, dict) and "error" not in monthly_profit:
                    combined_data["monthly_profit"] = monthly_profit

            # Add monthly revenue by product - with fallback
            if "monthly_revenue_by_product" in results:
                monthly_product_data = results["monthly_revenue_by_product"]
                if isinstance(monthly_product_data, dict) and "error" not in monthly_product_data:
                    formatted_product_data = {}
                    for product, details in monthly_product_data.items():
                        if isinstance(details, dict) and "monthly_revenue" in details:
                            product_name = product.replace('_', ' ').replace('Plan', ' Plan')
                            formatted_product_data[f"{product_name}_monthly_trend"] = details["monthly_revenue"]
                    
                    if formatted_product_data:
                        combined_data["product_monthly_trends"] = formatted_product_data
                        print(f"📊 Added product monthly trends for {len(formatted_product_data)} products")
            else:
                # Fallback: try to compute directly
                print("⚠️ monthly_revenue_by_product not in results, attempting direct computation...")
                try:
                    if hasattr(self.analytics, 'monthly_revenue_by_product'):
                        monthly_product_data = self.analytics.monthly_revenue_by_product()
                        if monthly_product_data:
                            formatted_product_data = {}
                            for product, details in monthly_product_data.items():
                                if isinstance(details, dict) and "monthly_revenue" in details:
                                    product_name = product.replace('_', ' ').replace('Plan', ' Plan')
                                    formatted_product_data[f"{product_name}_monthly_trend"] = details["monthly_revenue"]
                            
                            if formatted_product_data:
                                combined_data["product_monthly_trends"] = formatted_product_data
                                results["monthly_revenue_by_product"] = monthly_product_data
                                print(f"📊 Added product monthly trends via direct call: {len(formatted_product_data)} products")
                except Exception as e:
                    print(f"⚠️ Could not compute monthly_revenue_by_product directly: {e}")

            # Add revenue by product
            if "revenue_by_product" in results:
                revenue_by_product = results["revenue_by_product"]
                if isinstance(revenue_by_product, dict) and "error" not in revenue_by_product:
                    product_totals = {}
                    for product, revenue in revenue_by_product.items():
                        product_name = product.replace('_', ' ').replace('Plan', ' Plan')
                        product_totals[product_name] = revenue
                    combined_data["revenue_by_product"] = product_totals
            else:
                # Fallback
                try:
                    product_revenue = self.analytics.revenue_by_product()
                    if product_revenue:
                        product_totals = {}
                        for product, revenue in product_revenue.items():
                            product_name = product.replace('_', ' ').replace('Plan', ' Plan')
                            product_totals[product_name] = revenue
                        combined_data["revenue_by_product"] = product_totals
                except Exception as e:
                    print(f"⚠️ Could not get revenue_by_product: {e}")

            # Add revenue by region
            if "revenue_by_region" in results:
                revenue_by_region = results["revenue_by_region"]
                if isinstance(revenue_by_region, dict) and "error" not in revenue_by_region:
                    combined_data["revenue_by_region"] = revenue_by_region

            # Add top customers
            if "revenue_by_customer" in results:
                revenue_by_customer = results["revenue_by_customer"]
                if isinstance(revenue_by_customer, dict) and "error" not in revenue_by_customer:
                    top_customers = {}
                    if revenue_by_customer:
                        sorted_customers = sorted(revenue_by_customer.items(), key=lambda x: x[1], reverse=True)[:5]
                        top_customers = dict(sorted_customers)
                    combined_data["top_customers"] = top_customers

            # Add anomalies
            combined_data["anomalies"] = {}

            if "detect_revenue_spikes" in results:
                overall_anomalies = results["detect_revenue_spikes"]
                if isinstance(overall_anomalies, dict) and "error" not in overall_anomalies:
                    if overall_anomalies:
                        combined_data["anomalies"]["overall"] = overall_anomalies

            # Get product-level anomalies
            try:
                if hasattr(self.analytics, 'detect_revenue_spikes'):
                    product_anomalies = self.analytics.detect_revenue_spikes(by_product=True)
                    if product_anomalies and isinstance(product_anomalies, dict) and product_anomalies:
                        combined_data["anomalies"]["product_level"] = product_anomalies
                        print(f"📊 Added product-level anomalies: {len(product_anomalies)} products affected")
            except Exception as e:
                print(f"⚠️ Could not get product-level anomalies: {e}")

            if not combined_data.get("anomalies"):
                del combined_data["anomalies"]

            # Add payment status and risk indicators
            try:
                if hasattr(self.analytics, 'df') and 'payment_status' in self.analytics.df.columns:
                    payment_counts = self.analytics.df['payment_status'].value_counts().to_dict()
                    combined_data["payment_status_counts"] = payment_counts
                    
                    if 'revenue' in self.analytics.df.columns:
                        failed_revenue = self.analytics.df[self.analytics.df['payment_status'] == 'failed']['revenue'].sum()
                        pending_revenue = self.analytics.df[self.analytics.df['payment_status'] == 'pending']['revenue'].sum()
                        combined_data["revenue_at_risk"] = float(failed_revenue + pending_revenue)
                        combined_data["failed_payments_count"] = int(payment_counts.get('failed', 0))
                        combined_data["pending_payments_count"] = int(payment_counts.get('pending', 0))
            except:
                pass

            # Add missing customers
            try:
                if hasattr(self.analytics, 'df') and 'customer' in self.analytics.df.columns:
                    missing_customers = self.analytics.df['customer'].isna().sum()
                    combined_data["missing_customers"] = int(missing_customers)
                    if missing_customers > 0:
                        combined_data["missing_customers_percentage"] = round((missing_customers / len(self.analytics.df)) * 100, 1)
            except:
                pass

            # Add summary statistics
            if combined_data.get("monthly_growth"):
                growth_values = [v for v in combined_data["monthly_growth"].values() if isinstance(v, (int, float)) and v != 0]
                if growth_values:
                    combined_data["positive_growth_months"] = len([v for v in growth_values if v > 0])
                    combined_data["negative_growth_months"] = len([v for v in growth_values if v < 0])
                    combined_data["max_growth"] = max(growth_values) if growth_values else 0
                    combined_data["min_growth"] = min(growth_values) if growth_values else 0
                    combined_data["avg_growth"] = sum(growth_values) / len(growth_values) if growth_values else 0
                    
                    # Get the latest growth value (most recent month)
                    latest_month = list(combined_data["monthly_growth"].keys())[-1] if combined_data["monthly_growth"] else None
                    latest_growth = list(combined_data["monthly_growth"].values())[-1] if combined_data["monthly_growth"] else 0
                    combined_data["latest_growth"] = latest_growth
                    combined_data["latest_growth_month"] = latest_month
                    
                    # Calculate growth trend (improving or worsening)
                    growth_list = list(combined_data["monthly_growth"].values())
                    if len(growth_list) >= 3:
                        first_third = sum(growth_list[:len(growth_list)//3]) / (len(growth_list)//3)
                        last_third = sum(growth_list[-len(growth_list)//3:]) / (len(growth_list)//3)
                        combined_data["growth_trend"] = "improving" if last_third > first_third else "worsening" if last_third < first_third else "stable"
                    else:
                        combined_data["growth_trend"] = "insufficient_data"
                    
                    print(f"📈 Growth metrics calculated: avg={combined_data['avg_growth']:.2%}, trend={combined_data['growth_trend']}, latest={latest_growth:.2%}")
                else:
                    combined_data["positive_growth_months"] = 0
                    combined_data["negative_growth_months"] = 0
                    combined_data["max_growth"] = 0
                    combined_data["min_growth"] = 0
                    combined_data["avg_growth"] = 0
                    combined_data["growth_trend"] = "no_growth_data"

            # Debug print
            print("\n📊 Combined data for insight agent:")
            print(f"  - Total Revenue: ${combined_data.get('total_revenue', 0):,.0f}")
            print(f"  - Profit Margin: {combined_data.get('profit_margin', 0)*100:.1f}%")
            if combined_data.get("product_monthly_trends"):
                print(f"  - Product monthly trends: {len(combined_data['product_monthly_trends'])} products")
            if combined_data.get("anomalies"):
                print(f"  - Anomalies: {len(combined_data['anomalies'].get('product_level', {}))} product-level")

            # Step 4: Build filtered insight data based on question type
            question_type = self.detect_question_type(question) if question else "overview"
            print(f"\n🔍 Building insight data for question type: {question_type}")
            
            insight_data = {}
            
            if question_type == "forecast":
                print("📈 Using forecast-focused data for insight agent")
                insight_data = {
                    "product_monthly_trends": combined_data.get("product_monthly_trends", {}),
                    "monthly_growth": combined_data.get("monthly_growth", {}),
                    "monthly_profit": combined_data.get("monthly_profit", {}),
                    "revenue_by_product": combined_data.get("revenue_by_product", {}),
                    "total_revenue": combined_data.get("total_revenue", 0),
                    "profit_margin": combined_data.get("profit_margin", 0),
                    "question_type": "forecast"
                }
                if combined_data.get("monthly_growth"):
                    growth_values = [v for v in combined_data["monthly_growth"].values() if isinstance(v, (int, float)) and v != 0]
                    if growth_values:
                        insight_data["positive_growth_months"] = combined_data.get("positive_growth_months", 0)
                        insight_data["negative_growth_months"] = combined_data.get("negative_growth_months", 0)
                        insight_data["avg_growth"] = sum(growth_values) / len(growth_values) if growth_values else 0
                        
            elif question_type == "risk":
                print("⚠️ Using risk-focused data for insight agent")
                insight_data = {
                    "payment_status": combined_data.get("payment_status_counts", {}),
                    "revenue_at_risk": combined_data.get("revenue_at_risk", 0),
                    "missing_customers": combined_data.get("missing_customers", 0),
                    "failed_payments_count": combined_data.get("failed_payments_count", 0),
                    "pending_payments_count": combined_data.get("pending_payments_count", 0),
                    "anomalies": combined_data.get("anomalies", {}),
                    "product_monthly_trends": combined_data.get("product_monthly_trends", {}),
                    "question_type": "risk"
                }
                
            elif question_type == "performance":
                print("📊 Using performance-focused data for insight agent")
                insight_data = {
                    "total_revenue": combined_data.get("total_revenue", 0),
                    "total_profit": combined_data.get("total_profit", 0),
                    "profit_margin": combined_data.get("profit_margin", 0),
                    "product_monthly_trends": combined_data.get("product_monthly_trends", {}),
                    "top_customers": combined_data.get("top_customers", {}),
                    "revenue_by_region": combined_data.get("revenue_by_region", {}),
                    "monthly_growth": combined_data.get("monthly_growth", {}),
                    "question_type": "performance"
                }
                
            elif question_type == "revenue_analysis":
                print("💰 Using revenue analysis data for insight agent")
                insight_data = {
                    "total_revenue": combined_data.get("total_revenue", 0),
                    "product_monthly_trends": combined_data.get("product_monthly_trends", {}),
                    "revenue_by_product": combined_data.get("revenue_by_product", {}),
                    "revenue_by_region": combined_data.get("revenue_by_region", {}),
                    "top_customers": combined_data.get("top_customers", {}),
                    "monthly_growth": combined_data.get("monthly_growth", {}),
                    "question_type": "revenue_analysis"
                }
                
            else:
                print("📋 Using all data for insight agent (general overview)")
                insight_data = combined_data
                insight_data["question_type"] = "general"

            # Debug print insight data
            print(f"\n📊 Insight data prepared:")
            print(f"  - Keys: {list(insight_data.keys())}")
            if 'product_monthly_trends' in insight_data:
                print(f"  - product_monthly_trends: {list(insight_data['product_monthly_trends'].keys())}")

            # Step 5: Generate insights
            try:
                if question:
                    raw_insights, insights = self.insight_agent.generate_insights(insight_data, question)
                    # Track LLM cost
                    input_text = str(insight_data)
                    output_text = str(insights) if insights else ""
                    
                    self.cost_tracker.track_call(
                        model='gpt-4o-mini',
                        input_tokens=len(input_text.split()) if input_text else 0,
                        output_tokens=len(output_text.split()) if output_text else 0,
                        agent='insight',
                        user='system',
                        session_id=self.session_id
                    )
                else:
                    raw_insights, insights = self.insight_agent.generate_insights(
                        insight_data, question="General business performance overview"
                    )
                    
                self.audit_logger.log_action(
                    action_type='insights_generated',
                    agent='autonomous',
                    details={'insights_length': len(insights) if insights else 0},
                    session_id=self.session_id
                )
                
            except Exception as e:
                self.healer.analyze_failure(e, {'tool': 'insight_generation', 'question': question})
                raw_insights = {"error": str(e)}
                insights = f"Error generating insights: {str(e)}"

            # Audit log completion
            self.audit_logger.log_action(
                action_type='run_complete',
                agent='autonomous',
                details={
                    'tools_used': list(results.keys()),
                    'failed_tools': failed_tools,
                    'skipped_tools': skipped_tools,
                    'has_charts': 'charts' in results,
                    'success': len(failed_tools) < len(plan)
                },
                session_id=self.session_id
            )
            self.perf_tracker.export_metrics()
            
            # Ensure JSON-safe return values
            return (
                make_json_safe(raw_plan),
                make_json_safe(plan),
                make_json_safe(results),
                make_json_safe(raw_insights),
                make_json_safe(insights)
            )
            
        except Exception as e:
            # Critical failure
            context = {
                'tool': 'autonomous_run',
                'question': question,
                'error_type': type(e).__name__
            }
            action = self.healer.analyze_failure(e, context)
            
            self.audit_logger.log_action(
                action_type='run_critical_error',
                agent='autonomous',
                details={
                    'error': str(e),
                    'suggestion': action.suggestion if action else None
                },
                session_id=self.session_id
            )
            
            error_result = {
                "compute_kpis": {"error": f"Analysis failed: {str(e)}"}
            }
            return (
                make_json_safe("Error in analysis"),
                make_json_safe({"plan": []}),
                make_json_safe(error_result),
                make_json_safe({"error": str(e)}),
                make_json_safe(f"Analysis failed: {str(e)}")
            )
    

    @timer(operation='cached_run_with_params')
    def cached_run_with_params(self, tool_name, **params):
        """Cache tool results with parameters to avoid repeated computation."""
        try:
            cache_key = f"{tool_name}_{hash(frozenset(params.items()))}"
            
            if cache_key in self.analytics_cache:
                self.audit_logger.log_action(
                    action_type='cache_hit',
                    agent='autonomous',
                    details={'tool': tool_name, 'params': params},
                    session_id=self.session_id
                )
                return self.analytics_cache[cache_key]
            
            tool_method = getattr(self.analytics, tool_name, None)
            if tool_method is None:
                raise ValueError(f"Tool {tool_name} not found")
            
            result = tool_method(**params)
            self.analytics_cache[cache_key] = result
            
            self.audit_logger.log_action(
                action_type='cache_miss',
                agent='autonomous',
                details={'tool': tool_name, 'params': params},
                session_id=self.session_id
            )
            
            return result
            
        except Exception as e:
            self.healer.analyze_failure(e, {
                'tool': tool_name,
                'params': params,
                'cache_keys': list(self.analytics_cache.keys())
            })
            raise