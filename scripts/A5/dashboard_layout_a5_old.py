# TO RUN: 
# conda activate env700-shiny
# shiny run --reload scripts/A4/dashboard_layout_a4.py 

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
# -----------------------------------------------------------------------


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
# Summary table setup
years = [2020, 2021, 2022, 2023, 2024, 2025]

# we already went through the overlap stats
overlap_stats = fire_stats_all

# Load yearly fire distance statistics
dist_list = []

for year in years:
    data = pd.read_csv(
        output_folder / f"fire_stats_{year}.csv"
    )

    data["Year"] = year
    dist_list.append(data)

dist_stats = pd.concat(
    dist_list,
    ignore_index=True
)


# Combine overlap and distance statistics
summary_table = pd.merge(
    overlap_stats,
    dist_stats,
    on=["C System", "Year"],
    how="outer"
)

# Sort by year and wetland system
summary_table = summary_table.sort_values(
    ["Year", "C System"]
).reset_index(drop=True)

# Rename columns for dashboard presentation
summary_table = summary_table.rename(columns={
    "C System": "Wetland System",
    "Year": "Year",
    "Burned Area (ha)": "Burned Area (ha)",
    "Total Wetland Area (ha)": "Total Wetland Area (ha)",
    "Percent Wetland Area Burned": "% of Wetland Area Burned",
    "Percent of Fire Area in Wetlands": "% of Fire Area in Wetlands",
    "Avg_Dist_Fire_km": "Average Distance to Fire (km)",
    "Std_Dist_Fire_km": "Standard Deviation of Distance (km)",
    "Median_Dist_Fire_km": "Median Distance to Fire (km)"
})
# re-order columns for presentation
summary_table = summary_table[
    [
        "Year",
        "Wetland System",
        "Burned Area (ha)",
        "Total Wetland Area (ha)",
        "% of Wetland Area Burned",
        "% of Fire Area in Wetlands",
        "Average Distance to Fire (km)",
        "Standard Deviation of Distance (km)",
        "Median Distance to Fire (km)"
    ]
]

# change formatting to shorten decimals, show percents
summary_table = summary_table.round(3)


# -----------------------------------------------------------------------
# VISUALIZATIONS SETUP

# IMPORT DATA
# -----------------------------------------------------------------------

# establish paths to datasets

project_fldr = Path(__file__).resolve().parents[2]
raw_fldr = project_fldr / 'data' / 'raw'
processed_fldr = project_fldr / 'data' / 'processed'
figure_fldr = project_fldr/"figures"

# set a path to the main box folder based on machine's os
# if windows: 
if platform.system() == 'Windows':
    box_path = Path.home() / 'Box'
# if mac:
else:
    box_path = Path.home() / "Library" / "CloudStorage" / "Box-Box"

#Confirm that the box path is valid
if box_path.exists():
    print(f'Box folder found at {box_path}')
else:
    print(f'Failed to locate the Box folder.\nIs the BoxDrive app running?\nAre you logged in?')

# create path object that goes to the specific folder on Box drive
# uploading wetlands that are bigger than a hectare
html_map_path = box_path / 'ENVIRON 712L-Students' / 'Data' / 'BunkerAndersonTseng' / 'html_maps'

# --------------------------fire-explore-data----------------------------
# california outline
ca_outline = gpd.read_file(processed_fldr/"fire_explore/ca_outline.geojson")

# pull in the fires into dfs from geojsons
fires = ["fire_2020", "fire_2021", "fire_2022", "fire_2023", "fire_2024", "fire_2025"]
years=[2020, 2021, 2022, 2023, 2024, 2025]

for fire, year in zip(fires, years):
    globals()[fire] = gpd.read_file(
        processed_fldr/ "fire_explore" / f"fire_{year}.geojson"
    )

fire_dfs = [fire_2020, fire_2021, fire_2022, fire_2023, fire_2024, fire_2025]

years = [2020, 2021, 2022, 2023, 2024, 2025]

# remove timestamp columns because they are not serializable for JSON
for fire_df in fire_dfs:
    fire_df.drop(columns=["ALARM_DATE", "CONT_DATE"], inplace=True)

# ------------------------wetland-explore-data---------------------------
# palustrine and riverine to come later
ca_outline = gpd.read_file(processed_fldr/'wetland_explore'/"ca_outline.geojson")
marine = gpd.read_file(processed_fldr/'wetland_explore'/"marine_simpler.geojson")
estuarine = gpd.read_file(processed_fldr/'wetland_explore'/"estuarine_simpler.geojson")
lacustrine = gpd.read_file(processed_fldr/'wetland_explore'/"lacustrine_simpler.geojson")

# -----------------------------------------------------------------------
# MAP SET UP
# -----------------------------------------------------------------------
# bounding coordinates for California and rest of map
minx, miny, maxx, maxy = ca_outline.total_bounds

fire_colors = {
    "2020": "#D7191C",  # Deep red
    "2021": "#E7471A",  # Red-orange
    "2022": "#F46D1F",  # Orange
    "2023": "#F99524",  # Golden orange
    "2024": "#FDC43A",  # Gold
    "2025": "#FFFF33"   # Yellow
}

