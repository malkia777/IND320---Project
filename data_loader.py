import pandas as pd
import requests
import streamlit as st

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
