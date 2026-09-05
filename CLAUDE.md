# Pharma Shipment Risk Analyzer

Streamlit app that scores uploaded pharma shipment data for cold-chain and
delivery risk. Three files carry all the logic: `risk_logic.py` (scoring rules,
UI-agnostic), `app.py` (Streamlit UI, calls into `risk_logic.py`),
`generate_sample_data.py` (produces the bundled demo dataset).

## Commands

- Run the app: `streamlit run app.py`
- Regenerate the demo dataset: `python generate_sample_data.py` (writes
  `sample_data.xlsx`, seeded with `np.random.default_rng(42)` — don't hand-edit
  the xlsx, edit the generator and re-run instead)
- No test suite exists yet. If you add one, put risk-scoring assertions in a
  standalone `test_risk_logic.py` — that module has no Streamlit dependency, so
  it doesn't need `streamlit run` or a browser to test. Cover at least: missing
  required columns, an empty upload (0 rows), non-numeric temperature values,
  and a large file (1000+ rows) for basic performance sanity.

## Risk-scoring rules — the single source of truth is `risk_logic.py`

**IMPORTANT: never reimplement or duplicate this formula elsewhere (e.g. inline
in `app.py`).** If thresholds change, change them only in `risk_logic.py`.

`Risk_Score` (0-100) sums four capped components:
- Temperature excursion: 10 pts per °C outside the required range, capped 50
- Delivery delay: 1 pt per 2 hours late, capped 25
- Handling incidents: 5 pts per incident, capped 15
- Shipment value exposure: scales to 10 at $50,000+, capped 10

Tiers: High >= 60, Medium 30-59, Low < 30 (`HIGH_RISK_THRESHOLD` /
`MEDIUM_RISK_THRESHOLD` in `risk_logic.py`). "Temperature excursion" is a
separate boolean flag (recorded min/max temp outside the required range) and is
reported independently of risk tier — a shipment can excurse without being
High risk overall, and vice versa (e.g. a large delay alone can push it High).

These thresholds are illustrative defaults for a demo, not a validated clinical
or regulatory standard — say so if asked to justify them, don't invent a
citation.

## Data contract

Uploaded `.xlsx` files must contain the exact columns listed in
`risk_logic.REQUIRED_COLUMNS` (case-sensitive). `app.py` already validates this
and shows a Streamlit error listing missing columns — don't add a second
validation path. `Delay_Hours` is computed from the delivery date columns if
not already present in the upload.

## Constraints

- This app is a training/demo artifact. All bundled data is synthetic
  (`generate_sample_data.py`). Never present its output as real shipment,
  patient, or regulatory data.
- The "Recommendations" section is deterministic templated text
  (`build_recommendations` in `risk_logic.py`), not a live model call — keep it
  that way unless the user explicitly asks to wire in an LLM call, since that
  adds an API-key dependency this demo intentionally avoids.
