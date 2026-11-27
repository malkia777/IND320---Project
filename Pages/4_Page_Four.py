import calendar
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from urllib.parse import quote
from pymongo import MongoClient


# Olive cursor.
olive_svg = """
<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"
     viewBox="0 0 32 32">
    <path d="M19 12 Q22 7 27 5"
          fill="none" stroke="#374526" stroke-width="2"/>
    <ellipse cx="24" cy="7" rx="6" ry="3"
             fill="#73834D" transform="rotate(-30 24 7)"/>
    <ellipse cx="14" cy="20" rx="10" ry="12"
             fill="#52683D" transform="rotate(30 14 20)"/>
    <ellipse cx="11" cy="16" rx="3" ry="5"
             fill="#91A46C" transform="rotate(30 11 16)"/>
</svg>
"""

cursor = f'url("data:image/svg+xml,{quote(olive_svg)}") 16 16, auto'


# Geometric net pattern inspired by a keffiyeh.
keffiyeh_svg = """
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48"
     viewBox="0 0 48 48">
    <rect width="48" height="48" fill="#FAF7EF"/>
    <g fill="none" stroke="#000000" stroke-width="1.5">
        <path d="M-24 0L24 48 M0 0L48 48 M24 0L72 48"/>
        <path d="M-24 48L24 0 M0 48L48 0 M24 48L72 0"/>
    </g>
    <g fill="#000000">
        <rect x="21" y="9" width="6" height="6"
              transform="rotate(45 24 12)"/>
        <rect x="21" y="33" width="6" height="6"
              transform="rotate(45 24 36)"/>
    </g>
</svg>
"""

pattern = f'url("data:image/svg+xml,{quote(keffiyeh_svg)}")'


