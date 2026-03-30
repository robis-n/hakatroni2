"""FastAPI routes."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Recommendation, ReportHistory, TrendPersistenceMetric
from app.schemas import ProductOut, RecommendationOut, TrendOut
from app.services.pipeline import run_pipeline

router = APIRouter()


@router.post("/upload/excel")
def upload_excel(
    sales_file: Optional[UploadFile] = File(None),
    inventory_file: Optional[UploadFile] = File(None),
    products_file: Optional[UploadFile] = File(None),
    trends_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    tmp = Path("data/uploads")
    tmp.mkdir(parents=True, exist_ok=True)

    def _save(upload: Optional[UploadFile]) -> Optional[Path]:
        if not upload:
            return None
        p = tmp / upload.filename
        p.write_bytes(upload.file.read())
        return p

    result = run_pipeline(db, _save(sales_file), _save(inventory_file), _save(products_file), _save(trends_file))
    return {"message": "Pipeline completed", "report": result["report"]}


@router.post("/connect/sql")
def connect_sql(connection_string: str, sales_table: str, inventory_table: str, products_table: str, trends_table: str):
    # For MVP this endpoint documents expected payload and returns guidance.
    return {
        "message": "SQL connection accepted for MVP; load to files or extend ingest_sources/load_from_sql in production.",
        "connection_string": connection_string,
        "tables": {"sales": sales_table, "inventory": inventory_table, "products": products_table, "trends": trends_table},
    }


@router.get("/products", response_model=list[ProductOut])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@router.get("/recommendations", response_model=list[RecommendationOut])
def get_recommendations(db: Session = Depends(get_db)):
    return db.query(Recommendation).all()


@router.get("/report/daily")
def get_daily_report(db: Session = Depends(get_db)):
    report = db.query(ReportHistory).order_by(ReportHistory.generated_at.desc()).first()
    if not report:
        raise HTTPException(status_code=404, detail="No report generated yet")
    return {"generated_at": report.generated_at, "report_path": report.report_path, "summary": report.summary_text}


@router.get("/product/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    rec = db.query(Recommendation).filter(Recommendation.product_id == product_id).first()
    trend = db.query(TrendPersistenceMetric).filter(TrendPersistenceMetric.product_id == product_id).first()
    return {"product": ProductOut.model_validate(product), "recommendation": RecommendationOut.model_validate(rec) if rec else None, "trend": TrendOut.model_validate(trend) if trend else None}


@router.get("/trends/{product_id}", response_model=TrendOut)
def get_trend(product_id: str, db: Session = Depends(get_db)):
    trend = db.query(TrendPersistenceMetric).filter(TrendPersistenceMetric.product_id == product_id).first()
    if not trend:
        raise HTTPException(status_code=404, detail="Trend not found")
    return trend


@router.post("/run/demo")
def run_demo(db: Session = Depends(get_db)):
    result = run_pipeline(db)
    return {"message": "Demo pipeline completed", "report": result["report"], "recommendations": len(result["recommendations"])}
