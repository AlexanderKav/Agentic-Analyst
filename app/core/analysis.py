# app/core/analysis.py
import time
import pandas as pd
from typing import Dict, Any, Tuple, Optional

from connectors.data_loader import DataLoader
from agents.schema_mapper import SchemaMapper
from agents.autonomous_analyst import AutonomousAnalyst
from agents.analytics_agent import AnalyticsAgent
from agents.insight_agent import InsightAgent
from agents.planner_agent import PlannerAgent
from agents.visualization_agent import VisualizationAgent

class AnalysisOrchestrator:
    """Orchestrates the entire analysis pipeline"""
    
    def __init__(self, data_loader: Optional[DataLoader] = None):
        self.data_loader = data_loader or DataLoader()
        self.planner = PlannerAgent()
        self.insight = InsightAgent()
        self.viz = VisualizationAgent()
    
    async def analyze(
        self,
        question: str,
        source_type: str,
        source_config: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], float]:
        """
        Run complete analysis pipeline
        """
        start_time = time.time()
        
        try:
            # Step 1: Load data
            print(f"📂 Loading data from {source_type}...")
            df = self._load_data(source_type, source_config)
            print(f"✅ Loaded {len(df)} rows")
            
            # Step 2: Clean and map schema
            print("🧹 Cleaning and mapping schema...")
            mapper = SchemaMapper(df)
            clean_df, mapping, warnings = mapper.map_schema()
            print(f"✅ Schema mapped. Shape: {clean_df.shape}")
            
            # Step 3: Initialize agents with cleaned data
            analytics = AnalyticsAgent(clean_df)
            
            # Step 4: Create autonomous analyst
            analyst = AutonomousAnalyst(
                planner=self.planner,
                analytics=analytics,
                insight_agent=self.insight,
                viz_agent=self.viz
            )
            
            # Step 5: Run analysis
            print(f"❓ Question: {question}")
            raw_plan, plan, results, raw_insights, insights = analyst.run(question)
            print(f"📋 Plan: {plan}")
            print(f"📊 Results keys: {list(results.keys()) if results else 'None'}")
            
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
                "execution_time": execution_time
            }, execution_time
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "execution_time": execution_time
            }, execution_time
    
    def _load_data(self, source_type: str, config: Dict[str, Any]) -> pd.DataFrame:
        """Load data based on source type"""
        if source_type == "database":
            return self.data_loader.load('database', config)
        elif source_type in ["csv", "excel"]:
            # For file uploads, config contains the file path
            file_path = config.get('path')
            if not file_path:
                raise ValueError("No file path provided")
            return self.data_loader.load('csv', file_path)
        elif source_type == "google_sheets":
            return self.data_loader.load('google_sheets', {
                'sheet_id': config.get('sheet_id'),
                'range': config.get('range', 'A1:Z1000')
            })
        else:
            raise ValueError(f"Unsupported source type: {source_type}")