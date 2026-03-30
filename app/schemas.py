"""Pydantic API schemas."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


class ProductOut(BaseModel):
    product_id: str
    product_name: str
    category: Optional[str] = None
    reorder_threshold: float
    supplier_lead_time_days: int

    class Config:
        from_attributes = True


class RecommendationOut(BaseModel):
    product_id: str
    as_of_date: date
    recommended_action: str
    recommended_reorder_qty: float
    reorder_urgency: Optional[str]
    confidence_score: Optional[float]
    explanation: Optional[str]

    class Config:
        from_attributes = True


class TrendOut(BaseModel):
    product_id: str
    as_of_date: date
    trend_direction: str
    trend_strength: float
    expected_trend_duration_days: int
    trend_variability_score: float
    trend_confidence: float
    trend_type: str
    trend_impact_multiplier: float

    class Config:
        from_attributes = True
