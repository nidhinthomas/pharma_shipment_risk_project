"""Generates sample_data.xlsx: a synthetic pharma shipment dataset for demo purposes.

Run: python generate_sample_data.py
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

N = 50

PRODUCTS = [
    ("Vaxinol Vaccine", -20, -15),
    ("BioTherra Biologic", 2, 8),
    ("InsuMax Insulin", 2, 8),
    ("Cardiozen Injectable", 2, 8),
    ("Panacure Oral Tablets", 15, 25),
    ("Allerclear Oral Solid", 15, 25),
    ("DiagnoStrip Reagent", 2, 8),
    ("Oncofirm Biologic", -20, -15),
]

CITIES = [
    "Mumbai", "Hyderabad", "Frankfurt", "Basel", "Singapore",
    "Chicago", "Sao Paulo", "Nairobi", "Dublin", "Bangkok",
]

CARRIERS = ["ColdLink Air", "MedFreight Global", "PharmaExpress", "BioTrans Logistics", "RapidRx Cargo"]

rows = []
for i in range(1, N + 1):
    product, req_min, req_max = PRODUCTS[rng.integers(0, len(PRODUCTS))]
    origin, dest = rng.choice(CITIES, size=2, replace=False)
    carrier = CARRIERS[rng.integers(0, len(CARRIERS))]

    ship_date = pd.Timestamp("2026-06-01") + pd.Timedelta(days=int(rng.integers(0, 90)))
    transit_days = int(rng.integers(1, 6))
    expected_delivery = ship_date + pd.Timedelta(days=transit_days)

    # Most shipments arrive on time or slightly late; a minority are badly delayed.
    delay_hours = max(0, rng.normal(loc=4, scale=10))
    if rng.random() < 0.12:
        delay_hours += rng.uniform(24, 72)
    actual_delivery = expected_delivery + pd.Timedelta(hours=float(delay_hours))

    # Most shipments stay within range; a minority excurse outside it.
    excursion_roll = rng.random()
    if excursion_roll < 0.18:
        drift = rng.uniform(2, 9)
        recorded_min = req_min - drift if rng.random() < 0.5 else req_min + rng.uniform(0.5, 2)
        recorded_max = req_max + drift if rng.random() < 0.5 else req_max - rng.uniform(0.5, 2)
    else:
        recorded_min = req_min + rng.uniform(0.2, 2.5)
        recorded_max = req_max - rng.uniform(0.2, 2.5)
    recorded_min, recorded_max = min(recorded_min, recorded_max), max(recorded_min, recorded_max)

    handling_incidents = int(rng.choice([0, 0, 0, 1, 1, 2, 3], p=[0.45, 0.15, 0.1, 0.13, 0.07, 0.06, 0.04]))
    shipment_value = int(rng.uniform(5_000, 250_000))

    rows.append({
        "Shipment_ID": f"SHP-{i:04d}",
        "Product_Name": product,
        "Origin": origin,
        "Destination": dest,
        "Carrier": carrier,
        "Ship_Date": ship_date.date(),
        "Expected_Delivery_Date": expected_delivery.date(),
        "Actual_Delivery_Date": actual_delivery.date(),
        "Required_Temp_Min_C": req_min,
        "Required_Temp_Max_C": req_max,
        "Recorded_Min_Temp_C": round(recorded_min, 1),
        "Recorded_Max_Temp_C": round(recorded_max, 1),
        "Delay_Hours": round(delay_hours, 1),
        "Handling_Incidents": handling_incidents,
        "Shipment_Value_USD": shipment_value,
    })

df = pd.DataFrame(rows)
df.to_excel("sample_data.xlsx", index=False)
print(f"Wrote sample_data.xlsx with {len(df)} shipments.")
