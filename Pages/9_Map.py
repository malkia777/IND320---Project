from datetime import date

import folium
import geopandas as gpd
import pandas as pd
import requests
import streamlit as st

from branca.colormap import LinearColormap
from shapely.geometry import Point
from streamlit_folium import st_folium

from data_loader import load_data

from urllib.parse import quote


# Olive cursor.
olive_svg = """
<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32">
    <path d="M18 13 Q22 6 28 5"
          stroke="#52683D" stroke-width="3" fill="none"/>
    <ellipse cx="24" cy="8" rx="6" ry="3" fill="#73934D"/>
    <ellipse cx="14" cy="21" rx="10" ry="12"
             fill="#52683D" transform="rotate(25 14 21)"/>
    <ellipse cx="11" cy="17" rx="3" ry="5" fill="#91A46C"/>
</svg>
"""

cursor = f'url("data:image/svg+xml,{quote(olive_svg)}") 16 16, auto'

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: #FFFFFF;
        color: #000000;
    }}

    [data-testid="stHeader"] {{
        background-color: #000000;
        border-bottom: 4px solid #CE1126;
    }}

    [data-testid="stSidebar"] {{
        background-color: #00843D;
    }}

    h1, h2, h3, h4, h5, h6,
    p, a, label, button,
    [data-testid="stCaptionContainer"],
    [data-testid="stWidgetLabel"],
    [data-testid="stSidebarNav"] a span {{
        font-family: "Courier New", monospace !important;
        color: #000000 !important;
    }}

    [data-testid="stHeader"] * {{
        color: #FFFFFF !important;
    }}

    [data-testid="stSidebarNav"] a:hover,
    [data-testid="stSidebarNav"] a[aria-current="page"] {{
        background-color: #A9D5AE;
    }}

    [data-baseweb="select"] > div,
    [data-testid="stDateInput"] input {{
        background-color: #FFFFFF;
        color: #000000;
    }}

    .block-container {{
        padding-top: 5rem;
    }}

    h1 {{
        border-bottom: 3px solid #00843D;
        padding-bottom: 18px;
    }}

    *, *::before, *::after {{
        cursor: {cursor} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("Map and area selection")


@st.cache_data
def load_boundaries(filename):
    return gpd.read_file(filename).to_crs("EPSG:4326")


@st.cache_data(ttl=86400)
def weather_value(lat, lon, start, end, property_name):
    # Include the previous UTC day to cover the first Norwegian day.
    response = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": lat,
            "longitude": lon,
            "start_date": str(start - pd.Timedelta(days=1)),
            "end_date": str(end),
            "models": "era5",
            "hourly": property_name,
            "timezone": "UTC",
        },
        timeout=90,
    )
    response.raise_for_status()

    weather = pd.DataFrame(response.json()["hourly"])
    weather["time"] = (
        pd.to_datetime(weather["time"], utc=True)
        .dt.tz_convert("Europe/Oslo")
    )

    selected = weather[
        (weather["time"].dt.date >= start)
        & (weather["time"].dt.date <= end)
    ][property_name]

    if selected.empty or selected.isna().any():
        return None

    # Average temperature; total precipitation or snowfall.
    if property_name == "temperature_2m":
        return float(selected.mean())

    return float(selected.sum())


boundary_layer = st.selectbox(
    "Boundary layer",
    ["Price areas", "Water areas"],
)

