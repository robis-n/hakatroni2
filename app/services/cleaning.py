"""Data cleaning and transformation pipeline."""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def clean_dataframes(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    cleaned: Dict[str, pd.DataFrame] = {}

    for name, df in data.items():
        frame = df.copy()
        frame = frame.drop_duplicates()

        if "date" in frame.columns:
            frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.date
            frame = frame.dropna(subset=["date"])

        if name == "sales":
            for col in ["quantity_sold", "revenue"]:
                if col not in frame.columns:
                    frame[col] = 0
                frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0)
            frame = frame.groupby(["product_id", "date"], as_index=False).agg({"quantity_sold": "sum", "revenue": "sum"})
            frame = frame.sort_values(["product_id", "date"])
            frame["rolling_7d_qty"] = frame.groupby("product_id")["quantity_sold"].transform(lambda s: s.rolling(7, min_periods=1).mean())
            frame["rolling_30d_qty"] = frame.groupby("product_id")["quantity_sold"].transform(lambda s: s.rolling(30, min_periods=1).mean())
            frame["dow"] = pd.to_datetime(frame["date"]).dt.dayofweek
            frame["month"] = pd.to_datetime(frame["date"]).dt.month

        if name == "inventory":
            for col in ["inventory_on_hand", "incoming_orders"]:
                frame[col] = pd.to_numeric(frame.get(col, 0), errors="coerce").fillna(0)

        if name == "trends":
            for col in ["market_trend_score", "competitor_signal", "social_trend_score", "seasonality_factor"]:
                frame[col] = pd.to_numeric(frame.get(col, 0.5), errors="coerce").fillna(0.5)

        if name == "products":
            frame["reorder_threshold"] = pd.to_numeric(frame.get("reorder_threshold", 0), errors="coerce").fillna(0)
            frame["supplier_lead_time_days"] = pd.to_numeric(frame.get("supplier_lead_time_days", 7), errors="coerce").fillna(7).astype(int)

        cleaned[name] = frame

    return cleaned


def average_daily_demand(sales: pd.DataFrame) -> pd.DataFrame:
    demand = sales.groupby("product_id", as_index=False).agg(avg_daily_demand=("quantity_sold", "mean"), demand_std=("quantity_sold", "std"))
    demand["demand_std"] = demand["demand_std"].fillna(0)
    demand["historical_demand_score"] = np.clip((demand["avg_daily_demand"] / demand["avg_daily_demand"].max()), 0, 1)
    return demand
