"""Risk-scoring business rules for pharma shipments.

Score components (each capped, summed to a 0-100 Risk_Score):
  - Temperature excursion : 10 pts per deg C outside the required range, capped at 50
  - Delivery delay        : 1 pt per 2 hours late, capped at 25
  - Handling incidents    : 5 pts per incident, capped at 15
  - Shipment value exposure: scales to 10 at $50,000+, capped at 10

Tiers: High >= 60, Medium 30-59, Low < 30.
See CLAUDE.md for the rationale and how to retune these thresholds.
"""
import pandas as pd

REQUIRED_COLUMNS = [
    "Shipment_ID", "Product_Name", "Origin", "Destination", "Carrier",
    "Expected_Delivery_Date", "Actual_Delivery_Date",
    "Required_Temp_Min_C", "Required_Temp_Max_C",
    "Recorded_Min_Temp_C", "Recorded_Max_Temp_C",
    "Handling_Incidents", "Shipment_Value_USD",
]

HIGH_RISK_THRESHOLD = 60
MEDIUM_RISK_THRESHOLD = 30

TIER_COLORS = {"Low": "#0ca30c", "Medium": "#fab219", "High": "#d03b3b"}
TIER_ORDER = ["Low", "Medium", "High"]


def validate_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in REQUIRED_COLUMNS if c not in df.columns]


def compute_risk(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for date_col in ["Expected_Delivery_Date", "Actual_Delivery_Date"]:
        df[date_col] = pd.to_datetime(df[date_col])

    if "Delay_Hours" not in df.columns:
        df["Delay_Hours"] = (
            (df["Actual_Delivery_Date"] - df["Expected_Delivery_Date"])
            .dt.total_seconds() / 3600
        ).clip(lower=0)

    excursion_below = (df["Required_Temp_Min_C"] - df["Recorded_Min_Temp_C"]).clip(lower=0)
    excursion_above = (df["Recorded_Max_Temp_C"] - df["Required_Temp_Max_C"]).clip(lower=0)
    df["Excursion_Magnitude_C"] = pd.concat([excursion_below, excursion_above], axis=1).max(axis=1)
    df["Temp_Excursion"] = df["Excursion_Magnitude_C"] > 0

    temp_score = (df["Excursion_Magnitude_C"] * 10).clip(upper=50)
    delay_score = (df["Delay_Hours"] / 2).clip(upper=25)
    handling_score = (df["Handling_Incidents"] * 5).clip(upper=15)
    value_score = (df["Shipment_Value_USD"] / 50_000 * 10).clip(upper=10)

    df["Risk_Score"] = (temp_score + delay_score + handling_score + value_score).clip(upper=100).round(1)

    df["Risk_Tier"] = pd.cut(
        df["Risk_Score"],
        bins=[-1, MEDIUM_RISK_THRESHOLD, HIGH_RISK_THRESHOLD, 101],
        labels=["Low", "Medium", "High"],
    )

    return df


def build_recommendations(df: pd.DataFrame) -> list[str]:
    total = len(df)
    high_risk = df[df["Risk_Tier"] == "High"]
    excursions = df[df["Temp_Excursion"]]
    recs = []

    if len(excursions) > 0:
        top_carrier = excursions["Carrier"].value_counts().idxmax()
        pct = len(excursions) / total * 100
        recs.append(
            f"{len(excursions)} shipments ({pct:.0f}%) recorded a temperature excursion — "
            f"prioritize a cold-chain audit for **{top_carrier}**, the carrier most represented "
            f"among excursions."
        )

    delayed = df[df["Delay_Hours"] > 24]
    if len(delayed) > 0:
        recs.append(
            f"{len(delayed)} shipments arrived more than 24 hours late. Review transit routing "
            f"and carrier SLAs for repeat offenders before the next contract cycle."
        )

    incident_shipments = df[df["Handling_Incidents"] >= 2]
    if len(incident_shipments) > 0:
        recs.append(
            f"{len(incident_shipments)} shipments logged 2+ handling incidents. "
            f"Inspect packaging and handling procedures for these lanes."
        )

    if len(high_risk) > 0:
        recs.append(
            f"{len(high_risk)} shipments are High risk overall — inspect these first; "
            f"see the table above for the top 5 by score."
        )

    if not recs:
        recs.append("No major risk signals detected in this batch — shipments are broadly within cold-chain and schedule tolerances.")

    return recs
