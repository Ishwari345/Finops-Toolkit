from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from prophet import Prophet

DATA_PATH = "cost-analysis.csv"

# ---------- LOAD RAW DATA ----------
df_raw = pd.read_csv(DATA_PATH, parse_dates=["date"])
df_raw = df_raw.sort_values("date")

# Aggregate by date
daily = df_raw.groupby("date").agg(
    total_cost=("total_cost", "sum"),
    total_units=("units", "sum")
).reset_index()
daily["unit_cost"] = daily["total_cost"] / daily["total_units"]

# ---------- PREPARE DATA FOR PROPHET ----------
ts = daily[["date", "total_cost"]].rename(columns={"date": "ds", "total_cost": "y"})

# Train Prophet model once at startup
model = Prophet(interval_width=0.95)
model.fit(ts)

# Predict on existing dates (historical anomaly detection)
forecast = model.predict(ts[["ds"]])

# Merge forecast back into daily dataframe
daily_prophet = daily.copy()
daily_prophet["yhat"] = forecast["yhat"]
daily_prophet["yhat_upper"] = forecast["yhat_upper"]
daily_prophet["yhat_lower"] = forecast["yhat_lower"]

# ---------- FASTAPI APP ----------
app = FastAPI(title="FinOps ML Service (Prophet)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnomalyRequest(BaseModel):
    sensitivity: float = 1.5  # multiplier for upper bound


@app.get("/")
def root():
    return {"message": "FinOps ML Service with Prophet running"}


@app.post("/detect-anomalies")
def detect_anomalies(req: AnomalyRequest):
    """
    Prophet-based anomaly detection:
    - expected_cost = yhat
    - upper band = yhat_upper
    - anomaly if actual_cost > yhat_upper * sensitivity
    """
    sensitivity = float(req.sensitivity)

    df = daily_prophet.copy()

    # Point-wise dynamic threshold
    df["dynamic_upper"] = df["yhat_upper"] * sensitivity
    df["is_anomaly"] = df["total_cost"] > df["dynamic_upper"]

    # Severity based on how far above expected value
    def severity(row):
        if not row["is_anomaly"]:
            return "NONE"
        if row["yhat"] <= 0:
            return "HIGH"
        gap_ratio = (row["total_cost"] - row["yhat"]) / row["yhat"]
        if gap_ratio > 0.4:
            return "HIGH"
        if gap_ratio > 0.2:
            return "MEDIUM"
        return "LOW"

    df["severity"] = df.apply(severity, axis=1)

    anomalies = []
    for _, row in df.iterrows():
        anomalies.append({
            "date": row["date"].strftime("%Y-%m-%d"),
            "total_cost": float(row["total_cost"]),
            "unit_cost": float(row["unit_cost"]),
            "expected_cost": float(row["yhat"]),
            "is_anomaly": bool(row["is_anomaly"]),
            "severity": row["severity"]
        })

    mean_cost = df["total_cost"].mean()
    avg_dynamic_upper = df["dynamic_upper"].mean()

    return {
        "mean_cost": float(mean_cost),
        "std_cost": None,
        "threshold": float(avg_dynamic_upper),
        "anomalies": anomalies,
        "security_alert_count": int(sum(1 for a in anomalies if a["severity"] == "HIGH"))
    }


@app.get("/unit-cost")
def unit_cost_timeseries():
    """
    Returns unit cost over time (cost per unit).
    """
    return daily[["date", "unit_cost"]].assign(
        date=lambda d: d["date"].dt.strftime("%Y-%m-%d"),
        unit_cost=lambda d: d["unit_cost"].astype(float)
    ).to_dict(orient="records")


@app.get("/rca")
def root_cause_analysis(
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    """
    Root Cause Analysis:
    - Filter raw data for that date
    - Group by service, region, tag
    - Return top contributors
    """
    subset = df_raw[df_raw["date"] == pd.to_datetime(date)]
    if subset.empty:
        return {"date": date, "message": "No data for this date"}

    by_service = subset.groupby("service")["total_cost"].sum().sort_values(ascending=False)
    by_region = subset.groupby("region")["total_cost"].sum().sort_values(ascending=False)
    by_tag = subset.groupby("tag")["total_cost"].sum().sort_values(ascending=False)

    top_service = by_service.index[0]
    top_region = by_region.index[0]
    top_tag = by_tag.index[0]

    return {
        "date": date,
        "top_service": {
            "name": top_service,
            "cost": float(by_service.iloc[0])
        },
        "top_region": {
            "name": top_region,
            "cost": float(by_region.iloc[0])
        },
        "top_tag": {
            "name": top_tag,
            "cost": float(by_tag.iloc[0])
        },
        "message": (
            f"Highest cost driver on {date}: "
            f"service={top_service}, region={top_region}, tag={top_tag}"
        )
    }
