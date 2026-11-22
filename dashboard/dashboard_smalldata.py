# TO RUN:
# conda activate env700-shiny
# shiny run --reload dashboard/dashboard_smalldata.py

# if mason and struggling, run below
# cd ~/Desktop/Duke/Environmental\ Data\ Exploration/Wildfire-Wetland_BunkerAndersonTseng/dashboard
# shiny run --reload dashboard_smalldata.py

# be a little patient with it starting, need to see this line in terminal output
#       INFO:     Application startup complete.


# import packages
import pandas as pd
import seaborn as sns
import ipywidgets as widgets
import matplotlib.pyplot as plt
from IPython.display import display, clear_output
import platform
from pathlib import Path
import geopandas as gpd
import calendar
import pygris
from shiny import App, ui, render, reactive
import matplotlib.ticker as ticker
import folium
#for sankey
import plotly.graph_objects as go
from shinywidgets import output_widget, render_widget

from pathlib import Path
import pandas as pd
import geopandas as gpd
import platform
import numpy as np

from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_plotly

import plotly.graph_objects as go
import plotly.express as px

# ----------------------------------------------------------
# DATA SETUP
# ----------------------------------------------------------

# Maps
# establish paths to datasets

project_fldr = Path(__file__).resolve().parents[1]
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

# -----------------------random-points-graph-----------------------------

n100000 = gpd.read_file(
    processed_fldr / "n100000_random_pts.geojson"
)

print("n100,000 random points found and loaded")


# ============================================================
# DEVELOP THE PLOTTING FUNCTION
# ============================================================

