import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from urllib.parse import quote
from plotly.subplots import make_subplots
from scipy.signal import spectrogram
from statsmodels.tsa.seasonal import STL
from data_loader import load_data


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


# Watermelon seeds for the outer edges.
seed_svg = """
<svg xmlns="http://www.w3.org/2000/svg" width="60" height="140"
     viewBox="0 0 60 140">
    <ellipse cx="20" cy="30" rx="4" ry="8"
             fill="#202020" transform="rotate(-25 20 30)"/>
    <ellipse cx="40" cy="100" rx="4" ry="8"
             fill="#202020" transform="rotate(25 40 100)"/>
</svg>
"""

seeds = f'url("data:image/svg+xml,{quote(seed_svg)}")'


st.markdown(
    f"""
    <style>
    /* Watermelon flesh with seeds along the outer edges. */
    .stApp {{
        background-color: #F8B5B9;
        background-image: {seeds}, {seeds};
        background-repeat: repeat-y, repeat-y;
        background-position: left top, right top;
        color: #000000;
    }}

    /* Green rind and a cream inner stripe. */
    [data-testid="stHeader"] {{
        background-color: #22543D;
        border-bottom: 8px solid #F4F0D8;
    }}

    [data-testid="stHeader"] * {{
        color: #FFFFFF !important;
    }}

    /* Dark green sidebar. */
    [data-testid="stSidebar"] {{
        background-color: #22543D;
    }}

    /* Boxy black text in the main area. */
    h1, h2, h3, h4, h5, h6,
    p, a, label, button,
    [data-testid="stCaptionContainer"],
    [data-testid="stWidgetLabel"] {{
        font-family: "Courier New", monospace !important;
        color: #000000 !important;
    }}

    /* White sidebar text. */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] button,
    [data-testid="stSidebarNav"] a span {{
        color: #FFFFFF !important;
    }}

    [data-testid="stSidebarNav"] a:hover,
    [data-testid="stSidebarNav"] a[aria-current="page"] {{
        background-color: #356B50;
    }}

    .block-container {{
        padding-top: 5rem;
    }}

    h1 {{
        border-bottom: 3px solid #22543D;
        padding-bottom: 18px;
    }}

    /* Readable inputs and tab labels. */
    [data-baseweb="select"] > div,
    [data-testid="stNumberInput"] input {{
        background-color: #FFF4F4;
        color: #000000;
    }}

    [data-baseweb="select"] input,
    [data-baseweb="tab"] {{
        color: #000000 !important;
    }}

    /* Olive cursor. */
    *, *::before, *::after {{
        cursor: {cursor} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# Apply matching colours and readable labels to both charts.
def style_chart(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFF0F0",
        plot_bgcolor="#FFF0F0",
        font=dict(
            family="Courier New, monospace",
            size=14,
            color="#000000",
        ),
        title=dict(font=dict(size=18, color="#000000")),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font=dict(color="#000000"),
        ),
        margin=dict(l=75, r=45, t=75, b=65),
    )

    fig.update_xaxes(
        title_font=dict(size=15, color="#000000"),
        tickfont=dict(size=13, color="#000000"),
        gridcolor="#E6CCCC",
        automargin=True,
    )

    fig.update_yaxes(
        title_font=dict(size=15, color="#000000"),
        tickfont=dict(size=13, color="#000000"),
        gridcolor="#E6CCCC",
        automargin=True,
    )

    # Explicitly colour subplot headings.
    fig.update_annotations(
        font=dict(
            family="Courier New, monospace",
            size=16,
            color="#000000",
        )
    )

    return fig


@st.cache_data(show_spinner=False, max_entries=20)
def calculate_stl(filling, seasonal, trend, robust):
    result = STL(
        filling,
        period=52,
        seasonal=seasonal,
        trend=trend,
        robust=robust,
    ).fit()

    return result.trend, result.seasonal, result.resid


@st.cache_data(show_spinner=False, max_entries=20)
def calculate_spectrogram(filling, window, overlap):
    frequencies, times, power = spectrogram(
        filling.to_numpy(),
        fs=52,
        window=np.hanning(int(window)),
        nperseg=int(window),
        noverlap=int(overlap),
        detrend="constant",
        scaling="density",
        mode="psd",
    )

    power_db = 10 * np.log10(
        np.maximum(power, np.finfo(float).tiny)
    )

    return frequencies, times, power_db

st.title("Reservoir analysis")
st.write(
    "Choose an area to explore how its reservoir filling levels change over time. "
    "The STL tab separates the long-term trend from the yearly pattern. "
    "The Spectrogram tab shows how strong different repeating patterns are over time."
)

with st.spinner("Loading reservoir data…"):
    df = load_data()


# Save local selector changes for the map, weather and forecasting pages.
def save_area_selection():
    kind = st.session_state["analysis_area_type"]
    numbers = sorted(
        df.loc[df["Area_type"] == kind, "Area_number"].unique().tolist()
    )

    number = st.session_state.get("analysis_area_number", 3)

    # Changing area type may require a different area number.
    if number not in numbers:
        number = numbers[0]

    st.session_state["analysis_area_number"] = number
    st.session_state["reservoir_area"] = (kind, number)


# Initialise the controls from the shared map selection.
saved_type, saved_number = st.session_state.get(
    "reservoir_area", ("EL", 3)
)

st.session_state["analysis_area_type"] = saved_type

available_numbers = sorted(
    df.loc[df["Area_type"] == saved_type, "Area_number"].unique().tolist()
)

st.session_state["analysis_area_number"] = (
    saved_number if saved_number in available_numbers
    else available_numbers[0]
)

# Choose one area for both analysis tabs.
area_type = st.radio(
    "Area type",
    ["EL", "NO", "VASS"],
    key="analysis_area_type",
    on_change=save_area_selection,
)

area = df[df["Area_type"] == area_type]

area_number = st.selectbox(
    "Area number",
    sorted(area["Area_number"].unique().tolist()),
    key="analysis_area_number",
    on_change=save_area_selection,
)

# Store the current selection for the other pages.
st.session_state["reservoir_area"] = (area_type, area_number)


# Get weekly filling levels for the selected area.
filling = (
    area[area["Area_number"] == area_number]
    .set_index("Date")["Filling_level"]
    .sort_index()
)

stl_tab, spec_tab = st.tabs(["STL", "Spectrogram"])

with stl_tab:
    seasonal = st.slider("Seasonal smoother", 7, 53, 7, step=2)
    trend = st.slider("Trend smoother (weeks)", 53, 209, 105, step=2)
    robust = st.checkbox("Robust fitting", value=True)

    with st.spinner("Calculating trends and seasonality…"):
        trend_values, seasonal_values, residual_values = calculate_stl(filling, 
                                                                       seasonal, trend, robust)

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=["Observed", "Trend", "Seasonal", "Residual"],
    )

    components = [("Observed", filling, "#22543D"), ("Trend", trend_values, "#781F36"), 
                  ("Seasonal", seasonal_values, "#22543D"),("Residual", residual_values, "#333333"),]

    for row, (name, values, color) in enumerate(components, start=1):
        fig.add_trace(
            go.Scatter(
                x=filling.index,
                y=values,
                name=name,
                mode="lines",
                line=dict(color=color, width=1.5),
            ),
            row=row,
            col=1,
        )

    fig = style_chart(fig)
    fig.update_layout(
        height=850,
        showlegend=False,
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Filling level", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=4, col=1)

    st.plotly_chart(fig, width="stretch")

with spec_tab:
    window = st.number_input(
        "Window length (weeks)", min_value=2, value=156
    )
    overlap = st.number_input(
        "Window overlap (weeks)", min_value=0, value=104
    )

    if overlap >= window or window > len(filling):
        st.warning(
            "Use an overlap smaller than the window "
            "and a window that fits the data."
        )
    else:
        with st.spinner("Calculating the spectrogram…"):frequencies, times, power_db = calculate_spectrogram(filling, 
                                                                                                             window, overlap)

        fig = go.Figure(
            go.Heatmap(
                x=times,
                y=frequencies,
                z=power_db,
                colorscale=[
                    [0.0, "#FFF0F0"],
                    [0.35, "#EE8D99"],
                    [0.7, "#A73550"],
                    [1.0, "#22543D"],
                ],
                colorbar=dict(
                    title=dict(
                        text="Power (dB)",
                        font=dict(color="#000000"),
                    ),
                    tickfont=dict(color="#000000"),
                ),
            )
        )

        fig = style_chart(fig)
        fig.update_layout(
            title="Reservoir filling spectrogram",
            xaxis_title="Years since start (52 weeks per year)",
            yaxis_title="Cycles per year",
            height=500,
        )

        st.plotly_chart(fig, width="stretch")