st.markdown(
    f"""
    <style>
    /* Cream main area with black, boxy lettering. */
    .stApp {{
        background-color: #FAF7EF;
        color: #000000;
    }}

    h1, h2, h3, h4, h5, h6,
    p, a, label, button,
    [data-testid="stCaptionContainer"],
    [data-testid="stWidgetLabel"] {{
        font-family: "Courier New", monospace !important;
        color: #000000 !important;
    }}

    .block-container {{
        padding-top: 5rem;
    }}

    /* Three sections across the top: black, white and green. */
    [data-testid="stHeader"] {{
        background: linear-gradient(
            to right,
            #000000 0%,
            #000000 33.33%,
            #FFFFFF 33.33%,
            #FFFFFF 66.66%,
            #00843D 66.66%,
            #00843D 100%
        );
        border-bottom: 3px solid #000000;
    }}

    /* Keep toolbar controls readable over all three colours. */
    [data-testid="stHeader"] button {{
        background-color: #FAF7EF;
        color: #000000 !important;
    }}

    /* Keffiyeh-inspired sidebar. */
    [data-testid="stSidebar"] {{
        background-color: #FAF7EF;
        background-image: {pattern};
        background-repeat: repeat;
        background-size: 48px 48px;
    }}

    /* Plain backing keeps page names readable. */
    [data-testid="stSidebarNav"] {{
        background-color: #FAF7EF;
        margin: 16px;
        padding: 12px 4px;
        border: 2px solid #000000;
        border-radius: 8px;
    }}

    [data-testid="stSidebarNav"] a,
    [data-testid="stSidebarNav"] a span,
    [data-testid="stSidebarNav"] p {{
        color: #000000 !important;
    }}

    [data-testid="stSidebarNav"] a:hover,
    [data-testid="stSidebarNav"] a[aria-current="page"] {{
        background-color: #E0E7D5;
    }}

    h1 {{
        border-bottom: 3px solid #00843D;
        padding-bottom: 18px;
    }}

    /* Light selection boxes with black text. */
    [data-baseweb="select"] > div {{
        background-color: #FFFFFF;
        color: #000000;
    }}

    [data-baseweb="select"] input {{
        color: #000000 !important;
    }}

    /* Keep the olive cursor. */
    *, *::before, *::after {{
        cursor: {cursor} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("Cross-border electricity transfers")


@st.cache_resource
def get_collection():
    # Read the MongoDB connection string from Streamlit secrets.
    client = MongoClient(st.secrets["mongo"]["uri"], tz_aware=True)
    return client["ind320"]["crossborder_flows"]


@st.cache_data(ttl=600, max_entries=3)
def load_data(connection):
    # Download only the selected connection.
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


def style_chart(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FAF7EF",
        plot_bgcolor="#FAF7EF",
        font=dict(
            family="Courier New, monospace",
            size=15,
            color="#000000",
        ),
        title=dict(
            font=dict(size=18, color="#000000"),
        ),
        legend=dict(
            orientation="h",
            y=-0.25,
            font=dict(size=14, color="#000000"),
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font=dict(size=14, color="#000000"),
        ),
        margin=dict(l=75, r=25, t=85, b=110),
    )

    fig.update_xaxes(
        title_font=dict(size=16, color="#000000"),
        tickfont=dict(size=14, color="#000000"),
        automargin=True,
    )

    fig.update_yaxes(
        title_font=dict(size=16, color="#000000"),
        tickfont=dict(size=14, color="#000000"),
        automargin=True,
    )

    # Put pie labels outside the slices so they remain readable.
    fig.update_traces(
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(size=14, color="#000000"),
        automargin=True,
        selector=dict(type="pie"),
    )

    return fig

@st.cache_data(ttl=600)
def load_connections():
    return sorted(get_collection().distinct("connection"))

with st.spinner("Loading available electricity connections…"):
    connections = load_connections()

if not connections:
    st.info("No data have been uploaded yet.")
    st.stop()

# Give the flow chart more room.
left, right = st.columns([1, 2])

# Use consistent colours in both charts.
colors = {
    "into Norway": "#52683D",
    "out of Norway": "#781F36",
}

with left:
    st.subheader("Annual transfers")

    connection = st.radio("Connection", connections)
    with st.spinner("Loading electricity transfer data…"):
        df = load_data(connection)

    if df.empty:
        st.info("No observations for this connection.")
        st.stop()

    years = sorted(df["time"].dt.year.unique(), reverse=True)
    year = st.selectbox("Year", years)

    # Estimate interval durations before filtering to the selected year.
    next_time = df.groupby("direction")["time"].shift(-1)
    df["hours"] = (next_time - df["time"]).dt.total_seconds() / 3600

    yearly = df[df["time"].dt.year == year].copy()

    # Use 15-minute and hourly intervals, matching the notebook.
    valid = yearly["hours"].isin([0.25, 1.0]) & yearly["flow_mw"].notna()
    energy = yearly[valid].copy()
    energy["energy_mwh"] = energy["flow_mw"] * energy["hours"]

    annual = energy.groupby("direction")["energy_mwh"].sum().reindex(
        ["into Norway", "out of Norway"]
    )

    if annual.isna().any() or (annual < 0).any() or annual.sum() <= 0:
        st.info("Insufficient valid data for the pie chart.")
    else:
        # Interactive energy-share chart.
        fig = go.Figure(
            go.Pie(
                labels=annual.index,
                values=annual.values,
                marker=dict(
                    colors=[colors[direction] for direction in annual.index],
                    line=dict(color="#FAF7EF", width=2),
                ),
                textinfo="percent",
                textfont=dict(color="#FFFFFF"),
                hovertemplate=(
                    "%{label}<br>"
                    "%{value:,.1f} MWh<br>"
                    "%{percent}<extra></extra>"
                ),
                sort=False,
            )
        )

        fig.update_layout(
            title=f"{connection}: estimated energy, {year}",
            height=420,
        )

        st.plotly_chart(style_chart(fig), width="stretch")

    st.caption(
        "Totals represent available observations, "
        "which may cover only part of the year."
    )

    # Show coverage so partial years are not mistaken for complete years.
    with st.expander("Observed hours used in the pie chart"):
        st.dataframe(
            energy.groupby("direction")["hours"].sum().rename("Hours")
        )

with right:
    st.subheader("Daily flow")

    # Start with a month that actually contains observations.
    available_months = sorted(
        yearly["time"].dt.month.unique().tolist()
    )

    months = st.pills(
        "Months",
        options=list(range(1, 13)),
        format_func=lambda month: calendar.month_abbr[month],
        selection_mode="multi",
        default=[available_months[0]],
    )

    selected = yearly[yearly["time"].dt.month.isin(months)]

    if selected.empty:
        st.info("Select months containing data.")
    else:
        fig = go.Figure()

        # Plot each direction separately.
        for direction, group in selected.groupby("direction"):

            # Separate months prevent lines crossing unselected months.
            for index, (_, month_data) in enumerate(
                group.groupby(group["time"].dt.month)
            ):
                fig.add_trace(
                    go.Scatter(
                        x=month_data["time"],
                        y=month_data["flow_mw"],
                        name=direction,
                        legendgroup=direction,
                        showlegend=index == 0,
                        mode="lines",
                        line=dict(
                            color=colors[direction],
                            width=2,
                        ),
                        hovertemplate=(
                            "%{x|%d %b %Y %H:%M}<br>"
                            "%{y:,.1f} MW"
                            "<extra>%{fullData.name}</extra>"
                        ),
                    )
                )

        fig.update_layout(
            title=f"{connection}: electricity flow, {year}",
            xaxis_title="Date (Europe/Oslo)",
            yaxis_title="Power (MW)",
            hovermode="x unified",
            height=480,
        )

        fig = style_chart(fig)
        fig.update_xaxes(gridcolor="#E0DED5")
        fig.update_yaxes(gridcolor="#E0DED5")

        st.plotly_chart(fig, width="stretch")

with st.expander("Data source"):
    st.write(
        "ENTSO-E cross-border electricity flows, stored in Cassandra, "
        "extracted using Spark and read here from MongoDB. "
        "Energy totals are estimated from observation intervals."
    )
    st.markdown("[ENTSO-E](https://transparency.entsoe.eu/)")