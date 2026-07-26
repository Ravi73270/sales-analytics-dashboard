"""
Region-wise revenue breakdown -- donut chart.
"""
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR = Path(__file__).resolve().parent.parent / "notebooks"

orders = pd.read_csv(f"{DATA_DIR}/orders.csv")
customers = pd.read_csv(f"{DATA_DIR}/customers.csv")
merged = orders.merge(customers, on="customer_id")

region_revenue = merged.groupby("region")["sales"].sum().sort_values(ascending=False)

print("Revenue by region:")
print(region_revenue)

colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2"]

fig, ax = plt.subplots(figsize=(7, 7))
wedges, texts, autotexts = ax.pie(
    region_revenue.values,
    labels=region_revenue.index,
    autopct="%1.1f%%",
    startangle=90,
    colors=colors,
    wedgeprops=dict(width=0.4)  # donut style
)
ax.set_title("Revenue Share by Region", fontsize=14)
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/region_revenue.png", dpi=120)
plt.close()

print(f"\nSaved chart to {OUT_DIR}/region_revenue.png")
