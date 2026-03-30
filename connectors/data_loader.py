"""Unified data loader for all data sources."""

import os
import pandas as pd
from .csv_sheets import CSVConnector
from .google_sheets import GoogleSheetsConnector
from .database_connector import DatabaseConnector
from .excel_connector import ExcelConnector

class DataLoader:
    """Unified data loader for CSV, Excel, Google Sheets, and Databases"""
    
    def __init__(self):
        self.sources = {
            'csv': self._load_csv,
            'excel': self._load_excel,
            'google_sheets': self._load_sheets,
            'database': self._load_database
        }
    
    def load(self, source_type, source_config):
        """Load data from specified source"""
        if source_type not in self.sources:
            raise ValueError(f"Unknown source type: {source_type}. Use: csv, excel, google_sheets, or database")
        
        loader = self.sources[source_type]
        print(f"Loading data from {source_type}...")
        return loader(source_config)
    
    def _load_csv(self, config):
        """Load from CSV file"""
        if isinstance(config, str):
            # Simple string path
            connector = CSVConnector(config)
        else:
            # Dict with options
            path = config.get('path')
            if not path:
                raise ValueError("CSV config must include 'path'")
            delimiter = config.get('delimiter', ',')
            encoding = config.get('encoding', 'utf-8')
            connector = CSVConnector(path, delimiter=delimiter, encoding=encoding)
        return connector.fetch_data()
    
    def _load_excel(self, config):
        """Load from Excel file"""
        if isinstance(config, str):
            # Simple string path
            connector = ExcelConnector(config)
        else:
            # Dict with options
            path = config.get('path')
            if not path:
                raise ValueError("Excel config must include 'path'")
            sheet_name = config.get('sheet_name', 0)
            header = config.get('header', 0)
            connector = ExcelConnector(path, sheet_name=sheet_name, header=header)
        return connector.fetch_data()
        
    def _load_sheets(self, config):
        """Load from Google Sheets"""
        if isinstance(config, str):
            # Simple sheet ID
            connector = GoogleSheetsConnector(config)
        else:
            # Dict with options
            sheet_id = config.get('sheet_id')
            if not sheet_id:
                raise ValueError("Google Sheets config must include 'sheet_id'")
            sheet_range = config.get('range', 'A1:Z1000')
            connector = GoogleSheetsConnector(sheet_id, sheet_range)
        return connector.fetch_sheet()
    
    def _load_database(self, config):
        """Load from database"""
        # config can be connection string or dict with options
        if isinstance(config, str):
            connector = DatabaseConnector(config)
            raise ValueError("For database, please provide a dict with 'table' or 'query'")
        else:
            connection = config.get('connection_string')
            if not connection:
                raise ValueError("Database config must include 'connection_string'")
            
            query = config.get('query')
            table = config.get('table')
            
            connector = DatabaseConnector(connection)
            
            if query:
                return connector.fetch_query(query)
            elif table:
                return connector.fetch_table(table)
            else:
                raise ValueError("Database config must include either 'query' or 'table'")
    
    def load_from_env(self):
        """Load data based on environment variables"""
        source_type = os.getenv('DATA_SOURCE_TYPE', 'csv')
        
        if source_type == 'csv':
            path = os.getenv('CSV_PATH', 'data.csv')
            return self.load('csv', path)
        
        elif source_type == 'excel':
            path = os.getenv('EXCEL_PATH')
            if not path:
                raise ValueError("EXCEL_PATH environment variable not set")
            sheet_name = os.getenv('EXCEL_SHEET', 0)
            return self.load('excel', {'path': path, 'sheet_name': sheet_name})
        
        elif source_type == 'google_sheets':
            sheet_id = os.getenv('SHEET_ID')
            if not sheet_id:
                raise ValueError("SHEET_ID environment variable not set")
            return self.load('google_sheets', sheet_id)
        
        elif source_type == 'database':
            conn_string = os.getenv('DB_CONNECTION')
            db_query = os.getenv('DB_QUERY')
            db_table = os.getenv('DB_TABLE')
            
            if not conn_string:
                raise ValueError("DB_CONNECTION environment variable not set")
            
            config = {'connection_string': conn_string}
            if db_query:
                config['query'] = db_query
            elif db_table:
                config['table'] = db_table
            else:
                raise ValueError("Either DB_QUERY or DB_TABLE must be set")
            
            return self.load('database', config)
        
        else:
            raise ValueError(f"Unknown DATA_SOURCE_TYPE: {source_type}")


# Convenience functions for common use cases
def load_csv(path, delimiter=',', encoding='utf-8'):
    """Quick load CSV"""
    return DataLoader().load('csv', {'path': path, 'delimiter': delimiter, 'encoding': encoding})

def load_excel(path, sheet_name=0):
    """Quick load Excel"""
    return DataLoader().load('excel', {'path': path, 'sheet_name': sheet_name})

def load_database(conn_string, table=None, query=None):
    """Quick load database"""
    config = {'connection_string': conn_string}
    if table:
        config['table'] = table
    elif query:
        config['query'] = query
    return DataLoader().load('database', config)

def load_sheets(sheet_id, sheet_range='A1:Z1000'):
    """Quick load Google Sheets"""
    return DataLoader().load('google_sheets', {'sheet_id': sheet_id, 'range': sheet_range})