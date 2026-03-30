"""SQLAlchemy ORM models."""
from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import Column, Date, DateTime, Float, Integer, String, Text

from app.database import Base


class Product(Base):
    __tablename__ = "products"
    product_id = Column(String, primary_key=True, index=True)
    product_name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    reorder_threshold = Column(Float, default=0)
    supplier_lead_time_days = Column(Integer, default=7)


class SalesHistory(Base):
    __tablename__ = "sales_history"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True, nullable=False)
    date = Column(Date, nullable=False)
    quantity_sold = Column(Float, default=0)
    revenue = Column(Float, default=0)


class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True, nullable=False)
    date = Column(Date, nullable=False)
    inventory_on_hand = Column(Float, default=0)
    incoming_orders = Column(Float, default=0)


class TrendSignal(Base):
    __tablename__ = "trend_signals"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True, nullable=False)
    date = Column(Date, nullable=False)
    market_trend_score = Column(Float, default=0)
    competitor_signal = Column(Float, default=0)
    social_trend_score = Column(Float, default=0)
    seasonality_factor = Column(Float, default=0)
    trend_signal_source = Column(String, default="mock")


class TrendPersistenceMetric(Base):
    __tablename__ = "trend_persistence_metrics"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True, nullable=False)
    as_of_date = Column(Date, nullable=False)
    trend_direction = Column(String)
    trend_strength = Column(Float)
    expected_trend_duration_days = Column(Integer)
    trend_variability_score = Column(Float)
    trend_confidence = Column(Float)
    trend_type = Column(String)
    trend_impact_multiplier = Column(Float)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True, nullable=False)
    as_of_date = Column(Date, nullable=False)
    recommended_action = Column(String, nullable=False)
    recommended_reorder_qty = Column(Float, default=0)
    reorder_urgency = Column(String)
    confidence_score = Column(Float)
    explanation = Column(Text)


class ReportHistory(Base):
    __tablename__ = "report_history"
    id = Column(Integer, primary_key=True, index=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    report_path = Column(String)
    summary_text = Column(Text)
