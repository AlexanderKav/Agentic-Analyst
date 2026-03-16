from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class DataSourceType(str, Enum):
    CSV = "csv"
    EXCEL = "excel"
    DATABASE = "database"
    GOOGLE_SHEETS = "google_sheets"

class AnalysisRequest(BaseModel):
    """Request model for analysis endpoint"""
    question: str = Field(..., description="The question to analyze")
    data_source: DataSourceType = Field(..., description="Type of data source")
    source_config: Dict[str, Any] = Field(..., description="Configuration for the data source")
    
    class Config:
        json_schema_extra = {  # Changed from schema_extra to json_schema_extra
            "example": {
                "question": "What were our top products by revenue?",
                "data_source": "database",
                "source_config": {
                    "connection_string": "postgresql://user:pass@localhost:5432/db",
                    "table": "sales"
                }
            }
        }

class DatabaseConfig(BaseModel):
    """Database connection configuration"""
    connection_string: str
    table: Optional[str] = None
    query: Optional[str] = None