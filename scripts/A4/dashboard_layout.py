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





## FIRE DISTANCE WIDGET
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


# ==========================================
# 4. DASHBOARD UI
# ==========================================

app_ui = ui.page_sidebar(

    ui.sidebar(
        ui.h4("Dashboard Filters"),

        ui.input_select(
            "year",
            "Select Year:",
            choices=[str(y) for y in year_list],
            selected=str(year_list[0])
        )
    ),

    ui.h2("Wetland & Wildfire Analysis"),

    ui.card(
        ui.card_header("Distance to Nearest Fire"),
        ui.output_plot("fire_plot")
    )

)
# ==========================================
# 5. SERVER
# ==========================================

def server(input, output, session):

    @render.plot
    def fire_plot():
        year = int(input.year())
        return plot_firedist(year)


# ==========================================
# 6. RUN APPLICATION
# ==========================================

app = App(app_ui, server)

