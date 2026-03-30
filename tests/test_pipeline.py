from app.services.demo_data import generate_demo_files
from app.services.ingestion import ingest_sources
from app.services.cleaning import clean_dataframes, average_daily_demand
from pathlib import Path


def test_demo_generation_and_cleaning(tmp_path: Path):
    files = generate_demo_files(tmp_path)
    raw = ingest_sources(files["sales"], files["inventory"], files["products"], files["trends"])
    cleaned = clean_dataframes(raw)

    assert "sales" in cleaned
    assert cleaned["sales"].shape[0] > 0
    demand = average_daily_demand(cleaned["sales"])
    assert "avg_daily_demand" in demand.columns
    assert demand["avg_daily_demand"].min() >= 0
