"""Excel-parsing boundary for uploaded and bundled shipment files."""
import pandas as pd


class ShipmentDataError(Exception):
    """Raised when a shipment file can't be parsed as Excel."""


def load_shipment_data(source) -> pd.DataFrame:
    try:
        return pd.read_excel(source)
    except Exception as exc:
        raise ShipmentDataError(f"Could not read the Excel file: {exc}") from exc
