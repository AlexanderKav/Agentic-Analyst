# scripts/migrate_sqlite.py
import sqlite3
import os

def migrate_sqlite():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'agentic_analyst.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'reset_token' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN reset_token VARCHAR(255)")
        print("✅ Added reset_token column")
    else:
        print("⏭️ reset_token column already exists")
    
    if 'reset_token_expires' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN reset_token_expires TIMESTAMP")
        print("✅ Added reset_token_expires column")
    else:
        print("⏭️ reset_token_expires column already exists")
    
    conn.commit()
    conn.close()
    print("✅ Migration complete!")

if __name__ == "__main__":
    migrate_sqlite()