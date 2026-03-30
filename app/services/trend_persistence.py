"""Heuristic trend persistence and variability analysis for MVP."""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_trend_persistence(trends: pd.DataFrame) -> pd.DataFrame:
    records = []
    if trends.empty:
        return pd.DataFrame()

    trends = trends.sort_values(["product_id", "date"])
    for product_id, grp in trends.groupby("product_id"):
        recent = grp.tail(28).copy()
        if recent.empty:
            continue

        base_score = recent[["market_trend_score", "competitor_signal", "social_trend_score", "seasonality_factor"]].mean(axis=1)
        slope = np.polyfit(np.arange(len(base_score)), base_score.values, 1)[0] if len(base_score) > 2 else 0.0
        variability = float(base_score.std(ddof=0))
        strength = float(np.clip(base_score.tail(7).mean() - base_score.head(7).mean(), -1, 1))

        if slope > 0.01:
            direction = "rising"
        elif slope < -0.01:
            direction = "falling"
        else:
            direction = "stable"

        if variability > 0.22 and abs(strength) > 0.15:
            trend_type = "short-term spike" if direction == "rising" else "short-term declining signal"
            duration = 7
            confidence = 0.45
            impact = 1.05 if direction == "rising" else 0.95
        elif variability <= 0.15 and direction == "rising" and len(recent) >= 21:
            trend_type = "medium-term emerging trend"
            duration = 35
            confidence = 0.78
            impact = 1.18
        elif variability <= 0.12 and recent["seasonality_factor"].mean() > 0.65:
            trend_type = "stable seasonal trend"
            duration = 42
            confidence = 0.82
            impact = 1.12 if direction != "falling" else 0.9
        elif variability <= 0.10 and abs(strength) > 0.08:
            trend_type = "long-term structural trend"
            duration = 56
            confidence = 0.85
            impact = 1.2 if direction == "rising" else 0.85
        else:
            trend_type = "volatile / uncertain trend"
            duration = 14
            confidence = 0.5
            impact = 1.0

        records.append(
            {
                "product_id": product_id,
                "trend_direction": direction,
                "trend_strength": round(strength, 3),
                "expected_trend_duration_days": duration,
                "trend_variability_score": round(float(np.clip(variability, 0, 1)), 3),
                "trend_confidence": round(confidence, 3),
                "trend_type": trend_type,
                "trend_impact_multiplier": round(impact, 3),
                "trend_persistence_score": round(float(np.clip((duration / 56) * (1 - variability), 0, 1)), 3),
            }
        )

    return pd.DataFrame(records)
