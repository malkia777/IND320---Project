import json
from datetime import date
from io import StringIO
from urllib.parse import quote

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from river import linear_model, preprocessing, optim

from data_loader import load_data


# Simple Palestinian theme and olive cursor.
olive_svg = """
<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32">
    <path d="M18 13 Q22 6 28 5"
          stroke="#52683D" stroke-width="3" fill="none"/>
    <ellipse cx="24" cy="8" rx="6" ry="3" fill="#73934D"/>
    <ellipse cx="14" cy="21" rx="10" ry="12"
             fill="#52683D" transform="rotate(25 14 21)"/>
    <ellipse cx="11" cy="17" rx="3" ry="5" fill="#91A46C"/>
</svg>
"""
cursor = f'url("data:image/svg+xml,{quote(olive_svg)}") 16 16, auto'

st.markdown(
    f"""
    <style>
    .stApp {{
        background: #FFFFFF;
        color: #000000;
    }}
    [data-testid="stHeader"] {{
        background: #000000;
        border-bottom: 4px solid #CE1126;
    }}
    [data-testid="stSidebar"] {{
        background: #00843D;
    }}
    h1, h2, h3, p, a, label, button,
    [data-testid="stCaptionContainer"],
    [data-testid="stSidebarNav"] a span {{
        font-family: "Courier New", monospace !important;
        color: #000000 !important;
    }}
    [data-testid="stHeader"] * {{
        color: #FFFFFF !important;
    }}
    .block-container {{
        padding-top: 5rem;
    }}
    *, *::before, *::after {{
        cursor: {cursor} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# Files are stored in the project's data folder.
with open("data/best_river_settings.json") as file:
    defaults = json.load(file)


@st.cache_data(ttl=86400)
def load_weather(lat, lon, start, end):
    response = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": lat,
            "longitude": lon,
            "start_date": str(start),
            "end_date": str(end),
            "models": "era5",
            "hourly": "temperature_2m,precipitation,snowfall",
            "timezone": "UTC",
        },
        timeout=90,
    )
    response.raise_for_status()
    weather = pd.DataFrame(response.json()["hourly"])
    weather["time"] = (
        pd.to_datetime(weather["time"], utc=True)
        .dt.tz_convert("Europe/Oslo")
        .dt.tz_localize(None)
    )
    return weather.set_index("time")


@st.cache_data(ttl=86400)
def load_rates(start, end):
    response = requests.get(
        "https://data.norges-bank.no/api/data/EXR/B.EUR+USD.NOK.SP",
        params={
            "startPeriod": str(start),
            "endPeriod": str(end),
            "format": "csv",
            "locale": "en",
        },
        timeout=60,
    )
    response.raise_for_status()
    data = pd.read_csv(StringIO(response.text), sep=";")
    data["TIME_PERIOD"] = pd.to_datetime(data["TIME_PERIOD"])
    data["OBS_VALUE"] = pd.to_numeric(data["OBS_VALUE"])

    return data.pivot(
        index="TIME_PERIOD", columns="BASE_CUR", values="OBS_VALUE"
    ).rename(columns={"EUR": "EUR_NOK", "USD": "USD_NOK"})


def river_forecast(
    weekly, sources=("weather", "rates"), history_weeks=None,
    horizon=13, lags=(1, 2, 4), learning_rate=0.005, l2=0.01,
):
    source_columns = {
        "weather": ["temperature_2m", "precipitation", "snowfall"],
        "rates": ["EUR_NOK", "USD_NOK"],
    }
    columns = ["Filling_level"]
    for source in sources:
        columns.extend(source_columns[source])

    data = weekly.sort_index()[columns].astype(float)
    if history_weeks is not None:
        data = data.iloc[-history_weeks:]

    filling = data["Filling_level"].to_numpy()

    def features(origin):
        x = {
            f"filling_lag_{lag}": float(filling[origin - lag + 1])
            for lag in lags
        }
        for column in columns[1:]:
            x[column] = float(data[column].iloc[origin])
        return x

    predictions = []

    # A separate River model predicts each future week.
    for step in range(1, horizon + 1):
        model = (
            preprocessing.StandardScaler()
            | linear_model.LinearRegression(
                optimizer=optim.SGD(learning_rate),
                intercept_lr=learning_rate,
                l2=l2,
            )
        )
        for origin in range(max(lags) - 1, len(data) - step):
            change = filling[origin + step] - filling[origin]
            model.learn_one(features(origin), float(change))

        change = model.predict_one(features(len(data) - 1))
        predictions.append(float(filling[-1] + change))

    dates = pd.date_range(
        data.index[-1] + pd.Timedelta(weeks=1),
        periods=horizon,
        freq="7D",
    )
    return pd.Series(predictions, index=dates, name="Forecast")

def forecast_chart(observed, forecast, title):
    fig = go.Figure()

    # Keep the observed values visible throughout the animation.
    fig.add_trace(go.Scatter(
        x=observed.index,
        y=observed,
        name="Observed",
        mode="lines",
        line=dict(color="#00843D", width=2),
    ))

    # Begin with the first forecast week.
    fig.add_trace(go.Scatter(
        x=forecast.index[:1],
        y=forecast.iloc[:1],
        name="Forecast",
        mode="lines+markers",
        line=dict(color="#CE1126", width=2),
    ))

    # Each frame reveals one additional forecast week.
    fig.frames = [
        go.Frame(
            name=str(week),
            data=[
                go.Scatter(
                    x=forecast.index[:week],
                    y=forecast.iloc[:week],
                    mode="lines+markers",
                    line=dict(color="#CE1126", width=2),
                )
            ],
            traces=[1],
        )
        for week in range(1, len(forecast) + 1)
    ]

    # Fix the axes so the chart does not jump during playback.
    values = pd.concat([observed, forecast]).dropna()
    padding = max(float(values.max() - values.min()) * 0.1, 0.02)

    fig.update_layout(
        template="plotly_white",
        title=dict(text=title, font=dict(color="#000000")),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(
            family="Courier New, monospace",
            color="#000000",
        ),
        legend=dict(font=dict(color="#000000")),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font=dict(color="#000000"),
        ),
        hovermode="x unified",
        height=550,
        margin=dict(l=75, r=25, t=80, b=150),

        # Animation buttons.
        updatemenus=[dict(
            type="buttons",
            direction="left",
            x=0,
            y=-0.25,
            showactive=False,
            bgcolor="#FFFFFF",
            font=dict(color="#000000"),
            buttons=[
                dict(
                    label="▶ Play",
                    method="animate",
                    args=[
                        None,
                        {
                            "frame": {"duration": 450, "redraw": False},
                            "transition": {"duration": 0},
                            "fromcurrent": True,
                            "mode": "immediate",
                        },
                    ],
                ),
                dict(
                    label="❚❚ Pause",
                    method="animate",
                    args=[
                        [None],
                        {
                            "frame": {"duration": 0, "redraw": False},
                            "transition": {"duration": 0},
                            "mode": "immediate",
                        },
                    ],
                ),
            ],
        )],

        # Select a forecast week manually.
        sliders=[dict(
            active=0,
            x=0,
            y=-0.08,
            len=1,
            font=dict(color="#000000"),
            currentvalue=dict(prefix="Forecast week: "),
            steps=[
                dict(
                    label=str(week),
                    method="animate",
                    args=[
                        [str(week)],
                        {
                            "frame": {"duration": 0, "redraw": False},
                            "transition": {"duration": 0},
                            "mode": "immediate",
                        },
                    ],
                )
                for week in range(1, len(forecast) + 1)
            ],
        )],
    )

    fig.update_xaxes(
        title_text="Date",
        range=[
            min(observed.index.min(), forecast.index.min()),
            max(observed.index.max(), forecast.index.max()),
        ],
        autorange=False,
        title_font=dict(color="#000000"),
        tickfont=dict(color="#000000"),
        gridcolor="#E5E5E5",
    )

    fig.update_yaxes(
        title_text="Reservoir filling",
        range=[values.min() - padding, values.max() + padding],
        autorange=False,
        tickformat=".0%",
        title_font=dict(color="#000000"),
        tickfont=dict(color="#000000"),
        gridcolor="#E5E5E5",
    )

    return fig


st.title("Reservoir filling forecast")
st.write(
    "Test predictions against observed filling and forecast beyond the "
    "dataset. The initial settings come from your Optuna search."
)

df = load_data()
reservoirs = df[df["Area_type"] == "EL"]
regions = sorted(reservoirs["Area_number"].unique().tolist())

selected_type, selected_number = st.session_state.get(
    "reservoir_area", ("EL", 3)
)
initial_region = selected_number if selected_type == "EL" else 3

with st.form("forecast_controls"):
    region = st.selectbox(
        "Region", regions,
        index=regions.index(initial_region) if initial_region in regions else 0,
        format_func=lambda number: f"NO{number}",
    )
    interval = st.date_input(
        "Historical interval",
        value=st.session_state.get(
            "map_timeframe",
            (date(2018, 1, 1), date(2024, 12, 31)),),)
    
    sources = st.multiselect(
        "Additional sources", ["weather", "rates"],
        default=defaults["sources"],
    )
    st.caption("Reservoir history is always included.")

    horizon = st.slider(
        "Forecast horizon (weeks)", 4, 26, int(defaults["horizon"])
    )
    histories = list(dict.fromkeys(
        [None, 104, 156, 260, defaults["history_weeks"]]
    ))
    history = st.selectbox(
        "Training history", histories,
        index=histories.index(defaults["history_weeks"]),
        format_func=lambda n: "All available" if n is None else f"{n} weeks",
    )
    lags = st.multiselect(
        "Reservoir lags",
        sorted(set([1, 2, 4, 13, 26, 52] + defaults["lags"])),
        default=defaults["lags"],
    )
    st.caption("Lag 1 is the latest observation; lag 2 is one week earlier.")

    learning_rate = st.number_input(
        "Learning rate", min_value=0.000001,
        value=float(defaults["learning_rate"]), format="%.8f",
    )
    l2 = st.number_input(
        "L2 regularisation", min_value=0.0,
        value=float(defaults["l2"]), format="%.8f",
    )
    run = st.form_submit_button("Run forecast")


if run:
    if len(interval) != 2 or not lags:
        st.info("Select both dates and at least one lag.")
        st.stop()

    selected = reservoirs[
        (reservoirs["Area_number"] == region)
        & (reservoirs["Date"].dt.date >= interval[0])
        & (reservoirs["Date"].dt.date <= interval[1])
    ]
    if selected.empty:
        st.info("No reservoir data for this selection.")
        st.stop()

    filling = selected.set_index("Date")["Filling_level"].sort_index()
    weeks = pd.date_range(filling.index.min(), filling.index.max(), freq="W-SUN")
    weekly = filling.reindex(weeks).to_frame("Filling_level")
    start = (weeks[0] - pd.Timedelta(days=6)).date()
    end = weeks[-1].date()

    with st.spinner("Loading sources and forecasting…"):
        if "weather" in sources:
            locations = pd.read_csv("data/weather_locations.csv")
            points = locations[
                (locations["Area_type"] == "EL")
                & (locations["Area_number"] == region)
            ]
            if points.empty:
                st.info("No weather location saved. Select NO3 or remove weather.")
                st.stop()

            point = points.iloc[0]
            weather = load_weather(
                float(point["latitude"]), float(point["longitude"]),
                start - pd.Timedelta(days=1), end,
            )
            weather = weather[
                (weather.index >= pd.Timestamp(start))
                & (weather.index < pd.Timestamp(end) + pd.Timedelta(days=1))
            ]
            weekly = weekly.join(weather.resample("W-SUN").agg({
                "temperature_2m": "mean",
                "precipitation": lambda s: s.sum(min_count=1),
                "snowfall": lambda s: s.sum(min_count=1),
            }))

        if "rates" in sources:
            weekly = weekly.join(load_rates(start, end).resample("W-SUN").mean())

        if not np.isfinite(weekly.to_numpy()).all():
            st.info("Missing inputs: change the interval or selected sources.")
            st.dataframe(weekly.isna().sum().rename("Missing weeks"))
            st.stop()

        training_weeks = len(weekly) - horizon
        if history is not None:
            training_weeks = min(training_weeks, history)
        if training_weeks <= max(lags) - 1 + horizon:
            st.info("Use more history or reduce the horizon or lags.")
            st.stop()

        settings = dict(
            sources=sources, history_weeks=history, lags=lags,
            learning_rate=learning_rate, l2=l2,
        )
        truth = weekly["Filling_level"].iloc[-horizon:]
        test = river_forecast(weekly.iloc[:-horizon], horizon=horizon, **settings)
        future = river_forecast(weekly, horizon=horizon, **settings)

    if not (np.isfinite(test).all() and np.isfinite(future).all()):
        st.error("Unstable predictions: try a lower learning rate.")
        st.stop()

    test_tab, future_tab = st.tabs(["Test against truth", "Future forecast"])

    with test_tab:
        st.metric("Test MAE (percentage points)", f"{(truth-test).abs().mean()*100:.2f}")
        st.plotly_chart(
            forecast_chart(truth, test, f"NO{region}: forecast against truth"),
            width="stretch",
        )
        st.dataframe(pd.DataFrame({"Observed": truth, "Forecast": test}))

    with future_tab:
        st.plotly_chart(
            forecast_chart(
                weekly["Filling_level"].iloc[-104:], future,
                f"NO{region}: next {horizon} weeks after the dataset",
            ),
            width="stretch",
        )
        st.dataframe(future.to_frame())
        st.caption(
            "Forecast dates follow the last observation, not today. "
            "Future actual values are not included in this dataset."
        )

    st.caption(
        "Inputs are assumed available at each forecast origin. "
        "Saved settings were tuned for NO3. Changing settings after "
        "viewing the test makes subsequent comparisons exploratory."
    )