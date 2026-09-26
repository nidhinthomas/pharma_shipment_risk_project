from io import BytesIO

import pandas as pd
import pytest

from pharma_risk.data_loading import ShipmentDataError, load_shipment_data


def test_load_shipment_data_from_valid_in_memory_xlsx():
    buffer = BytesIO()
    pd.DataFrame({"a": [1, 2], "b": [3, 4]}).to_excel(buffer, index=False)
    buffer.seek(0)

    result = load_shipment_data(buffer)

    assert list(result.columns) == ["a", "b"]
    assert len(result) == 2


def test_load_shipment_data_on_garbage_bytes_raises_with_cause():
    buffer = BytesIO(b"this is not a valid xlsx file")

    with pytest.raises(ShipmentDataError) as exc_info:
        load_shipment_data(buffer)

    assert exc_info.value.__cause__ is not None
