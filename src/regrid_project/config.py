import os

# === BASE PATHS ===
BASE_PATH = r"D:\Alecsander\Data_Leonardo_30KM\Regrid_project"
PATH_MAPBIOMAS_DIR = os.path.join(BASE_PATH, "Coverage_mapbiomas")
# Optional: directory to store MapBiomas files already cropped per buffer/site
PATH_MAPBIOMAS_CUT = os.path.join(BASE_PATH, "Coverage_mapbiomas_cut")

# === SITE CONFIGURATION (BUFFERS) ===
# Dictionary: "SITE_NAME": "SHAPEFILE_PATH"
SITES = {
    "ATTO": os.path.join(BASE_PATH, r"Buffers\ATTO_buffer_30km\buffer_30km_ATTO.shp"),
    "K34":  os.path.join(BASE_PATH, r"Buffers\K34_buffer_30km\buffer_30km_K34.shp"),
    "K67":  os.path.join(BASE_PATH, r"Buffers\K67_buffer_30km\buffer_30km_K67.shp")
}

# === VARIABLE CONFIGURATION ===
# List with variable prefixes.
# The script will look for folders with pattern: {VAR}_{SITE}_ECOSTRESS
VARIABLES = ["LST", "NDVI", "Rg", "SM"]

# === OUTPUT CONFIGURATION ===
# Output root folder. Within it, we'll create subfolders by site/variable
OUTPUT_ROOT = os.path.join(BASE_PATH, "Output_Regrid_OCO3_Multi")

# === OCO-3 PIXEL CONFIGURATION (VIRTUAL) ===
# X (Width/Longitude) = 2.20km | Y (Height/Latitude) = 1.66km
TARGET_RES_X = 2200.0 
TARGET_RES_Y = 1660.0

# === FOREST FILTER (MAPBIOMAS) ===
FOREST_CLASSES = [3, 4, 5, 6]

# Create root folder if it doesn't exist
os.makedirs(OUTPUT_ROOT, exist_ok=True)
# Ensure mapbiomas cut folder exists
os.makedirs(PATH_MAPBIOMAS_CUT, exist_ok=True)
