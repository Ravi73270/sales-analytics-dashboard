"""
Customer Segmentation via RFM (Recency, Frequency, Monetary) + K-Means.

Convert this into a Jupyter notebook (jupytext or just copy cell-by-cell)
once you're happy with it -- keeping it as a .py while building makes it
easier to iterate and diff in git.
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

from pathlib import Path
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR = Path(__file__).resolve().parent.parent / "notebooks"

orders = pd.read_csv(f"{DATA_DIR}/orders.csv", parse_dates=["order_date"])
customers = pd.read_csv(f"{DATA_DIR}/customers.csv")

# ---------- RFM ----------
snapshot_date = orders["order_date"].max() + pd.Timedelta(days=1)

rfm = orders.groupby("customer_id").agg(
    recency=("order_date", lambda x: (snapshot_date - x.max()).days),
    frequency=("order_id", "nunique"),
    monetary=("sales", "sum"),
).reset_index()

# ---------- Scale + K-Means ----------
features = rfm[["recency", "frequency", "monetary"]]
scaled = StandardScaler().fit_transform(features)

# Elbow method to justify k (saved as a chart, not just picked blindly)
inertias = []
k_range = range(2, 9)
for k in k_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(scaled)
    inertias.append(km.inertia_)

plt.figure(figsize=(7, 4))
plt.plot(list(k_range), inertias, marker="o")
plt.xlabel("k (number of clusters)")
plt.ylabel("Inertia")
plt.title("Elbow Method for Optimal k")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/elbow_plot.png", dpi=120)
plt.close()

K = 4  # chosen from elbow plot -- adjust after you look at elbow_plot.png
kmeans = KMeans(n_clusters=K, random_state=42, n_init=10)
rfm["cluster"] = kmeans.fit_predict(scaled)

# ---------- Label clusters by their RFM profile ----------
cluster_profile = rfm.groupby("cluster")[["recency", "frequency", "monetary"]].mean()

# Label by RFM profile rather than monetary rank alone: high recency (days
# since last order) means "gone stale" regardless of how much they used to
# spend, so that cluster becomes "At Risk" first; the rest are ranked by
# monetary value.
recency_threshold = cluster_profile["recency"].mean() + cluster_profile["recency"].std()
labels = {}
at_risk_clusters = cluster_profile[cluster_profile["recency"] > recency_threshold].index.tolist()
remaining = cluster_profile.drop(index=at_risk_clusters).sort_values("monetary", ascending=False)
remaining_names = ["Champions", "Loyal Customers", "Occasional / Low-Value"]
for i, c in enumerate(remaining.index.tolist()):
    labels[c] = remaining_names[i] if i < len(remaining_names) else f"Segment {c}"
for c in at_risk_clusters:
    labels[c] = "At Risk"

rfm["segment"] = rfm["cluster"].map(labels)

print("Cluster profile (avg recency/frequency/monetary):")
print(cluster_profile)
print("\nSegment sizes:")
print(rfm["segment"].value_counts())

# ---------- Visualize ----------
plt.figure(figsize=(8, 6))
for seg in rfm["segment"].unique():
    subset = rfm[rfm["segment"] == seg]
    plt.scatter(subset["frequency"], subset["monetary"], label=seg, alpha=0.6)
plt.xlabel("Frequency (# orders)")
plt.ylabel("Monetary (total spend)")
plt.title("Customer Segments (RFM + K-Means)")
plt.legend()
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/customer_segments.png", dpi=120)
plt.close()

# ---------- Save output for Power BI / Excel ----------
rfm_out = rfm.merge(customers[["customer_id", "customer_name", "region", "segment" if False else "segment"]].rename(columns={"segment": "customer_type"}), on="customer_id", how="left")
rfm_out.to_csv(f"{DATA_DIR}/customer_segments.csv", index=False)
print(f"\nSaved segment assignments to {DATA_DIR}/customer_segments.csv")
print(f"Saved charts to {OUT_DIR}/elbow_plot.png and {OUT_DIR}/customer_segments.png")
