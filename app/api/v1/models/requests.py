from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from enum import Enum
import re
import os

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
        json_schema_extra = {
            "example": {
                "question": "What were our top products by revenue?",
                "data_source": "database",
                "source_config": {
                    "connection_string": "postgresql://user:pass@localhost:5432/db",
                    "table": "sales"
                }
            }
        }

class DatabaseConnectionRequest(BaseModel):
    """Request model for database connection with analysis"""
    question: str = Field(..., description="The question to analyze")
    connection_config: Dict[str, Any] = Field(..., description="Database connection configuration")

class DatabaseTestRequest(BaseModel):
    """Request model for testing database connection"""
    db_type: str
    host: Optional[str] = "localhost"  # Default to localhost
    port: Optional[str] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    table: Optional[str] = None
    query: Optional[str] = None
    use_query: Optional[bool] = False
    
    @validator('db_type')
    def validate_db_type(cls, v):
        allowed = ['postgresql', 'mysql', 'sqlite']
        if v not in allowed:
            raise ValueError(f"Database type must be one of: {allowed}")
        return v
    
    @validator('host')
    def validate_host(cls, v):
        if v:
            # Allow localhost, IP addresses, and hostnames
            if not re.match(r'^[a-zA-Z0-9\.\-_]+$', v):
                raise ValueError("Invalid host format. Use only letters, numbers, dots, hyphens, and underscores.")
        return v
    
    @validator('port')
    def validate_port(cls, v):
        if v:
            try:
                port_num = int(v)
                if port_num < 1024 or port_num > 65535:
                    raise ValueError("Port must be between 1024 and 65535")
            except ValueError:
                raise ValueError("Invalid port number")
        return v
    
    @validator('database')
    def validate_database(cls, v, values):
        """Validate database name/path based on db_type"""
        db_type = values.get('db_type')
        
        if v is None:
            raise ValueError("Database name is required")
            
        if db_type == 'sqlite':
            # SQLite accepts full file paths
            v = v.strip('"\'')
            
            if not re.match(r'^[a-zA-Z0-9_\ \-\.\\/:]+$', v):
                raise ValueError("Invalid database file path. Use only letters, numbers, spaces, and path characters.")
        else:
            # PostgreSQL/MySQL database names
            if not re.match(r'^[a-zA-Z0-9_\-]+$', v):
                raise ValueError("Database name contains invalid characters. Use only letters, numbers, underscores, and hyphens.")
        
        return v
    
    @validator('table')
    def validate_table(cls, v):
        if v:
            v = v.strip()
            if not re.match(r'^[a-zA-Z0-9_]+$', v):
                raise ValueError("Invalid table name. Use only letters, numbers, and underscores")
        return v

class GoogleSheetsRequest(BaseModel):
    """Request model for Google Sheets analysis"""
    question: str
    sheet_config: dict

class GoogleSheetsTestRequest(BaseModel):
    """Request model for testing Google Sheets connection"""
    sheet_id: str
    sheet_range: Optional[str] = "A1:Z1000"