"""Required-column data contract for uploaded shipment files."""
import pandas as pd

REQUIRED_COLUMNS = [
    "Shipment_ID", "Product_Name", "Origin", "Destination", "Carrier",
    "Expected_Delivery_Date", "Actual_Delivery_Date",
    "Required_Temp_Min_C", "Required_Temp_Max_C",
    "Recorded_Min_Temp_C", "Recorded_Max_Temp_C",
    "Handling_Incidents", "Shipment_Value_USD",
]


def validate_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in REQUIRED_COLUMNS if c not in df.columns]
