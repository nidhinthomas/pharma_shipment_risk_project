import time

import pandas as pd
import pytest

from pharma_risk.scoring import compute_risk


def _df(*rows):
    return pd.DataFrame(list(rows))


# --- Tier boundary pins (right-closed pd.cut: boundary score falls in the LOWER tier) ---

def test_score_60_is_medium_not_high(shipment_row_factory):
    row = shipment_row_factory(
        Recorded_Max_Temp_C=13,  # 5C excess -> temp_score 50 (at cap)
        Expected_Delivery_Date="2026-01-01T00:00:00",
        Actual_Delivery_Date="2026-01-01T20:00:00",  # 20h -> delay_score 10
        Shipment_Value_USD=0,
    )
    result = compute_risk(_df(row))
    assert result["Risk_Score"].iloc[0] == 60.0
    assert result["Risk_Tier"].iloc[0] == "Medium"


def test_score_60_1_is_high(shipment_row_factory):
    row = shipment_row_factory(
        Recorded_Max_Temp_C=13,  # temp_score 50
        Expected_Delivery_Date="2026-01-01T00:00:00",
        Actual_Delivery_Date="2026-01-01T20:00:00",  # delay_score 10
        Shipment_Value_USD=500,  # value_score 0.1
    )
    result = compute_risk(_df(row))
    assert result["Risk_Score"].iloc[0] == 60.1
    assert result["Risk_Tier"].iloc[0] == "High"


def test_score_30_is_low_not_medium(shipment_row_factory):
    row = shipment_row_factory(
        Recorded_Max_Temp_C=11,  # 3C excess -> temp_score 30
        Shipment_Value_USD=0,
    )
    result = compute_risk(_df(row))
    assert result["Risk_Score"].iloc[0] == 30.0
    assert result["Risk_Tier"].iloc[0] == "Low"


def test_score_30_1_is_medium(shipment_row_factory):
    row = shipment_row_factory(
        Recorded_Max_Temp_C=11,  # temp_score 30
        Shipment_Value_USD=500,  # value_score 0.1
    )
    result = compute_risk(_df(row))
    assert result["Risk_Score"].iloc[0] == 30.1
    assert result["Risk_Tier"].iloc[0] == "Medium"


# --- Per-component caps ---

def test_temperature_component_caps_at_50(shipment_row_factory):
    row = shipment_row_factory(Recorded_Max_Temp_C=1000, Shipment_Value_USD=0)  # 992C excess
    result = compute_risk(_df(row))
    assert result["Risk_Score"].iloc[0] == 50.0


def test_delay_component_caps_at_25(shipment_row_factory):
    row = shipment_row_factory(
        Expected_Delivery_Date="2026-01-01", Actual_Delivery_Date="2026-01-22",  # 504h
        Shipment_Value_USD=0,
    )
    result = compute_risk(_df(row))
    assert result["Risk_Score"].iloc[0] == 25.0


def test_handling_component_caps_at_15(shipment_row_factory):
    row = shipment_row_factory(Handling_Incidents=10, Shipment_Value_USD=0)
    result = compute_risk(_df(row))
    assert result["Risk_Score"].iloc[0] == 15.0


def test_value_component_caps_at_10(shipment_row_factory):
    row = shipment_row_factory(Shipment_Value_USD=5_000_000)
    result = compute_risk(_df(row))
    assert result["Risk_Score"].iloc[0] == 10.0


def test_all_components_maxed_caps_total_at_100(shipment_row_factory):
    row = shipment_row_factory(
        Recorded_Max_Temp_C=1000,
        Expected_Delivery_Date="2026-01-01", Actual_Delivery_Date="2026-01-22",
        Handling_Incidents=100,
        Shipment_Value_USD=10_000_000,
    )
    result = compute_risk(_df(row))
    assert result["Risk_Score"].iloc[0] == 100.0
    assert result["Risk_Tier"].iloc[0] == "High"


# --- Excursion direction ---

def test_excursion_below_range_only(shipment_row_factory):
    row = shipment_row_factory(Recorded_Min_Temp_C=-1)  # Required min is 2 -> 3C below
    result = compute_risk(_df(row))
    assert result["Excursion_Magnitude_C"].iloc[0] == 3
    assert bool(result["Temp_Excursion"].iloc[0]) is True


def test_excursion_above_range_only(shipment_row_factory):
    row = shipment_row_factory(Recorded_Max_Temp_C=10)  # Required max is 8 -> 2C above
    result = compute_risk(_df(row))
    assert result["Excursion_Magnitude_C"].iloc[0] == 2
    assert bool(result["Temp_Excursion"].iloc[0]) is True


