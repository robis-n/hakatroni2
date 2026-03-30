"""Streamlit dashboard for recommendations and trend visibility."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

from app.config import settings

st.set_page_config(page_title="Inventory Trend Assistant", layout="wide")
st.title("AI Inventory Trend & Replenishment Assistant")

engine = create_engine(settings.database_url)

recs = pd.read_sql("SELECT * FROM recommendations", engine)
products = pd.read_sql("SELECT * FROM products", engine)
trends = pd.read_sql("SELECT * FROM trend_persistence_metrics", engine)
sales = pd.read_sql("SELECT * FROM sales_history", engine)

if recs.empty:
    st.warning("No recommendations found. Run POST /run/demo from the API first.")
    st.stop()

view = recs.merge(products, on="product_id", how="left").merge(trends[["product_id", "trend_type", "expected_trend_duration_days", "trend_variability_score", "trend_direction"]], on="product_id", how="left")

urgency_filter = st.multiselect("Filter by urgency", sorted(view["reorder_urgency"].dropna().unique().tolist()), default=sorted(view["reorder_urgency"].dropna().unique().tolist()))
action_filter = st.multiselect("Filter by action", sorted(view["recommended_action"].dropna().unique().tolist()), default=sorted(view["recommended_action"].dropna().unique().tolist()))

filtered = view[view["reorder_urgency"].isin(urgency_filter) & view["recommended_action"].isin(action_filter)]

st.subheader("Product Recommendations")
st.dataframe(
    filtered[
        [
            "product_id",
            "product_name",
            "recommended_action",
            "recommended_reorder_qty",
            "reorder_urgency",
            "confidence_score",
            "trend_type",
            "expected_trend_duration_days",
            "trend_variability_score",
        ]
    ],
    use_container_width=True,
)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Top Urgent SKUs")
    st.dataframe(filtered.sort_values(["reorder_urgency", "confidence_score"], ascending=[True, False]).head(10)[["product_id", "product_name", "recommended_action", "recommended_reorder_qty", "confidence_score"]])

with col2:
    st.subheader("Actions Mix")
    fig = px.histogram(filtered, x="recommended_action", color="reorder_urgency")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Historical Sales vs 7-Day Rolling Average")
selected = st.selectbox("Select product", sorted(sales["product_id"].unique()))
sp = sales[sales["product_id"] == selected].copy()
sp["date"] = pd.to_datetime(sp["date"])
sp = sp.sort_values("date")
sp["rolling7"] = sp["quantity_sold"].rolling(7, min_periods=1).mean()
fig2 = px.line(sp, x="date", y=["quantity_sold", "rolling7"], labels={"value": "Units", "variable": "Series"})
st.plotly_chart(fig2, use_container_width=True)

latest_report = sorted(settings.report_dir.glob("daily_report_*.csv"))
if latest_report:
    report_path = latest_report[-1]
    st.download_button("Download latest daily report", data=report_path.read_bytes(), file_name=report_path.name)
