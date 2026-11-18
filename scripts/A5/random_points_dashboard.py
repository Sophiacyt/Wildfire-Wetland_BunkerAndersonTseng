
# TO RUN:
# conda activate env700-shiny
# shiny run --reload scripts/A5/random_points_dashboard.py

# If Mason and running from the A5 directory:
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
import seaborn as sns
import matplotlib.pyplot as plt

from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_widget

import plotly.graph_objects as go


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
# READ IN THE RANDOM POINTS
# ============================================================

n100000 = gpd.read_file(
    processed_fldr / "n100000_random_pts.geojson"
)

print("n100,000 found and loaded")


# ============================================================
# DEFINE COWARDIN SYSTEM COLORS AND SYMBOLS
# ============================================================

system_colors = {
    "Marine": "#02518a",
    "Estuarine": "#0b2ce9",
    "Riverine": "#17becf",
    "Lacustrine": "#01f694",
    "Palustrine": "#4bcb00"
}

system_markers = {
    "Marine": "o",
    "Estuarine": "s",
    "Riverine": "^",
    "Lacustrine": "D",
    "Palustrine": "P"
}

# ============================================================
# DEVELOP THE PLOTTING FUNCTION
# ============================================================

def plot_points(System, Subsystems):
# Subset data based on selected System and Subsystems
    df_subset = n100000.loc[
        (n100000["C System"] == System) &
        (n100000["C Subsystem"].isin(Subsystems))
    ].copy()

    # Handle cases where no observations match
    if df_subset.empty:

        fig = go.Figure()

        fig.add_annotation(
            text="No matching observations",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False
        )

        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            width=960,
            height=800
        )

        return fig

    # Create Plotly figure
    fig = go.Figure()

    # Get selected subsystems
    subsystem_order = sorted(df_subset["C Subsystem"].dropna().unique())

    # Plot points and regression lines for each subsystem
    for subsystem in subsystem_order:

        subset = df_subset[
            df_subset["C Subsystem"] == subsystem
        ].dropna(subset=["Wet_dist", "Fire_dist"])

        if subset.empty:
            continue

        # System marker shape
        marker = system_markers.get(System, "circle")

        # Subsystem color
        color = subsystem_colors.get(subsystem, "#808080")

        # Scatter points
        fig.add_trace(go.Scatter(
            x=subset["Wet_dist"],
            y=subset["Fire_dist"],
            mode="markers",
            name=subsystem,
            legendgroup=subsystem,
            marker=dict(
                color=color,
                symbol=marker,
                size=7,
                opacity=0.7
            ),
            hovertemplate=(
                "<b>%{fullData.name}</b><br>"
                "Wetland Distance: %{x:,.2f} m<br>"
                "Fire Distance: %{y:,.2f} m"
                "<extra></extra>"
            )
        ))

        # Calculate regression
        if len(subset) >= 2 and subset["Wet_dist"].nunique() > 1:

            slope, intercept = np.polyfit(
                subset["Wet_dist"],
                subset["Fire_dist"],
                1
            )

            predictions = (
                slope * subset["Wet_dist"] + intercept
            )

            ss_res = np.sum(
                (subset["Fire_dist"] - predictions) ** 2
            )

            ss_tot = np.sum(
                (subset["Fire_dist"] - subset["Fire_dist"].mean()) ** 2
            )

            r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else np.nan

            # Regression line endpoints
            x_line = np.array([
                subset["Wet_dist"].min(),
                subset["Wet_dist"].max()
            ])

            y_line = slope * x_line + intercept

            # Regression line with hover information
            fig.add_trace(go.Scatter(
                x=x_line,
                y=y_line,
                mode="lines",
                name=f"{subsystem} Regression",
                legendgroup=subsystem,
                line=dict(
                    color=color,
                    width=3
                ),
                customdata=[
                    [r2, slope, intercept, len(subset)]
                ] * 2,
                hovertemplate=(
                    f"<b>{subsystem} Regression</b><br>"
                    "R²: %{customdata[0]:.4f}<br>"
                    "Slope: %{customdata[1]:.4f}<br>"
                    "Intercept: %{customdata[2]:,.2f}<br>"
                    "Observations: %{customdata[3]:,}"
                    "<extra></extra>"
                )
            ))

    # Update layout
    fig.update_layout(
        title="10,000 Random Points in California",
        xaxis_title="Distance to Nearest Wetland (m)",
        yaxis_title="Distance to Nearest Fire (m)",
        width=960,
        height=800,
        hovermode="closest",
        legend=dict(
            title="Cowardin Subsystem",
            x=0.95,
            y=0.95,
            xanchor="right",
            yanchor="top"
        )
    )

    fig.update_xaxes(tickformat=",")
    fig.update_yaxes(tickformat=",")

    return fig


# ============================================================
# ESTABLISH DROPDOWN OPTIONS
# ============================================================

