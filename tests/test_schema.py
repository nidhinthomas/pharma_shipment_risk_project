import pandas as pd

from pharma_risk.schema import REQUIRED_COLUMNS, validate_columns


def test_validate_columns_no_missing(valid_shipments_df):
    assert validate_columns(valid_shipments_df) == []


def test_validate_columns_reports_missing_in_schema_order(missing_columns_df):
    assert validate_columns(missing_columns_df) == ["Carrier", "Shipment_Value_USD"]


def test_validate_columns_all_missing_on_empty_frame():
    assert validate_columns(pd.DataFrame()) == REQUIRED_COLUMNS
