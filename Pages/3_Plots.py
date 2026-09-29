import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Plots",
    layout="wide",
)

st.title("Plots of the data")

@st.cache_data
def load_data():
    df = pd.read_csv("Project/data/reservoirs.csv")

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

    return df

df = load_data()

# From the notebook: filter to one area so "a column" means one
# consistent time series, not 9 overlapping regions mixed together.
area = df[df["Area_type"] == "NO"].sort_values("Date")

value_cols = [
    "Filling_level", "Capacity_TWh", "Filling_TWh",
    "Filling_level_prev_week", "Change_filling_level",
]

# --- Streamlit-specific: widgets for column and month selection ---
col_choice = st.selectbox("Column to plot", options=["All columns"] + value_cols)

# build the list of months present in the data, for the slider's options
months = pd.date_range(area["Date"].min(), area["Date"].max(), freq="MS")
month_labels = months.strftime("%Y-%m")

start_label, end_label = st.select_slider(
    "Month range",
    options=month_labels,
    value=(month_labels[0], month_labels[0]),  # default: first month only
)

start_date = pd.Timestamp(start_label)
end_date = pd.Timestamp(end_label) + pd.offsets.MonthEnd(1)

subset = area[(area["Date"] >= start_date) & (area["Date"] <= end_date)]

# --- From the notebook: normalize columns to 0-1 so they share an axis
# despite having different units/scales (Capacity_TWh excluded, since
# it's constant within one area and would divide by zero) ---
normalize_cols = ["Filling_level", "Filling_TWh", "Filling_level_prev_week", "Change_filling_level"]

# --- Streamlit-specific: render the plot based on the widget choices ---
fig, ax = plt.subplots(figsize=(10, 5))

if col_choice == "All columns":
    norm = (subset[normalize_cols] - subset[normalize_cols].min()) / (
        subset[normalize_cols].max() - subset[normalize_cols].min()
    )
    for col in normalize_cols:
        ax.plot(subset["Date"], norm[col], label=col, linewidth=1.2)
    ax.set_ylabel("Normalized value (0-1)")
    ax.legend()
    ax.set_title("All columns (normalized), Norway")
else:
    ax.plot(subset["Date"], subset[col_choice], linewidth=1.2, color="tab:blue")
    ax.set_ylabel(col_choice)
    ax.set_title(f"{col_choice}, Norway")

ax.set_xlabel("Date")
st.pyplot(fig)