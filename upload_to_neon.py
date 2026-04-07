# save as upload_to_neon.py
import psycopg2
import pandas as pd

# Your Neon connection string
CONN_STRING = "postgresql://neondb_owner:npg_DCdXg0ftab9m@ep-fancy-math-agb4pb6l-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Read CSV
df = pd.read_csv("C:/Users/alexk/Desktop/data.csv")

# Connect and upload
conn = psycopg2.connect(CONN_STRING)
cur = conn.cursor()

# Create table
cur.execute("DROP TABLE IF EXISTS sales_data")
cur.execute("""
    CREATE TABLE sales_data (
        date DATE,
        customer VARCHAR(100),
        product VARCHAR(100),
        region VARCHAR(50),
        revenue DECIMAL(10,2),
        cost DECIMAL(10,2),
        currency VARCHAR(3),
        quantity INTEGER,
        payment_status VARCHAR(20),
        notes TEXT
    )
""")

# Insert data
for _, row in df.iterrows():
    cur.execute("""
        INSERT INTO sales_data VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, tuple(row))

conn.commit()
print(f"✅ Uploaded {len(df)} rows")
cur.close()
conn.close()


    