system_list = sorted(
    n100000["C System"].dropna().unique()
)


# Initial System selection
initial_system = (
    "Riverine" if "Riverine" in system_list
    else system_list[0]
)


# ============================================================
# SANKEY GRAPH TO INPUT TO DASHBOARD
# ============================================================

# read in the wetlands file
# wetlands = gpd.read_file(wetlands_path)

# print("wetlands data found and loaded!")


# def plot_sankey(wetlands):

#     # 1. Define Cowardin System colors
#     system_colors = {
#         "Marine": "#02518a",
#         "Estuarine": "#0b2ce9",
#         "Riverine": "#17becf",
#         "Lacustrine": "#01f694",
#         "Palustrine": "#4bcb00"
#     }

#     df = wetlands.copy()

#     df["Hectares"] = pd.to_numeric(df["Hectares"], errors="coerce")
#     df = df.dropna(subset=["Hectares"])

#     cols = ["C System", "C Subsystem", "C Class"]

#     for col in cols:
#         df[col] = df[col].fillna("Unknown").astype(str).str.strip()


#     # 2. Calculate total hectares for each transition

#     flow1 = (
#         df.groupby(["C System", "C Subsystem"])["Hectares"]
#         .sum()
#         .reset_index()
#     )

#     flow2 = (
#         df.groupby(["C Subsystem", "C Class"])["Hectares"]
#         .sum()
#         .reset_index()
#     )


#     # 3. Create separate nodes for each classification level

#     systems = df["C System"].unique().tolist()
#     subsystems = df["C Subsystem"].unique().tolist()
#     classes = df["C Class"].unique().tolist()

#     labels = (
#         [f"System: {x}" for x in systems]
#         + [f"Subsystem: {x}" for x in subsystems]
#         + [f"Class: {x}" for x in classes]
#     )

#     system_map = {x: i for i, x in enumerate(systems)}

#     subsystem_map = {
#         x: i + len(systems)
#         for i, x in enumerate(subsystems)
#     }

#     class_map = {
#         x: i + len(systems) + len(subsystems)
#         for i, x in enumerate(classes)
#     }


#     # 4. Build links

#     sources = (
#         flow1["C System"].map(system_map).tolist()
#         + flow2["C Subsystem"].map(subsystem_map).tolist()
#     )

#     targets = (
#         flow1["C Subsystem"].map(subsystem_map).tolist()
#         + flow2["C Class"].map(class_map).tolist()
#     )

#     values = (
#         flow1["Hectares"].tolist()
#         + flow2["Hectares"].tolist()
#     )


#     # 5. Assign colors to Subsystems and Classes

#     # Subsystem colors
#     subsystem_colors = {

#         # Riverine
#         "Intermittent": system_colors["Riverine"],
#         "Streambed": system_colors["Riverine"],
#         "Unknown Perennial": system_colors["Riverine"],
#         "Tidal": system_colors["Riverine"],
#         "Lower Perennial": system_colors["Riverine"],
#         "Upper Perennial": system_colors["Riverine"],

#         # Marine
#         "Subtidal": system_colors["Marine"],

#         # Lacustrine
#         "Limnetic": system_colors["Lacustrine"],
#         "Littoral": system_colors["Lacustrine"],
#         "Unknown": system_colors["Lacustrine"],

#         # Estuarine
#         "Intertidal": system_colors["Estuarine"],

#         # Palustrine
#         "N/A": system_colors["Palustrine"]
#     }


#     # Class colors
#     class_colors = {

#         # Marine
#         "Unconsolidated Bottom": system_colors["Marine"],
#         "Aquatic Bed": system_colors["Marine"],

#         # Lacustrine
#         "Unconsolidated Shore": system_colors["Lacustrine"],
#         "Rock Bottom": system_colors["Lacustrine"],

#         # Estuarine
#         "Rocky Shore": system_colors["Estuarine"],
#         "Reef": system_colors["Estuarine"],

#         # Riverine
#         "Streambed": system_colors["Riverine"],

#         # Palustrine
#         "Emergent": system_colors["Palustrine"],
#         "Scrub-Shrub": system_colors["Palustrine"],
#         "Forested": system_colors["Palustrine"],
#         "Unknown": system_colors["Palustrine"]
#     }


#     # 6. Assign colors to all nodes

#     node_colors = (

#         # System nodes
#         [system_colors.get(x, "#808080") for x in systems]

#         # Subsystem nodes
#         + [subsystem_colors.get(x, "#808080") for x in subsystems]

#         # Class nodes
#         + [class_colors.get(x, "#808080") for x in classes]
#     )


#     # 7. Assign colors to System -> Subsystem links

#     # Default: match the destination Subsystem color
#     link_colors_1 = [
#         subsystem_colors.get(x, "#808080")
#         for x in flow1["C Subsystem"]
#     ]


#     # Special cases for System -> Subsystem links

#     for i, row in flow1.iterrows():

