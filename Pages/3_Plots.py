import pandas as pd
import streamlit as st
import matplotlib as plt

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

area = df[df["Area_type"] == "NO"].sort_values("Date")

# All CSV columns except Date itself (Date is the x-axis, not a
# plottable series) are offered in the dropdown, per the spec's
# "any single column in the CSV."
all_cols = [c for c in df.columns if c != "Date"]
numeric_cols = [c for c in all_cols if pd.api.types.is_numeric_dtype(area[c])]

# --- Streamlit-specific: widgets for column and month selection ---
col_choice = st.selectbox("Column to plot", options=["All columns"] + all_cols)

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
normalize_cols = [c for c in ["Filling_level", "Filling_TWh",
                               "Filling_level_prev_week", "Change_filling_level"]
                   if c in numeric_cols]

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
    st.pyplot(fig)

elif col_choice in numeric_cols:
    ax.plot(subset["Date"], subset[col_choice], linewidth=1.2, color="tab:blue")
    ax.set_xlabel("Date")
    ax.set_ylabel(col_choice)
    ax.set_title(f"{col_choice}, Norway")
    st.pyplot(fig)

else:
    # Non-numeric column selected (e.g. Area_type, Next_publishdate):
    # not meaningfully plottable as a line series, so show a message
    # instead of crashing or drawing a nonsensical chart.
    plt.close(fig)
    st.info(
        f"'{col_choice}' is not a numeric column, so it can't be shown "
        "as a line plot. Try a measurement column instead."
    )
    st.write(subset[["Date", col_choice]])