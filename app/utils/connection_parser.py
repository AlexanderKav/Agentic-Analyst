# app/utils/connection_parser.py
import re
from urllib.parse import urlparse

def parse_connection_string(connection_string):
    """Parse various database connection string formats"""
    
    # PostgreSQL format: postgresql://user:pass@host:port/db
    if connection_string.startswith('postgresql://'):
        parsed = urlparse(connection_string)
        return {
            'type': 'postgresql',
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/'),
            'username': parsed.username,
            'password': parsed.password,
            'ssl': parsed.query == 'sslmode=require'
        }
    
    # MySQL format: mysql://user:pass@host:port/db
    elif connection_string.startswith('mysql://'):
        parsed = urlparse(connection_string)
        return {
            'type': 'mysql',
            'host': parsed.hostname,
            'port': parsed.port or 3306,
            'database': parsed.path.lstrip('/'),
            'username': parsed.username,
            'password': parsed.password
        }
    
    # Environment variable format
    elif 'DB_HOST' in connection_string:
        # Parse key=value pairs
        pairs = dict(re.findall(r'(\w+)=([^;\n]+)', connection_string))
        return {
            'type': pairs.get('DB_TYPE', 'postgresql'),
            'host': pairs.get('DB_HOST'),
            'port': int(pairs.get('DB_PORT', 5432)),
            'database': pairs.get('DB_NAME'),
            'username': pairs.get('DB_USER'),
            'password': pairs.get('DB_PASSWORD')
        }
    
    raise ValueError(f"Unsupported connection string format: {connection_string}")