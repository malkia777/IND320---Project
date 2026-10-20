import calendar
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from pymongo import MongoClient

st.title("Cross-border electricity transfers")

@st.cache_resource
def get_collection():
    # Read the mongo connection string from streamlit secrets
    client = MongoClient(st.secrets["mongo"]["uri"], tz_aware=True)
    return client["ind320"]["crossborder_flows"]


@st.cache_data(ttl=600, max_entries=3)
def load_data(connection):
    #Downloading only selected connection
    records = get_collection().find(
        {"connection": connection},
        {"_id": 0, "time": 1, "direction": 1, "flow_mw": 1},
    )
    df = pd.DataFrame(list(records))

    if not df.empty:
        df["time"] = pd.to_datetime(df["time"], utc=True).dt.tz_convert(
            "Europe/Oslo"
        )
        df = df.sort_values(["direction", "time"])

    return df


collection = get_collection()
connections = sorted(collection.distinct("connection"))

if not connections:
    st.info("No data have been uploaded yet.")
    st.stop()

left, right = st.columns(2)

with left:
    connection = st.radio("Connection", connections)
    df = load_data(connection)

    years = sorted(df["time"].dt.year.unique(), reverse=True)
    year = st.selectbox("Year", years)

    # Estimate interval durations before filtering to the selected year.
    next_time = df.groupby("direction")["time"].shift(-1)
    df["hours"] = (next_time - df["time"]).dt.total_seconds() / 3600

    yearly = df[df["time"].dt.year == year].copy()

    # Match the notebook: use 15-minute and hourly intervals only.
    valid = yearly["hours"].isin([0.25, 1.0]) & yearly["flow_mw"].notna()
    energy = yearly[valid].copy()
    energy["energy_mwh"] = energy["flow_mw"] * energy["hours"]

    annual = energy.groupby("direction")["energy_mwh"].sum().reindex(
        ["into Norway", "out of Norway"]
    )

    if annual.isna().any() or annual.sum() <= 0:
        st.info("Insufficient data for the pie chart.")
    else:
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.pie(
            annual,
            labels=annual.index,
            autopct="%1.1f%%",
            startangle=90,
        )
        ax.set_title(f"{connection}: estimated energy, {year}")
        st.pyplot(fig)
        plt.close(fig)

    # Show coverage so partial years are not mistaken for complete years.
    st.write("Observed hours used in the pie chart:")
    st.dataframe(
        energy.groupby("direction")["hours"].sum().rename("Hours")
    )

with right:
    months = st.pills(
        "Months",
        options=list(range(1, 13)),
        format_func=lambda month: calendar.month_abbr[month],
        selection_mode="multi",
        default=[1],
    )

    selected = yearly[yearly["time"].dt.month.isin(months)]

    if selected.empty:
        st.info("Select months containing data.")
    else:
        fig, ax = plt.subplots(figsize=(7, 5))

        # Plot each direction separately.
        for direction, group in selected.groupby("direction"):
            color = (
                "tab:blue" if direction == "into Norway" else "tab:orange"
            )

            # Separate months prevent lines crossing unselected months.
            for index, (_, month_data) in enumerate(
                group.groupby(group["time"].dt.month)
            ):
                ax.plot(
                    month_data["time"],
                    month_data["flow_mw"],
                    label=direction if index == 0 else None,
                    color=color,
                    linewidth=1,
                )

        ax.set_title(f"{connection}: electricity flow, {year}")
        ax.set_xlabel("Date (Europe/Oslo)")
        ax.set_ylabel("Power (MW)")
        ax.legend()

        st.pyplot(fig)
        plt.close(fig)

with st.expander("Data source"):
    st.write(
        "ENTSO-E cross-border electricity flows, stored in Cassandra, "
        "extracted using Spark and read here from MongoDB. "
        "Energy totals are estimated from observation intervals."
    )
    st.markdown("[ENTSO-E](https://transparency.entsoe.eu/)")