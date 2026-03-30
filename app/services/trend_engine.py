"""Combines internal and external trend signals into trend-adjusted demand scores."""
from __future__ import annotations

import pandas as pd

from app.config import settings


def build_trend_features(demand_df: pd.DataFrame, trends_df: pd.DataFrame, persistence_df: pd.DataFrame) -> pd.DataFrame:
    latest_trends = trends_df.sort_values("date").groupby("product_id", as_index=False).tail(1)
    cols = ["product_id", "market_trend_score", "competitor_signal", "social_trend_score", "seasonality_factor"]
    merged = demand_df.merge(latest_trends[cols], on="product_id", how="left")
    merged = merged.merge(
        persistence_df[["product_id", "trend_persistence_score", "trend_impact_multiplier"]],
        on="product_id",
        how="left",
    )

    merged = merged.fillna(
        {
            "market_trend_score": 0.5,
            "competitor_signal": 0.5,
            "social_trend_score": 0.5,
            "seasonality_factor": 0.5,
            "trend_persistence_score": 0.5,
            "trend_impact_multiplier": 1.0,
        }
    )

    weights = settings.trend_weights
    merged["adjusted_demand_score"] = (
        weights["historical_demand_score"] * merged["historical_demand_score"]
        + weights["market_trend_score"] * merged["market_trend_score"]
        + weights["competitor_trend_score"] * merged["competitor_signal"]
        + weights["social_trend_score"] * merged["social_trend_score"]
        + weights["seasonality_score"] * merged["seasonality_factor"]
        + weights["trend_persistence_score"] * merged["trend_persistence_score"]
    ) * merged["trend_impact_multiplier"]
    return merged