def plot_points(System, Subsystems=None):

    # --------------------------------------------------------
    # SUBSET DATA
    # --------------------------------------------------------

    if System == "All Wetland Systems":

        # Include all wetland systems and subsystems
        df_subset = n100000.copy()

        subsystem_title = "All Subsystems"

    else:

        # Include only the selected wetland system
        if Subsystems is None:
            Subsystems = []

        df_subset = n100000.loc[
            (n100000["C System"] == System) &
            (n100000["C Subsystem"].isin(Subsystems))
        ].copy()

        # Format subsystem title
        if len(Subsystems) > 1:
            subsystem_title = "All Subsystems"
        elif len(Subsystems) == 1:
            subsystem_title = Subsystems[0]
        else:
            subsystem_title = "No Subsystems"

    # Remove observations missing either distance
    df_subset = df_subset.dropna(
        subset=["Wet_dist", "Fire_dist"]
    )

    # --------------------------------------------------------
    # HANDLE EMPTY DATA
    # --------------------------------------------------------

    if df_subset.empty:

        fig = go.Figure()

        fig.add_annotation(
            text="No matching observations",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=18)
        )

        if System == "All Wetland Systems":
            plot_title = (
                "100,000 Random Points in California — "
                "All Wetland Systems"
            )
        else:
            plot_title = (
                f"100,000 Random Points in California — "
                f"{System}: {subsystem_title}"
            )

        fig.update_layout(
            title=plot_title,
            xaxis_title="Distance to Nearest Wetland (m)",
            yaxis_title="Distance to Nearest Fire (m)",
            width=960,
            height=800,
            showlegend=False
        )

        return fig

    # --------------------------------------------------------
    # DETERMINE WHETHER OLS TRENDLINE CAN BE CALCULATED
    # --------------------------------------------------------

    use_trendline = (
        len(df_subset) >= 2
        and df_subset["Wet_dist"].nunique() > 1
    )

    # --------------------------------------------------------
    # CREATE FIGURE
    # --------------------------------------------------------

    fig = go.Figure()

    # --------------------------------------------------------
    # ALL WETLAND SYSTEMS
    # --------------------------------------------------------

    if System == "All Wetland Systems":

        # Add one scatter trace for each wetland system
        for wetland_system in system_colors:

            system_subset = df_subset.loc[
                df_subset["C System"] == wetland_system
            ]

            if system_subset.empty:
                continue

            fig.add_trace(
                go.Scatter(
                    x=system_subset["Wet_dist"],
                    y=system_subset["Fire_dist"],
                    mode="markers",
                    name=wetland_system,
                    marker=dict(
                        color=system_colors[wetland_system],
                        symbol="circle",
                        size=7,
                        opacity=0.7
                    ),
                    hoverinfo="skip",
                    showlegend=False
                )
            )

        # ----------------------------------------------------
        # ONE OVERALL REGRESSION LINE
        # ----------------------------------------------------

        if use_trendline:

            x = df_subset["Wet_dist"].to_numpy()
            y = df_subset["Fire_dist"].to_numpy()

            # Calculate overall OLS regression
            slope, intercept = np.polyfit(x, y, 1)

            # Calculate predicted values
            y_pred = slope * x + intercept

            # Calculate R-squared
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)

            r2 = (
                1 - ss_res / ss_tot
                if ss_tot > 0
                else np.nan
            )

            # Add overall regression line
            x_line = np.linspace(
                x.min(),
                x.max(),
                100
            )

            y_line = slope * x_line + intercept

            fig.add_trace(
                go.Scatter(
                    x=x_line,
                    y=y_line,
                    mode="lines",
                    name="Overall Regression",
                    line=dict(
                        color="black",
                        width=4
                    ),
                    hoverinfo="skip",
                    showlegend=False
                )
            )

            # Add regression statistics annotation
            fig.add_annotation(
                x=0.98,
                y=0.98,
                xref="paper",
                yref="paper",
                text=(
                    f"<b>System: All Wetland Systems<br>"
                    f"Subsystem: Not applicable<br>"
                    f"Slope: {slope:.4f}<br>"
                    f"Y-intercept: {intercept:.4f}<br>"
                    f"R² = {r2:.4f}</b>"
                ),
                showarrow=False,
                xanchor="right",
                yanchor="top",
                font=dict(
                    size=16,
                    color="black"
                ),
                bgcolor="white",
                bordercolor="black",
                borderwidth=1,
                borderpad=8
            )

    # --------------------------------------------------------
    # INDIVIDUAL WETLAND SYSTEM
    # --------------------------------------------------------

    else:

        # Add points using the selected system color
        color = system_colors.get(System, "#808080")

        fig.add_trace(
            go.Scatter(
                x=df_subset["Wet_dist"],
                y=df_subset["Fire_dist"],
                mode="markers",
                name=System,
                marker=dict(
                    color=color,
                    symbol="circle",
                    size=7,
                    opacity=0.7
                ),
                hoverinfo="skip",
                showlegend=False
            )
        )

        # ----------------------------------------------------
        # ONE REGRESSION LINE
        # ----------------------------------------------------

        if use_trendline:

            x = df_subset["Wet_dist"].to_numpy()
            y = df_subset["Fire_dist"].to_numpy()

            # Calculate OLS regression
            slope, intercept = np.polyfit(x, y, 1)

            # Calculate predicted values
            y_pred = slope * x + intercept

            # Calculate R-squared
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)

            r2 = (
                1 - ss_res / ss_tot
                if ss_tot > 0
                else np.nan
            )

            # Generate regression line
            x_line = np.linspace(
                x.min(),
                x.max(),
                100
            )

            y_line = slope * x_line + intercept

            fig.add_trace(
                go.Scatter(
                    x=x_line,
                    y=y_line,
                    mode="lines",
                    name="Regression",
                    line=dict(
                        color="black",
                        width=4
                    ),
                    hoverinfo="skip",
                    showlegend=False
                )
            )

            # Add regression statistics annotation
            fig.add_annotation(
                x=0.98,
                y=0.98,
                xref="paper",
                yref="paper",
                text=(
                    f"<b>System: {System}<br>"
                    f"Subsystem: {subsystem_title}<br>"
                    f"Slope: {slope:.4f}<br>"
                    f"Y-intercept: {intercept:.4f}<br>"
                    f"R² = {r2:.4f}</b>"
                ),
                showarrow=False,
                xanchor="right",
                yanchor="top",
                font=dict(
                    size=16,
                    color="black"
                ),
                bgcolor="white",
                bordercolor="black",
                borderwidth=1,
                borderpad=8
            )

    # --------------------------------------------------------
    # FORMAT FIGURE TITLE
    # --------------------------------------------------------

    if System == "All Wetland Systems":

        plot_title = (
            "100,000 Random Points in California — "
            "All Wetland Systems"
        )

    else:

        plot_title = (
            f"100,000 Random Points in California — "
            f"{System}: {subsystem_title}"
        )

    # --------------------------------------------------------
    # FORMAT FIGURE
    # --------------------------------------------------------

    fig.update_layout(
        title=plot_title,
        xaxis_title="Distance to Nearest Wetland (m)",
        yaxis_title="Distance to Nearest Fire (m)",
        width=960,
        height=800,
        showlegend=False,
        hovermode="closest",
        hoverdistance=30
    )

    # Add commas to axis tick labels
    fig.update_xaxes(tickformat=",")
    fig.update_yaxes(tickformat=",")

    return fig


# ============================================================
# ESTABLISH DROPDOWN OPTIONS
# ============================================================

system_list = sorted(
    n100000["C System"].dropna().unique()
)

# Add All Wetland Systems option
system_choices = [
    "All Wetland Systems"
] + system_list

# Initial system selection
initial_system = "All Wetland Systems"

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
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{x}/{y}",
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


