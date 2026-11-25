from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import streamlit as st
from scipy.fft import dct, idct
from scipy.stats import median_abs_deviation
from sklearn.neighbors import LocalOutlierFactor

st.title("Weather analysis")
st.write("Explore unusually warm or cold days using SPC and LOF.")


@st.cache_data
def load_temperature(lat, lon):
    #download hourly ERA5 temperatures for 2024 and average them by day.
    response = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params=dict(latitude=lat, longitude=lon, start_date="2024-01-01",
                    end_date="2024-12-31", models="era5",
                    hourly="temperature_2m", timezone="UTC"),
        timeout=60,
    )
    response.raise_for_status()
    weather = pd.DataFrame(response.json()["hourly"])
    weather["time"] = pd.to_datetime(weather["time"])
    return weather.set_index("time")["temperature_2m"].resample("D").mean()


def show_results(temperature, flagged, lower=None, upper=None):
    # Draw the daily temperatures and mark flagged days in red.
    outliers = temperature[flagged]
    fig, ax = plt.subplots()
    ax.plot(temperature.index, temperature)
    if lower is not None:
        ax.plot(temperature.index, lower, "--", color="grey")
        ax.plot(temperature.index, upper, "--", color="grey")
    ax.scatter(outliers.index, outliers, color="red", zorder=3)
    ax.set_ylabel("Temperature (°C)")
    fig.autofmt_xdate()
    st.pyplot(fig)
    plt.close(fig)
    st.write(f"Flagged days: {len(outliers)} of {len(temperature)}")
    st.dataframe(outliers.to_frame("Temperature (°C)"))


# Find the sampled point for the area selected on page 5. Default to NO3.
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

point = points.iloc[0]
temperature = load_temperature(float(point["latitude"]), float(point["longitude"]))

if len(temperature) != 366 or temperature.isna().any():
    st.error("The analysis needs a temperature value for every day of 2024.")
    st.stop()

spc_tab, lof_tab = st.tabs(["Outliers / SPC", "Anomalies / LOF"])

with spc_tab:
    cutoff = st.slider("Slow DCT components to remove", 1, 30, 6)
    n_std = st.slider("Number of standard deviations", 1.0, 5.0, 3.0, step=0.5)

    # Remove the slow seasonal changes to get SATV.
    y = temperature.to_numpy()
    coefficients = dct(y, type=1, norm="forward")
    coefficients[:cutoff] = 0
    satv = idct(coefficients, type=1, norm="forward")

    # Use the median and robust spread to set the limits.
    centre = np.median(satv)
    distance = n_std * median_abs_deviation(satv, scale="normal")
    baseline = y - satv + centre
    flagged = np.abs(satv - centre) > distance

    # Show the limits on the original temperature plot.
    show_results(temperature, flagged, baseline - distance, baseline + distance)

with lof_tab:
    percent = st.slider("Outlier percentage", 0.5, 10.0, 1.0, step=0.5)

    # Compare each day's temperature with 20 similar temperatures.
    lof = LocalOutlierFactor(n_neighbors=20, contamination=percent / 100)
    flagged = lof.fit_predict(temperature.to_frame()) == -1
    show_results(temperature, flagged)