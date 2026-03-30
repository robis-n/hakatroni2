"""Application configuration for the AI Inventory Trend & Replenishment Assistant."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and sensible defaults."""

    app_name: str = "AI Inventory Trend & Replenishment Assistant"
    database_url: str = Field(default="sqlite:///./inventory_ai.db", alias="DATABASE_URL")
    data_dir: Path = Field(default=Path("data"), alias="DATA_DIR")
    report_dir: Path = Field(default=Path("data/reports"), alias="REPORT_DIR")
    forecast_horizons: tuple[int, int, int] = (7, 14, 30)
    default_urgency_days: int = 7

    trend_weights: Dict[str, float] = {
        "historical_demand_score": 0.35,
        "market_trend_score": 0.20,
        "competitor_trend_score": 0.15,
        "social_trend_score": 0.10,
        "seasonality_score": 0.10,
        "trend_persistence_score": 0.10,
    }

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
settings.report_dir.mkdir(parents=True, exist_ok=True)
settings.data_dir.mkdir(parents=True, exist_ok=True)
