"""Daily reporting output generation."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


def generate_daily_report(recommendations: pd.DataFrame, output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"daily_report_{stamp}.csv"
    xlsx_path = output_dir / f"daily_report_{stamp}.xlsx"
    txt_path = output_dir / f"daily_summary_{stamp}.txt"

    report_cols = [
        "product_id",
        "product_name",
        "category",
        "recommended_action",
        "recommended_reorder_qty",
        "reorder_urgency",
        "days_of_cover",
        "predicted_stockout_date",
        "overstock_flag",
        "trend_type",
        "expected_trend_duration_days",
        "trend_variability_score",
        "confidence_score",
        "explanation",
    ]
    report_df = recommendations[report_cols].sort_values(["reorder_urgency", "confidence_score"], ascending=[True, False])
    report_df.to_csv(csv_path, index=False)
    report_df.to_excel(xlsx_path, index=False)

    urgent = (report_df["reorder_urgency"] == "urgent").sum()
    inc = (report_df["recommended_action"].isin(["increase order", "urgent reorder"])) .sum()
    dec = (report_df["recommended_action"] == "decrease order").sum()
    temporary = report_df["trend_type"].isin(["short-term spike", "short-term declining signal"]).sum()
    persistent = report_df["trend_type"].isin(["medium-term emerging trend", "stable seasonal trend", "long-term structural trend"]).sum()

    manager_summary = (
        f"Today, {urgent} products require urgent attention. "
        f"{inc} products should be reordered sooner due to increased trend-adjusted demand. "
        f"{dec} products show declining demand and should have reduced replenishment. "
        f"{temporary} demand surges appear temporary, while {persistent} show persistent multi-week trends."
    )
    txt_path.write_text(manager_summary)

    return {
        "csv": str(csv_path),
        "excel": str(xlsx_path),
        "summary_text": manager_summary,
        "summary_path": str(txt_path),
    }
