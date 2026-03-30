# app/api/v1/models/analysis.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Numeric, Date, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    analysis_type = Column(String)  # 'file', 'database', 'google_sheets'
    question = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Hybrid: Keep raw JSON for full context (backward compatible)
    raw_results = Column(JSON)  # Full analysis results (replaces old 'results' column)
    data_source = Column(JSON)  # Sanitized (no passwords)
    
    # Relationships to new structured tables
    metrics = relationship("AnalysisMetric", back_populates="analysis", cascade="all, delete-orphan")
    charts = relationship("AnalysisChart", back_populates="analysis", cascade="all, delete-orphan")
    insights = relationship("AnalysisInsight", back_populates="analysis", cascade="all, delete-orphan")
    
    # Relationship to User
    user = relationship("User", back_populates="analyses")
    
    # Helper methods
    def extract_and_store_metrics(self, results: dict):
        """Extract key metrics from analysis results and store them"""
        from app.core.metrics_extractor import MetricsExtractor
        extractor = MetricsExtractor()
        metrics = extractor.extract(results)
        
        for metric in metrics:
            db_metric = AnalysisMetric(
                analysis_id=self.id,
                metric_type=metric['metric_type'],
                metric_value=metric['metric_value'],
                metric_date=metric.get('metric_date'),
                category=metric.get('category'),
                category_name=metric.get('category_name')
            )
            self.metrics.append(db_metric)
    
    def extract_and_store_insights(self, insights_data: dict):
        """Extract insights from analysis results"""
        from app.core.insights_extractor import InsightsExtractor
        extractor = InsightsExtractor()
        insights = extractor.extract(insights_data)
        
        for insight in insights:
            db_insight = AnalysisInsight(
                analysis_id=self.id,
                insight_text=insight['text'],
                insight_type=insight['type'],
                confidence_score=insight.get('confidence_score')
            )
            self.insights.append(db_insight)
    
    def store_chart_reference(self, chart_type: str, chart_path: str, chart_data: dict = None):
        """Store chart reference"""
        chart = AnalysisChart(
            analysis_id=self.id,
            chart_type=chart_type,
            chart_path=chart_path,
            chart_data=chart_data
        )
        self.charts.append(chart)


class AnalysisMetric(Base):
    """Structured metrics table for queryable KPIs"""
    __tablename__ = "analysis_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_history.id"), nullable=False)
    metric_type = Column(String(50))  # 'total_revenue', 'profit_margin', 'avg_order_value', etc.
    metric_value = Column(Numeric(20, 2))  # For numeric metrics
    metric_date = Column(Date, nullable=True)  # For time-series metrics
    category = Column(String(100), nullable=True)  # 'product', 'region', 'customer'
    category_name = Column(String(255), nullable=True)  # Specific product/region/customer name
    
    # Relationships
    analysis = relationship("AnalysisHistory", back_populates="metrics")
    
    # Indexes for fast queries
    __table_args__ = (
        Index('idx_analysis_metrics_type_value', 'metric_type', 'metric_value'),
        Index('idx_analysis_metrics_category', 'category', 'category_name'),
        Index('idx_analysis_metrics_date', 'metric_date'),
    )


class AnalysisChart(Base):
    """Chart storage reference"""
    __tablename__ = "analysis_charts"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_history.id"), nullable=False)
    chart_type = Column(String(50))  # 'monthly_growth', 'revenue_by_product', etc.
    chart_path = Column(String(255))  # Path to saved chart image
    chart_data = Column(JSON, nullable=True)  # Optional: chart configuration data
    
    # Relationships
    analysis = relationship("AnalysisHistory", back_populates="charts")


class AnalysisInsight(Base):
    """Structured insights table"""
    __tablename__ = "analysis_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_history.id"), nullable=False)
    insight_text = Column(Text)  # The actual insight text
    insight_type = Column(String(50))  # 'answer', 'anomaly', 'recommendation', 'summary'
    confidence_score = Column(Numeric(5, 2), nullable=True)  # 0-1 confidence score
    
    # Relationships
    analysis = relationship("AnalysisHistory", back_populates="insights")
    
    __table_args__ = (
        Index('idx_analysis_insights_type', 'insight_type'),
    )