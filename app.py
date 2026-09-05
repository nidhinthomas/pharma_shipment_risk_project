import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from risk_logic import (
    HIGH_RISK_THRESHOLD,
    TIER_COLORS,
    TIER_ORDER,
    build_recommendations,
    compute_risk,
    validate_columns,
)

st.set_page_config(page_title="Pharma Shipment Risk Analyzer", page_icon="🌡️", layout="wide")

st.title("🌡️ Pharma Shipment Risk Analyzer")
st.caption("Upload a shipment Excel file to flag cold-chain and delivery risk.")

uploaded_file = st.file_uploader("Upload shipment Excel file (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    raw_df = pd.read_excel(uploaded_file)
    source_label = uploaded_file.name
else:
    raw_df = pd.read_excel("sample_data.xlsx")
    source_label = "sample_data.xlsx (bundled demo data — upload your own file above)"

st.info(f"Using: **{source_label}**")

missing = validate_columns(raw_df)
if missing:
    st.error(
        "The uploaded file is missing required columns: "
        + ", ".join(f"`{c}`" for c in missing)
    )
    st.stop()

df = compute_risk(raw_df)

total_shipments = len(df)
high_risk_count = int((df["Risk_Tier"] == "High").sum())
excursion_count = int(df["Temp_Excursion"].sum())

col1, col2, col3 = st.columns(3)
col1.metric("Total Shipments", total_shipments)
col2.metric("High-Risk Shipments", high_risk_count, help=f"Risk score >= {HIGH_RISK_THRESHOLD}")
col3.metric("Temperature Excursions", excursion_count, help="Recorded temp outside required range")

st.subheader("Top 5 Highest-Risk Shipments")
top5 = df.sort_values("Risk_Score", ascending=False).head(5)
st.dataframe(
    top5[[
        "Shipment_ID", "Product_Name", "Carrier", "Risk_Score", "Risk_Tier",
        "Temp_Excursion", "Delay_Hours", "Handling_Incidents",
    ]],
    hide_index=True,
    use_container_width=True,
)

st.subheader("Risk Distribution")
tier_counts = df["Risk_Tier"].value_counts().reindex(TIER_ORDER, fill_value=0)

fig = go.Figure(
    go.Bar(
        x=tier_counts.index,
        y=tier_counts.values,
        marker_color=[TIER_COLORS[t] for t in tier_counts.index],
        text=tier_counts.values,
        textposition="outside",
        hovertemplate="%{x} risk: %{y} shipments<extra></extra>",
    )
)
fig.update_layout(
    xaxis_title="Risk Tier",
    yaxis_title="Number of Shipments",
    showlegend=False,
    plot_bgcolor="#fcfcfb",
    paper_bgcolor="#fcfcfb",
    yaxis=dict(gridcolor="#e1e0d9", zeroline=False),
    margin=dict(t=20, b=20),
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Recommendations")
for rec in build_recommendations(df):
    st.markdown(f"- {rec}")

with st.expander("View full shipment data with computed risk fields"):
    st.dataframe(df, hide_index=True, use_container_width=True)
