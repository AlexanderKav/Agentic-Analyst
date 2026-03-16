# app/core/data_source.py
import pandas as pd
import tempfile
import os
from typing import BinaryIO

class DataSourceHandler:
    """Handles file uploads and temporary storage"""
    
    @staticmethod
    async def save_upload_file(upload_file) -> str:
        """Save uploaded file temporarily and return path"""
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(upload_file.filename)[1]) as tmp_file:
            content = await upload_file.read()
            tmp_file.write(content)
            return tmp_file.name
    
    @staticmethod
    def read_uploaded_file(file_path: str, file_type: str) -> pd.DataFrame:
        """Read uploaded file into DataFrame"""
        if file_type == 'csv':
            return pd.read_csv(file_path)
        elif file_type in ['xlsx', 'xls']:
            return pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")