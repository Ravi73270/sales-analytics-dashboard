"""
Generates a realistic Superstore-style synthetic sales dataset.
Why synthetic instead of downloading Kaggle's Superstore/Olist datasets?
This sandbox can't reach Kaggle, and generating it ourselves means you
fully understand the schema (useful when you explain it in interviews).
The structure mirrors real retail data closely enough that every SQL/Python
technique you learn here transfers directly to the real Superstore/Olist CSVs
if you want to swap datasets later.

Output: data/customers.csv, data/products.csv, data/orders.csv
"""
import numpy as np
import pandas as pd
from faker import Faker
from datetime import date, timedelta

np.random.seed(42)
fake = Faker()
Faker.seed(42)

# ---------- Dimensions ----------
REGIONS = ["North", "South", "East", "West", "Central"]
STATES_BY_REGION = {
    "North": ["Delhi", "Punjab", "Haryana", "Uttarakhand"],
    "South": ["Karnataka", "Tamil Nadu", "Kerala", "Andhra Pradesh"],
    "East": ["West Bengal", "Odisha", "Bihar", "Jharkhand"],
    "West": ["Maharashtra", "Gujarat", "Rajasthan", "Goa"],
    "Central": ["Madhya Pradesh", "Chhattisgarh", "Uttar Pradesh"],
}
SEGMENTS = ["Consumer", "Corporate", "Home Office"]

CATEGORIES = {
    "Furniture": ["Chairs", "Tables", "Bookcases", "Furnishings"],
    "Office Supplies": ["Storage", "Binders", "Paper", "Art", "Labels"],
    "Technology": ["Phones", "Accessories", "Machines", "Copiers"],
}

N_CUSTOMERS = 600
N_PRODUCTS = 220
N_ORDERS = 9000  # order line items

# ---------- Customers ----------
customers = []
for i in range(1, N_CUSTOMERS + 1):
    region = np.random.choice(REGIONS)
    customers.append({
        "customer_id": f"CUST-{i:05d}",
        "customer_name": fake.name(),
        "segment": np.random.choice(SEGMENTS, p=[0.55, 0.30, 0.15]),
        "region": region,
        "state": np.random.choice(STATES_BY_REGION[region]),
        "signup_date": fake.date_between(start_date="-3y", end_date="-1y"),
    })
customers_df = pd.DataFrame(customers)

# ---------- Products ----------
products = []
for i in range(1, N_PRODUCTS + 1):
    category = np.random.choice(list(CATEGORIES.keys()), p=[0.2, 0.55, 0.25])
    sub_category = np.random.choice(CATEGORIES[category])
    base_cost = round(np.random.uniform(8, 400), 2)
    margin_factor = np.random.uniform(1.15, 1.9)  # markup over cost
    products.append({
        "product_id": f"PROD-{i:05d}",
        "product_name": f"{sub_category[:-1] if sub_category.endswith('s') else sub_category} {fake.word().capitalize()} {i}",
        "category": category,
        "sub_category": sub_category,
        "unit_cost": base_cost,
        "unit_price": round(base_cost * margin_factor, 2),
    })
products_df = pd.DataFrame(products)

# ---------- Orders (fact table, line-item grain) ----------
start_date = date(2024, 1, 1)
end_date = date(2025, 12, 31)
date_range_days = (end_date - start_date).days

# seasonality: bump Nov-Dec (festive/holiday), dip in Jun-Jul
def seasonal_weight(d):
    month = d.month
    if month in (11, 12):
        return 1.6
    if month in (6, 7):
        return 0.7
    return 1.0

order_rows = []
order_counter = 1
customer_ids = customers_df["customer_id"].tolist()
product_ids = products_df["product_id"].tolist()
product_lookup = products_df.set_index("product_id")

# distribute N_ORDERS across days weighted by seasonality
days = [start_date + timedelta(days=x) for x in range(date_range_days + 1)]
weights = np.array([seasonal_weight(d) for d in days], dtype=float)
weights /= weights.sum()
chosen_days = np.random.choice(len(days), size=N_ORDERS, p=weights)

for idx in chosen_days:
    order_date = days[idx]
    cust_id = np.random.choice(customer_ids)
    prod_id = np.random.choice(product_ids)
    prod = product_lookup.loc[prod_id]
    quantity = np.random.randint(1, 8)
    discount = np.random.choice([0, 0.05, 0.1, 0.15, 0.2, 0.3], p=[0.35, 0.2, 0.2, 0.12, 0.08, 0.05])
    unit_price = prod["unit_price"]
    unit_cost = prod["unit_cost"]
    sales = round(unit_price * quantity * (1 - discount), 2)
    cost = round(unit_cost * quantity, 2)
    profit = round(sales - cost, 2)
    ship_days = np.random.randint(1, 7)

    order_rows.append({
        "order_id": f"ORD-{order_counter:06d}",
        "order_date": order_date,
        "ship_date": order_date + timedelta(days=int(ship_days)),
        "customer_id": cust_id,
        "product_id": prod_id,
        "quantity": quantity,
        "discount": discount,
        "sales": sales,
        "cost": cost,
        "profit": profit,
    })
    order_counter += 1

orders_df = pd.DataFrame(order_rows)

# ---------- Save ----------
from pathlib import Path
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

customers_df.to_csv(DATA_DIR / "customers.csv", index=False)
products_df.to_csv(DATA_DIR / "products.csv", index=False)
orders_df.to_csv(DATA_DIR / "orders.csv", index=False)

print(f"customers: {len(customers_df)} rows")
print(f"products:  {len(products_df)} rows")
print(f"orders:    {len(orders_df)} rows")
print(f"date range: {orders_df['order_date'].min()} to {orders_df['order_date'].max()}")
print(f"total sales: {orders_df['sales'].sum():,.2f}")
print(f"total profit: {orders_df['profit'].sum():,.2f}")
