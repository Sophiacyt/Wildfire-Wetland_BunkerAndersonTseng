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

## Data Sources
1. fire
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

Replace `YOUR_PROJECT_FOLDER` and `your_dataset.csv` with the appropriate folder and file names for your project.

### Data cleaning 
### Statistical analysis 
### Mapping

