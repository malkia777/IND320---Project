import pandas as pd
import streamlit as st
import plotly.express as px
from urllib.parse import quote
from data_loader import load_data


# Olive mouse cursor.
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


# Cross-stitch-style geometric motif inspired by tatreez.
tatreez_svg = """
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="96"
     viewBox="0 0 48 96">
    <g stroke="#000000" stroke-width="2" fill="none">
        <path d="M20 8l8 8m0-8l-8 8
                 M12 16l8 8m0-8l-8 8
                 M28 16l8 8m0-8l-8 8
                 M4 24l8 8m0-8l-8 8
                 M20 24l8 8m0-8l-8 8
                 M36 24l8 8m0-8l-8 8
                 M12 32l8 8m0-8l-8 8
                 M28 32l8 8m0-8l-8 8
                 M20 40l8 8m0-8l-8 8"/>
        <path d="M20 64l8 8m0-8l-8 8
                 M12 72l8 8m0-8l-8 8
                 M28 72l8 8m0-8l-8 8
                 M20 80l8 8m0-8l-8 8"/>
    </g>
</svg>
"""

pattern = f'url("data:image/svg+xml,{quote(tatreez_svg)}")'


st.markdown(
    f"""
    <style>
    /* Black main background. */
    .stApp,
    [data-testid="stHeader"] {{
        background-color: #000000;
        color: #FFFFFF;
    }}

    .block-container {{
        padding-top: 5rem;
    }}

    /* Blocky lettering to suggest an embroidery style. */
    h1, h2, h3, h4, h5, h6,
    p, a, label, button,
    [data-testid="stCaptionContainer"],
    [data-testid="stWidgetLabel"] {{
        font-family: "Courier New", monospace !important;
        color: #FFFFFF !important;
    }}

    h1 {{
        font-weight: bold;
        letter-spacing: 2px;
        border-bottom: 2px solid #781F36;
        padding-bottom: 18px;
    }}

    /* Burgundy sidebar with black motifs along the edges. */
    [data-testid="stSidebar"] {{
        background-color: #781F36;
        background-image: {pattern}, {pattern};
        background-repeat: repeat-y, repeat-y;
        background-position: left top, right top;
        background-size: 32px 64px;
    }}

    /* Keep navigation clear of the patterned edges. */
    [data-testid="stSidebarNav"] {{
        margin-left: 24px;
        margin-right: 24px;
        background-color: #781F36;
    }}

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] button,
    [data-testid="stSidebarNav"] a span {{
        color: #000000 !important;
        font-weight: bold;
    }}

    /* Dark selection box with white text. */
    [data-baseweb="select"] > div {{
        background-color: #181818;
        color: #FFFFFF;
        font-family: "Courier New", monospace;
    }}

    [data-baseweb="select"] input {{
        color: #FFFFFF !important;
    }}

    /* Olive cursor. */
    *, *::before, *::after {{
        cursor: {cursor} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("Plots of the data")

with st.spinner("Loading reservoir data…"):
    df = load_data()
    
# Select the area type.
area_type = st.radio(
    "Area type",
    ["EL", "NO", "VASS"],
    horizontal=True,
)

area = df[df["Area_type"] == area_type].sort_values("Date")

# Include the first and last available months.
months = pd.period_range(
    area["Date"].min().to_period("M"),
    area["Date"].max().to_period("M"),
    freq="M",
).astype(str).tolist()

start_label, end_label = st.select_slider(
    "Date interval",
    options=months,
    value=(months[0], months[-1]),
)

start_date = pd.Timestamp(start_label)
end_date = pd.Timestamp(end_label) + pd.DateOffset(months=1)

# Filter the observations to the selected interval.
subset = area[
    (area["Date"] >= start_date) &
    (area["Date"] < end_date)
].copy()

col_choice = st.selectbox(
    "Column to plot",
    [
        "Filling_level",
        "Capacity_TWh",
        "Filling_TWh",
        "Filling_level_prev_week",
        "Change_filling_level",
    ],
)

# Use a separate interactive line for each area.
subset["Area"] = subset["Area_number"].map(
    lambda number: f"{area_type} {number}"
)

fig = px.line(
    subset,
    x="Date",
    y=col_choice,
    color="Area",
    template="plotly_dark",
    color_discrete_sequence=[
        "#40B879",
        "#E75B64",
        "#FFFFFF",
        "#D7B66C",
        "#72B7D2",
        "#C89CDB",
    ],
)

# Match the chart to the page theme.
fig.update_layout(
    title=f"{col_choice.replace('_', ' ')} · {area_type}",
    paper_bgcolor="#000000",
    plot_bgcolor="#000000",
    font=dict(
        family="Courier New, monospace",
        color="#FFFFFF",
    ),
    xaxis_title="Date",
    yaxis_title=col_choice.replace("_", " "),
    legend_title="Area",
    hovermode="x unified",
    margin=dict(l=20, r=20, t=70, b=30),
)

fig.update_xaxes(
    gridcolor="#292929",
    rangeslider_visible=True,
)

fig.update_yaxes(gridcolor="#292929")
fig.update_traces(line=dict(width=2))

st.plotly_chart(fig, width="stretch")