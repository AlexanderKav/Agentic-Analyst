"""CSV file connector for fetching data."""

import pandas as pd
import os

class CSVConnector:
    """Simple connector to load data from CSV files."""
    
    def __init__(self, file_path: str):
        """
        Initialize CSV connector.
        
        Args:
            file_path: Path to the CSV file
        """
        self.file_path = file_path
        
    def fetch_data(self) -> pd.DataFrame:
        """
        Fetch data from CSV file.
        
        Returns:
            pandas DataFrame containing the CSV data
            
        Raises:
            FileNotFoundError: If the CSV file doesn't exist
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"CSV file not found: {self.file_path}")
        
        return pd.read_csv(self.file_path)
    
    def test_connection(self) -> bool:
        """
        Test if file exists and is readable.
        
        Returns:
            True if file exists and is readable, False otherwise
        """
        return os.path.exists(self.file_path) and os.access(self.file_path, os.R_OK)