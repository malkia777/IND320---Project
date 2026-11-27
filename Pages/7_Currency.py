from datetime import date
from io import StringIO
from urllib.parse import quote

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


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


st.markdown(
    f"""
    <style>
    /* Cream background with black, boxy text. */
    .stApp {{
        background-color: #F2E6CE;
        color: #000000;
    }}

    h1, h2, h3, h4, h5, h6,
    p, a, label, button,
    [data-testid="stCaptionContainer"],
    [data-testid="stWidgetLabel"] {{
        font-family: "Courier New", monospace !important;
        color: #000000 !important;
    }}

    /* Burgundy top bar with an olive border. */
    [data-testid="stHeader"] {{
        background-color: #781F36;
        border-bottom: 4px solid #52683D;
    }}

    [data-testid="stHeader"] * {{
        color: #FAF7EF !important;
    }}

    /* Burgundy sidebar with cream navigation text. */
    [data-testid="stSidebar"] {{
        background-color: #781F36;
    }}

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] button,
    [data-testid="stSidebarNav"] a span {{
        color: #FAF7EF !important;
    }}

    [data-testid="stSidebarNav"] a:hover,
    [data-testid="stSidebarNav"] a[aria-current="page"] {{
        background-color: #952D48;
    }}

    .block-container {{
        padding-top: 5rem;
    }}

    /* Pomegranate icon beside the title. */
    .currency-heading {{
        display: flex;
        align-items: center;
        gap: 16px;
        border-bottom: 3px solid #781F36;
        margin-bottom: 24px;
        padding-bottom: 14px;
    }}

    .currency-heading h1 {{
        margin: 0;
        padding: 0;
    }}

    /* Readable date fields. */
    [data-testid="stDateInput"] input {{
        background-color: #FAF7EF;
        color: #000000 !important;
        font-family: "Courier New", monospace;
    }}

    *, *::before, *::after {{
        cursor: {cursor} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# Draw the pomegranate directly, without a separate image file.
st.markdown(
    """
    <div class="currency-heading">
        <svg width="65" height="75" viewBox="0 0 70 80"
             role="img" aria-label="Pomegranate"
             style="flex-shrink:0">
            <path d="M26 22 L24 10 L32 15 L36 5
                     L40 15 L48 10 L45 24"
                  fill="#781F36"/>
            <circle cx="35" cy="47" r="27" fill="#A73550"/>
            <path d="M35 25 A22 22 0 0 1 35 69 Z"
                  fill="#F0C6AC"/>
            <g fill="#781F36">
                <ellipse cx="41" cy="36" rx="3" ry="4"/>
                <ellipse cx="49" cy="42" rx="3" ry="4"/>
                <ellipse cx="40" cy="47" rx="3" ry="4"/>
                <ellipse cx="49" cy="53" rx="3" ry="4"/>
                <ellipse cx="40" cy="59" rx="3" ry="4"/>
            </g>
        </svg>
        <h1>Currency exchange rates</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write(
    "Explore EUR/NOK and USD/NOK exchange rates from Norges Bank. "
    "The values show how many Norwegian kroner are needed "
    "to buy one euro or one US dollar."
)


@st.cache_data(ttl=86400)
def load_rates(start_date, end_date):
    # Download daily exchange rates for the selected period.
    response = requests.get(
        "https://data.norges-bank.no/api/data/EXR/B.EUR+USD.NOK.SP",
        params={
            "startPeriod": str(start_date),
            "endPeriod": str(end_date),
            "format": "csv",
            "locale": "en",
        },
        timeout=60,
    )
    response.raise_for_status()

    data = pd.read_csv(StringIO(response.text), sep=";")

    # Return an empty table if the period contains no observations.
    if data.empty:
        return pd.DataFrame(columns=["EUR_NOK", "USD_NOK"])

    data["TIME_PERIOD"] = pd.to_datetime(data["TIME_PERIOD"])
    data["OBS_VALUE"] = pd.to_numeric(data["OBS_VALUE"])

    # Give each currency its own column.
    rates = data.pivot(
        index="TIME_PERIOD",
        columns="BASE_CUR",
        values="OBS_VALUE",
    )

    rates = rates.rename(
        columns={"EUR": "EUR_NOK", "USD": "USD_NOK"}
    )
    rates.index.name = "Date"

    return rates.sort_index()


# Start with the same historical period as the notebook.
selected_dates = st.date_input(
    "Date interval",
    value=(date(2018, 1, 1), date(2024, 12, 31)),
    min_value=date(2018, 1, 1),
    max_value=date.today(),
)

if len(selected_dates) != 2:
    st.info("Choose a start and end date.")
    st.stop()

currencies = st.multiselect(
    "Currencies to display",
    options=["EUR_NOK", "USD_NOK"],
    default=["EUR_NOK", "USD_NOK"],
    format_func=lambda currency: currency.replace("_", "/"),
)

if not currencies:
    st.info("Select at least one currency.")
    st.stop()

with st.spinner("Loading exchange rates…"):
    rates = load_rates(selected_dates[0], selected_dates[1])

if rates.empty:
    st.info("No exchange-rate observations are available for this interval.")
    st.stop()


# Consistent colours for the two currencies.
colors = {
    "EUR_NOK": "#781F36",
    "USD_NOK": "#52683D",
}

fig = go.Figure()

for currency in currencies:
    fig.add_trace(
        go.Scatter(
            x=rates.index,
            y=rates[currency],
            name=currency.replace("_", "/"),
            mode="lines",
            line=dict(color=colors[currency], width=2),
            connectgaps=False,
            hovertemplate=(
                "%{x|%d %b %Y}<br>"
                "%{y:.4f} NOK"
                "<extra>%{fullData.name}</extra>"
            ),
        )
    )

fig.update_layout(
    template="plotly_white",
    title=dict(
        text="Exchange rates over time",
        font=dict(size=18, color="#000000"),
    ),
    paper_bgcolor="#FAF7EF",
    plot_bgcolor="#FAF7EF",
    font=dict(
        family="Courier New, monospace",
        size=14,
        color="#000000",
    ),
    xaxis_title="Date",
    yaxis_title="NOK per EUR or USD",
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="#FFFFFF",
        font=dict(color="#000000"),
    ),
    legend=dict(
        orientation="h",
        y=1.12,
        font=dict(color="#000000"),
    ),
    margin=dict(l=80, r=30, t=110, b=65),
    height=500,
)

fig.update_xaxes(
    title_font=dict(size=15, color="#000000"),
    tickfont=dict(size=13, color="#000000"),
    gridcolor="#DED5C5",
    automargin=True,
)

fig.update_yaxes(
    title_font=dict(size=15, color="#000000"),
    tickfont=dict(size=13, color="#000000"),
    gridcolor="#DED5C5",
    automargin=True,
)

st.plotly_chart(fig, width="stretch")

st.caption(
    "A rising rate means the Norwegian krone is weakening against "
    "that currency; a falling rate means it is strengthening. "
    "Observations are generally available on business days."
)

with st.expander("View exchange-rate data"):
    st.dataframe(rates[currencies], width="stretch")

st.download_button(
    "Download selected exchange rates",
    data=rates[currencies].to_csv().encode("utf-8"),
    file_name="exchange_rates.csv",
    mime="text/csv",
)

st.markdown(
    "[Source: Norges Bank]"
    "(https://www.norges-bank.no/en/topics/Statistics/exchange_rates/)"
)