if boundary_layer == "Water areas":
    with st.spinner("Loading water-area boundaries…"):
        water_areas = load_boundaries("data/water_areas.geojson")

    # These identifiers belong to the drainage dataset, not VASS statistics.
    water_areas["water_id"] = water_areas["vassdragsomradenr"].astype(str)

    st.info(
        "These are drainage areas from NVE Atlas. Their numbers are not "
        "the VASS groups used in Magasinstatistikk. Selecting one does "
        "not change the reservoir region used by the other pages."
    )

    selected_water = st.session_state.get("water_area")

    # Colours distinguish boundaries; they do not represent measurements.
    palette = [
        "#52683D", "#781F36", "#B88A3B",
        "#477B82", "#75628D", "#759C78",
    ]

    def water_style(feature):
        number = feature["properties"]["water_id"]
        selected = number == selected_water

        return {
            "fillColor": palette[int(number) % len(palette)],
            "fillOpacity": 0.3,
            "color": "#CE1126" if selected else "#000000",
            "weight": 5 if selected else 1,
        }

    water_map = folium.Map(
        location=[65, 13],
        zoom_start=5,
        tiles="OpenStreetMap",
    )

    folium.GeoJson(
        water_areas.to_json(),
        name="Drainage areas",
        style_function=water_style,
        tooltip=folium.GeoJsonTooltip(
            fields=["water_id", "vassdragsomradenavn"],
            aliases=["Drainage area:", "Name:"],
        ),
    ).add_to(water_map)

    # Preserve the olive cursor and boxy font inside the map frame.
    water_map.get_root().header.add_child(
        folium.Element(
            f"""
            <style>
            .leaflet-container,
            .leaflet-tooltip {{
                font-family: "Courier New", monospace;
                color: #000000;
            }}
            .leaflet-container,
            .leaflet-container * {{
                cursor: {cursor} !important;
            }}
            </style>
            """
        )
    )

    west, south, east, north = water_areas.total_bounds
    water_map.fit_bounds([[south, west], [north, east]])

    result = st_folium(
        water_map,
        height=650,
        use_container_width=True,
        returned_objects=["last_clicked"],
        key="water_area_map",
    )

    clicked = result.get("last_clicked")

    if clicked:
        coordinates = (clicked["lng"], clicked["lat"])

        if coordinates != st.session_state.get("last_water_map_click"):
            st.session_state["last_water_map_click"] = coordinates

            match = water_areas[
                water_areas.geometry.covers(Point(*coordinates))
            ]

            if not match.empty:
                st.session_state["water_area"] = match.iloc[0]["water_id"]
                st.rerun()

    if selected_water is not None:
        selected_row = water_areas[
            water_areas["water_id"] == selected_water
        ].iloc[0]

        st.success(
            f"Selected drainage area: {selected_water} — "
            f"{selected_row['vassdragsomradenavn']}"
        )

    # Finish this page run before executing the price-area calculations.
    st.stop()


with st.spinner("Loading price-area boundaries…"):
    areas = load_boundaries("data/price_areas.geojson")

# Shared historical timeframe for the map and forecasting page.
interval = st.date_input(
    "Timeframe",
    value=st.session_state.get(
        "map_timeframe",
        (date(2018, 1, 1), date(2024, 12, 31)),
    ),
    min_value=date(2018, 1, 1),
    max_value=date.today(),
)

if len(interval) != 2:
    st.info("Select a start and end date.")
    st.stop()

start, end = interval
st.session_state["map_timeframe"] = (start, end)

colour_by = st.selectbox(
    "Colour areas by",
    ["Price area", "Reservoir filling", "Weather property"],
)

area_colours = {
    1: "#52683D",
    2: "#781F36",
    3: "#B88A3B",
    4: "#477B82",
    5: "#75628D",
}

areas["display_value"] = areas["budomr"]
areas["fill_colour"] = areas["Area_number"].map(area_colours)
legend = None


