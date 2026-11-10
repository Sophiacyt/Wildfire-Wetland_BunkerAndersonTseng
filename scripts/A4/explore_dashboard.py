# TO RUN: 
# conda activate env700-shiny
# shiny run --reload scripts/A4/explore_dashboard.py 

# if mason and struggling, run below
# shiny run --reload explore_dashboard.py

# be a little patient with it starting, need to see this line in terminal output
#       INFO:     Application startup complete.

# import packages
import folium
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shiny import App, ui

# -----------------------------------------------------------------------
# IMPORT DATA
# -----------------------------------------------------------------------

# establish paths to datasets
project_fldr = Path.cwd().parents[1]
raw_fldr = project_fldr / 'data' / 'raw'
processed_fldr = project_fldr / 'data' / 'processed'
figure_fldr = project_fldr/"figures"

# --------------------------fire-explore-data----------------------------
# california outline
ca_outline = gpd.read_file(processed_fldr/"fire_explore/ca_outline.geojson")

# pull in the fires into dfs from geojsons
fires = ["fire_2020", "fire_2021", "fire_2022", "fire_2023", "fire_2024", "fire_2025"]
years=[2020, 2021, 2022, 2023, 2024, 2025]

for fire, year in zip(fires, years):
    globals()[fire] = gpd.read_file(
        processed_fldr/ "fire_explore" / f"fire_{year}.geojson"
    )

fire_dfs = [fire_2020, fire_2021, fire_2022, fire_2023, fire_2024, fire_2025]

years = [2020, 2021, 2022, 2023, 2024, 2025]

# remove timestamp columns because they are not serializable for JSON
for fire_df in fire_dfs:
    fire_df.drop(columns=["ALARM_DATE", "CONT_DATE"], inplace=True)

# ------------------------wetland-explore-data---------------------------
# palustrine and riverine to come later
ca_outline = gpd.read_file(processed_fldr/'wetland_explore'/"ca_outline.geojson")
marine = gpd.read_file(processed_fldr/'wetland_explore'/"marine_simpler.geojson")
estuarine = gpd.read_file(processed_fldr/'wetland_explore'/"estuarine_simpler.geojson")
lacustrine = gpd.read_file(processed_fldr/'wetland_explore'/"lacustrine_simpler.geojson")

# -----------------------------------------------------------------------
# MAP SET UP
# -----------------------------------------------------------------------
# bounding coordinates for California and rest of map
minx, miny, maxx, maxy = ca_outline.total_bounds

fire_colors = {
    "2020": "#D7191C",  # Deep red
    "2021": "#E7471A",  # Red-orange
    "2022": "#F46D1F",  # Orange
    "2023": "#F99524",  # Golden orange
    "2024": "#FDC43A",  # Gold
    "2025": "#FFFF33"   # Yellow
}

#plot wetlands, by system color
system_colors = {
    "Marine": "#02518a",
    "Estuarine": "#0b2ce9",
    "Riverine": "#17becf",
    "Lacustrine": "#01f694",
    "Palustrine": "#4bcb00"
}

# --------------------------fire-explore-map-----------------------------
fire_map_left = folium.Map(
    zoom_start=6,
    tiles=None,
)

# ESRI satellite basemap
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri, Maxar, Earthstar Geographics, and the GIS User Community",
    name="Satellite Imagery",
    overlay=False,
    control=False
).add_to(fire_map_left)

# this should leave us so that the initial zoom is the outline of california
fire_map_left.fit_bounds([
    [miny, minx],  # Southwest corner
    [maxy, maxx]   # Northeast corner
])

# add CA outline
folium.GeoJson(
    ca_outline.to_json(),
    style_function=lambda x: {
        "color": "black",
        "fillOpacity": 0,
        "weight": 2
    },
    control= False # always on
).add_to(fire_map_left)

