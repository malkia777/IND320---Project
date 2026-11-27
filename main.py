import streamlit as st

st.set_page_config(
    page_title="IND320 - Reservoirs Project",
    layout="wide",
)

def home():
    from urllib.parse import quote

    # Draw a small olive to use as the mouse cursor.
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

    # Cream background, green accents, black cursive text, and olive cursor.
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: #F2E6CE;
            color: #000000;
        }}

        /* Dark olive top bar. */
        [data-testid="stHeader"] {{
            background-color: #35452A;
        }}

        /* Beige sidebar. */
        [data-testid="stSidebar"] {{
            background-color: #E8DABD;
        }}

        /* Black cursive text. */
        h1, h2, h3, h4, h5, h6,
        p, a, label, button,
        [data-testid="stCaptionContainer"] {{
            font-family: "Segoe Print", "Bradley Hand", cursive;
            color: #000000 !important;
        }}

        /* Black navigation text, including the selected page. */
        [data-testid="stSidebarNav"] a,
        [data-testid="stSidebarNav"] a span,
        [data-testid="stSidebarNav"] p {{
            color: #000000 !important;
        }}

        /* Olive underline below the page title. */
        h1 {{
            border-bottom: 3px solid #52683D;
            padding-bottom: 18px;
        }}

        a {{
            text-decoration-color: #52683D !important;
        }}

        /* Olive mouse cursor. */
        *, *::before, *::after {{
            cursor: {cursor} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
        /* Tree trunk beside the navigation links. */
        [data-testid="stSidebarNav"] ul {
            border-left: 7px solid #655039;
            margin-left: 24px;
            padding-left: 0;
        }

        /* Leave room for a branch beside each link. */
        [data-testid="stSidebarNav"] li {
            position: relative;
            list-style: none;
            padding-left: 36px;
            margin: 16px 0;
        }

        /* Branch connecting the trunk to each page. */
        [data-testid="stSidebarNav"] li::before {
            content: "";
            position: absolute;
            left: 0;
            top: 50%;
            width: 35px;
            height: 3px;
            background: #655039;
            transform: rotate(-12deg);
            transform-origin: left center;
            pointer-events: none;
        }

        /* Olive leaf on each branch. */
        [data-testid="stSidebarNav"] li::after {
            content: "";
            position: absolute;
            left: 12px;
            top: calc(50% - 13px);
            width: 20px;
            height: 9px;
            background: #52683D;
            border-radius: 100% 0 100% 0;
            transform: rotate(-20deg);
            pointer-events: none;
        }

        /* Black cursive page names. */
        [data-testid="stSidebarNav"] a,
        [data-testid="stSidebarNav"] a span {
            font-family: "Segoe Print", "Bradley Hand", cursive;
            color: #000000 !important;
        }

        /* Highlight the page under the mouse or currently selected. */
        [data-testid="stSidebarNav"] a:hover,
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background-color: #DCE3CC;
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.title("IND320 – Reservoirs Project")
    st.caption("Malk · IND320 — Data to Decision")

    st.write(
        "This project explores Norwegian reservoir filling levels "
        "alongside weather, electricity transfers and currency exchange rates."
    )

    st.write(
        "Use the sidebar to explore the data, investigate patterns "
        "and forecast reservoir filling levels."
    )

    st.divider()

    st.subheader("Explore the project")

    left, middle, right = st.columns(3)

    with left:
        st.markdown(
            """
            <svg width="70" height="80" viewBox="0 0 70 80"
                 role="img" aria-label="Fig">
                <path d="M35 15 Q33 8 39 3"
                      stroke="#52683D" stroke-width="5" fill="none"/>
                <path d="M35 13 C29 27 10 34 12 54
                         C14 78 56 78 58 54
                         C60 34 41 27 35 13"
                      fill="#704064"/>
                <path d="M35 28 C28 40 23 44 24 56
                         C25 69 45 69 46 56
                         C47 44 42 40 35 28"
                      fill="#CF8190"/>
                <g fill="#F2DDBB">
                    <circle cx="31" cy="48" r="1.5"/>
                    <circle cx="39" cy="51" r="1.5"/>
                    <circle cx="33" cy="58" r="1.5"/>
                    <circle cx="40" cy="61" r="1.5"/>
                </g>
            </svg>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Explore data")
        st.write(
            "View reservoir measurements, compare areas "
            "and explore electricity transfers."
        )
        st.page_link("Pages/2_Data_Table.py", label="View data tables")
        st.page_link("Pages/3_Plots.py", label="Explore reservoir plots")
        st.page_link("Pages/4_Page_Four.py", label="Explore electricity transfers")

    with middle:
        st.markdown(
            """
            <svg width="70" height="80" viewBox="0 0 70 80"
                 role="img" aria-label="Pomegranate">
                <path d="M26 22 L24 10 L32 15 L36 5
                         L40 15 L48 10 L45 24"
                      fill="#9D2938"/>
                <circle cx="35" cy="47" r="27" fill="#B83B48"/>
                <path d="M35 25 A22 22 0 0 1 35 69 Z"
                      fill="#F0C6AC"/>
                <g fill="#9D1635">
                    <ellipse cx="41" cy="36" rx="3" ry="4"/>
                    <ellipse cx="49" cy="42" rx="3" ry="4"/>
                    <ellipse cx="40" cy="47" rx="3" ry="4"/>
                    <ellipse cx="49" cy="53" rx="3" ry="4"/>
                    <ellipse cx="40" cy="59" rx="3" ry="4"/>
                </g>
            </svg>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Analyse patterns")
        st.write(
            "Investigate reservoir trends and seasonality, "
            "and identify unusual weather observations."
        )
        st.page_link("Pages/5_Reservoir_Analysis.py", label="Analyse reservoirs")
        st.page_link("Pages/6_Weather_Analysis.py", label="Analyse weather")

    with right:
        st.markdown(
            """
            <svg width="70" height="80" viewBox="0 0 70 80"
                 role="img" aria-label="Lemon">
                <path d="M43 23 Q49 10 63 15
                         Q57 29 43 23"
                      fill="#52683D"/>
                <path d="M12 57 C4 45 20 24 37 25
                         L46 21 L49 29
                         C64 39 54 61 35 67
                         L25 72 L22 65 Z"
                      fill="#E8C644"/>
                <path d="M19 48 Q22 35 35 33"
                      stroke="#FFF0A2" stroke-width="4"
                      stroke-linecap="round" fill="none"/>
            </svg>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Forecast filling")
        st.write(
            "Use River to predict reservoir filling for the coming "
            "months and compare predictions with historical observations."
        )
        st.page_link("Pages/8_Forecasting.py", label="Forecast reservoir filling")
        st.page_link("Pages/7_Currency.py", label="Explore currency exchange rates")

    st.divider()

    st.subheader("Data sources")

    st.markdown(
        """
        - **[NVE Magasinstatistikk](https://www.nve.no/energi/analyser-og-statistikk/magasinstatistikk/)**  
          Weekly reservoir filling levels and storage information.
        - **[ENTSO-E](https://transparency.entsoe.eu/)**  
          Cross-border electricity transfers.
        - **[Open-Meteo](https://open-meteo.com/)**  
          Historical temperature, precipitation and snowfall.
        - **[Norges Bank](https://www.norges-bank.no/en/topics/Statistics/exchange_rates/)**  
          EUR/NOK and USD/NOK exchange rates.
        """
    )

    st.caption(
        "The notebook's main historical period is 2018–2024. "
        "Coverage differs between sources; the downloaded ENTSO-E "
        "dataset contains only one day. Each analysis should be "
        "interpreted using its displayed dates."
    )

    st.divider()

    st.markdown(
        "[View the project on GitHub]"
        "(https://github.com/malkia777/IND320---Project)"
    )


pages = {
    "Start here": [
        st.Page(home, title="Home", default=True),
        st.Page("Pages/9_Map.py", title="Map and area selection"),
    ],
    "Explore data": [
        st.Page("Pages/2_Data_Table.py", title="Data overview"),
        st.Page("Pages/3_Plots.py", title="Reservoir plots"),
        st.Page("Pages/4_Page_Four.py", title="Electricity transfers"),
        st.Page("Pages/7_Currency.py", title="Currency"),
    ],
    "Analyse patterns": [
        st.Page("Pages/5_Reservoir_Analysis.py", title="Reservoir analysis"),
        st.Page("Pages/6_Weather_Analysis.py", title="Weather and correlation"),
    ],
    "Predict": [
        st.Page("Pages/8_Forecasting.py", title="Forecasting"),
    ],
}

navigation = st.navigation(pages, position="sidebar")
navigation.run()