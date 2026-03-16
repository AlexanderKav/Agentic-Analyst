from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
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

class DatabaseConnectionRequest(BaseModel):
    """Request model for database connection"""
    question: str = Field(..., description="The question to analyze")
    connection_config: Dict[str, Any] = Field(..., description="Database connection configuration")

class DatabaseTestRequest(BaseModel):
    """Request model for testing database connection"""
    db_type: str
    host: Optional[str] = None
    port: Optional[str] = None
    database: str
    username: Optional[str] = None
    password: Optional[str] = None