# define legend maker
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

# # SANKEY DIAGRAM
# wetlands_subset_path = box_path / 'ENVIRON 712L-Students' / 'Data' / 'BunkerAndersonTseng' / 'wetlands_subset'
# wetlands = gpd.read_file(
#     wetlands_subset_path / "wetlands_subset.gpkg"
# )

# print("wetlands data secured!")

def plot_sankey():

    df = pd.read_csv(processed_fldr / 'wetlands_dataframe.csv')

    df["Hectares"] = pd.to_numeric(df["Hectares"], errors="coerce")
    df = df.dropna(subset=["Hectares"])

    cols = ["C System", "C Subsystem", "C Class"]

    for col in cols:
        df[col] = df[col].fillna("Unknown").astype(str)

    # Calculate total hectares for each transition
    flow1 = (
        df.groupby(["C System", "C Subsystem"])["Hectares"]
        .sum()
        .reset_index()
    )

    flow2 = (
        df.groupby(["C Subsystem", "C Class"])["Hectares"]
        .sum()
        .reset_index()
    )

    # Create separate nodes for each classification level
    systems = df["C System"].unique().tolist()
    subsystems = df["C Subsystem"].unique().tolist()
    classes = df["C Class"].unique().tolist()

    labels = (
        [f"System: {x}" for x in systems]
        + [f"Subsystem: {x}" for x in subsystems]
        + [f"Class: {x}" for x in classes]
    )

    system_map = {x: i for i, x in enumerate(systems)}

    subsystem_map = {
        x: i + len(systems)
        for i, x in enumerate(subsystems)
    }

    class_map = {
        x: i + len(systems) + len(subsystems)
        for i, x in enumerate(classes)
    }

    # Build links
    sources = (
        flow1["C System"].map(system_map).tolist()
        + flow2["C Subsystem"].map(subsystem_map).tolist()
    )

    targets = (
        flow1["C Subsystem"].map(subsystem_map).tolist()
        + flow2["C Class"].map(class_map).tolist()
    )

    values = (
        flow1["Hectares"].tolist()
        + flow2["Hectares"].tolist()
    )

    # Generate Sankey diagram
    fig_subset = go.Figure(go.Sankey(
        node=dict(label=labels),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            hovertemplate=(
                "%{source.label} → %{target.label}<br>"
                "Area: %{value:.2f} hectares"
                "<extra></extra>"
            )
        )
    ))

    fig_subset.update_layout(
        title="Wetland Area in Hectares for California Wetlands larger than 1ha by Cowardin System, Subsystem, and Class",
        font_size=11,
        height=700
    )

    return fig_subset


# FIRE DATA GRAPH 

# Read in cleaned fire dataset
project_fldr = Path(__file__).resolve().parents[1]

# Locate the processed data folder
processed_fldr = project_fldr / 'data' / 'processed'

# Load the fire shapefile
fire_shp_25 = gpd.read_file(
    processed_fldr / 'fire_shp_25' / 'fire_shp_25.shp'
)

# Convert dates to datetime
fire_shp_25['ALARM_DATE'] = pd.to_datetime(
    fire_shp_25['ALARM_DATE'], utc=True
)

fire_shp_25['CONT_DATE'] = pd.to_datetime(
    fire_shp_25['CONT_DATE'], utc=True
)

# Convert alarm month to categorical
fire_shp_25['Alarm Mo_1'] = pd.Categorical(
    values=fire_shp_25['Alarm Mo_1'],
    categories=calendar.month_abbr[1:]
)

# Map fire cause codes to descriptions
code_to_cause = {
    1: "Lightning",
    2: "Equipment Use",
    3: "Smoking",
    4: "Campfire",
    5: "Debris",
    6: "Railroad",
    7: "Arson",
    8: "Playing with fire",
    9: "Miscellaneous",
    10: "Vehicle",
    11: "Powerline",
    12: "Firefighter Training",
    13: "Non-Firefighter Training",
    14: "Unknown/Unidentified",
}

fire_shp_25['CAUSE_NAME'] = fire_shp_25['CAUSE'].map(
    code_to_cause
)

# Available fire causes for dropdown
cause_list = sorted(
    fire_shp_25['CAUSE_NAME'].dropna().unique()
)

# Fixed containment date range
cont_start_date = "2020-01-01"
cont_end_date = "2025-12-31"


