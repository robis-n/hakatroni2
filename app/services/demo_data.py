"""Creates demo datasets when no input files are provided."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import numpy as np
import pandas as pd


def generate_demo_files(data_dir: Path) -> dict[str, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    sales_path = data_dir / "sample" / "sales.csv"
    inventory_path = data_dir / "sample" / "inventory.csv"
    products_path = data_dir / "sample" / "products.csv"
    trends_path = data_dir / "sample" / "trends.csv"
    sales_path.parent.mkdir(parents=True, exist_ok=True)

    products = pd.DataFrame(
        [
            {"product_id": "P100", "product_name": "Hydration Bottle", "category": "Home", "reorder_threshold": 120, "supplier_lead_time_days": 8},
            {"product_id": "P200", "product_name": "Yoga Mat Pro", "category": "Fitness", "reorder_threshold": 60, "supplier_lead_time_days": 10},
            {"product_id": "P300", "product_name": "Protein Mixer", "category": "Fitness", "reorder_threshold": 80, "supplier_lead_time_days": 6},
            {"product_id": "P400", "product_name": "Desk Organizer", "category": "Office", "reorder_threshold": 70, "supplier_lead_time_days": 12},
            {"product_id": "P500", "product_name": "Smart LED Lamp", "category": "Electronics", "reorder_threshold": 40, "supplier_lead_time_days": 14},
        ]
    )

    today = date.today()
    days = 120
    rows = []
    trend_rows = []
    rng = np.random.default_rng(42)

    base = {"P100": 23, "P200": 11, "P300": 16, "P400": 9, "P500": 6}
    for d in range(days):
        dt = today - timedelta(days=days - d)
        season = 1 + 0.12 * np.sin((2 * np.pi * d) / 30)
        for pid, avg in base.items():
            signal = 0
            if pid == "P100" and d > 95:
                signal = 7
            if pid == "P500" and 85 <= d <= 92:
                signal = 12
            if pid == "P400" and d > 80:
                signal = -2
            qty = max(0, int(rng.normal(avg * season + signal, 2.5)))
            rows.append({"product_id": pid, "date": dt, "quantity_sold": qty, "revenue": round(qty * rng.uniform(12, 55), 2)})

            trend_rows.append(
                {
                    "product_id": pid,
                    "date": dt,
                    "market_trend_score": round(float(np.clip(rng.normal(0.55 + signal / 30, 0.15), 0, 1)), 3),
                    "competitor_signal": round(float(np.clip(rng.normal(0.50 + signal / 40, 0.2), 0, 1)), 3),
                    "social_trend_score": round(float(np.clip(rng.normal(0.45 + signal / 25, 0.22), 0, 1)), 3),
                    "seasonality_factor": round(float(np.clip(season / 1.2, 0, 1.2)), 3),
                    "trend_signal_source": "mock_external",
                }
            )

    inventory = pd.DataFrame(
        [
            {"product_id": "P100", "date": today, "inventory_on_hand": 150, "incoming_orders": 120},
            {"product_id": "P200", "date": today, "inventory_on_hand": 90, "incoming_orders": 40},
            {"product_id": "P300", "date": today, "inventory_on_hand": 210, "incoming_orders": 0},
            {"product_id": "P400", "date": today, "inventory_on_hand": 300, "incoming_orders": 0},
            {"product_id": "P500", "date": today, "inventory_on_hand": 35, "incoming_orders": 60},
        ]
    )

    products.to_csv(products_path, index=False)
    pd.DataFrame(rows).to_csv(sales_path, index=False)
    inventory.to_csv(inventory_path, index=False)
    pd.DataFrame(trend_rows).to_csv(trends_path, index=False)

    return {"products": products_path, "sales": sales_path, "inventory": inventory_path, "trends": trends_path}
