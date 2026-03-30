# scripts/test-db-connections.py
import psycopg2
import mysql.connector
import pandas as pd
from sqlalchemy import create_engine

def test_postgresql():
    print("\n" + "="*60)
    print("Testing PostgreSQL Connection")
    print("="*60)
    
    try:
        # Connection parameters - Updated port to 5433
        conn_params = {
            'host': 'localhost',
            'port': 5433,  # Changed from 5432
            'database': 'sales_db',
            'user': 'analyst_user',
            'password': 'analyst_pass123'
        }
        
        # Test connection
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Execute a query
        cursor.execute("SELECT COUNT(*) FROM sales")
        count = cursor.fetchone()[0]
        print(f"✅ Connected to PostgreSQL successfully!")
        print(f"📊 Total rows in sales table: {count}")
        
        # Get sample data
        df = pd.read_sql("SELECT * FROM sales LIMIT 5", conn)
        print("\n📋 Sample data:")
        print(df[['sale_date', 'customer', 'product', 'revenue']])
        
        # Check views
        cursor.execute("SELECT COUNT(*) FROM monthly_revenue")
        view_count = cursor.fetchone()[0]
        print(f"\n📈 Monthly revenue view has {view_count} rows")
        
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

def test_mysql():
    print("\n" + "="*60)
    print("Testing MySQL Connection")
    print("="*60)
    
    try:
        # Connection parameters - Updated port to 3307
        conn_params = {
            'host': 'localhost',
            'port': 3307,  # Changed from 3306
            'database': 'sales_db',
            'user': 'analyst_user',
            'password': 'analyst_pass123'
        }
        
        # Test connection
        conn = mysql.connector.connect(**conn_params)
        cursor = conn.cursor()
        
        # Execute a query
        cursor.execute("SELECT COUNT(*) FROM sales")
        count = cursor.fetchone()[0]
        print(f"✅ Connected to MySQL successfully!")
        print(f"📊 Total rows in sales table: {count}")
        
        # Get sample data
        engine = create_engine(f"mysql+pymysql://{conn_params['user']}:{conn_params['password']}@{conn_params['host']}:{conn_params['port']}/{conn_params['database']}")
        df = pd.read_sql("SELECT * FROM sales LIMIT 5", engine)
        print("\n📋 Sample data:")
        print(df[['sale_date', 'customer', 'product', 'revenue']])
        
        # Check views
        cursor.execute("SELECT COUNT(*) FROM monthly_revenue")
        view_count = cursor.fetchone()[0]
        print(f"\n📈 Monthly revenue view has {view_count} rows")
        
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        return False

if __name__ == "__main__":
    print("\n🚀 Testing Database Connections\n")
    print("📝 Using ports: PostgreSQL=5433, MySQL=3307\n")
    
    postgres_ok = test_postgresql()
    mysql_ok = test_mysql()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"PostgreSQL (port 5433): {'✅ PASSED' if postgres_ok else '❌ FAILED'}")
    print(f"MySQL (port 3307):      {'✅ PASSED' if mysql_ok else '❌ FAILED'}")