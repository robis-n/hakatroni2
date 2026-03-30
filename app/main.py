"""FastAPI application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Product
from app.services.pipeline import run_pipeline

app = FastAPI(title=settings.app_name)
app.include_router(router)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Product).count() == 0:
            run_pipeline(db)
    finally:
        db.close()


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
