# Wildfire Wetland_BunkerAndersonTseng
Group Project - Wildfire &amp; Wetland
Group project about wildfire & wetland

- Team Name: Wildfire and Wetland Interactions in California (Team 8)
- Team Members: Kat Anderson, Mason Bunker, Sophia Tseng
- Intended Audience: Wildfire and wetland researchers

## Research Question: What role do wetlands plan in wildfire movement across the landscape? 
### Optional Research Questions: 
1. Do fires cross wetland boundaries?
2. Are wildfires less frequent near wetlands? 
3. Has wetland loss occured due to wildfires? 

## Data 
### Data Dictionary
#### Wetland Dataset
Unit of observation: Each row represents one wetland observation

| Variable Name | Unit of Measurement | Source Definition |
|---|---|---|
| C Code | N/A | Alphanumeric code identifying the wetland classification of the polygon | 
| NWI Type | N/A | General description of the wetland based on the Cowardin wetland classification | 
| Hectares | N/A | Polygons larger than 1 hectare | 
| NWI ID | N/A | NWI Unique ID| 
|geometry|||
|C System|N/A| Cowardin System Definition. Has 5 types: marine, estuarine, riverine lacustrine, and palustrine|
|C Subsystem |N/A| Cowardin Subsystem Definition. |
|C Class |N/A| Cowardin class determined by aerial imagery of the wetland. |
	

#### Fire SHP Dataset
Unit of observation: Each row represents one fire incident

| Variable Name | Unit of Measurement | Source Definition |
|---|---|---|
| YEAR_ | Int64 | Year in which the fire started |
| STATE | Text | State in which the fire started |
| AGENCY | Text | Direct protection agency responsible for fire |
| UNIT_ID | Text | ICS code for unit |
| FIRE_NAME | Text | Name of the fire, UPPER CASE, without “fire” or “incident" following name |
| INC_NUM | Text | Number assigned by the Emergency Command Center of the responsible agency for the fire |
| IRWINID | Text | IRWIN stands for Integrated Reporting of Wildland Fire Information, a global unique identifier assigned at the onset of an incident. |
| ALARM_DATE | DateTime | DD/MM/YYYY format, date of fire discovery |
| CONT_DATE | DateTime | DD/MM/YYYY format Containment date for the fire |
| C_METHOD | Int| Method used to collect perimeter data |
| CAUSE | Int | Reason fire ignited |
| OBJECTIVE | N/A | Tactic for fire response |
| GIS_ACRES | Float | GIS calculated area, in acres |
| COMPLEX_ID | Text | If part of complex, the complex incident number |
| COMPLEX_NAME | Text | If part of complex, the complex name |
| COMMENTS | Text | Miscellaneous comments |
| FIRE_NUM | Text | Former numbering system preceding incident numbers |
| Shape_Length |||
| Shape_Area |||
| GlobalID | Text |Unique ID|
| geometry |||


#### Fire CSV Dataset
Unit of observation: Each row represents one fire incident

| Variable Name | Unit of Measurement | Source Definition |
|---|---|---|
OBJECTID | Text | Random object id |
Year | Int64 | Year in which the fire started |
State | Text | State in which the fire started |
Agency | Text | Direct protection agency responsible for fire |
Unit ID | Text | ICS code for unit | 
Fire Name | Text | Name of the fire, UPPER CASE, without "fire" or "incident" following name |
Local Incident Number | Text | Number assigned by the Emergency Command Center of the responsible agency for the fire | 
IRWIN ID | Text | IRWIN stands for Integrated Reporting of Wildland Fire Information, a global unique identifier assigned at the onset of an incident. |
Alarm Date | DateTime | DD/MM/YYYY format, date of fire discovery |
Containment Date | DateTime | DD/MM/YYYY format Containment date for the fire |
Cause | Int | Reason fire ignited |
Collection Method | Int | Method used to collect perimeter data |
Management Objective
GIS Calculated Acres | Float | GIS calculated area, in acres |
Comments | Text | Miscellaneous comments |
Complex Name | Text | If part of complex, the complex name |
Complex ID | Text | If part of complex, the complex number |
Fire Number (historical use) | Text | Former numbering system preceding incident numbers |
GlobalID | Text | Unique ID |
Decade | Int64 | Decade in which fire started
Shape__Area | Float | Area inside fire perimeter, acres
Shape__Length | Float | Area of fire perimeter, ft


Minimum mapping requirements for CalFire: 
1. Wildland timber fires greater than 10 acres.
2. Wildland brush fires greater than 50 acres.
3. Wildland grass fires greater than 300 acres.
4. Wildland fires destroying three or more residential or commercial structures.
5. Wildland fires resulting in a fatality.
Minimum mapping requirements for State Parks:
1. All prescribed fires
Minimum Mapping requirements for BLM, NPS, & USFW:
1. Wildland fires 10 acres or greater
2. All prescribed fires

### Sources
1. California Department of Forestry and Fire Protection
2. California wetlands from the National Wetlands Inventory

## Methods
### Import Data
To work with large datasets, we use **Box Drive** to store and access data rather than uploading large files directly to GitHub.
#### 1. Set Up Box Drive
- Download and install [Box Drive](https://www.box.com/resources/downloads).
- Log in using your Duke account.
- Make sure Box Drive is running and your project data is accessible.

#### 2. Organize Project Data
- Store large datasets in the appropriate folder within the class Box Drive.
- Keep project data organized in folders.
- Do not upload large datasets to GitHub. GitHub should contain our code, documentation, and other project files.

#### 3. Access Data in Python (VS Code)

```python
import platform
from pathlib import Path
import pandas as pd

# Set the main Box folder path
if platform.system() == "Windows":
    box_path = Path.home() / "Box"
else:
    box_path = (
        Path.home()
        / "Library"
        / "CloudStorage"
        / "Box-Box"
    )

# Verify that the Box folder exists
if box_path.exists():
    print(f"Box folder found at {box_path}")
else:
    print("Box folder not found. Check that Box Drive is running and you are logged in.")

# Specify the path to a dataset
data_path = (
    box_path
    / "ENVIRON 712L-Students"
    / "Data"
    / "YOUR_PROJECT_FOLDER"
    / "your_dataset.csv"
)

# Load the dataset
df = pd.read_csv(data_path)

# Preview the data
df.head()
```

Replace `YOUR_PROJECT_FOLDER` and `your_dataset.csv` with the appropriate folder and file names

### Data cleaning 
### Statistical analysis 
### Mapping

