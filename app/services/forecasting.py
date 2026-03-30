"""Demand forecasting and stock coverage calculations."""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from app.config import settings


def forecast_by_product(feature_df: pd.DataFrame, inventory_df: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame:
    latest_inventory = inventory_df.sort_values("date").groupby("product_id", as_index=False).tail(1)
    merged = feature_df.merge(latest_inventory[["product_id", "inventory_on_hand", "incoming_orders"]], on="product_id", how="left")
    merged = merged.merge(products_df[["product_id", "reorder_threshold", "supplier_lead_time_days"]], on="product_id", how="left")
    merged = merged.fillna({"inventory_on_hand": 0, "incoming_orders": 0, "reorder_threshold": 0, "supplier_lead_time_days": 7})

    for horizon in settings.forecast_horizons:
        merged[f"forecast_{horizon}d"] = np.maximum(0, merged["avg_daily_demand"] * horizon * (0.8 + merged["adjusted_demand_score"]))

    merged["days_of_cover"] = (merged["inventory_on_hand"] + merged["incoming_orders"]) / merged["avg_daily_demand"].replace(0, 0.1)
    merged["predicted_stockout_date"] = merged["days_of_cover"].apply(lambda d: (date.today() + timedelta(days=int(max(d, 0)))).isoformat())
    merged["overstock_flag"] = merged["days_of_cover"] > 60
    merged["reorder_urgency"] = merged.apply(_urgency, axis=1)
    return merged


def _urgency(row: pd.Series) -> str:
    lead = max(row.get("supplier_lead_time_days", 7), 1)
    if row["days_of_cover"] <= lead:
        return "urgent"
    if row["days_of_cover"] <= lead + 5:
        return "high"
    if row["days_of_cover"] <= 30:
        return "medium"
    return "low"
