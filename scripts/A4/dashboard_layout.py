# TO RUN: 
# conda activate env700-shiny
# shiny run --reload scripts/A4/dashboard_layout.py 

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
# -----------------------------------------------------------------------

## FIRE DISTANCE WIDGET SETUP
# load data
# Set path to Box folder
if platform.system() == 'Windows':
    box_path = Path.home() / 'Box'
else:
    box_path = Path.home() / "Library" / "CloudStorage" / "Box-Box"

# Path to saved spatial data
output_folder = (
    box_path / 'ENVIRON 712L-Students' /
    'Data' / 'BunkerAndersonTseng' /
    'fire_distance_data'
)

# Available years
year_list = [2020, 2021, 2022, 2023, 2024, 2025]

# Load all fire data
fire_data = {}

for year in year_list:
    fire_data[year] = gpd.read_file(
        output_folder / f'nearest_fires_{year}.gpkg'
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
# -----------------------------------------------------------------------
# WETLANDS BURNED WIDGET SETUP
# Path to saved fire overlap data
overlap_folder = (
    box_path / 'ENVIRON 712L-Students' /
    'Data' / 'BunkerAndersonTseng' /
    'fire_overlap_data'
)

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
def plot_fireint(system):

    g = sns.catplot(
        data=system,
        x='Year',
        y='Percent Wetland Area Burned',
        height=3,
        aspect=2,
        color="orange",
        kind='bar'
    )

    g.set(
        title=f"Percent of Wetland Area Burned by Year ({system['C System'].iloc[0]})",
        xlabel="Year",
        ylabel="Wetland Area Burned (%)"
    )

    return g.figure




# -----------------------------------------------------------------------
# Dashboard Layout

# Dashboard Layout

app_ui = ui.page_fluid(

    # -----------------------------------------------------------------------
    # Add some color and font choices
    ui.tags.style("""
            body {
                background-color: #F7F7F2;
                font-family: 'Arial', sans-serif;
                color: #333D36;
            }
    
            h1 {
                color: #244B38;
                font-size: 36px;
                font-weight: bold;
            }
    
            h3 {
                color: #244B38;
                font-weight: bold;
            }
    
            h4 {
                color: #789477;
            }
    
            p {
                font-size: 16px;
                line-height: 1.6;
            }
        """),

    # Header
    ui.h1("Wildfires and Wetlands"),
    ui.p(
        "What is the spatial relationship between wildfires "
        "and California wetlands between 2020 and 2025?"
    ),
    ui.hr(),

    #---------------------------------------------------

    # BACKGROUND INFO
    
    # Wildfire Data
    ui.h3("Wildfire Data"),
    ui.p("Wildfire shapefile data comes from the California Historical Fire Perimeters dataset, maintained by CalFire, "
    "and reporting fires greater than or equal to 10 acres inside the state between 1910 and 2025. For " \
    "this project, data has been subset to years between 2020 and 2025."), 
    ui.tags.ul(),

    ui.hr(),

    # Wetlands data
    ui.h3("Wetlands Data"),
    ui.p("Wetlands shapefile data comes from the National Wetland Inventory, downloaded for the state of California. This dataset" \
    "divides wetlands into Cowardin (1979) wetlands classifications of 5 systems, and additional subsystems," \
    "classes, and subclasses. System descriptions are as follows." ),
    
    ui.tags.ul( # add some bullet points for systems
        ui.tags.li("Marine: open ocean or high energy wetlands with salinity greater than 0.5ppt."),
        ui.tags.li("Estuarine: semi-enclosed or low energy wetlands with salinity greater than 0.5ppt."),
        ui.tags.li("Riverine: freshwater wetlands confined to a channel."),
        ui.tags.li("Lacustrine: freshwater wetlands exceeding 20 acres or being deeper than 2.5m."),
        ui.tags.li("Palustrine: freshwater wetlands dominated by trees or woody vegetation, or those" \
        "freshwater inland wetlands less than 20 acres or shallower than 2.5m.")
),

    ui.hr(),

    #---------------------------------------------------

    # DISTANCE TO NEAREST FIRE WIDGET
    ui.h3("Distance to Nearest Fire"),
    ui.input_select(
        "year",
        "Select Year:",
        choices=[str(y) for y in year_list],
        selected=str(year_list[0])
    ),
    ui.div(

    # put plot in a container so that it does not get stretched out
    ui.output_plot("fire_plot"),
    style="max-width: 850px; margin: margin: 30px auto 30px auto;"
    ),

    ui.hr(),

    #---------------------------------------------------
    
    # PCT BURNED AREA WIDGET
    ui.h3("Percent of Wetland Area Burned by Wetland Type"),
    ui.input_select(
        "system",
        "Select Wetland System:",
        choices=system_list,
        selected=system_list[0]
    ),
    ui.div(

    # put plot in a container so that it does not get stretched out
    ui.output_plot("fireint_plot"),
    style="max-width: 850px; margin: margin: 30px auto 30px auto;"
)

)





# ---------------------------------------------
# INIT SERVER

def server(input, output, session):

    @render.plot
    def fire_plot():
        year = int(input.year())
        return plot_firedist(year)

    @render.plot
    def fireint_plot():
        selected_system = input.system()

        system = fire_stats_all[
            fire_stats_all['C System'] == selected_system
        ]

        return plot_fireint(system)
# ---------------------------------------------
# run application

app = App(app_ui, server)

