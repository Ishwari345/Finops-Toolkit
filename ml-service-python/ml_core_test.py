import pandas as pd

DATA_PATH = "cost-analysis.csv"

df = pd.read_csv(DATA_PATH, parse_dates=["date"])
df = df.sort_values("date")

# Aggregate by date (in case there are multiple rows per day later)
daily = df.groupby("date").agg(
    total_cost=("total_cost", "sum"),
    total_units=("units", "sum")
).reset_index()
daily["unit_cost"] = daily["total_cost"] / daily["total_units"]

mean_cost = daily["total_cost"].mean()
std_cost = daily["total_cost"].std()
threshold = mean_cost + 2 * std_cost  # basic sensitivity

print(f"Mean cost: {mean_cost:.2f}")
print(f"Std dev: {std_cost:.2f}")
print(f"Threshold: {threshold:.2f}\n")

print("Potential anomalies (cost > threshold):")
for _, row in daily.iterrows():
    if row["total_cost"] > threshold:
        print(f"{row['date'].date()} -> cost={row['total_cost']}, unit_cost={row['unit_cost']:.2f}")
