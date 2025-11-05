import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "raw"
STD = BASE / "data" / "standardized"
STD.mkdir(parents=True, exist_ok=True)


def write(df, name):
    out = STD / name
    df.to_csv(out, index=False)
    print(f"WROTE {out}  ({len(df)} rows)")


def main():
    # Aircraft
    ac = pd.read_csv(RAW / "aircraft.csv").rename(
        columns={"ac_id": "aircraft_id", "tail_num": "tail_number"}
    )[["aircraft_id", "tail_number", "fleet", "model"]]
    write(ac, "aircraft.csv")

    # Telemetry
    se = pd.read_csv(RAW / "sensor_readings.csv").rename(
        columns={"ac_id": "aircraft_id", "timestamp": "ts"}
    )[["reading_id", "aircraft_id", "ts", "sensor", "value"]]
    write(se, "sensor_readings.csv")

    # Parts
    pa = pd.read_csv(RAW / "parts.csv").rename(
        columns={"part_no": "part_number"}
    )[["part_number", "name", "vendor", "mtbf_hours", "criticality"]]
    write(pa, "parts.csv")

    # Work Orders
    wo = pd.read_csv(RAW / "work_orders.csv").rename(
        columns={"ac_id": "aircraft_id", "part_no": "part_number", "ata": "ata_code"}
    )[["wo_id", "aircraft_id", "part_number", "opened_ts", "closed_ts", "action", "ata_code"]]
    write(wo, "work_orders.csv")

    # Alerts
    alerts = []
    alert_id = 1
    for _, row in se.iterrows():
        risk = 0.0
        rec = None
        if row["sensor"] == "oil_temp" and row["value"] > 200:
            risk = 0.8
            rec = "check_oil_cooling"
        if row["sensor"] == "vibration" and row["value"] > 3.0:
            risk = max(risk, 0.7)
            rec = rec or "inspect_bearing"
        if risk > 0:
            alerts.append({
                "alert_id": alert_id,
                "aircraft_id": row["aircraft_id"],
                "sensor": row["sensor"],
                "risk_score": risk,
                "created_ts": row["ts"],
                "recommended_action": rec
            })
            alert_id += 1

    al = pd.DataFrame(alerts)
    write(al, "alerts.csv")

    # Feature: Latest Oil Temp Per Aircraft
    oil = se[se["sensor"] == "oil_temp"].sort_values("ts").groupby("aircraft_id").tail(1)
    feat = oil.rename(columns={"value": "last_oil_temp"}).merge(
        ac, on="aircraft_id", how="left"
    )[["aircraft_id", "tail_number", "fleet", "model", "last_oil_temp"]]
    write(feat, "features_aircraft_health.csv")


if __name__ == "__main__":
    main()