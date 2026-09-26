"""Deterministic, templated recommendation text derived from scored shipments.

Not a live model call by design — see CLAUDE.md Constraints.
"""
import pandas as pd


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
