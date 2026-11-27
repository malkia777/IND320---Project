import pandas as pd
import streamlit as st
from urllib.parse import quote
from data_loader import load_data


# Keep the olive cursor.
olive_svg = """
<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"
     viewBox="0 0 32 32">
    <path d="M19 12 Q22 7 27 5"
          fill="none" stroke="#374526" stroke-width="2"/>
    <ellipse cx="24" cy="7" rx="6" ry="3"
             fill="#73834D" transform="rotate(-30 24 7)"/>
    <ellipse cx="14" cy="20" rx="10" ry="12"
             fill="#52683D" transform="rotate(30 14 20)"/>
    <ellipse cx="11" cy="16" rx="3" ry="5"
             fill="#91A46C" transform="rotate(30 11 16)"/>
</svg>
"""

cursor = f'url("data:image/svg+xml,{quote(olive_svg)}") 16 16, auto'


st.markdown(
    f"""
    <style>
    /* White middle section with black text. */
    .stApp {{
        background-color: #FFFFFF;
        color: #000000;
    }}

    /* Red sidebar with black navigation text. */
    [data-testid="stSidebar"] {{
        background-color: #CE1126;
        color: #000000;
    }}

    [data-testid="stSidebarNav"] a,
    [data-testid="stSidebarNav"] a span,
    [data-testid="stSidebarNav"] p {{
        color: #000000 !important;
    }}

    /* Boxy font instead of cursive. */
    h1, h2, h3, h4, h5, h6,
    p, a, label, button, input,
    [data-testid="stCaptionContainer"],
    [data-testid="stWidgetLabel"] {{
        font-family: "Courier New", monospace !important;
        color: #000000 !important;
    }}

    /* Black upper bar with white text and icons. */
    [data-testid="stHeader"] {{
        background-color: #000000;
    }}

    [data-testid="stHeader"] * {{
        color: #FFFFFF !important;
    }}

    /* Leave room below the upper bar. */
    .block-container {{
        padding-top: 5rem;
    }}

    /* Green lower section with black text. */
    .flag-footer {{
        background-color: #00843D;
        color: #000000;
        font-family: "Courier New", monospace;
        padding: 24px;
        margin-top: 40px;
        text-align: center;
        font-weight: bold;
    }}

    /* Olive cursor throughout the page. */
    *, *::before, *::after {{
        cursor: {cursor} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("Reservoir data table")
st.write("Explore weekly reservoir measurements using the sparklines below.")

with st.spinner("Loading reservoir data…"):
    df = load_data()

# Select the area type.
area_type = st.radio(
    "Area type",
    ["EL", "NO", "VASS"],
    horizontal=True,
)

area = df[df["Area_type"] == area_type].sort_values("Date")

# Keep the first available month, as in your original page.
month_start = area["Date"].min().to_period("M").start_time
month_end = month_start + pd.DateOffset(months=1)

first_month = area[
    (area["Date"] >= month_start)
    & (area["Date"] < month_end)
]

measurements = [
    "Filling_level",
    "Capacity_TWh",
    "Filling_TWh",
    "Filling_level_prev_week",
    "Change_filling_level",
]

# Each area number gets one row containing weekly values.
table = (
    first_month.groupby("Area_number")[measurements]
    .agg(list)
    .reset_index()
)

st.write(f"Showing {area_type}, {month_start:%Y-%m}")

# Green sparklines to match the Palestinian colour theme.
st.dataframe(
    table,
    column_config={
        column: st.column_config.LineChartColumn(
            column,
            color="#00843D",
        )
        for column in measurements
    },
    hide_index=True,
    width="stretch",
)

# Green bottom section.
st.markdown(
    """
    <div class="flag-footer">
        IND320 · Reservoir measurements · NVE Magasinstatistikk
    </div>
    """,
    unsafe_allow_html=True,
)