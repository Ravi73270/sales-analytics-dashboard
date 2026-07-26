"""
Product Performance: Pareto (80/20) + ABC classification.
Answers: which products/categories actually drive revenue, and which are
dead weight worth discontinuing or repricing.
"""
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR = Path(__file__).resolve().parent.parent / "notebooks"

orders = pd.read_csv(f"{DATA_DIR}/orders.csv")
products = pd.read_csv(f"{DATA_DIR}/products.csv")

merged = orders.merge(products, on="product_id")

# ---------- Revenue by product ----------
prod_revenue = merged.groupby(["product_id", "product_name", "category"]).agg(
    revenue=("sales", "sum"),
    profit=("profit", "sum"),
).reset_index().sort_values("revenue", ascending=False)

prod_revenue["cum_revenue"] = prod_revenue["revenue"].cumsum()
prod_revenue["cum_pct"] = prod_revenue["cum_revenue"] / prod_revenue["revenue"].sum() * 100

# ABC classification: A = top 80% of cumulative revenue, B = next 15%, C = rest
def classify(pct):
    if pct <= 80:
        return "A"
    elif pct <= 95:
        return "B"
    return "C"

prod_revenue["abc_class"] = prod_revenue["cum_pct"].apply(classify)

class_summary = prod_revenue.groupby("abc_class").agg(
    n_products=("product_id", "count"),
    total_revenue=("revenue", "sum"),
).reset_index()
class_summary["pct_of_products"] = round(class_summary["n_products"] / len(prod_revenue) * 100, 1)
class_summary["pct_of_revenue"] = round(class_summary["total_revenue"] / prod_revenue["revenue"].sum() * 100, 1)

print("ABC Classification Summary:")
print(class_summary)
print(f"\n{class_summary.loc[class_summary.abc_class=='A','pct_of_products'].values[0]}% of products "
      f"(Class A) drive {class_summary.loc[class_summary.abc_class=='A','pct_of_revenue'].values[0]}% of revenue")

# ---------- Pareto chart ----------
fig, ax1 = plt.subplots(figsize=(10, 5))
top_n = 40
subset = prod_revenue.head(top_n)
ax1.bar(range(len(subset)), subset["revenue"], color="steelblue")
ax1.set_xlabel(f"Products (top {top_n}, ranked by revenue)")
ax1.set_ylabel("Revenue", color="steelblue")
ax2 = ax1.twinx()
ax2.plot(range(len(subset)), subset["cum_pct"], color="darkorange", marker="o", markersize=3)
ax2.axhline(80, color="red", linestyle="--", linewidth=1)
ax2.set_ylabel("Cumulative % of Revenue", color="darkorange")
plt.title("Pareto Analysis: Product Revenue Contribution")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/pareto_chart.png", dpi=120)
plt.close()

# ---------- Category-level rollup ----------
cat_summary = merged.groupby("category").agg(
    revenue=("sales", "sum"),
    profit=("profit", "sum"),
).reset_index().sort_values("revenue", ascending=False)
cat_summary["margin_pct"] = round(cat_summary["profit"] / cat_summary["revenue"] * 100, 2)
print("\nCategory summary:")
print(cat_summary)

prod_revenue.to_csv(f"{DATA_DIR}/product_abc_analysis.csv", index=False)
print(f"\nSaved full product-level ABC analysis to {DATA_DIR}/product_abc_analysis.csv")
print(f"Saved Pareto chart to {OUT_DIR}/pareto_chart.png")
