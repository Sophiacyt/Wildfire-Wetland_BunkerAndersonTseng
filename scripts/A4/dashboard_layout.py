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
import matplotlib.ticker as ticker

# -----------------------------------------------------------------------
# FIRE BY CAUSE WIDGET SETUP
# --------------------------------------------------
# FIRE BY CAUSE DATA SETUP
# --------------------------------------------------

# Read in cleaned fire dataset
project_fldr = Path(__file__).resolve().parents[2]

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

size_options = {
    "All sizes": 0,
    "10,000+ hectares": 100_000_000,
    "50,000+ hectares": 500_000_000,
    "100,000+ hectares": 1_000_000_000,
    "500,000+ hectares": 5_000_000_000
}

def plot_fire_cause(alarm_start_date, alarm_end_date, cause, size):

    # Filter the fire data
    fire_subset = fire_shp_25.loc[
    (fire_shp_25['ALARM_DATE'] >= pd.to_datetime(alarm_start_date, utc=True)) &
    (fire_shp_25['ALARM_DATE'] <= pd.to_datetime(alarm_end_date, utc=True)) &
    (fire_shp_25['CONT_DATE'] >= pd.Timestamp("2020-01-01", tz="UTC")) &
    (fire_shp_25['CONT_DATE'] <= pd.Timestamp("2025-12-31 23:59:59", tz="UTC")) &
    (fire_shp_25['CAUSE_NAME'] == cause) &
    (fire_shp_25['Shape_Area'] >= size)
    ]

    # Create the plot
    the_plot = sns.relplot(
        data=fire_subset,
        x='Alarm Mo_1',
        y='Shape_Area',
        hue='CAUSE_NAME',
        size='Shape_Area',
        alpha=0.7,
        legend=True
    )

    # Add labels and title
    the_plot.set_axis_labels(
        'Alarm Month',
        'Fire Size (hectares)'
    )
    the_plot.set(title='Fire by Cause')

    # Format the y-axis from square meters to hectares
    ax = the_plot.ax
    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, pos: f'{x / 10_000:g}')
    )

    return the_plot.figure











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

    # add sophia's plot that shows fire by cause with date slider
    ui.input_date_range(
    "alarm_dates",
    "Select Alarm Date Range:",
    start="2020-01-01",
    end="2025-12-31",
    min="2020-01-01",
    max="2025-12-31"
    ),

    ui.input_select(
        "cause",
        "Select Fire Cause:",
        choices=cause_list,
        selected="Lightning"
    ),

    ui.input_select(
        "fire_size",
        "Minimum Fire Size:",
        choices={
            "All sizes": 0,
            "10,000+ hectares": 100_000_000,
            "50,000+ hectares": 500_000_000,
            "100,000+ hectares": 1_000_000_000,
            "500,000+ hectares": 5_000_000_000
        },
        selected=0
    ),

    ui.output_plot("fire_cause_plot"),

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
# ---------------------------------------------
# run application

app = App(app_ui, server)

