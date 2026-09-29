import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    df_file = pd.read_csv("data/reservoirs.csv") 
    
    df = df_file.copy()

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

    df = df.sort_values("Date")

    return df

df = load_data()