if colour_by != "Price area":
    values = {}
    missing_areas = []

    if colour_by == "Reservoir filling":
        df = load_data()

        selected = df[
            (df["Area_type"] == "EL")
            & (df["Date"].dt.date >= start)
            & (df["Date"].dt.date <= end)
        ]

        # Mean reservoir filling over the selected period.
        values = selected.groupby("Area_number")["Filling_level"].mean().to_dict()
        legend_title = "Mean reservoir filling (%)"
        values = {
            number: value * 100
            for number, value in values.items()
            if pd.notna(value)
        }

    else:
        properties = {
            "Mean temperature (°C)": "temperature_2m",
            "Total precipitation (mm)": "precipitation",
            "Total snowfall (cm)": "snowfall",
        }

        legend_title = st.selectbox(
            "Weather property",
            list(properties),
        )
        property_name = properties[legend_title]
        locations = pd.read_csv("data/weather_locations.csv")

        with st.spinner("Loading weather for saved locations…"):
            for number in areas["Area_number"]:
                points = locations[
                    (locations["Area_type"] == "EL")
                    & (locations["Area_number"] == number)
                ]

                if points.empty:
                    missing_areas.append(f"NO{number}")
                    continue

                point = points.iloc[0]

                try:
                    value = weather_value(
                        float(point["latitude"]),
                        float(point["longitude"]),
                        start,
                        end,
                        property_name,
                    )
                except requests.RequestException:
                    value = None

                if value is None:
                    missing_areas.append(f"NO{number}")
                else:
                    values[number] = value

        st.caption(
            "Weather values represent the saved sampled location in each "
            "area, not an average over the entire polygon."
        )

        if missing_areas:
            st.info(
                "Weather unavailable for "
                + ", ".join(missing_areas)
                + ". These areas are grey."
            )

    # Use a numeric colour scale for available values.
    if values:
        minimum = min(values.values())
        maximum = max(values.values())

        # Give the legend a usable range when values are identical.
        if minimum == maximum:
            minimum -= 1
            maximum += 1

        legend = LinearColormap(
            ["#FFF3CD", "#91AD69", "#22543D"],
            vmin=minimum,
            vmax=maximum,
            caption=legend_title,
        )

    areas["fill_colour"] = areas["Area_number"].map(
        lambda number: (
            legend(values[number])
            if legend is not None and number in values
            else "#BDBDBD"
        )
    )

    areas["display_value"] = areas["Area_number"].map(
        lambda number: (
            f"{values[number]:.2f}"
            if number in values
            else "No data"
        )
    )

    if not values:
        st.warning("No values are available for this timeframe.")


# Reuse the area selected on another page.
selected_type, selected_number = st.session_state.get(
    "reservoir_area", ("EL", 3)
)


def area_style(feature):
    properties = feature["properties"]
    number = int(properties["Area_number"])
    selected = selected_type == "EL" and number == selected_number

    return {
        "fillColor": properties["fill_colour"],
        "fillOpacity": 0.4,
        "color": "#CE1126" if selected else "#000000",
        "weight": 5 if selected else 1.5,
    }


# OpenStreetMap replaces the CARTO tiles requiring an API key.
map_view = folium.Map(
    location=[65, 13],
    zoom_start=5,
    tiles="OpenStreetMap",
)


# Apply the font and olive cursor inside the map itself.
map_view.get_root().header.add_child(
    folium.Element(
        f"""
        <style>
        .leaflet-container,
        .leaflet-tooltip,
        .leaflet-popup-content {{
            font-family: "Courier New", monospace;
            color: #000000;
        }}

        .leaflet-tooltip {{
            background: #FFFFFF;
            border: 1px solid #00843D;
        }}

        .leaflet-container,
        .leaflet-container * {{
            cursor: {cursor} !important;
        }}
        </style>
        """
    )
)

folium.GeoJson(
    areas.to_json(),
    name="Price areas",
    style_function=area_style,
    tooltip=folium.GeoJsonTooltip(
        fields=["budomr", "display_value"],
        aliases=["Price area:", "Value:"],
    ),
).add_to(map_view)

if legend is not None:
    legend.add_to(map_view)

# Fit all five price areas into the initial view.
west, south, east, north = areas.total_bounds
map_view.fit_bounds([[south, west], [north, east]])

result = st_folium(
    map_view,
    height=650,
    use_container_width=True,
    returned_objects=["last_clicked"],
    key="price_area_map",
)

# Select the polygon containing the clicked location.
clicked = result.get("last_clicked")

if clicked:
    coordinates = (clicked["lng"], clicked["lat"])

    if coordinates != st.session_state.get("last_map_click"):
        st.session_state["last_map_click"] = coordinates

        match = areas[
            areas.geometry.covers(Point(*coordinates))
        ]

        if not match.empty:
            number = int(match.iloc[0]["Area_number"])
            st.session_state["reservoir_area"] = ("EL", number)
            st.rerun()

area_type, area_number = st.session_state.get(
    "reservoir_area", ("EL", 3)
)

if area_type == "EL":
    st.success(f"Selected area: NO{area_number}")

st.caption(
    "This map currently contains electricity price-area boundaries. "
    "Water-area boundaries must be added separately."
)
