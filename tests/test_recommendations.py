import pandas as pd

from pharma_risk.recommendations import build_recommendations
from pharma_risk.scoring import compute_risk


def _scored(*rows):
    return compute_risk(pd.DataFrame(list(rows)))


def test_fallback_message_when_no_signals(shipment_row_factory):
    df = _scored(shipment_row_factory())
    recs = build_recommendations(df)
    assert len(recs) == 1
    assert "No major risk signals" in recs[0]


def test_excursion_message_names_carrier_with_most_excursions(shipment_row_factory):
    df = _scored(
        shipment_row_factory(Shipment_ID="1", Carrier="Carrier-X", Recorded_Max_Temp_C=10),
        shipment_row_factory(Shipment_ID="2", Carrier="Carrier-X", Recorded_Max_Temp_C=10),
        shipment_row_factory(Shipment_ID="3", Carrier="Carrier-X", Recorded_Max_Temp_C=10),
        shipment_row_factory(Shipment_ID="4", Carrier="Carrier-Y", Recorded_Max_Temp_C=10),
        shipment_row_factory(Shipment_ID="5", Carrier="Carrier-Z"),  # no excursion
    )
    recs = build_recommendations(df)
    assert any("Carrier-X" in r and "4 shipments" in r for r in recs)


def test_delay_exactly_24h_not_flagged(shipment_row_factory):
    df = _scored(shipment_row_factory(
        Expected_Delivery_Date="2026-01-01T00:00:00", Actual_Delivery_Date="2026-01-02T00:00:00",
    ))
    recs = build_recommendations(df)
    assert not any("hours late" in r for r in recs)


def test_delay_24_1h_flagged(shipment_row_factory):
    df = _scored(shipment_row_factory(
        Expected_Delivery_Date="2026-01-01T00:00:00", Actual_Delivery_Date="2026-01-02T00:06:00",
    ))
    recs = build_recommendations(df)
    assert any("1 shipments" in r and "hours late" in r for r in recs)


def test_one_handling_incident_not_flagged(shipment_row_factory):
    df = _scored(shipment_row_factory(Handling_Incidents=1))
    recs = build_recommendations(df)
    assert not any("handling incidents" in r for r in recs)


def test_two_handling_incidents_flagged(shipment_row_factory):
    df = _scored(shipment_row_factory(Handling_Incidents=2))
    recs = build_recommendations(df)
    assert any("1 shipments logged 2+ handling incidents" in r for r in recs)


def test_high_risk_count_matches(shipment_row_factory):
    df = _scored(
        shipment_row_factory(Shipment_ID="1", Handling_Incidents=10),  # score 15, not High
        shipment_row_factory(
            Shipment_ID="2", Recorded_Max_Temp_C=1000, Handling_Incidents=10,
            Shipment_Value_USD=5_000_000,
        ),  # capped components sum well above 60 -> High
    )
    high_risk_count = int((df["Risk_Tier"] == "High").sum())
    recs = build_recommendations(df)
    assert any(f"{high_risk_count} shipments are High risk overall" in r for r in recs)


def test_build_recommendations_is_deterministic(shipment_row_factory):
    df = _scored(
        shipment_row_factory(Shipment_ID="1", Recorded_Max_Temp_C=10),
        shipment_row_factory(Shipment_ID="2", Handling_Incidents=3),
    )
    assert build_recommendations(df) == build_recommendations(df)
