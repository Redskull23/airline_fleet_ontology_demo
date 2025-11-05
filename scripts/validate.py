import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
STD = BASE / "data" / "standardized"


def load(name):
    return pd.read_csv(STD / name)


def main():
    print("=== SCHEMA CHECKS ===")
    ac = load("aircraft.csv")
    se = load("sensor_readings.csv")
    wo = load("work_orders.csv")

    print(ac.columns.tolist())
    print(se.columns.tolist())
    print(wo.columns.tolist())

    print("\n=== RANGE CHECK: oil_temp should be between 100-230 ===")
    oil = se[se["sensor"] == "oil_temp"]
    outliers = oil[(oil["value"] < 100) | (oil["value"] > 230)]
    print(f"Out-of-range rows: {len(outliers)}")


if __name__ == "__main__":
    main()