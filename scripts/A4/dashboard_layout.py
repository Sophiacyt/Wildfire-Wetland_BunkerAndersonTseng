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
# Set path to Box folder
if platform.system() == 'Windows':
    box_path = Path.home() / 'Box'
else:
    box_path = Path.home() / "Library" / "CloudStorage" / "Box-Box"

# Path to saved spatial data
output_folder = (
    box_path / 'ENVIRON 712L-Students' /
    'Data' / 'BunkerAndersonTseng' /
    'fire_overlap_data'
)
# go through list of systems, years and load file, store in dictionary
fire_stats_list=[]
year_list = [2020, 2021, 2022, 2023, 2024, 2025]

for year in year_list:

    # Read the CSV for the selected year
    data = pd.read_csv(
        output_folder / f'fire_ol_stats_{year}.csv'
    )

    # Add a column identifying the year
    data['Year'] = year

    # Add dataframe to list
    fire_stats_list.append(data)

# Combine all yearly dataframes
fire_stats_all = pd.concat(fire_stats_list, ignore_index=True)

# plotting function
def plot_fireint(system):
    g = sns.catplot(
        data = system,
        x = 'Year',
        y = 'Percent Wetland Area Burned',
        height=3,
        aspect=2,
        color="orange",
        kind='bar'
        )
    
    g.set(
        title = f"Percent of Wetland Area Burned by Year ({system['C System'].iloc[0]})",
        xlabel="Year",
        ylabel="Wetland Area Burned (%)"
    );
    return g.figure




# -----------------------------------------------------------------------
# Dashboard Layout

app_ui = ui.page_fluid(
    # Header

    ui.h1("Wildfires and Wetlands"),
    ui.p("What is the spatial relationship between wildfires and California wetlands between 2020 and 2025?"),
    ui.hr(),

    # Background Information to go here

    ui.h3("Wildfire Data"),
    ui.p(), # ui.p is for paragraph!
    ui.tags.ul(),   # ui.tags.ul is for bullet points!


    ui.hr(),


    ui.h3("Wetlands Data"),


    



  # Distance to nearest fire widget

    ui.hr(), # this is code for horizontal line

    # Visualizations
    ui.h3("Distance to Nearest Fire"),
    ui.input_select(
            "year",
            "Select Year:",
            choices=[str(y) for y in year_list],
            selected=str(year_list[0])
        ),
    ui.output_plot("fire_plot")
)


# Pct burned area widget
### FINISH WORKING HERE
ui.hr()
# visualization
ui.h3("Percent of Wetlands Area Burned by Wetland Type"),
ui.input_select(
    "system",
    "Select Wetland Type"
    choices=["Palustrine", "Lacustrine", "Riverine", "Marine", "Estuarine"],
    selected=str()
)









# ---------------------------------------------
# init server

def server(input, output, session):

    @render.plot
    def fire_plot():
        year = int(input.year())
        return plot_firedist(year)

    def pct_plot():
        system = str(input.system())
        return plot_fireint(system)


# ---------------------------------------------
# run application

app = App(app_ui, server)

