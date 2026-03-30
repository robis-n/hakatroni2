"""Data ingestion utilities for file and SQL sources."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from sqlalchemy import create_engine


COMMON_COLUMN_ALIASES = {
    "sku": "product_id",
    "item_id": "product_id",
    "item_name": "product_name",
    "sold_qty": "quantity_sold",
    "qty": "quantity_sold",
    "stock": "inventory_on_hand",
    "lead_time": "supplier_lead_time_days",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {col: COMMON_COLUMN_ALIASES.get(col.lower().strip(), col.lower().strip()) for col in df.columns}
    return df.rename(columns=renamed)


def load_file(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path, engine="openpyxl")
    else:
        raise ValueError(f"Unsupported file format: {path}")
    return normalize_columns(df)


def load_from_sql(connection_string: str, table_mapping: Dict[str, str]) -> Dict[str, pd.DataFrame]:
    engine = create_engine(connection_string)
    data = {}
    for dataset_name, table_name in table_mapping.items():
        data[dataset_name] = normalize_columns(pd.read_sql_table(table_name, con=engine))
    return data


def ingest_sources(
    sales_path: Optional[Path] = None,
    inventory_path: Optional[Path] = None,
    products_path: Optional[Path] = None,
    trends_path: Optional[Path] = None,
) -> Dict[str, pd.DataFrame]:
    sources = {}
    if sales_path and sales_path.exists():
        sources["sales"] = load_file(sales_path)
    if inventory_path and inventory_path.exists():
        sources["inventory"] = load_file(inventory_path)
    if products_path and products_path.exists():
        sources["products"] = load_file(products_path)
    if trends_path and trends_path.exists():
        sources["trends"] = load_file(trends_path)
    return sources
