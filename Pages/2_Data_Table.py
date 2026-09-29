import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Table of data",
    layout="wide",
)

st.title("Table of the data")

@st.cache_data
def load_data():
    df = pd.read_csv("Project/data/reservoirs.csv")
    
    
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

area = df[df["Area_type"] == "NO"].sort_values("Date")

first_month_start = area["Date"].min()
first_month_end = first_month_start + pd.DateOffset(months=1)
first_month = area[(area["Date"] >= first_month_start) & (area["Date"] < first_month_end)]

def to_values(col):
    series = first_month[col]
    if pd.api.types.is_numeric_dtype(series):
        return series.tolist()
    return [] 

table = pd.DataFrame({
    "Column": df.columns,
    "First month values": [to_values(col) for col in df.columns],
})

st.write(f"Showing area: NO, first month starting {first_month_start.date()}")

st.dataframe(
    table,
    column_config={
        "First month values": st.column_config.LineChartColumn(
            "First month values", width="medium",
        ),
    },
    hide_index=True,
    use_container_width=True,
)