# Pharma Shipment Risk Analyzer

Streamlit app that scores uploaded pharma shipment data for cold-chain and
delivery risk. The `pharma_risk/` package carries all UI-agnostic logic;
`app.py` is the Streamlit UI and only calls into it; `generate_sample_data.py`
produces the bundled demo dataset.

### Module map (`pharma_risk/`)

- `schema.py` — `REQUIRED_COLUMNS`, `validate_columns`
- `scoring.py` — thresholds, tier colors/order, `compute_risk` — **the single
  source of truth for the risk formula**
- `recommendations.py` — `build_recommendations`
- `data_loading.py` — `load_shipment_data` / `ShipmentDataError`; the one
  module with error handling (wraps `pd.read_excel` for malformed uploads)

## Commands

- Run the app: `streamlit run app.py`
- Regenerate the demo dataset: `python generate_sample_data.py` (writes
  `sample_data.xlsx`, seeded with `np.random.default_rng(42)` — don't hand-edit
  the xlsx, edit the generator and re-run instead)
- Run tests: `pytest` (or `python -m pytest`) from the repo root — no install
  step needed (root `conftest.py` puts the repo root on `sys.path`). Coverage
  includes missing required columns, an empty upload (0 rows), non-numeric
  temperature values, and a large file (1000+ rows) for basic performance
  sanity.

## Risk-scoring rules — the single source of truth is `pharma_risk/scoring.py`

**IMPORTANT: never reimplement or duplicate this formula elsewhere (e.g. inline
in `app.py`).** If thresholds change, change them only in `pharma_risk/scoring.py`.

`Risk_Score` (0-100) sums four capped components:
- Temperature excursion: 10 pts per °C outside the required range, capped 50
- Delivery delay: 1 pt per 2 hours late, capped 25
- Handling incidents: 5 pts per incident, capped 15
- Shipment value exposure: scales to 10 at $50,000+, capped 10

Tiers use a right-closed `pd.cut`, so the boundary score itself falls into the
**lower** tier: High is score > 60, Medium is 30 < score <= 60, Low is
score <= 30 (`HIGH_RISK_THRESHOLD` / `MEDIUM_RISK_THRESHOLD` in
`pharma_risk/scoring.py`). "Temperature excursion" is a separate boolean flag
(recorded min/max temp outside the required range) and is reported
independently of risk tier — a shipment can excurse without being High risk
overall, and vice versa (e.g. a large delay alone can push it High).

These thresholds are illustrative defaults for a demo, not a validated clinical
or regulatory standard — say so if asked to justify them, don't invent a
citation.

## Data contract

Uploaded `.xlsx` files must contain the exact columns listed in
`pharma_risk.schema.REQUIRED_COLUMNS` (case-sensitive). `app.py` already
validates this and shows a Streamlit error listing missing columns — don't add
a second validation path. `Delay_Hours` is computed from the delivery date
columns if not already present in the upload.

## Constraints

- This app is a training/demo artifact. All bundled data is synthetic
  (`generate_sample_data.py`). Never present its output as real shipment,
  patient, or regulatory data.
- The "Recommendations" section is deterministic templated text
  (`build_recommendations` in `pharma_risk/recommendations.py`), not a live
  model call — keep it that way unless the user explicitly asks to wire in an
  LLM call, since that adds an API-key dependency this demo intentionally
  avoids.
