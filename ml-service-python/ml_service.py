from fastapi import FastAPI, Query, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import io
from prophet import Prophet

DATA_PATH = "cost-analysis.csv"


def process_dataset(df_raw: pd.DataFrame):
    """
    Takes a raw cost dataframe (columns: date, service, region, tag,
    total_cost, units) and runs the full pipeline: aggregation,
    Prophet forecasting, and anomaly-ready merged data.
    Returns (df_raw, daily, daily_prophet).
    """
    required_cols = {"date", "total_cost", "units"}
    missing = required_cols - set(df_raw.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df_raw = df_raw.copy()
    df_raw["date"] = pd.to_datetime(df_raw["date"])
    df_raw = df_raw.sort_values("date")

    daily = df_raw.groupby("date").agg(
        total_cost=("total_cost", "sum"),
        total_units=("units", "sum")
    ).reset_index()
    daily["unit_cost"] = daily["total_cost"] / daily["total_units"]

    ts = daily[["date", "total_cost"]].rename(columns={"date": "ds", "total_cost": "y"})

    model = Prophet(interval_width=0.95)
    model.fit(ts)
    forecast = model.predict(ts[["ds"]])

    daily_prophet = daily.copy()
    daily_prophet["yhat"] = forecast["yhat"]
    daily_prophet["yhat_upper"] = forecast["yhat_upper"]
    daily_prophet["yhat_lower"] = forecast["yhat_lower"]

    return df_raw, daily, daily_prophet


def run_anomaly_detection(daily_prophet: pd.DataFrame, sensitivity: float = 1.5):
    """
    Shared anomaly-detection logic used by both the default dataset
    endpoint and the uploaded-CSV endpoint.
    """
    df = daily_prophet.copy()
    df["dynamic_upper"] = df["yhat_upper"] * sensitivity
    df["is_anomaly"] = df["total_cost"] > df["dynamic_upper"]

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


def run_rca(df_raw: pd.DataFrame, date: str):
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
        "top_service": {"name": top_service, "cost": float(by_service.iloc[0])},
        "top_region": {"name": top_region, "cost": float(by_region.iloc[0])},
        "top_tag": {"name": top_tag, "cost": float(by_tag.iloc[0])},
        "message": (
            f"Highest cost driver on {date}: "
            f"service={top_service}, region={top_region}, tag={top_tag}"
        )
    }


# ---------- LOAD DEFAULT DATASET AT STARTUP ----------
df_raw = pd.read_csv(DATA_PATH, parse_dates=["date"])
df_raw, daily, daily_prophet = process_dataset(df_raw)

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
    return run_anomaly_detection(daily_prophet, float(req.sensitivity))


@app.get("/unit-cost")
def unit_cost_timeseries():
    return daily[["date", "unit_cost"]].assign(
        date=lambda d: d["date"].dt.strftime("%Y-%m-%d"),
        unit_cost=lambda d: d["unit_cost"].astype(float)
    ).to_dict(orient="records")


@app.get("/rca")
def root_cause_analysis(date: str = Query(..., description="Date in YYYY-MM-DD format")):
    return run_rca(df_raw, date)


# ---------- NEW: UPLOAD YOUR OWN CSV ----------
@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), sensitivity: float = 1.5):
    """
    Accepts a user-uploaded CSV with the same schema as cost-analysis.csv
    (columns: date, service, region, tag, total_cost, units).
    Runs the full pipeline (forecast + anomaly detection) on it and
    returns the analysis without touching the default in-memory dataset.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    contents = await file.read()
    try:
        uploaded_df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    try:
        up_raw, up_daily, up_daily_prophet = process_dataset(uploaded_df)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {e}")

    anomaly_result = run_anomaly_detection(up_daily_prophet, sensitivity)
    unit_cost_result = up_daily[["date", "unit_cost"]].assign(
        date=lambda d: d["date"].dt.strftime("%Y-%m-%d"),
        unit_cost=lambda d: d["unit_cost"].astype(float)
    ).to_dict(orient="records")

    return {
        "filename": file.filename,
        "rows_processed": len(uploaded_df),
        "anomaly_detection": anomaly_result,
        "unit_cost_timeseries": unit_cost_result
    }