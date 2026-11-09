import pandas as pd
import streamlit as st
import requests
from data_loader import load_data
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import STL

st.title("Reservoir analysis")
st.write(
    "Choose an area to explore how its reservoir filling levels change over time. "
    "The STL tab separates the long-term trend from the yearly pattern. "
    "The Spectrogram tab shows how strong different repeating patterns are over time."
)

df = load_data()

# Choose one area for both tabs. Select EL and 3 for NO3.
area_type = st.radio("Area type", ["EL", "NO", "VASS"])
area = df[df["Area_type"] == area_type]
area_number = st.selectbox("Area number", sorted(area["Area_number"].unique()))

# Keep the selected area's weekly filling levels in date order.
filling = (
    area[area["Area_number"] == area_number]
    .set_index("Date")["Filling_level"]
    .sort_index()
)

stl_tab, spec_tab = st.tabs(["STL", "Spectrogram"])

with stl_tab:
    # A larger seasonal smoother keeps the yearly pattern more consistent.
    seasonal = st.slider("Seasonal smoother", 7, 53, 7, step=2)

    # The default trend window is about two years (105 weeks).
    trend = st.slider("Trend smoother (weeks)", 53, 209, 105, step=2)

    # Robust fitting gives unusual weeks less influence.
    robust = st.checkbox("Robust fitting", value=True)

    # Split the series into trend, yearly pattern and what remains.
    result = STL(
        filling, period=52, seasonal=seasonal, trend=trend, robust=robust
    ).fit()
    fig = result.plot()
    st.pyplot(fig)
    plt.close(fig)

with spec_tab:
    # Look at three years at a time. Sharing two years moves
    # the next window forward by one year (156 - 104 = 52 weeks).
    window = st.number_input("Window length (weeks)", min_value=2, value=156)
    overlap = st.number_input("Window overlap (weeks)", min_value=0, value=104)

    if overlap >= window or window > len(filling):
        st.warning("Use an overlap smaller than the window and a window that fits the data.")
    else:
        # Fs=52 puts the frequency axis in cycles per year.
        fig, ax = plt.subplots()
        ax.specgram(filling.to_numpy(), NFFT=window, noverlap=overlap,
                    Fs=52, detrend="mean")
        ax.set_xlabel("Years since start")
        ax.set_ylabel("Cycles per year")
        st.pyplot(fig)
        plt.close(fig)

#so page 6 knows which area was selected for the analysis
st.session_state["reservoir_area"] = (area_type, area_number) 