#         # Estuarine -> Subtidal is Estuarine blue
#         if (
#             row["C System"] == "Estuarine"
#             and row["C Subsystem"] == "Subtidal"
#         ):
#             link_colors_1[i] = system_colors["Estuarine"]

#         # Marine -> Intertidal is Marine blue
#         elif (
#             row["C System"] == "Marine"
#             and row["C Subsystem"] == "Intertidal"
#         ):
#             link_colors_1[i] = system_colors["Marine"]


#     # 8. Assign colors to Subsystem -> Class links

#     link_colors_2 = []

#     for _, row in flow2.iterrows():

#         subsystem = row["C Subsystem"]
#         class_name = row["C Class"]

#         # Riverine: all links coming from these Subsystems
#         if subsystem in [
#             "Unknown Perennial",
#             "Tidal",
#             "Lower Perennial",
#             "Upper Perennial"
#         ]:
#             color = system_colors["Riverine"]

#         # Lacustrine: all links coming from these Subsystems
#         elif subsystem in ["Limnetic", "Littoral"]:
#             color = system_colors["Lacustrine"]

#         # Estuarine: all links coming from Intertidal
#         elif subsystem == "Intertidal":
#             color = system_colors["Estuarine"]

#         # Marine: Subtidal -> Aquatic Bed
#         elif (subsystem, class_name) == ("Subtidal", "Aquatic Bed"):
#             color = system_colors["Marine"]

#         # Palustrine: N/A -> Aquatic Bed
#         elif (subsystem, class_name) == ("N/A", "Aquatic Bed"):
#             color = system_colors["Palustrine"]

#         # All other links use their destination Class color
#         else:
#             color = class_colors.get(class_name, "#808080")

#         link_colors_2.append(color)


#     # Combine link colors
#     link_colors = link_colors_1 + link_colors_2


#     # 9. Generate the Sankey diagram

#     fig_subset = go.Figure(go.Sankey(
#         node=dict(
#             label=labels,
#             color=node_colors,
#             pad=15,
#             thickness=20,
#             line=dict(color="black", width=0.3)
#         ),
#         link=dict(
#             source=sources,
#             target=targets,
#             value=values,
#             color=link_colors,
#             hovertemplate=(
#                 "%{source.label} → %{target.label}<br>"
#                 "Area: %{value:,.2s} hectares"
#                 "<extra></extra>"
#             )
#         )
#     ))


#     # 10. Format and display figure

#     fig_subset.update_layout(
#         title="Wetland Area in Hectares for California Wetlands larger than 1ha by Cowardin System, Subsystem, and Class",
#         font_size=11,
#         width=1100,
#         height=700
#     )

#     return fig_subset


# ============================================================
# DEVELOP SHINY UI
# ============================================================

app_ui = ui.page_fluid(

    # Dashboard title
    ui.h2("Random Points: Wetlands vs Fires"),

    ui.hr(),

    ui.layout_sidebar(

        # ----------------------------------------
        # SIDEBAR: USER INPUTS
        # ----------------------------------------

        ui.sidebar(

            ui.h4("Filter Wetland Classification"),

            # C System
            ui.input_select(
                "system",
                "System:",
                choices=system_list,
                selected=initial_system
            ),

            # C Subsystem checkboxes
            ui.output_ui("subsystem_choices"),

        ),

        # ----------------------------------------
        # MAIN PANEL: PLOT
        # ----------------------------------------

        ui.card(

            ui.card_header(
                "Distance to Wetlands vs Fire"
            ),

            ui.output_plot(
                "distance_plot",
                height="700px"
            )
        ),

        # Sankey card (currently commented out)
        # ui.card(
        #     ui.card_header("Wetland Classification Sankey Diagram"),
        #     output_widget("sankey_plot"),
        # )

    )
)


# ============================================================
# INIT SERVER
# ============================================================

def server(input, output, session):

    # --------------------------------------------------------
    # DYNAMIC SUBSYSTEM CHECKBOXES
    # --------------------------------------------------------

    @render.ui
    def subsystem_choices():

        selected_system = input.system()

        # Find available subsystems for selected System
        available_subsystems = sorted(
            n100000.loc[
                n100000["C System"] == selected_system,
                "C Subsystem"
            ].dropna().unique()
        )

        # Display available subsystems as checkboxes
        return ui.input_checkbox_group(
            "subsystems",
            "Subsystems:",
            choices=available_subsystems,
            selected=available_subsystems
        )


    # --------------------------------------------------------
    # REACTIVE PLOT
    # --------------------------------------------------------

    @render.plot
    def distance_plot():

        # Get current selections
        selected_system = input.system()
        selected_subsystems = input.subsystems() or []

        # Generate updated plot
        return plot_points(
            System=selected_system,
            Subsystems=selected_subsystems
        )


# ============================================================
# RUN APPLICATION
# ============================================================

app = App(app_ui, server)