def plot_fire_cause(alarm_start_date, alarm_end_date, cause):

    # Filter the fire data
    fire_subset = fire_shp_25.loc[
    (fire_shp_25['ALARM_DATE'] >= pd.to_datetime(alarm_start_date, utc=True)) &
    (fire_shp_25['ALARM_DATE'] <= pd.to_datetime(alarm_end_date, utc=True)) &
    (fire_shp_25['CONT_DATE'] >= pd.Timestamp("2020-01-01", tz="UTC")) &
    (fire_shp_25['CONT_DATE'] <= pd.Timestamp("2025-12-31 23:59:59", tz="UTC")) &
    (fire_shp_25['CAUSE_NAME'].isin(cause))
    ]

    # Create the plot
    the_plot = sns.relplot(
        data=fire_subset,
        x='Alarm Mo_1',
        y='Shape_Area',
        hue='CAUSE_NAME',
        alpha=0.7,
        legend=True
    )

    # Add labels and title
    the_plot.set_axis_labels(
        'Alarm Month',
        'Fire Size (hectares)'
    )
    the_plot.set(title='Fire by Cause')

    # Change legend title
    if the_plot._legend is not None:
        the_plot._legend.set_title("Fire Cause")

    # Format the y-axis from square meters to hectares
    ax = the_plot.ax
    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, pos: f'{x / 10_000:g}')
    )

    # Adjust spacing to prevent labels from being cut off
    the_plot.figure.tight_layout()

    return the_plot.figure


# ----------------------------------------------------------
# PCT WETLANDS BURNED WIDGET SETUP
# ----------------------------------------------------------

# Path to saved fire overlap data
overlap_folder = processed_fldr / 'fire_overlap_data' 

year_list = [2020, 2021, 2022, 2023, 2024, 2025]
# Load yearly fire overlap data
fire_stats_list = []

for year in year_list:

    # Read the CSV for the selected year
    data = pd.read_csv(
        overlap_folder / f'fire_ol_stats_{year}.csv'
    )

    # Add a column identifying the year
    data['Year'] = year

    # Add dataframe to list
    fire_stats_list.append(data)

# Combine all yearly dataframes
fire_stats_all = pd.concat(fire_stats_list, ignore_index=True)

# Get available wetland systems for dropdown
system_list = sorted(fire_stats_all['C System'].unique())


# Plotting function
def plot_fireint(years, systems):

    # Filter data to selected years and wetland systems
    fireint_subset = fire_stats_all.loc[
        (fire_stats_all['Year'].isin([int(year) for year in years])) &
        (fire_stats_all['C System'].isin(systems))
    ]

    # Create grouped bar chart
    g = sns.catplot(
        data=fireint_subset,
        x='Year',
        y='Percent Wetland Area Burned',
        height=3.5,
        aspect=1.5,
        hue='C System',
        hue_order=[s for s in system_list if s in systems],
        palette=system_colors,
        kind='bar'
    )

    g.set(
        title="Percent of Wetland Area Burned by Year and Wetland System",
        xlabel="Year",
        ylabel="Wetland Area Burned (%)"
    )

    if g._legend is not None:
        g._legend.set_title("Wetland System")

    g.figure.tight_layout()

    return g.figure



# # ----------------------------------------------------------
# # DISTANCE TO NEAREST FIRE SETUP
# # ----------------------------------------------------------

output_folder = processed_fldr / 'fire_distance_data'


# Available years
year_list = [2020, 2021, 2022, 2023, 2024, 2025]

# Load all fire data
fire_data = {}

for year in year_list:
    fire_data[year] = pd.read_csv(
        output_folder / f'nearest_fires_{year}.csv'
    )


# Plotting function
def plot_firedist(year):

    g = sns.displot(
        data=fire_data[year],
        x='Dist_Closest_km',
        height=3,
        aspect=2,
        color="orange"
    )

    g.set(
        title="Distance from Wetlands to Nearest Fire (km)",
        xlabel="Distance (km)",
        ylabel="Count"
    )

    return g.figure


# ----------------------------------------------------------
# SUMMARY TABLE SETUP
# ----------------------------------------------------------

years = [2020, 2021, 2022, 2023, 2024, 2025]

# we already went through the overlap stats
overlap_stats = fire_stats_all

# Load yearly fire distance statistics
dist_list = []

for year in years:
    data = pd.read_csv(
        output_folder / f"fire_stats_{year}.csv"
    )

    data["Year"] = year
    dist_list.append(data)

dist_stats = pd.concat(
    dist_list,
    ignore_index=True
)


# Combine overlap and distance statistics
summary_table = pd.merge(
    overlap_stats,
    dist_stats,
    on=["C System", "Year"],
    how="outer"
)

# Sort by year and wetland system
summary_table = summary_table.sort_values(
    ["Year", "C System"]
).reset_index(drop=True)

