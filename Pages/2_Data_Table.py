import pandas as pd
import streamlit as st
import requests


st.title("Table of the data")

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

    df["Date"] = pd.to_datetime(df["Date"], format="ISO8601", errors="coerce")
    df["Next_publishdate"] = pd.to_datetime(df["Next_publishdate"], format="ISO8601", errors="coerce")

    return df.sort_values("Date")


df = load_data()

#select area type
area_type = st.radio("Area type", ["EL", "NO", "VASS"], horizontal=True)
area = df[df["Area_type"] == area_type].sort_values("Date")

#the first month available for this area type.
month_start = area["Date"].min().to_period("M").start_time
month_end = month_start + pd.DateOffset(months=1)

first_month = area[
    (area["Date"] >= month_start) & ## keep rows where date is on/after the start of the month
    (area["Date"] < month_end) #and the ones befire the end
]

measurements = [
    "Filling_level",
    "Capacity_TWh",
    "Filling_TWh",
    "Filling_level_prev_week",
    "Change_filling_level",
]

#each area number gets its own row
table = (
    first_month.groupby("Area_number")[measurements]
    .agg(list)
    .reset_index()
)

st.write(f"Showing {area_type}, {month_start:%Y-%m}")

st.dataframe(
    table,
    column_config={
        column: st.column_config.LineChartColumn(column)
        for column in measurements
    },
    hide_index=True,
    use_container_width=True,
)