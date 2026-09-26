import pandas as pd
import pytest

from pharma_risk.schema import REQUIRED_COLUMNS


def make_shipment_row(**overrides) -> dict:
    """A single valid shipment row with no excursion, delay, or incidents."""
    row = {
        "Shipment_ID": "SHP-0001",
        "Product_Name": "Test Product",
        "Origin": "CityA",
        "Destination": "CityB",
        "Carrier": "TestCarrier",
        "Expected_Delivery_Date": "2026-01-01",
        "Actual_Delivery_Date": "2026-01-01",
        "Required_Temp_Min_C": 2,
        "Required_Temp_Max_C": 8,
        "Recorded_Min_Temp_C": 3,
        "Recorded_Max_Temp_C": 7,
        "Handling_Incidents": 0,
        "Shipment_Value_USD": 1000,
    }
    row.update(overrides)
    return row


@pytest.fixture
def shipment_row_factory():
    return make_shipment_row


@pytest.fixture
def valid_shipments_df() -> pd.DataFrame:
    rows = [
        make_shipment_row(Shipment_ID="SHP-0001", Carrier="Carrier-A"),
        make_shipment_row(
            Shipment_ID="SHP-0002", Carrier="Carrier-B",
            Recorded_Max_Temp_C=13,  # 5C above the required max -> excursion
        ),
        make_shipment_row(
            Shipment_ID="SHP-0003", Carrier="Carrier-B",
            Recorded_Min_Temp_C=-2,  # below the required min -> excursion
        ),
        make_shipment_row(
            Shipment_ID="SHP-0004", Carrier="Carrier-C",
            Expected_Delivery_Date="2026-01-01", Actual_Delivery_Date="2026-01-03",
        ),
        make_shipment_row(
            Shipment_ID="SHP-0005", Carrier="Carrier-D",
            Handling_Incidents=3,
        ),
        make_shipment_row(
            Shipment_ID="SHP-0006", Carrier="Carrier-E",
            Shipment_Value_USD=60_000,
        ),
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def missing_columns_df(valid_shipments_df) -> pd.DataFrame:
    return valid_shipments_df.drop(columns=["Carrier", "Shipment_Value_USD"])


@pytest.fixture
def empty_shipments_df() -> pd.DataFrame:
    dtypes = {
        "Shipment_ID": "object",
        "Product_Name": "object",
        "Origin": "object",
        "Destination": "object",
        "Carrier": "object",
        "Expected_Delivery_Date": "datetime64[ns]",
        "Actual_Delivery_Date": "datetime64[ns]",
        "Required_Temp_Min_C": "float64",
        "Required_Temp_Max_C": "float64",
        "Recorded_Min_Temp_C": "float64",
        "Recorded_Max_Temp_C": "float64",
        "Handling_Incidents": "float64",
        "Shipment_Value_USD": "float64",
    }
    assert set(dtypes) == set(REQUIRED_COLUMNS)
    return pd.DataFrame({col: pd.Series(dtype=dtype) for col, dtype in dtypes.items()})


@pytest.fixture
def non_numeric_temp_df() -> pd.DataFrame:
    return pd.DataFrame([make_shipment_row(Recorded_Max_Temp_C="N/A")])


@pytest.fixture
def large_shipments_df() -> pd.DataFrame:
    import random

    rng = random.Random(42)
    rows = []
    for i in range(1200):
        rows.append(make_shipment_row(
            Shipment_ID=f"SHP-{i:05d}",
            Carrier=rng.choice(["Carrier-A", "Carrier-B", "Carrier-C"]),
            Recorded_Min_Temp_C=rng.uniform(-1, 4),
            Recorded_Max_Temp_C=rng.uniform(6, 11),
            Handling_Incidents=rng.choice([0, 0, 1, 2]),
            Shipment_Value_USD=rng.uniform(1_000, 100_000),
        ))
    return pd.DataFrame(rows)
