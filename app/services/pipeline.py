"""End-to-end orchestration for ingestion, analysis, recommendation, and persistence."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    InventorySnapshot,
    Product,
    Recommendation,
    ReportHistory,
    SalesHistory,
    TrendPersistenceMetric,
    TrendSignal,
)
from app.services.cleaning import average_daily_demand, clean_dataframes
from app.services.demo_data import generate_demo_files
from app.services.forecasting import forecast_by_product
from app.services.ingestion import ingest_sources
from app.services.recommendation_engine import generate_recommendations
from app.services.reporting import generate_daily_report
from app.services.trend_engine import build_trend_features
from app.services.trend_persistence import compute_trend_persistence


def run_pipeline(
    db: Session,
    sales_path: Optional[Path] = None,
    inventory_path: Optional[Path] = None,
    products_path: Optional[Path] = None,
    trends_path: Optional[Path] = None,
) -> dict:
    if not any([sales_path, inventory_path, products_path, trends_path]):
        demo_paths = generate_demo_files(settings.data_dir)
        sales_path, inventory_path, products_path, trends_path = (
            demo_paths["sales"],
            demo_paths["inventory"],
            demo_paths["products"],
            demo_paths["trends"],
        )

    raw = ingest_sources(sales_path, inventory_path, products_path, trends_path)
    cleaned = clean_dataframes(raw)

    sales = cleaned.get("sales", pd.DataFrame(columns=["product_id", "date", "quantity_sold", "revenue"]))
    inventory = cleaned.get("inventory", pd.DataFrame(columns=["product_id", "date", "inventory_on_hand", "incoming_orders"]))
    products = cleaned.get("products", pd.DataFrame(columns=["product_id", "product_name", "category", "reorder_threshold", "supplier_lead_time_days"]))
    trends = cleaned.get("trends", pd.DataFrame(columns=["product_id", "date", "market_trend_score", "competitor_signal", "social_trend_score", "seasonality_factor", "trend_signal_source"]))

    demand = average_daily_demand(sales)
    persistence = compute_trend_persistence(trends)
    features = build_trend_features(demand, trends, persistence)
    analysis = forecast_by_product(features, inventory, products)
    recs = generate_recommendations(analysis, persistence, products)
    report = generate_daily_report(recs, settings.report_dir)

    _persist_inputs(db, products, sales, inventory, trends)
    _persist_outputs(db, recs, persistence, report)

    return {"recommendations": recs.to_dict(orient="records"), "report": report}


def _persist_inputs(db: Session, products: pd.DataFrame, sales: pd.DataFrame, inventory: pd.DataFrame, trends: pd.DataFrame) -> None:
    db.query(Product).delete()
    db.query(SalesHistory).delete()
    db.query(InventorySnapshot).delete()
    db.query(TrendSignal).delete()

    for _, row in products.iterrows():
        db.add(Product(**row.to_dict()))
    for _, row in sales.iterrows():
        db.add(SalesHistory(**row.to_dict()))
    for _, row in inventory.iterrows():
        db.add(InventorySnapshot(**row.to_dict()))
    for _, row in trends.iterrows():
        db.add(TrendSignal(**row.to_dict()))
    db.commit()


def _persist_outputs(db: Session, recs: pd.DataFrame, persistence: pd.DataFrame, report: dict[str, str]) -> None:
    db.query(Recommendation).delete()
    db.query(TrendPersistenceMetric).delete()

    today = date.today()
    for _, row in persistence.iterrows():
        db.add(TrendPersistenceMetric(as_of_date=today, **row.to_dict()))
    for _, row in recs.iterrows():
        db.add(
            Recommendation(
                product_id=row["product_id"],
                as_of_date=today,
                recommended_action=row["recommended_action"],
                recommended_reorder_qty=row["recommended_reorder_qty"],
                reorder_urgency=row["reorder_urgency"],
                confidence_score=row["confidence_score"],
                explanation=row["explanation"],
            )
        )

    db.add(ReportHistory(generated_at=datetime.utcnow(), report_path=report["csv"], summary_text=report["summary_text"]))
    db.commit()