# Rename columns for dashboard presentation
summary_table = summary_table.rename(columns={
    "C System": "Wetland System",
    "Year": "Year",
    "Burned Area (ha)": "Burned Area (ha)",
    "Total Wetland Area (ha)": "Total Wetland Area (ha)",
    "Percent Wetland Area Burned": "% of Wetland Area Burned",
    "Percent of Fire Area in Wetlands": "% of Fire Area in Wetlands",
    "Avg_Dist_Fire_km": "Average Distance to Fire (km)",
    "Std_Dist_Fire_km": "Standard Deviation of Distance (km)",
    "Median_Dist_Fire_km": "Median Distance to Fire (km)"
})
# re-order columns for presentation
summary_table = summary_table[
    [
        "Year",
        "Wetland System",
        "Burned Area (ha)",
        "Total Wetland Area (ha)",
        "% of Wetland Area Burned",
        "% of Fire Area in Wetlands",
        "Average Distance to Fire (km)",
        "Standard Deviation of Distance (km)",
        "Median Distance to Fire (km)"
    ]
]

# change formatting to shorten decimals, show percents
summary_table = summary_table.round(3)

#calculate total wetland area to display
total_wetland_ha = summary_table.loc[
    summary_table["Year"] == 2025,
    "Total Wetland Area (ha)"
].sum()

# calculate total burned area 2020-2026 to display
total_burned_wetland = summary_table["Burned Area (ha)"].sum()

# and calculate total percent of the burn
total_pct_burned_wetland = (
    total_burned_wetland / total_wetland_ha
) * 100

# and calculate overall total average dist from wetland to fire

total_average_distance = pd.concat(
    [fire_data[year]["Dist_Closest_km"] for year in year_list]
).mean()

# DASHBOARD CONTENT ----------------------------------------------------
print("all data and functions loaded in! Setting up dashboard now :)")


