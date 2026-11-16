# trial a shiny dashboard with multiple pages
# TO RUN: 
# conda activate env700-shiny
# shiny run --reload scripts/A5/dashboard_tabs.py 

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


# WIDGET SETUP SPACE


# DASHBOARD LAYOUT
app_ui = ui.page_navbar(
    # add home page
    ui.nav_panel(
        "Home",
        ui.h2("Central Questions"),
        ui.h2("Data Limitations"),
    ),

    # Add wildfire page
    ui.nav_panel(
        "Wildfire",
        ui.h2("CA Wildfire Data"),
        ui.p("Explore our fire dataset"),
    ),

    # add wetlands page
    ui.nav_panel(
        "Wetlands",
        ui.h2("CA Wetlands Data"),
        ui.p("Explore our wetlands dataset"),
    ),

    # add analysis page
    ui.nav_panel(
        "Analysis",
        ui.h2("Question 1: "),
        ui.h2("Question 2: "),
        ui.h2("Question 3: "),
    ),

    title="Wildfires & Wetlands",
    
    # add style choices via the header argument so it doesn't break the navbar
    header=ui.tags.style("""
        body {
            background-color: #F7F7F2;
            font-family: 'Calibri', 'Candara', 'Segoe UI', sans-serif;
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
)


# initialize server
def server(input, output, session):

    @render.plot
    def fire_cause_plot():
        # Get the selected alarm date range
        alarm_dates = input.alarm_dates()
        alarm_start_date = alarm_dates[0]
        alarm_end_date = alarm_dates[1]

        # Get the selected fire cause
        selected_cause = input.cause()

        # Get the selected minimum fire size
        selected_size = size_options[input.fire_size()]

        # Generate the plot
        return plot_fire_cause(
            alarm_start_date,
            alarm_end_date,
            selected_cause,
            selected_size
        )

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

    @render.table
    def summary_table_output():
        selected_year = int(input.summary_year())

        table = summary_table.loc[
            summary_table["Year"] == selected_year
        ]

        return table


# ---------------------------------------------
# run application
app = App(app_ui, server)
