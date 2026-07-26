"""
Loads the generated CSVs into a local SQLite file: data/sales.db
This is just so you can test-run every SQL query in sql/ without needing
Postgres installed right now. The DDL in sql/01_schema.sql is written for
Postgres — when you're ready, run that file against your own Postgres
instance with psql, then \\copy the three CSVs in. Every query in
sql/02_kpi_queries.sql runs unchanged on both engines (no Postgres-only
syntax was used).
"""
import sqlite3
import pandas as pd

from pathlib import Path
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "sales.db"

conn = sqlite3.connect(DB_PATH)

customers = pd.read_csv(f"{DATA_DIR}/customers.csv")
products = pd.read_csv(f"{DATA_DIR}/products.csv")
orders = pd.read_csv(f"{DATA_DIR}/orders.csv", parse_dates=["order_date", "ship_date"])

customers.to_sql("dim_customer", conn, if_exists="replace", index=False)
products.to_sql("dim_product", conn, if_exists="replace", index=False)
orders.to_sql("fact_sales", conn, if_exists="replace", index=False)

conn.execute("CREATE INDEX IF NOT EXISTS idx_fact_sales_date ON fact_sales(order_date)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_fact_sales_customer ON fact_sales(customer_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_fact_sales_product ON fact_sales(product_id)")
conn.commit()
conn.close()

print(f"Loaded into {DB_PATH}")
print(f"  dim_customer: {len(customers)} rows")
print(f"  dim_product:  {len(products)} rows")
print(f"  fact_sales:   {len(orders)} rows")