# for loop to add in the fires
for fire_df, year in zip(fire_dfs, years):
    folium.GeoJson(
        fire_df.to_json(),
        name=f"{year} Fires",
        style_function=lambda x, year=year: {
            "color": fire_colors[str(year)],
            "fillColor": fire_colors[str(year)],
            "fillOpacity": 0.9,
            "weight": 1.5
        },
        control=True
    ).add_to(fire_map_left)

folium.LayerControl(collapsed=False).add_to(fire_map_left)

fire_map_left # this would display in a notebook

# ------------------------wetland-explore-map----------------------------

# MAKE THE EXPLORE

# create the actual map as a base now
wetland_map_right = folium.Map(
    zoom_start=6,
    tiles=None,
)

# ESRI satellite basemap
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri, Maxar, Earthstar Geographics, and the GIS User Community",
    name="Satellite Imagery",
    overlay=False,
    control=False
).add_to(wetland_map_right)

# this should leave us so that the initial zoom is the outline of california
wetland_map_right.fit_bounds([
    [miny, minx],  # Southwest corner
    [maxy, maxx]   # Northeast corner
])

# add CA outline
folium.GeoJson(
    ca_outline.to_json(),
    style_function=lambda x: {
        "color": "black",
        "fillOpacity": 0,
        "weight": 2
    },
    control= False # always on
).add_to(wetland_map_right)

# Marine layer
folium.GeoJson(
    marine.to_json(),
    name="Marine System Wetlands",
    style_function=lambda x: {
        "color": system_colors["Marine"],
        "fillColor": system_colors["Marine"],
        "fillOpacity": 0.9,
        "weight": 0.5
    },
    control=True #can be toggled
).add_to(wetland_map_right)

# Estuarine layer
folium.GeoJson(
    estuarine.to_json(),
    name="Estuarine System Wetlands",
    style_function=lambda x: {
        "color": system_colors["Estuarine"],
        "fillColor": system_colors["Estuarine"],
        "fillOpacity": 0.9,
        "weight": 0.5
    },
    control=True #can be toggled
).add_to(wetland_map_right)

# Lacustrine layer
folium.GeoJson(
    lacustrine.to_json(),
    name="Lacustrine System Wetlands",
    style_function=lambda x: {
        "color": system_colors["Lacustrine"],
        "fillColor": system_colors["Lacustrine"],
        "fillOpacity": 0.9,
        "weight": 0.5
    },
    control=True #can be toggled
).add_to(wetland_map_right)

# Add layer control
folium.LayerControl(collapsed=False).add_to(wetland_map_right)

# -----------------------------------------------------------------------
# save maps just in case - this worked
#   fire_map_left.save("fire_map.html")
#   wetland_map_right.save("wetland_map.html")
# -----------------------------------------------------------------------

# -----------------------------------------------------------------------
# SHINY DASHBOARD
# -----------------------------------------------------------------------

# --------------------------dashboard-legend-----------------------------

def make_legend(colors):

    items = []

    for label, color in colors.items():
        items.append(
            ui.div(
                ui.span(
                    style=f"""
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    background-color: {color};
                    margin-right: 5px;
                    """,
                ),
                ui.span(label),
                style="display: flex; align-items: center; gap: 3px;"
            )
        )

    return ui.div(
        *items,
        style="""
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        padding: 10px;
        """
    )

# --------------------------dashboard-itself-----------------------------

app_ui = ui.page_fluid(

    ui.h2("California Wildfire & Wetland Dashboard"),

    ui.layout_columns(

        # WILDFIRE CONTAINER
        ui.card(
            ui.card_header("California Wildfires (2020–2025)"),

            make_legend(fire_colors),

            ui.HTML(fire_map_left._repr_html_()),

            height="800px"
        ),

        # WETLAND CONTAINER
        ui.card(
            ui.card_header("California Wetlands"),

            make_legend(system_colors),

            ui.HTML(wetland_map_right._repr_html_()),

            height="800px"
        ),

        col_widths=[6, 6]
    )
)

app = App(app_ui, server=None)

