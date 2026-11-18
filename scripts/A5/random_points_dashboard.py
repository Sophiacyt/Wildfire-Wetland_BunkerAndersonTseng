
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

import pandas as pd
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
n100000 = gpd.read_file(processed_fldr/"n100000_random_pts.geojson")

# ============================================================
# DEVELOP THE PLOTTING FUNCTION
# ============================================================

def plot_points(System, Subsystem, Class, Code):

    # Subset data based on selected dropdown values
    df_subset = n100000.loc[

        (n100000["C System"] == System) &

        (n100000["C Subsystem"] == Subsystem) &

        (n100000["C Class"] == Class) &

        (n100000["C Code"].isin(Code))

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
    n100000["C System"].dropna().unique()
)

subsystem_list = sorted(
    n100000["C Subsystem"].dropna().unique()
)

class_list = sorted(
    n100000["C Class"].dropna().unique()
)

codes = sorted(
    n100000["C Code"].dropna().unique()
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
# SANKEY GRAPH TO INPUT TO DASHBOARD
# ============================================================

read in the wetlands file
wetlands = gpd.read_file(wetlands_path)

def plot_sankey(wetlands):
    # 1. Define Cowardin System colors
    system_colors = {
        "Marine": "#02518a",
        "Estuarine": "#0b2ce9",
        "Riverine": "#17becf",
        "Lacustrine": "#01f694",
        "Palustrine": "#4bcb00"
    }

    df = wetlands.copy()

    df["Hectares"] = pd.to_numeric(df["Hectares"], errors="coerce")
    df = df.dropna(subset=["Hectares"])

    cols = ["C System", "C Subsystem", "C Class"]

    for col in cols:
        df[col] = df[col].fillna("Unknown").astype(str).str.strip()


    # 2. Calculate total hectares for each transition
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


    # 3. Create separate nodes for each classification level
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


    # 4. Build links
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


    # 5. Assign colors to Subsystems and Classes

    # Subsystem colors
    subsystem_colors = {
        # Riverine
        "Intermittent": system_colors["Riverine"],
        "Streambed": system_colors["Riverine"],
        "Unknown Perennial": system_colors["Riverine"],
        "Tidal": system_colors["Riverine"],
        "Lower Perennial": system_colors["Riverine"],
        "Upper Perennial": system_colors["Riverine"],

        # Marine
        "Subtidal": system_colors["Marine"],

        # Lacustrine
        "Limnetic": system_colors["Lacustrine"],
        "Littoral": system_colors["Lacustrine"],
        "Unknown": system_colors["Lacustrine"],

        # Estuarine
        "Intertidal": system_colors["Estuarine"],

        # Palustrine
        "N/A": system_colors["Palustrine"]
    }


    # Class colors
    class_colors = {
        # Marine
        "Unconsolidated Bottom": system_colors["Marine"],
        "Aquatic Bed": system_colors["Marine"],

        # Lacustrine
        "Unconsolidated Shore": system_colors["Lacustrine"],
        "Rock Bottom": system_colors["Lacustrine"],

        # Estuarine
        "Rocky Shore": system_colors["Estuarine"],
        "Reef": system_colors["Estuarine"],

        # Riverine
        "Streambed": system_colors["Riverine"],

        # Palustrine
        "Emergent": system_colors["Palustrine"],
        "Scrub-Shrub": system_colors["Palustrine"],
        "Forested": system_colors["Palustrine"],
        "Unknown": system_colors["Palustrine"]
    }


    # 6. Assign colors to all nodes

    node_colors = (
        # System nodes
        [system_colors.get(x, "#808080") for x in systems]

        # Subsystem nodes
        + [subsystem_colors.get(x, "#808080") for x in subsystems]

        # Class nodes
        + [class_colors.get(x, "#808080") for x in classes]
    )


    # 7. Assign colors to System -> Subsystem links

    # Default: match the destination Subsystem color
    link_colors_1 = [
        subsystem_colors.get(x, "#808080")
        for x in flow1["C Subsystem"]
    ]

    # Special cases for System -> Subsystem links
    for i, row in flow1.iterrows():

        # Estuarine -> Subtidal is Estuarine blue
        if (
            row["C System"] == "Estuarine"
            and row["C Subsystem"] == "Subtidal"
        ):
            link_colors_1[i] = system_colors["Estuarine"]

        # Marine -> Intertidal is Marine blue
        elif (
            row["C System"] == "Marine"
            and row["C Subsystem"] == "Intertidal"
        ):
            link_colors_1[i] = system_colors["Marine"]


    # 8. Assign colors to Subsystem -> Class links

    link_colors_2 = []

    for _, row in flow2.iterrows():

        subsystem = row["C Subsystem"]
        class_name = row["C Class"]

        # Riverine: all links coming from these Subsystems
        if subsystem in [
            "Unknown Perennial",
            "Tidal",
            "Lower Perennial",
            "Upper Perennial"
        ]:
            color = system_colors["Riverine"]

        # Lacustrine: all links coming from these Subsystems
        elif subsystem in ["Limnetic", "Littoral"]:
            color = system_colors["Lacustrine"]

        # Estuarine: all links coming from Intertidal
        elif subsystem == "Intertidal":
            color = system_colors["Estuarine"]

        # Marine: Subtidal -> Aquatic Bed
        elif (subsystem, class_name) == ("Subtidal", "Aquatic Bed"):
            color = system_colors["Marine"]

        # Palustrine: N/A -> Aquatic Bed
        elif (subsystem, class_name) == ("N/A", "Aquatic Bed"):
            color = system_colors["Palustrine"]

        # All other links use their destination Class color
        else:
            color = class_colors.get(class_name, "#808080")

        link_colors_2.append(color)


    # Combine link colors
    link_colors = link_colors_1 + link_colors_2


    # 9. Generate the Sankey diagram
    fig_subset = go.Figure(go.Sankey(
        node=dict(
            label=labels,
            color=node_colors,
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.3)
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            hovertemplate=(
                "%{source.label} → %{target.label}<br>"
                "Area: %{value:,.2s} hectares"
                "<extra></extra>"
            )
        )
    ))


    # 10. Format and display figure
    fig_subset.update_layout(
        title="Wetland Area in Hectares for California Wetlands larger than 1ha by Cowardin System, Subsystem, and Class",
        font_size=11,
        width=1100,
        height=700
    )

    return fig_subset


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
                height="700px",
            )

        ui.card(
            ui.card_header("Wetland Classification Sankey Diagram"),
            output_widget("sankey_plot"),

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
            0.loc[
                n100000["C System"] == selected_system,
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
            n100000.loc[
                (n100000["C System"] == selected_system) &
                (n100000["C Subsystem"] == selected_subsystem),
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
            n100000.loc[
                (n100000["C System"] == selected_system) &
                (n100000["C Subsystem"] == selected_subsystem) &
                (n100000["C Class"] == selected_class),
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