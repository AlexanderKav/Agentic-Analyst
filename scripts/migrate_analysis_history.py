# scripts/migrate_analysis_history.py
"""Migrate old JSON data to new structured format"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.api.v1.models.user import User 
from app.api.v1.models.analysis import AnalysisHistory
from app.core.metrics_extractor import MetricsExtractor
from app.core.insights_extractor import InsightsExtractor

def migrate_existing_analyses():
    """Migrate all existing analyses to new structure"""
    db = SessionLocal()
    
    try:
        # Get all analyses that haven't been migrated yet
        analyses = db.query(AnalysisHistory).all()
        
        print(f"Found {len(analyses)} analyses to migrate")
        
        for analysis in analyses:
            # Move old results to raw_results
            analysis.raw_results = analysis.results
            
            # Extract and store metrics
            results = analysis.raw_results.get('results', {})
            metrics_extractor = MetricsExtractor()
            metrics = metrics_extractor.extract(results)
            
            for metric in metrics:
                from app.api.v1.models.analysis import AnalysisMetric
                db_metric = AnalysisMetric(
                    analysis_id=analysis.id,
                    metric_type=metric['metric_type'],
                    metric_value=metric['metric_value'],
                    metric_date=metric.get('metric_date'),
                    category=metric.get('category'),
                    category_name=metric.get('category_name')
                )
                db.add(db_metric)
            
            # Extract and store insights
            insights_data = analysis.raw_results.get('insights', {})
            if isinstance(insights_data, dict):
                insights_extractor = InsightsExtractor()
                insights = insights_extractor.extract(insights_data)
                
                for insight in insights:
                    from app.api.v1.models.analysis import AnalysisInsight
                    db_insight = AnalysisInsight(
                        analysis_id=analysis.id,
                        insight_text=insight['text'],
                        insight_type=insight['type'],
                        confidence_score=insight.get('confidence_score')
                    )
                    db.add(db_insight)
            
            # Clear old results to save space (optional)
            # analysis.results = None
            
            db.commit()
            print(f"Migrated analysis {analysis.id}")
        
        print("Migration complete!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_existing_analyses()