def test_excursion_both_directions_takes_max_not_sum(shipment_row_factory):
    row = shipment_row_factory(Recorded_Min_Temp_C=-1, Recorded_Max_Temp_C=10)  # 3C below, 2C above
    result = compute_risk(_df(row))
    assert result["Excursion_Magnitude_C"].iloc[0] == 3


def test_recorded_exactly_at_bounds_is_not_an_excursion(shipment_row_factory):
    row = shipment_row_factory(Recorded_Min_Temp_C=2, Recorded_Max_Temp_C=8)
    result = compute_risk(_df(row))
    assert result["Excursion_Magnitude_C"].iloc[0] == 0
    assert bool(result["Temp_Excursion"].iloc[0]) is False


# --- Delay_Hours ---

def test_delay_hours_computed_from_dates_when_absent(shipment_row_factory):
    row = shipment_row_factory(
        Expected_Delivery_Date="2026-01-01T00:00:00", Actual_Delivery_Date="2026-01-01T10:00:00",
    )
    result = compute_risk(_df(row))
    assert result["Delay_Hours"].iloc[0] == 10.0


def test_delay_hours_preserved_when_already_present(shipment_row_factory):
    row = shipment_row_factory(
        Expected_Delivery_Date="2026-01-01T00:00:00", Actual_Delivery_Date="2026-01-01T10:00:00",
        Delay_Hours=999,
    )
    result = compute_risk(_df(row))
    assert result["Delay_Hours"].iloc[0] == 999


def test_early_arrival_clips_delay_to_zero(shipment_row_factory):
    row = shipment_row_factory(
        Expected_Delivery_Date="2026-01-02T00:00:00", Actual_Delivery_Date="2026-01-01T00:00:00",
    )
    result = compute_risk(_df(row))
    assert result["Delay_Hours"].iloc[0] == 0.0


# --- Data-quality edge cases ---

def test_non_numeric_temperature_raises_type_error(non_numeric_temp_df):
    with pytest.raises(TypeError):
        compute_risk(non_numeric_temp_df)


def test_empty_dataframe_returns_zero_rows_with_expected_columns(empty_shipments_df):
    result = compute_risk(empty_shipments_df)
    assert len(result) == 0
    for col in ["Delay_Hours", "Excursion_Magnitude_C", "Temp_Excursion", "Risk_Score", "Risk_Tier"]:
        assert col in result.columns


def test_large_dataframe_completes_quickly(large_shipments_df):
    start = time.monotonic()
    result = compute_risk(large_shipments_df)
    elapsed = time.monotonic() - start
    assert len(result) == len(large_shipments_df)
    assert elapsed < 5.0


# --- Golden values (hand-computed, not re-derived from the formula) ---

def test_golden_values(shipment_row_factory):
    low_row = shipment_row_factory(  # no excursion/delay/incidents; value_score 0.2
        Shipment_ID="LOW", Shipment_Value_USD=1000,
        Expected_Delivery_Date="2026-01-01T00:00:00", Actual_Delivery_Date="2026-01-01T00:00:00",
    )
    medium_row = shipment_row_factory(  # temp 20 + delay 5 + handling 5 + value 4 = 34.0
        Shipment_ID="MED",
        Recorded_Max_Temp_C=10,
        Expected_Delivery_Date="2026-01-01T00:00:00", Actual_Delivery_Date="2026-01-01T10:00:00",
        Handling_Incidents=1,
        Shipment_Value_USD=20_000,
    )
    high_row = shipment_row_factory(  # temp 50(capped) + delay 25(capped) + handling 15(capped) + value 10(capped) = 100.0
        Shipment_ID="HIGH",
        Recorded_Max_Temp_C=16,
        Expected_Delivery_Date="2026-01-01T00:00:00", Actual_Delivery_Date="2026-01-05T04:00:00",
        Handling_Incidents=5,
        Shipment_Value_USD=1_000_000,
    )

    result = compute_risk(_df(low_row, medium_row, high_row)).set_index("Shipment_ID")

    assert result.loc["LOW", "Risk_Score"] == 0.2
    assert result.loc["LOW", "Risk_Tier"] == "Low"

    assert result.loc["MED", "Risk_Score"] == 34.0
    assert result.loc["MED", "Risk_Tier"] == "Medium"

    assert result.loc["HIGH", "Risk_Score"] == 100.0
    assert result.loc["HIGH", "Risk_Tier"] == "High"
