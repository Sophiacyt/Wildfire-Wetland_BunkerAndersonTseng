
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
n10000 = gpd.read_file(processed_fldr/"n10000_random_pts.geojson")

# ============================================================
# DEVELOP THE PLOTTING FUNCTION
# ============================================================

def plot_points(System, Subsystem, Class, Code):

    # Subset data based on selected dropdown values
    df_subset = n10000.loc[

        (n10000["C System"] == System) &

        (n10000["C Subsystem"] == Subsystem) &

        (n10000["C Class"] == Class) &

        (n10000["C Code"].isin(Code))

    ].copy()


    # Handle cases where no observations match
    if df_subset.empty:

        fig, ax = plt.subplots(figsize=(8, 5))

        ax.text(
            0.5,
            0.5,
            "No matching observations",
            ha="center",
            va="center",
            transform=ax.transAxes
        )

        ax.set_axis_off()

        return fig


    # Create regression plot
    # Each selected C Code gets its own color and regression line
    dist_plot = sns.lmplot(
        data=df_subset,
        x="Wet_dist",
        y="Fire_dist",
        hue="C Code",
        height=8,
        aspect=1.2
    )


    # Set title and axis labels
    dist_plot.set_axis_labels(
        "Distance to Nearest Wetland (m)",
        "Distance to Nearest Fire (m)"
    )

    dist_plot.set(
        title=(
            "10,000 Random Points in California\n"
            "Distance to Wetlands vs Fire"
        )
    )


    # Adjust legend location
    if dist_plot.legend is not None:

        sns.move_legend(
            dist_plot,
            loc="upper right",
            bbox_to_anchor=(0.95, 0.95)
        )


    # Return matplotlib figure
    return dist_plot.fig


# ============================================================
# ESTABLISH DROPDOWN OPTIONS
# ============================================================

system_list = sorted(
    n10000["C System"].dropna().unique()
)

subsystem_list = sorted(
    n10000["C Subsystem"].dropna().unique()
)

class_list = sorted(
    n10000["C Class"].dropna().unique()
)

codes = sorted(
    n10000["C Code"].dropna().unique()
)


# Initial selections
initial_system = (
    "Riverine" if "Riverine" in system_list
    else system_list[0]
)

initial_subsystem = (
    "Intermittent" if "Intermittent" in subsystem_list
    else subsystem_list[0]
)

initial_class = (
    "Streambed" if "Streambed" in class_list
    else class_list[0]
)

initial_code = (
    ["R4SBA"] if "R4SBA" in codes
    else [codes[0]]
)


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

            # C Subsystem
            ui.input_select(
                "subsystem",
                "Subsystem:",
                choices=subsystem_list,
                selected=initial_subsystem
            ),

            # C Class
            ui.input_select(
                "class",
                "Class:",
                choices=class_list,
                selected=initial_class
            ),

            # C Code checkboxes
            ui.h5("Select C Codes:"),

            ui.output_ui("code_checkboxes"),

            width=300
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

        )
    )
)


# ============================================================
# INIT SERVER
# ============================================================

def server(input, output, session):

    # --------------------------------------------------------
    # UPDATE SUBSYSTEM OPTIONS
    # --------------------------------------------------------

    @reactive.effect
    def update_subsystem():

        selected_system = input.system()

        # Find available subsystems
        available_subsystems = sorted(
            n10000.loc[
                n10000["C System"] == selected_system,
                "C Subsystem"
            ].dropna().unique()
        )

        # Preserve selection if possible
        current = input.subsystem()

        if current in available_subsystems:
            selected = current

        elif available_subsystems:
            selected = available_subsystems[0]

        else:
            selected = None

        # Update dropdown
        ui.update_select(
            "subsystem",
            choices=available_subsystems,
            selected=selected,
            session=session
        )


    # --------------------------------------------------------
    # UPDATE CLASS OPTIONS
    # --------------------------------------------------------

    @reactive.effect
    def update_class():

        selected_system = input.system()
        selected_subsystem = input.subsystem()

        # Find available classes
        available_classes = sorted(
            n10000.loc[
                (n10000["C System"] == selected_system) &
                (n10000["C Subsystem"] == selected_subsystem),
                "C Class"
            ].dropna().unique()
        )

        # Preserve selection if possible
        current = input["class"]()

        if current in available_classes:
            selected = current

        elif available_classes:
            selected = available_classes[0]

        else:
            selected = None

        # Update dropdown
        ui.update_select(
            "class",
            choices=available_classes,
            selected=selected,
            session=session
        )


    # --------------------------------------------------------
    # GENERATE C CODE CHECKBOXES
    # --------------------------------------------------------

    @render.ui
    def code_checkboxes():

        selected_system = input.system()
        selected_subsystem = input.subsystem()
        selected_class = input["class"]()

        # Find available codes
        available_codes = sorted(
            n10000.loc[
                (n10000["C System"] == selected_system) &
                (n10000["C Subsystem"] == selected_subsystem) &
                (n10000["C Class"] == selected_class),
                "C Code"
            ].dropna().unique()
        )

        # Select initial code if available;
        # otherwise select the first available code
        if initial_code[0] in available_codes:
            selected = initial_code
        elif available_codes:
            selected = [available_codes[0]]
        else:
            selected = []

        # Create individual checkboxes
        return ui.input_checkbox_group(
            "codes",
            label="",
            choices=available_codes,
            selected=selected,
            inline=False
        )


    # --------------------------------------------------------
    # REACTIVE PLOT
    # --------------------------------------------------------

    @render.plot
    def distance_plot():

        # Get current selections
        selected_system = input.system()

        selected_subsystem = input.subsystem()

        selected_class = input["class"]()

        # Multiple checkbox selections return a list
        selected_codes = input.codes() or []

        # Generate updated plot
        return plot_points(

            System=selected_system,

            Subsystem=selected_subsystem,

            Class=selected_class,

            Code=selected_codes

        )


# ============================================================
# RUN APPLICATION
# ============================================================

app = App(app_ui, server)