"""Recommendation rules that incorporate trend persistence and stock risk."""
from __future__ import annotations

import numpy as np
import pandas as pd


def generate_recommendations(analysis_df: pd.DataFrame, persistence_df: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame:
    merged = analysis_df.merge(
        persistence_df[[
            "product_id",
            "trend_direction",
            "trend_strength",
            "expected_trend_duration_days",
            "trend_variability_score",
            "trend_confidence",
            "trend_type",
            "trend_impact_multiplier",
        ]],
        on="product_id",
        how="left",
    )
    merged = merged.merge(products_df[["product_id", "product_name", "category"]], on="product_id", how="left")
    merged = merged.fillna({"trend_direction": "stable", "trend_type": "volatile / uncertain trend", "trend_confidence": 0.5, "trend_variability_score": 0.5, "expected_trend_duration_days": 14, "trend_strength": 0.0, "trend_impact_multiplier": 1.0})

    recs = []
    for _, r in merged.iterrows():
        baseline_14d = r["avg_daily_demand"] * 14
        trend_adjusted_14d = r["forecast_14d"]
        gap = trend_adjusted_14d - (r["inventory_on_hand"] + r["incoming_orders"])

        persistence_boost = 1 + ((r["expected_trend_duration_days"] / 30) * (1 - r["trend_variability_score"]))
        qty = max(0, gap * persistence_boost)

        if r["reorder_urgency"] == "urgent":
            action = "urgent reorder"
        elif r["overstock_flag"] and r["trend_direction"] != "rising":
            action = "decrease order"
            qty = 0
        elif qty > r.get("reorder_threshold", 0) * 0.5:
            action = "increase order"
        elif r["trend_direction"] == "falling" and r["trend_variability_score"] < 0.2:
            action = "decrease order"
            qty = max(0, qty * 0.35)
        else:
            action = "maintain"
            qty = max(0, qty * 0.2)

        confidence = float(np.clip((r["trend_confidence"] * 0.6) + (1 - min(r["trend_variability_score"], 1)) * 0.4, 0, 1))
        explanation = (
            f"{action.title()} for {r['product_name']} because forecasted 14-day demand is "
            f"{trend_adjusted_14d:.1f} units vs available {(r['inventory_on_hand'] + r['incoming_orders']):.1f}. "
            f"Current stock covers {r['days_of_cover']:.1f} days, lead time is {int(r['supplier_lead_time_days'])} days, "
            f"trend type is {r['trend_type']} with expected persistence of {int(r['expected_trend_duration_days'])} days "
            f"and variability score {r['trend_variability_score']:.2f}."
        )

        recs.append({
            **r.to_dict(),
            "recommended_action": action,
            "recommended_reorder_qty": round(float(qty), 1),
            "confidence_score": round(confidence, 3),
            "explanation": explanation,
        })

    return pd.DataFrame(recs)
