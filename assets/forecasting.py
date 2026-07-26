"""
Revenue Forecasting.
Two models on purpose: a naive baseline (moving average) so you can always
explain "how much better is my real model than doing nothing", then ARIMA
for the actual forecast. In interviews, showing the baseline comparison
matters more than the fancier model alone.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA

from pathlib import Path
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR = Path(__file__).resolve().parent.parent / "notebooks"

orders = pd.read_csv(f"{DATA_DIR}/orders.csv", parse_dates=["order_date"])

monthly = orders.set_index("order_date").resample("MS")["sales"].sum()
monthly.index.name = "month"

# ---------- Train/test split (last 3 months held out) ----------
HOLDOUT = 3
train, test = monthly.iloc[:-HOLDOUT], monthly.iloc[-HOLDOUT:]

# ---------- Baseline: 3-month moving average ----------
baseline_forecast = pd.Series([train.iloc[-3:].mean()] * HOLDOUT, index=test.index)

# ---------- ARIMA ----------
model = ARIMA(train, order=(1, 1, 1), seasonal_order=(1, 1, 0, 12))
fit = model.fit()
arima_forecast = fit.get_forecast(steps=HOLDOUT)
arima_mean = arima_forecast.predicted_mean
arima_ci = arima_forecast.conf_int(alpha=0.2)  # 80% CI

# ---------- Evaluate ----------
def mape(actual, predicted):
    return np.mean(np.abs((actual - predicted) / actual)) * 100

print("Holdout evaluation (last 3 months):")
print(f"  Baseline (3-mo moving avg) MAPE: {mape(test, baseline_forecast):.2f}%")
print(f"  ARIMA MAPE:                      {mape(test, arima_mean):.2f}%")

# ---------- Refit on full data, forecast next 3 months forward ----------
full_model = ARIMA(monthly, order=(1, 1, 1), seasonal_order=(1, 1, 0, 12))
full_fit = full_model.fit()
future_forecast = full_fit.get_forecast(steps=3)
future_mean = future_forecast.predicted_mean
future_ci = future_forecast.conf_int(alpha=0.2)

print("\nNext 3 months forecast:")
forecast_table = pd.DataFrame({
    "forecast": future_mean,
    "lower_80": future_ci.iloc[:, 0],
    "upper_80": future_ci.iloc[:, 1],
})
print(forecast_table.round(2))

# ---------- Plot ----------
plt.figure(figsize=(11, 5))
plt.plot(monthly.index, monthly.values, label="Actual", color="steelblue")
plt.plot(future_mean.index, future_mean.values, label="Forecast", color="darkorange", marker="o")
plt.fill_between(future_ci.index, future_ci.iloc[:, 0], future_ci.iloc[:, 1],
                  color="darkorange", alpha=0.2, label="80% CI")
plt.title("Monthly Revenue: Actual + 3-Month Forecast")
plt.xlabel("Month")
plt.ylabel("Revenue")
plt.legend()
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/revenue_forecast.png", dpi=120)
plt.close()

forecast_table.to_csv(f"{DATA_DIR}/revenue_forecast.csv")
print(f"\nSaved chart to {OUT_DIR}/revenue_forecast.png")
print(f"Saved forecast table to {DATA_DIR}/revenue_forecast.csv")