app_ui = ui.page_navbar(

    # --------------------------------------------------
    # HOME tab
    # --------------------------------------------------

        ui.nav_panel(
        "Home",

        ui.card(
            ui.card_header('Wildfires & Wetlands Dashboard'),

            ui.p(
                'This dashboard uses CalFire fire perimeters data and National Wetlands Inventory '
                'wetland data to explore the relationship between wetlands and wildfires in California. California '
                'currently has over 3 million hectares of wetland, but has undergone an estimated loss of 90% in the last century. '
                'Wetlands supply many benefits including flood mitigation, water filtration, and carbon sequestration. Wildfire can be an ' \
                'important part of the wetland ecosystem, but also has the potential to negatively affect the quality of' \
                ' water, vegetation, and wildlife habitat, and could release stored carbon to the atmosphere, resulting in increased ' \
                'greenhouse gas emissions. ' 
                'Use our dashboards to examine wildfire impact on wetlands in the state from 2020 to 2025.'
            ),

            ui.h4("How are wetlands impacted by wildfires in the state of California?"),
            ui.tags.ul(
                ui.tags.li('How close are wetlands to wildfires?'),
                ui.tags.li('What types of wetlands are most impacted by wildfires?'),
                ui.tags.li('What is the spatial relationship between wetlands and wildfires, if any?'),
            ),

            ui.h4("Hypotheses"),
            ui.tags.ul(
                ui.tags.li(
                    'Wetlands will be less vulnerable to wildfires than non-wetland.'
                ),
                ui.tags.li(
                    'Riverine and palustrine wetlands will be more vulnerable to fire because they generally' \
                    'have more woody vegetation and less surface water than other wetland systems.'
                                ),
                ui.tags.li(
                    'There will be a stronger spatial relationship between wetland distance to fire ' \
                    'in the marine, estuarine, and lacustrine systems as compared to the riverine and palustrine systems.'
                ),
            )
        ),

        ui.card(
            ui.card_header('Data'),

            ui.h4('Wildfire Data'),
            ui.p(
                'The CA wildfire data is a direct download of the ',
                ui.tags.a(
                    'California Historic Fire Perimeters',
                    href="https://www.fire.ca.gov/what-we-do/fire-resource-assessment-program/fire-perimeters",
                    target="_blank"
                ),
                ' managed by CalFire. The dataset records fires greater than or equal to 10 acres by Year, Reporting Agency, '
                'Unit ID, Fire Name, Local Incident Number, Alarm Date, Containment Date, Cause, Collection Method, '
                'Management Objective, and GIS Calculated Acres. Raw data was projected in the '
                'California Albers Projection (EPSG:3310) but has been reprojected to EPSG:26910, UTM Zone 10N.'
            ),

            ui.h4('Wetlands Data'),
            ui.p(
                'The CA wetlands data is a direct download from the '
                'USFW National Wetland Inventory. Metadata for the NWI can be '
                'accessed from the ',
                ui.tags.a(
                    'Wetlands Mapper Tool',
                    href="https://fwsprimary.wim.usgs.gov/wetlands/apps/wetlands-mapper/",
                    target="_blank"
                ),
                '. Data was downloaded for the state of California and subset to include only wetlands '
                'greater than 1 hectare. Raw data was projected in equal-area Albers '
                'projection for the 1983 North American Datum, but has been reprojected '
                'to EPSG:26910, UTM Zone 10N.'
            ),
        ),

        ui.card(
            ui.card_header('Project Information'),
            ui.p('This dashboard was built as a final project for the Duke Nicholas School of the Environment course ENV712 - Environmental '
            'Data Exploration II: Applied Analysis and Visualization. Authors: Kat' \
            ' Anderson, Mason Bunker, Sophia Tseng.')
        ),

    ),
    # --------------------------------------------------
    # WILDFIRE tab
    # --------------------------------------------------

    ui.nav_panel(
    "Wildfire",

    # --------------------------------------------------
    # INFORMATION + FIRE EXPLORATION
    # --------------------------------------------------

    ui.layout_columns(

        # card on left with wildfire data info
        ui.card(
            ui.card_header("Wildfire Data"),

            ui.p(
                'Wildfire shapefile data comes from the California Historical Fire Perimeters'
                ' dataset, maintained by CalFire, and reporting fires greater than or equal to 10 acres'
                ' inside the state between 1910 and 2025. For this project, data has been subset to years '
                'between 2020 and 2025. '
            ),
            ui.p("Overall, the findings suggest that wildfire ignition causes are associated with " \
                "different seasonal patterns and fire-size distributions. Lightning is particularly notable "
                "for its association with large burned areas, while several human-related causes are more frequently " \
                "associated with smaller fires. These observations highlight the importance of considering both ignition " \
                "frequency and burned area when evaluating wildfire risk, rather than relying on fire occurrence alone."),
        ),

        # card on right with fire explore graph
        ui.card(
            ui.card_header("Explore Fire by Cause"),

            # FILTERS AND GRAPH
            ui.layout_columns(

                # FILTERS
                ui.div(
                    ui.input_date_range(
                        "alarm_dates",
                        "Select Alarm Date Range:",
                        start="2020-01-01",
                        end="2025-12-31",
                        min="2020-01-01",
                        max="2025-12-31"
                    ),

                    ui.input_checkbox_group(
                        "cause",
                        "Select Fire Cause:",
                        choices=cause_list,
                        selected=["Lightning"],
                        inline=True
                    ),
                ),

                # GRAPH
                ui.output_plot(
                    "fire_cause_plot",
                    height="450px"
                ),

                col_widths=[4, 8],
            ),
        ),

        col_widths=[4, 8],
    ),

    # card with wildfire map at bottom

    ui.card(
        ui.card_header("California Wildfires (2020–2025)"),

        make_legend(fire_colors),

        ui.HTML(fire_map_left._repr_html_()),
    ),

),

    # --------------------------------------------------
    # WETLANDS tab
    # --------------------------------------------------

    ui.nav_panel(
        "Wetlands",

        ui.layout_columns(

            # wetlands data info on left
            ui.card(
                ui.card_header("Wetlands Data"),

                ui.p(
                    "Wetlands shapefile data comes from the National Wetland Inventory, downloaded for the state of California, and has been "
                    "subset to wetlands above 10 acres. This dataset "
                    "Wetlands are classified following the Cowardin (1979) wetlands classifications of 5 systems, and additional subsystems, "
                    "classes, and subclasses. System descriptions are as follows."
                ),

                ui.tags.ul(
                    ui.tags.li("Marine: open ocean or high energy wetlands with salinity greater than 0.5ppt."),

                    ui.tags.li("Estuarine: semi-enclosed or low energy wetlands with salinity greater than 0.5ppt."),

                    ui.tags.li("Riverine: freshwater wetlands confined to a channel."),

                    ui.tags.li("Lacustrine: freshwater wetlands exceeding 20 acres or being deeper than 2.5m."),

                    ui.tags.li(
                        "Palustrine: freshwater wetlands dominated by trees or woody vegetation, or those "
                        "freshwater inland wetlands less than 20 acres or shallower than 2.5m."
                    ),
                ),
            ),

            # wetlands sankey diagram on right
            ui.card(
                ui.card_header("Wetland Classification Sankey Diagram"),

                output_widget("sankey_plot"),
            ),

            col_widths=[4, 8],
        ),

        # wetland map at bottom
        ui.card(
            ui.card_header("California Wetlands Map"),

            ui.HTML(wetland_map_right._repr_html_()),
        ),

    ),

    # --------------------------------------------------
    # ANALYSIS tab
    # --------------------------------------------------

    ui.nav_panel(
        "Analysis",

        # ---------------------------------------------------
        # INTRODUCTION
        # ---------------------------------------------------

        ui.card(
    ui.card_header("Analysis Overview"),

    ui.p(
        "To address our central questions about wildfire impacts on wetlands across "
        "California, take a spatial analysis approach. Both the NWI wetlands dataset and the "
        "CalFire fire dataset contain perimeter shapefiles, allowing us to examine the "
        "extent to which wetlands overlap with wildfire boundaries, compare wildfire occurance in wetland and "
        "non-wetland areas, and investigate how proximity to wetlands relates to wildfire occurance."
    ),
),

    ui.layout_columns(

        ui.card(
            ui.card_header("Total Wetland Area"),
            ui.h2(f"{total_wetland_ha:,.0f}"),
            ui.p("Hectares across California"),
        ),

        ui.card(
            ui.card_header("Total Burned Wetland Area"),
            ui.h2(f"{total_burned_wetland:,.0f}"),
            ui.p("Cumulative hectares, 2020–2025"),
        ),

        ui.card(
            ui.card_header("Wetland Burned"),
            ui.h2(f"{total_pct_burned_wetland:.1f}%"),
            ui.p("Cumulative annual burned area relative to total wetland area"),
        ),

        col_widths=[4, 4, 4],
    ),

        # ---------------------------------------------------
                # 1. distance to nearest fire
                # ---------------------------------------------------
        
                # ---------------------------------------------------
        # 1. DISTANCE TO NEAREST FIRE
        # ---------------------------------------------------

        ui.card(
            ui.card_header("1. Distance from Wetlands to Nearest Fire"),

            ui.layout_columns(

                # LEFT COLUMN: EXPLANATION AND FILTER
                ui.div(
                    ui.p(
                        "We perform a nearest-neighbor spatial join to determine the distance between each wetland "
                        "perimeter and its nearest wildfire, for each of the 6 years."
                    ),

                    ui.tags.ul(
                        ui.tags.li('Distribution heavily skewed to the right.'),
                        ui.tags.li(
                            f'Overall average distance to nearest fire: {total_average_distance:.2f} km.'
                        )
                    ),

                    ui.input_select(
                        "year",
                        "Select Year:",
                        choices=[str(y) for y in year_list],
                        selected=str(year_list[0])
                    ),
                ),

                # RIGHT COLUMN: GRAPH
                ui.output_plot("fire_plot"),

                col_widths=[4, 8],
            ),
        ),


        # ---------------------------------------------------
        # 2. PERCENT OF WETLAND AREA BURNED
        # ---------------------------------------------------

        ui.card(
            ui.card_header("2. Percent of Wetland Area Burned by Wetland Type"),

            ui.layout_columns(

                ui.div(
                    ui.p(
                        "We perform an intersection between the wetlands data and the " \
                        "fire data to identify wetland area that overlaps with fire perimeters. " \
                        "We use total wetland area for each system to determine the percent of each " \
                        "wetland system that was burned."
                    ),
                    ui.tags.ul(
                                ui.tags.li('Overall, percent of wetland area burned remains low, indicating a ' \
                                'majority of wetland area did not experience wildfire in the last 6 years.'),
                                ui.tags.li('Palustrine and riverine wetlands, which typically have more woody vegetation, have higher ' \
                                'percentages of wetland burned compared to the other three systems.'),
                                ui.tags.li('There are several years where estuarine, marine, or lacustrine systems did not experience wildfire.')
                    ),

                    

                    ui.input_checkbox_group(
                        "fireint_year",
                        "Select Year:",
                        choices=[str(y) for y in year_list],
                        selected=[str(y) for y in year_list],
                    ),

                    ui.input_checkbox_group(
                        "fireint_system",
                        "Select Wetland System:",
                        choices=system_list,
                        selected=system_list,
                        inline=False
                    ),
                ),

                ui.output_plot("fireint_plot"),

                col_widths=[4, 8],
            ),
        ),


        # ---------------------------------------------------
        # 3. SPATIAL RELATIONSHIP BETWEEN WETLANDS AND FIRES
        # ---------------------------------------------------

# ---------------------------------------------------
# 3. SPATIAL RELATIONSHIP BETWEEN WETLANDS AND FIRES
# ---------------------------------------------------

ui.card(
    ui.card_header("3. Spatial Relationship Between Wetlands and Fires"),

    ui.layout_columns(

        # ----------------------------------------------------
        # LEFT COLUMN: EXPLANATION + FILTERS
        # ----------------------------------------------------

        ui.div(
            ui.p(
                "This analysis uses 100,000 randomly generated points to examine the relationship between distance to the " \
                "nearest wetland and distance to the nearest fire. " \
            ),

            ui.tags.ul(
                ui.tags.li(
                    "A negative trendline would indicate that for a random point in the state, "
                    "as you get closer to a wildfire you get farther away from a wetland."
                ),
                ui.tags.li(
                    "Actual trendlines vary by wetland system and subsystem, with no R^2 values indicating significant trendlines."
                ),
            ),

            ui.hr(),

            ui.h4("Filter Wetland Classification"),

            ui.input_select(
                "system",
                "System:",
                choices=system_choices,
                selected=initial_system
            ),

            ui.output_ui("subsystem_choices"),

            ui.hr(),

            ui.output_ui("system_legend")
        ),

        # ----------------------------------------------------
        # RIGHT COLUMN: PLOT
        # ----------------------------------------------------

        ui.card(
            ui.card_header("Distance to Wetlands vs Fire"),
            output_widget("distance_plot")
        ),

        col_widths=[4, 8]
    )
),

        # ---------------------------------------------------
        # 4. SUMMARY STATISTICS
        # ---------------------------------------------------

        ui.card(
            ui.card_header("5. Summary Statistics"),

            ui.input_checkbox_group(
                "summary_year",
                "Select Year:",
                choices={
                    str(year): str(year)
                    for year in range(2020, 2026)
                },
                selected=["2020"]
            ),

            ui.output_table("summary_table_output"),
        ),

    ),

    title="Wildfires & Wetlands Dashboard",

)


