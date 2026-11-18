
# TO RUN:
# conda activate env700-shiny
# shiny run --reload scripts/A5/random_points_dashboard.py

# If running from the A5 directory:
# cd ~/Desktop/Duke/Environmental\ Data\ Exploration/Wildfire-Wetland_BunkerAndersonTseng/scripts/A5
# shiny run --reload random_points_dashboard.py

# Wait for:
# INFO: Application startup complete.


# ============================================================
# IMPORTS
# ============================================================

from pathlib import Path
import pandas as pd
import geopandas as gpd
import platform
import numpy as np

from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_plotly

import plotly.graph_objects as go
import plotly.express as px


# ============================================================
# ESTABLISH FILE PATHS
# ============================================================

project_fldr = Path(__file__).resolve().parents[2]

raw_fldr = project_fldr / "data" / "raw"
processed_fldr = project_fldr / "data" / "processed"
figure_fldr = project_fldr / "figures"


# Set Box folder path based on operating system
if platform.system() == "Windows":
    box_path = Path.home() / "Box"
else:
    box_path = (
        Path.home()
        / "Library"
        / "CloudStorage"
        / "Box-Box"
    )


# Confirm Box path
if box_path.exists():
    print(f"Box folder found at {box_path}")
else:
    raise FileNotFoundError(
        f"Failed to locate Box folder at {box_path}. "
        "Is Box Drive running and are you logged in?"
    )


# Establish dataset paths
wetlands_path = (
    box_path
    / "ENVIRON 712L-Students"
    / "Data"
    / "BunkerAndersonTseng"
    / "wetlands_subset"
    / "wetlands_subset.geojson"
)

simpler_path = (
    box_path
    / "ENVIRON 712L-Students"
    / "Data"
    / "BunkerAndersonTseng"
    / "simpler_wetlands"
)


# ============================================================
# DEFINE COWARDIN SYSTEM COLORS
# ============================================================

system_colors = {
    "Marine": "#02518a",
    "Estuarine": "#0b2ce9",
    "Riverine": "#17becf",
    "Lacustrine": "#01f694",
    "Palustrine": "#4bcb00"
}


# ============================================================
# READ IN THE RANDOM POINTS
# ============================================================

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
            height=800
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
                    hoverinfo="skip"
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
                    hoverinfo="skip"
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
        showlegend=(System == "All Wetland Systems"),
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


# ============================================================
# SANKEY GRAPH TO INPUT TO DASHBOARD
# ============================================================

# Sankey code remains commented out.
# Keep the existing commented-out Sankey function here
# if you want to retain it for future use.


# ============================================================
# DEVELOP SHINY UI
# ============================================================

app_ui = ui.page_fluid(

    # Dashboard title
    ui.h2("Random Points: Wetlands vs Fires"),

    ui.hr(),

    ui.layout_sidebar(

        # ----------------------------------------------------
        # SIDEBAR: USER INPUTS
        # ----------------------------------------------------

        ui.sidebar(

            ui.h4("Filter Wetland Classification"),

            # C System
            ui.input_select(
                "system",
                "System:",
                choices=system_choices,
                selected=initial_system
            ),

            # C Subsystem
            ui.output_ui("subsystem_choices")

        ),

        # ----------------------------------------------------
        # MAIN PANEL: PLOT
        # ----------------------------------------------------

        ui.card(

            ui.card_header(
                "Distance to Wetlands vs Fire"
            ),

            output_widget("distance_plot")

        )

        # ----------------------------------------------------
        # SANKEY CARD (CURRENTLY COMMENTED OUT)
        # ----------------------------------------------------

        # ui.card(
        #     ui.card_header(
        #         "Wetland Classification Sankey Diagram"
        #     ),
        #     output_widget("sankey_plot")
        # )

    )

)


# ============================================================
# INITIALIZE SERVER
# ============================================================

def server(input, output, session):

    # --------------------------------------------------------
    # DYNAMICALLY UPDATE SUBSYSTEM OPTIONS
    # --------------------------------------------------------

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


# ============================================================
# RUN APPLICATION
# ============================================================

app = App(app_ui, server)
