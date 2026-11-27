from pathlib import Path
from urllib.parse import quote
from data_loader import load_data
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import requests
import streamlit as st
from scipy.fft import dct, idct
from scipy.stats import median_abs_deviation
from sklearn.neighbors import LocalOutlierFactor


# Olive cursor.
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


# Small leaf accents along the outer edges.
leaf_svg = """
<svg xmlns="http://www.w3.org/2000/svg" width="55" height="180"
     viewBox="0 0 55 180">
    <path d="M15 150 Q35 90 25 30"
          fill="none" stroke="#87966A" stroke-width="2"/>
    <g fill="#87966A" opacity="0.5">
        <ellipse cx="18" cy="45" rx="12" ry="4"
                 transform="rotate(40 18 45)"/>
        <ellipse cx="34" cy="75" rx="12" ry="4"
                 transform="rotate(-35 34 75)"/>
        <ellipse cx="20" cy="105" rx="12" ry="4"
                 transform="rotate(35 20 105)"/>
        <ellipse cx="24" cy="135" rx="12" ry="4"
                 transform="rotate(-35 24 135)"/>
    </g>
</svg>
"""

leaves = f'url("data:image/svg+xml,{quote(leaf_svg)}")'


st.markdown(
    f"""
    <style>
    /* Cream background with subtle olive leaves at the edges. */
    .stApp {{
        background-color: #F2E6CE;
        background-image: {leaves}, {leaves};
        background-repeat: repeat-y, repeat-y;
        background-position: left top, right top;
        color: #000000;
    }}

    /* Pale sky-blue upper bar. */
    [data-testid="stHeader"] {{
        background-color: #C9E2EB;
        border-bottom: 3px solid #52683D;
    }}

    [data-testid="stHeader"] * {{
        color: #000000 !important;
    }}

    /* Olive-green sidebar. */
    [data-testid="stSidebar"] {{
        background-color: #52683D;
    }}

    /* Black, boxy main text. */
    h1, h2, h3, h4, h5, h6,
    p, a, label, button,
    [data-testid="stCaptionContainer"],
    [data-testid="stWidgetLabel"] {{
        font-family: "Courier New", monospace !important;
        color: #000000 !important;
    }}

    /* White sidebar navigation text. */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] button,
    [data-testid="stSidebarNav"] a span {{
        color: #FFFFFF !important;
    }}

    [data-testid="stSidebarNav"] a:hover,
    [data-testid="stSidebarNav"] a[aria-current="page"] {{
        background-color: #3D502E;
    }}

    .block-container {{
        padding-top: 5rem;
    }}

    h1 {{
        border-bottom: 3px solid #52683D;
        padding-bottom: 18px;
    }}

    [data-baseweb="tab"] {{
        color: #000000 !important;
    }}

    /* Olive cursor throughout the page. */
    *, *::before, *::after {{
        cursor: {cursor} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("Weather analysis")
st.write("Select a weather property and explore unusual observations "
         "using SPC or Local Outlier Factor."
         "Select area on the map.")

@st.cache_data
def load_weather(lat, lon):
    # Download hourly ERA5 temperature and precipitation for 2024.
    response = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params=dict(
            latitude=lat,
            longitude=lon,
            start_date="2024-01-01",
            end_date="2024-12-31",
            models="era5",
            hourly="temperature_2m,precipitation,snowfall",
            timezone="UTC",
        ),
        timeout=60,)
    
    response.raise_for_status()
    weather = pd.DataFrame(response.json()["hourly"])
    weather["time"] = pd.to_datetime(weather["time"])

    # Daily mean temperature and daily precipitation/snowfall totals.
    return (
        weather.set_index("time")
        [["temperature_2m", "precipitation", "snowfall"]]
        .resample("D")
        .agg({
            "temperature_2m": "mean",
            "precipitation": lambda s: s.sum(min_count=1),
            "snowfall": lambda s: s.sum(min_count=1),}))


def show_results(values, flagged, label, lower=None, upper=None):
    # Select the observations flagged by SPC or LOF.
    outliers = values[flagged]

    # Plot the original observations in dark green.
    fig = go.Figure(
        go.Scatter(
            x=values.index,
            y=values,
            name="Observed",
            mode="lines",
            line=dict(color="#3D502E", width=2),
        )
    )

    # Add black dashed SPC boundaries when supplied.
    if lower is not None:
        fig.add_trace(
            go.Scatter(
                x=values.index,
                y=lower,
                name="Lower limit",
                mode="lines",
                line=dict(color="#000000", dash="dash", width=1),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=values.index,
                y=upper,
                name="Upper limit",
                mode="lines",
                line=dict(color="#000000", dash="dash", width=1),
            )
        )

    # Highlight flagged days in burgundy.
    fig.add_trace(
        go.Scatter(
            x=outliers.index,
            y=outliers,
            name="Flagged days",
            mode="markers",
            marker=dict(
                color="#781F36",
                size=9,
                line=dict(color="#FFFFFF", width=1),
            ),
            hovertemplate=(
                "%{x|%d %b %Y}<br>"
                "Value: %{y:.2f}<extra>Flagged day</extra>"
            ),
        )
    )

    # Match the chart to the page, with explicit black labels.
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FAF7EF",
        plot_bgcolor="#FAF7EF",
        font=dict(
            family="Courier New, monospace",
            size=14,
            color="#000000",
        ),
        title=dict(
            text=label,
            font=dict(size=18, color="#000000"),
        ),
        xaxis_title="Date (UTC)",
        yaxis_title=label,
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font=dict(color="#000000"),
        ),
        legend=dict(
            orientation="h",
            y=-0.25,
            font=dict(size=14, color="#000000"),
        ),
        margin=dict(l=80, r=30, t=75, b=110),
        height=500,
    )

    fig.update_xaxes(
        title_font=dict(size=15, color="#000000"),
        tickfont=dict(size=13, color="#000000"),
        gridcolor="#DDD8C9",
        automargin=True,
    )

    fig.update_yaxes(
        title_font=dict(size=15, color="#000000"),
        tickfont=dict(size=13, color="#000000"),
        gridcolor="#DDD8C9",
        automargin=True,
    )

    st.plotly_chart(fig, width="stretch")

    st.write(f"Flagged days: {len(outliers)} of {len(values)}")
    st.dataframe(outliers.to_frame(label))


# Use the area selected on the reservoir analysis page. Default to NO3.
area_type, area_number = st.session_state.get("reservoir_area", ("EL", 3))
st.caption(f"Area: {area_type} {area_number} · 2024")

path = Path(__file__).resolve().parents[1] / "data" / "weather_locations.csv"
locations = pd.read_csv(path)
points = locations[
    (locations["Area_type"] == area_type)
    & (locations["Area_number"] == area_number)
]

if points.empty:
    st.info("No weather coordinates are saved for this area.")
    st.stop()

# Load weather for the selected area's saved location.
point = points.iloc[0]
with st.spinner("Loading weather data…"):
    weather = load_weather(
        float(point["latitude"]),
        float(point["longitude"]),
    )

if len(weather) != 366 or weather.isna().any().any():
    st.error("The analysis needs weather values for every day of 2024.")
    st.stop()

properties = {
    "Temperature": ("temperature_2m", "Daily mean temperature (°C)"),
    "Precipitation": ("precipitation", "Daily precipitation (mm)"),
    "Snowfall": ("snowfall", "Daily snowfall (cm)"),
}

@st.cache_data(show_spinner=False, max_entries=20)
def calculate_spc(values, cutoff, n_std):
    y = values.to_numpy()

    coefficients = dct(y, type=1, norm="forward")
    coefficients[:cutoff] = 0
    adjusted = idct(coefficients, type=1, norm="forward")

    centre = np.median(adjusted)
    distance = n_std * median_abs_deviation(
        adjusted, scale="normal"
    )

    baseline = y - adjusted + centre
    flagged = np.abs(adjusted - centre) > distance

    return flagged, baseline - distance, baseline + distance


@st.cache_data(show_spinner=False, max_entries=20)
def calculate_lof(values, percent):
    model = LocalOutlierFactor(
        n_neighbors=20,
        contamination=percent / 100,
    )

    return model.fit_predict(values.to_frame()) == -1


spc_tab, lof_tab, corr_tab = st.tabs(["SPC", "LOF",
                                      "Weather–reservoir correlation",])

with spc_tab:
    property_name = st.selectbox(
        "Weather property",
        list(properties),
        index=0,
        key="spc_property",
    )
    column, label = properties[property_name]
    values = weather[column]

    cutoff = st.slider("Slow DCT components to remove", 1, 30, 6)
    n_std = st.slider(
        "Number of standard deviations",
        1.0, 5.0, 3.0, step=0.5,
    )

    with st.spinner("Calculating SPC limits…"):
        flagged, lower, upper = calculate_spc(
            values, cutoff, n_std
        )

    show_results(values, flagged, label, lower, upper)

with lof_tab:
    property_name = st.selectbox(
        "Weather property",
        list(properties),
        index=0,
        key="lof_property",
    )
    column, label = properties[property_name]
    values = weather[column]

    percent = st.slider(
        "Outlier percentage",
        0.5, 10.0, 1.0, step=0.5,
    )

    with st.spinner("Finding unusual weather observations…"):
        flagged = calculate_lof(values, percent)

    show_results(values, flagged, label)

    st.caption(
        "LOF compares daily values, without accounting for their "
        "chronological order. Flagged days are unusual values, "
        "not necessarily measurement errors."
    )

with corr_tab:
    st.subheader("Sliding-window correlation")

    st.write(
        "Explore how the relationship between weather and reservoir "
        "filling changes over time."
    )

    property_name = st.selectbox(
        "Weather property",
        list(properties),
        index=0,
        key="correlation_property",
    )
    column, _ = properties[property_name]

    lag = st.slider(
        "Weather lag (weeks)",
        min_value=0,
        max_value=12,
        value=0,
    )

    window = st.slider(
        "Correlation window (weeks)",
        min_value=4,
        max_value=26,
        value=13,
    )

    st.caption(
        f"Lag {lag} compares reservoir filling with weather "
        f"from {lag} weeks earlier. Each correlation uses "
        f"{window} consecutive weekly pairs."
    )

    # Convert the existing daily weather data into weekly observations.
    # Temperature is averaged; precipitation and snowfall are summed.
    aggregation = (
        "mean" if column == "temperature_2m"
        else lambda values: values.sum(min_count=1)
    )

    weekly_weather = weather[column].resample("W-SUN").agg(aggregation)

    # Exclude partial weeks at the beginning or end of the weather data.
    complete_week = weather[column].resample("W-SUN").count() == 7
    weekly_weather = weekly_weather.where(complete_week)

    # Load reservoir filling for the same area as the weather analysis.
    reservoir_data = load_data()

    filling = (
        reservoir_data[
            (reservoir_data["Area_type"] == area_type)
            & (reservoir_data["Area_number"] == area_number)
        ]
        .set_index("Date")["Filling_level"]
        .sort_index()
    )

    # Keep a regular weekly timeline so a lag always means whole weeks.
    weekly_dates = pd.date_range(
        weekly_weather.index.min(),
        weekly_weather.index.max(),
        freq="W-SUN",
    )

    combined = pd.DataFrame({
        "Filling": filling.reindex(weekly_dates),
        "Weather": weekly_weather.reindex(weekly_dates),
    })

    # A positive lag moves earlier weather alongside later filling levels.
    combined["Lagged weather"] = combined["Weather"].shift(lag)

    # Respect the map timeframe, keeping only weeks fully inside it.
    map_interval = st.session_state.get("map_timeframe")

    if map_interval is not None:
        start, end = map_interval

        combined = combined[
            ((combined.index - pd.Timedelta(days=6)).date >= start)
            & (combined.index.date <= end)
        ]

    # Require a complete window of paired observations.
    combined["Correlation"] = (
        combined["Filling"]
        .rolling(window=window, min_periods=window)
        .corr(combined["Lagged weather"])
    )

    # Constant values can make correlation undefined.
    combined["Correlation"] = combined["Correlation"].replace(
        [np.inf, -np.inf], np.nan
    )

    if combined["Correlation"].notna().any():
        fig = go.Figure(
            go.Scatter(
                x=combined.index,
                y=combined["Correlation"],
                name="Rolling correlation",
                mode="lines",
                connectgaps=False,
                line=dict(color="#3D502E", width=2),
                hovertemplate=(
                    "%{x|%d %b %Y}<br>"
                    "Correlation: %{y:.2f}<extra></extra>"
                ),
            )
        )

        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="#781F36",
        )

        fig.update_layout(
            template="plotly_white",
            title=dict(
                text=f"{property_name} and reservoir filling",
                font=dict(color="#000000"),
            ),
            paper_bgcolor="#FAF7EF",
            plot_bgcolor="#FAF7EF",
            font=dict(
                family="Courier New, monospace",
                color="#000000",
            ),
            hoverlabel=dict(
                bgcolor="#FFFFFF",
                font=dict(color="#000000"),
            ),
            margin=dict(l=75, r=30, t=75, b=65),
        )

        fig.update_xaxes(
            title_text="Window end date",
            title_font=dict(color="#000000"),
            tickfont=dict(color="#000000"),
            gridcolor="#DDD8C9",
        )

        fig.update_yaxes(
            title_text="Correlation",
            range=[-1, 1],
            title_font=dict(color="#000000"),
            tickfont=dict(color="#000000"),
            gridcolor="#DDD8C9",
        )

        st.plotly_chart(fig, width="stretch")

        st.caption(
            "+1 indicates a strong positive relationship; "
            "−1 indicates a strong negative relationship. "
            "Values near zero indicate a weak linear relationship. "
            "Correlation does not establish causation."
        )

        with st.expander("View weekly values and correlations"):
            st.dataframe(combined)

    else:
        st.info(
            "No correlation can be calculated for these settings. "
            "Try a shorter window or lag, or select a map timeframe "
            "overlapping the available 2024 weather data. Constant "
            "weather values can also make correlation undefined."
        )

    st.caption(
        "This uses your current 2024 weather download and full "
        "Monday–Sunday weeks. Daily temperature is averaged weekly; "
        "daily precipitation and snowfall totals are summed."
    )