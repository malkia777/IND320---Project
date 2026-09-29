import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Plots",
    layout="wide",
)

st.title("Plots of the data")

@st.cache_data
def load_data():
    df = pd.read_csv("Project/data/reservoirs.csv")

    # renaming the columns of the dataset (same mapping as the notebook)
    df = df.rename(columns={
        'dato_Id': 'Date', "omrType": "Area_type", "omrnr": "Area_number",
        "iso_aar": "ISO_year", "iso_uke": "ISO_week",
        "fyllingsgrad": "Filling_level", "kapasitet_TWh": "Capacity_TWh",
        "fylling_TWh": "Filling_TWh",
        "neste_Publiseringsdato": "Next_publishdate",
        "fyllingsgrad_forrige_uke": "Filling_level_prev_week",
        "endring_fyllingsgrad": "Change_filling_level",
    })

    # 0001-01-01 is a "not set" placeholder in the source data, so it
    # is coerced to NaT rather than raising an out-of-bounds error.
    # format="ISO8601" is dropped here (Streamlit's environment may run
    # an older pandas that doesn't support it); letting pandas infer the
    # format works the same on this clean ISO-formatted data.
    for col in ["Date", "Next_publishdate"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # sorting the dataframe by date so the datapoints become sequential
    df = df.sort_values("Date")

    return df


df = load_data()

# Sanity check while debugging — remove once confirmed working.
# st.write(df["Date"].dtype)

# From the notebook: filter to one area so "a column" means one
# consistent time series, not 9 overlapping regions mixed together.
area = df[df["Area_type"] == "NO"].sort_values("Date")

all_cols = [c for c in df.columns if c != "Date"]
numeric_cols = [c for c in all_cols if pd.api.types.is_numeric_dtype(area[c])]

# --- Streamlit-specific: widgets for column and month selection ---
col_choice = st.selectbox("Column to plot", options=["All columns"] + all_cols)

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
    ax.set_xlabel("Date")
    st.pyplot(fig)

elif col_choice in numeric_cols:
    ax.plot(subset["Date"], subset[col_choice], linewidth=1.2, color="tab:blue")
    ax.set_xlabel("Date")
    ax.set_ylabel(col_choice)
    ax.set_title(f"{col_choice}, Norway")
    st.pyplot(fig)

else:
    plt.close(fig)
    st.info(
        f"'{col_choice}' is not a numeric column, so it can't be shown "
        "as a line plot. Try a measurement column instead."
    )
    st.write(subset[["Date", col_choice]])