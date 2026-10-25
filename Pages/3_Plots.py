import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import requests

st.title("Plots of the data")

@st.cache_data
def load_data():
    # Fetch reservoir data from the NVE API.
    response = requests.get(
        "https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/HentOffentligData",
        timeout=60,
    )
    response.raise_for_status()
    df = pd.DataFrame(response.json())

    df = df.rename(columns={
        'dato_Id': 'Date', "omrType": "Area_type", "omrnr": "Area_number",
        "iso_aar": "ISO_year", "iso_uke": "ISO_week",
        "fyllingsgrad": "Filling_level", "kapasitet_TWh": "Capacity_TWh",
        "fylling_TWh": "Filling_TWh",
        "neste_Publiseringsdato": "Next_publishdate",
        "fyllingsgrad_forrige_uke": "Filling_level_prev_week",
        "endring_fyllingsgrad": "Change_filling_level",
    })

    for col in ["Date", "Next_publishdate"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df = df.sort_values("Date")

    return df


df = load_data()

#select the areatype
area_type = st.radio("Area type", ["EL", "NO", "VASS"], horizontal=True)
area = df[df["Area_type"] == area_type].sort_values("Date")

# Include the first and last months in the slider
months = pd.period_range(
    area["Date"].min().to_period("M"),
    area["Date"].max().to_period("M"),
    freq="M",
).astype(str).tolist()

start_label, end_label = st.select_slider(
    "Download interval",
    options=months,
    value=(months[0], months[-1]),
)

start_date = pd.Timestamp(start_label)
end_date = pd.Timestamp(end_label) + pd.DateOffset(months=1)

# The selected interval controls both the download and the displayed plot.
subset = area[
    (area["Date"] >= start_date) &
    (area["Date"] < end_date)
]


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

fig, ax = plt.subplots(figsize=(10, 5))

for number, group in subset.groupby("Area_number"):
    ax.plot(
        group["Date"],
        group[col_choice],
        label=f"{area_type} {number}",
        linewidth=1.2,
    )

ax.set_xlabel("Date")
ax.set_ylabel(col_choice)
ax.set_title(f"{col_choice}, {area_type}")
ax.legend()

st.pyplot(fig)
plt.close(fig)