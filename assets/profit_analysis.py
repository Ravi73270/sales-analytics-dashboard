"""
Profit Analysis: where is money actually being made/lost, and does
discounting help or hurt.
"""
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR = Path(__file__).resolve().parent.parent / "notebooks"

orders = pd.read_csv(f"{DATA_DIR}/orders.csv")
products = pd.read_csv(f"{DATA_DIR}/products.csv")
merged = orders.merge(products, on="product_id")

# ---------- Discount vs. margin ----------
discount_summary = merged.groupby("discount").agg(
    n_line_items=("order_id", "count"),
    avg_profit=("profit", "mean"),
    total_revenue=("sales", "sum"),
    total_profit=("profit", "sum"),
).reset_index()
discount_summary["margin_pct"] = round(discount_summary["total_profit"] / discount_summary["total_revenue"] * 100, 2)
print("Discount vs Margin:")
print(discount_summary)

fig, ax1 = plt.subplots(figsize=(8, 5))
ax1.bar(discount_summary["discount"].astype(str), discount_summary["margin_pct"], color="seagreen")
ax1.set_xlabel("Discount Level")
ax1.set_ylabel("Profit Margin %")
ax1.set_title("Profit Margin by Discount Level")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/discount_vs_margin.png", dpi=120)
plt.close()

# ---------- Sub-category profit breakdown ----------
subcat = merged.groupby(["category", "sub_category"]).agg(
    revenue=("sales", "sum"),
    profit=("profit", "sum"),
).reset_index().sort_values("profit")
subcat["margin_pct"] = round(subcat["profit"] / subcat["revenue"] * 100, 2)

plt.figure(figsize=(9, 6))
colors = ["crimson" if p < 0 else "steelblue" for p in subcat["profit"]]
plt.barh(subcat["sub_category"], subcat["profit"], color=colors)
plt.xlabel("Total Profit")
plt.title("Profit by Sub-Category (red = loss-making)")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/subcategory_profit.png", dpi=120)
plt.close()

print("\nSub-category profit breakdown:")
print(subcat)

subcat.to_csv(f"{DATA_DIR}/subcategory_profit.csv", index=False)
print(f"\nSaved charts to {OUT_DIR}/discount_vs_margin.png and {OUT_DIR}/subcategory_profit.png")