#plot wetlands, by system color
system_colors = {
    "Marine": "#02518a",
    "Estuarine": "#0b2ce9",
    "Riverine": "#17becf",
    "Lacustrine": "#01f694",
    "Palustrine": "#4bcb00"
}

# --------------------------fire-explore-map-----------------------------
fire_map_left = folium.Map(
    zoom_start=6,
    tiles=None,
)

# ESRI satellite basemap
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri, Maxar, Earthstar Geographics, and the GIS User Community",
    name="Satellite Imagery",
    overlay=False,
    control=False
).add_to(fire_map_left)

# this should leave us so that the initial zoom is the outline of california
fire_map_left.fit_bounds([
    [miny, minx],  # Southwest corner
    [maxy, maxx]   # Northeast corner
])

# add CA outline
folium.GeoJson(
    ca_outline.to_json(),
    style_function=lambda x: {
        "color": "black",
        "fillOpacity": 0,
        "weight": 2
    },
    control= False # always on
).add_to(fire_map_left)

# for loop to add in the fires
for fire_df, year in zip(fire_dfs, years):
    folium.GeoJson(
        fire_df.to_json(),
        name=f"{year} Fires",
        style_function=lambda x, year=year: {
            "color": fire_colors[str(year)],
            "fillColor": fire_colors[str(year)],
            "fillOpacity": 0.9,
            "weight": 1.5
        },
        control=True
    ).add_to(fire_map_left)

folium.LayerControl(collapsed=False).add_to(fire_map_left)

fire_map_left # this would display in a notebook

# ------------------------wetland-explore-map----------------------------

# MAKE THE EXPLORE

# create the actual map as a base now
wetland_map_right = folium.Map(
    zoom_start=6,
    tiles=None,
)

# ESRI satellite basemap
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri, Maxar, Earthstar Geographics, and the GIS User Community",
    name="Satellite Imagery",
    overlay=False,
    control=False
).add_to(wetland_map_right)

# this should leave us so that the initial zoom is the outline of california
wetland_map_right.fit_bounds([
    [miny, minx],  # Southwest corner
    [maxy, maxx]   # Northeast corner
])

# add CA outline
folium.GeoJson(
    ca_outline.to_json(),
    style_function=lambda x: {
        "color": "black",
        "fillOpacity": 0,
        "weight": 2
    },
    control= False # always on
).add_to(wetland_map_right)

# Marine layer
folium.GeoJson(
    marine.to_json(),
    name="Marine System Wetlands",
    style_function=lambda x: {
        "color": system_colors["Marine"],
        "fillColor": system_colors["Marine"],
        "fillOpacity": 0.9,
        "weight": 0.5
    },
    control=True #can be toggled
).add_to(wetland_map_right)

# Estuarine layer
folium.GeoJson(
    estuarine.to_json(),
    name="Estuarine System Wetlands",
    style_function=lambda x: {
        "color": system_colors["Estuarine"],
        "fillColor": system_colors["Estuarine"],
        "fillOpacity": 0.9,
        "weight": 0.5
    },
    control=True #can be toggled
).add_to(wetland_map_right)

# Lacustrine layer
folium.GeoJson(
    lacustrine.to_json(),
    name="Lacustrine System Wetlands",
    style_function=lambda x: {
        "color": system_colors["Lacustrine"],
        "fillColor": system_colors["Lacustrine"],
        "fillOpacity": 0.9,
        "weight": 0.5
    },
    control=True #can be toggled
).add_to(wetland_map_right)

# Add layer control
folium.LayerControl(collapsed=False).add_to(wetland_map_right)

# -----------------------------------------------------------------------
# save maps just in case - this worked
#   fire_map_left.save("fire_map.html")
#   wetland_map_right.save("wetland_map.html")
# -----------------------------------------------------------------------
# --------------------------dashboard-legend-----------------------------

