import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Table of data",
    layout="wide",
)

st.title("Table of the data")

@st.cache_data
def load_data():
    df = pd.read_csv("data/reservoirs.csv")

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

value_cols = [
    "Filling_level", "Capacity_TWh", "Filling_TWh",
    "Filling_level_prev_week", "Change_filling_level",
]

table = pd.DataFrame({
    "Column": value_cols,
    "First month values": [first_month[col].tolist() for col in value_cols],
})

st.write(f"Showing area: NO, first month starting {first_month_start.date()}")

st.dataframe(
    table,
    column_config={
        "First month values": st.column_config.LineChartColumn(
            "First month values",
            width="medium",
        ),
    },
    hide_index=True,
    use_container_width=True,
)
