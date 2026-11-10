# TO RUN: 
# conda activate env700-shiny
# shiny run --reload scripts/A4/dashboard_layout.py 

# if mason and struggling, run below
# shiny run --reload dashboard_layout.py

# be a little patient with it starting, need to see this line in terminal output
#       INFO:     Application startup complete.

# import packages
import folium
from pathlib import Path
import pandas as pd
import geopandas as gpd