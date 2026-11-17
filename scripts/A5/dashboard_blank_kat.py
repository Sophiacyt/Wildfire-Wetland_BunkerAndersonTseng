# TO RUN:
# conda activate env700-shiny
# shiny run --reload scripts/A5/dashboard_blank_kat.py

# if mason and struggling, run below
# cd ~/Desktop/Duke/Environmental\ Data\ Exploration/Wildfire-Wetland_BunkerAndersonTseng/scripts/A4
# shiny run --reload dashboard_layout_a4.py

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








# DASHBOARD CONTENT ----------------------------------------------------

app_ui = ui.page_navbar(

    # --------------------------------------------------
    # HOME tab
    # --------------------------------------------------

    ui.nav_panel(
        "Home",

        # add a box with some project information
        ui.card(
            ui.card_header('Wildfires & Wetlands Dashboard'),

            ui.p(
                'This dashboard uses CalFire fire perimeters data and National Wetlands Inventory '
                'wetland data to explore the relationship between wetlands and wildfires in California.'
            ),

            ui.h4("Central Questions"),

            ui.tags.ul(
                ui.tags.li('What types of wetlands are most impacted by wildfires in the state of California?'),
                ui.tags.li('Are wetlands less likely to burn than other land in California?'),
                ui.tags.li('Is land near wetlands less likely to burn than land farther away?'),
            ),
        ),
    ),

    # --------------------------------------------------
    # WILDFIRE tab
    # --------------------------------------------------

    ui.nav_panel(
        "Wildfire",
    ),

    # --------------------------------------------------
    # WETLANDS tab
    # --------------------------------------------------

    ui.nav_panel(
        "Wetlands",
    ),

    # --------------------------------------------------
    # ANALYSIS tab
    # --------------------------------------------------

    ui.nav_panel(
        "Analysis",
    ),

    title="Wildfires & Wetlands Dashboard",

)

# DEFINE SERVER

def server(input, output, session):
    pass


app = App(app_ui, server)