def server(input, output, session):

    @render.plot
    def fire_cause_plot():

        # Get the selected alarm date range
        alarm_dates = input.alarm_dates()
        alarm_start_date = alarm_dates[0]
        alarm_end_date = alarm_dates[1]

        # Get the selected fire cause
        selected_cause = input.cause()

        # Generate the plot
        return plot_fire_cause(
            alarm_start_date,
            alarm_end_date,
            selected_cause
        )


    @render.plot
    def fireint_plot():

        selected_years = input.fireint_year()
        selected_systems = input.fireint_system()

        if not selected_years or not selected_systems:
            return None

        return plot_fireint(
            selected_years,
            selected_systems
        )


    @render.plot
    def fire_plot():
        year = int(input.year())
        return plot_firedist(year)

    @render.table
    def summary_table_output():
        selected_year = [int(year) for year in input.summary_year()]

        table = summary_table.loc[
            summary_table["Year"].isin(selected_year)
        ]

        return table


    @render_widget
    def sankey_plot():
        return plot_sankey()

    # dynamically update subsystem options
    @render.ui
    def subsystem_choices():

        selected_system = input.system()

        # Hide subsystem selection when all systems selected
        if selected_system == "All Wetland Systems":
            return ui.div()

        available_subsystems = sorted(
            n100000.loc[
                n100000["C System"] == selected_system,
                "C Subsystem"
            ].dropna().unique()
        )

        return ui.div(

            ui.input_select(
                "subsystems",
                "Subsystem:",
                choices=["All"] + available_subsystems,
                selected="All"
            )

        )    

    # dynamic system legend
    @render.ui
    def system_legend():

        selected_system = input.system()

        # Only display legend when all systems are selected
        if selected_system != "All Wetland Systems":
            return ui.div()

        return ui.div(

            ui.h5("Wetland System Colors"),

            *[
                ui.div(
                    ui.span(
                        "●",
                        style=(
                            f"color: {color}; "
                            "font-size: 20px; "
                            "margin-right: 8px;"
                        )
                    ),

                    ui.span(system),

                    style=(
                        "display: flex; "
                        "align-items: center; "
                        "margin-bottom: 5px;"
                    )
                )

                for system, color in system_colors.items()
            ]

        )

# --------------------------------------------------------
    # REACTIVE DISTANCE PLOT
    # --------------------------------------------------------

    @render_plotly
    def distance_plot():

        selected_system = input.system()

        # ----------------------------------------------------
        # ALL WETLAND SYSTEMS
        # ----------------------------------------------------

        if selected_system == "All Wetland Systems":

            return plot_points(
                System="All Wetland Systems"
            )

        # ----------------------------------------------------
        # INDIVIDUAL WETLAND SYSTEM
        # ----------------------------------------------------

        selected_subsystem = input.subsystems()

        # If All is selected, include every subsystem
        # belonging to the selected system.

        if selected_subsystem == "All":

            selected_subsystems = sorted(
                n100000.loc[
                    n100000["C System"] == selected_system,
                    "C Subsystem"
                ].dropna().unique()
            )

        else:

            selected_subsystems = [selected_subsystem]

        # Generate updated plot
        return plot_points(
            System=selected_system,
            Subsystems=selected_subsystems
        )

# ---------------------------------------------
# run application

print("Dashboard UI created successfully.", flush=True)
app = App(app_ui, server)