def make_legend(colors):

    items = []

    for label, color in colors.items():
        items.append(
            ui.div(
                ui.span(
                    style=f"""
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    background-color: {color};
                    margin-right: 5px;
                    """,
                ),
                ui.span(label),
                style="display: flex; align-items: center; gap: 3px;"
            )
        )

    return ui.div(
        *items,
        style="""
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        padding: 10px;
        """
    )




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
    ui.h1("California Wildfire & Wetlands Dashboard"),
    # describe the goals of the project
    ui.p("Central Question: What role do wetlands play in wildfire movement across California?"
    ),
    ui.p("Intended Audience: Wildfire or wetland researchers with some prior subject knowledge."
        ),
    ui.p("Limitations"),
    ui.tags.ul( # add some bullet points for systems
            ui.tags.li("Restricted to fires with available spatial data in the form of a vector perimeter."),
            ui.tags.li("Wetlands data subset to include only wetlands greater than 10 hectares in area"),
    ),

    
        ui.layout_columns(
    
            # WILDFIRE CONTAINER
            ui.card(
                ui.card_header("California Wildfires (2020–2025)"),
    
                make_legend(fire_colors),
    
                ui.HTML(fire_map_left._repr_html_()),
    
            ),
    
            # WETLAND CONTAINER
            ui.card(
                ui.card_header("California Wetlands"),
    
                make_legend(system_colors),
    
                ui.HTML(wetland_map_right._repr_html_()),
    

            ),
    
            col_widths=[6, 6]
        ),
    
    
    
    ui.hr(),

    #---------------------------------------------------

    # BACKGROUND INFO
    
    # Wildfire Data
    ui.h3("Wildfire Data"),
    ui.p("Wildfire shapefile data comes from the California Historical Fire Perimeters dataset, maintained by CalFire, "
    "and reporting fires greater than or equal to 10 acres inside the state between 1910 and 2025. For " \
    "this project, data has been subset to years between 2020 and 2025. Use the plot below to explore " \
    "fires in California from 2020 to 2025 by cause and by size."), 

    ui.p("Overall, the findings suggest that wildfire ignition causes are associated with " \
    "different seasonal patterns and fire-size distributions. Lightning is particularly notable "
    "for its association with large burned areas, while several human-related causes are more frequently " \
    "associated with smaller fires. These observations highlight the importance of considering both ignition " \
    "frequency and burned area when evaluating wildfire risk, rather than relying on fire occurrence alone."),


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
ui.div(

    # put plot in a container so that it does not get stretched out
    ui.output_plot("fire_cause_plot"),
    style="max-width: 850px; margin: 30px auto 30px auto;"
),
    
    ui.hr(),

    # Wetlands data
    ui.h3("Wetlands Data"),
    ui.p("Wetlands shapefile data comes from the National Wetland Inventory, downloaded for the state of California. This dataset" \
    " divides wetlands into Cowardin (1979) wetlands classifications of 5 systems, and additional subsystems, " \
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
    ui.h1("Analysis"),

    ui.p("To address our central question “What role do wetlands play in wildfire movement across the landscape?”, "
    "we have chosen to use spatial analysis. This fits our data, because both the wetlands data from the National Wetlands Inventory and "
    "the CalFires Fire Perimeters datasets have associated footprints. Spatial analysis also fits well with our central question, "
    "because we want to know where and how much overlap there is between wildfires and wetlands. We began our analysis with a simple "
    "examination of both sets of data (NWI wetlands and CalFire Fire Perimeters), learning about the spatial and temporal distribution of the data. "
    "We then used the package Geopandas to perform a nearest neighbor spatial join to determine the distance between each wetland observation "
    "and the nearest fire observation. Next, we performed a spatial join between our datasets to obtain the area of wetlands burned in 2025 and "
    "determined that there were 1,134 wetlands that experienced a fire in 2025. This join was validated using nearest neighbor data - "
    "the number of wetlands with a distance of 0 to the nearest fire matched the number of intersecting records following the spatial join. "
    "To include a robustness comparison, we include not only the amount of area burned as hectares, but also as a percentage of total wetland area and total fire area."),

    # DISTANCE TO NEAREST FIRE WIDGET
    ui.h3("Distance to Nearest Fire"),

    ui.p("The distribution of distance from each wetland to the nearest fire is heavily skewed " \
    "to the right, with the most wetlands having a fire between 0km and 20km away from their perimeter " \
    "during each year from 2020 to 2025."),
    ui.input_select(
        "year",
        "Select Year:",
        choices=[str(y) for y in year_list],
        selected=str(year_list[0])
    ),
    ui.div(

    # put plot in a container so that it does not get stretched out
    ui.output_plot("fire_plot"),
    style="max-width: 850px; margin: 30px auto 30px auto;"
    ),

    ui.hr(),

    #---------------------------------------------------
    
    # PCT BURNED AREA WIDGET
    ui.h3("Percent of Wetland Area Burned by Wetland Type"),
    ui.p("By comparing the percent of wetland area burned inside each system through the years," \
    " we can not only see which wetland systems have the most burned area, but also which years had" \
    " fires with great impact on wetlands. Overall, the percent of wetlands burned compared to total wetland" \
    " area remains low, indicating that a majority of wetlands in California did not experience a wildfire " \
    "in the last 5 years. Palustrine and Riverine wetlands had much larger percentages of area burned " \
    "compared to the other three systems."),

    ui.input_select(
        "system",
        "Select Wetland System:",
        choices=system_list,
        selected=system_list[0]
    ),
    ui.div(

    # put plot in a container so that it does not get stretched out
    ui.output_plot("fireint_plot"),
    style="max-width: 850px; margin: 30px auto 30px auto;"
),

#---------------------------------------------------
    # SUMMARY CHART 
    ui.h3("Summary Statistics"),

    ui.input_select(
        "summary_year",
        "Select Year:",
        choices={
            str(year): str(year)
            for year in range(2020, 2026)
        },
        selected="2020"
    ),

    ui.output_table("summary_table_output"),





#---------------------------------------------------


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

