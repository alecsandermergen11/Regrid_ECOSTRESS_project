# Regrid Project - OCO-3 Multi-Site Processing

Remote sensing data processing and regridding project (ECOSTRESS and MapBiomas) for three research sites in the Amazon (ATTO, K34 and K67).

## 📋 Description

This project performs integrated processing of data from:
- **ECOSTRESS**: Land Surface Temperature (LST), vegetation index (NDVI), global radiation (Rg) and soil moisture (SM) data
- **MapBiomas**: Forest cover mask for data filtering
- **OCO-3**: Regridding to virtual pixel resolution of 2.20 km (X) × 1.66 km (Y)

The data is processed for three research sites with 30 km buffers:
- **ATTO**: Research tower in Amazonas State
- **K34**: Research site at Km 34
- **K67**: Research site at Km 67

## 🗂️ Project Structure

```
├── src/                          # Shapefiles of 30 km buffers
│   └── Regrid_project/
│         ├── config.py                     # Centralized configuration of paths and parameters
│         ├── main.py                       # Main processing/regridding script
│         ├── ecostress_handler.py          # ECOSTRESS loading and processing functions
│         ├── mapbiomas_handler.py          # Forest mask creation functions
│         ├── extract_to_csv.py             # Time series extraction to CSV
│         └── plot_results.py               # Validation visualization generation
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── Buffers/                      # Shapefiles of 30 km buffers
│   ├── ATTO_buffer_30km/
│   ├── K34_buffer_30km/
│   └── K67_buffer_30km/
├── Coverage_mapbiomas_cut/       # Forest cover data MapBiomas (by year)
├── Rasters_buffers_data/         # Raw input data (ECOSTRESS TIFs)
│   ├── LST_ATTO_ECOSTRESS/
│   ├── NDVI_K34_ECOSTRESS/
│   └── ... (more site/variable combinations)
├── Output_Regrid_OCO3_Multi/     # Processed data (output)
│   ├── ATTO/
│   │   ├── LST/
│   │   ├── NDVI/
│   │   ├── Rg/
│   │   └── SM/
│   ├── K34/
│   └── K67/
├── Tables_CSVs/                 # Time series in CSV format
│   ├── ATTO_LST.csv
│   ├── ATTO_NDVI.csv
│   ├── ... (more site/variable combinations)
└── Validation_plots/            # Validation plots (4 panels)
```

## 🚀 How to Use

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note**: This project was developed and tested with Python 3.8+. It is recommended to use a virtual environment.

### 2. Configuration

Edit the `config.py` file to adjust:
- `BASE_PATH`: Base path of the project
- `SITES`: Dictionary with site names and shapefile paths for buffers
- `VARIABLES`: List of variables to process (LST, NDVI, Rg, SM)
- `OUTPUT_ROOT`: Output folder for processed data
- `TARGET_RES_X` / `TARGET_RES_Y`: OCO-3 pixel resolution in meters

### 3. Processing Workflow

**⚡ Performance Note**: This project uses **multiprocessing** for parallel execution. It automatically detects your CPU cores and uses them efficiently. See `MULTIPROCESSING_GUIDE.md` for details on configuring workers.

**Step 1: Main Processing (Regridding)**
There are two equivalent ways to run the project after the recent refactor that places library code under `src/regrid_project`:

- Recommended (no PYTHONPATH tweaks required):
```powershell
python run_main.py
```

- Alternatively (explicit package import):
```powershell
python -c "import sys; sys.path.insert(0, r'd:/Alecsander/Data_Leonardo_30KM/Regrid_project/src'); import regrid_project.main; regrid_project.main.process_single_file()"
```

This script:
- Reads raw ECOSTRESS data from the `Rasters_buffers_data/` directory
- Applies MapBiomas forest mask
- Performs regridding to OCO-3 resolution (2.20 × 1.66 km)
- Saves results to `Output_Regrid_OCO3_Multi/`
- **✨ Uses parallel processing**: Files are processed simultaneously across all available CPU cores

**Step 2: Time Series Extraction (CSV)**
Recommended wrapper (keeps `src/` on `sys.path` automatically):
```powershell
python run_extract.py
```

Or directly via package import:
```powershell
python -c "import sys; sys.path.insert(0, r'd:/Alecsander/Data_Leonardo_30KM/Regrid_project/src'); import regrid_project.extract_to_csv as et; et.main()"
```

This script:
- Reads processed data
- Extracts pixel-by-pixel values
- Converts UTM coordinates to Lat/Lon
- Saves in CSV format to `Tabelas_CSVs/`
- **✨ Uses parallel processing**: Raster files are extracted simultaneously

**Step 3: Visualization of Results**
Recommended wrapper:
```powershell
python run_plots.py
```

Or via package import:
```powershell
python -c "import sys; sys.path.insert(0, r'd:/Alecsander/Data_Leonardo_30KM/Regrid_project/src'); import regrid_project.plot_results as pr; pr.main()"
```

## Pre-cut MapBiomas (optional, recommended)

To avoid repeatedly cropping large MapBiomas rasters on every run, first prepare per-buffer pre-cut files. This saves time on subsequent pipeline runs.

Run the utility once:
```powershell
python prepare_mapbiomas_masks.py
```

This will create files under `Coverage_mapbiomas_cut/<SITE>/` such as `2024_coverage_ATTO.tif`. The pipeline will automatically use pre-cut files if available.

This script:
- Generates 4-panel validation plots for each ECOSTRESS file:
  - **Panel 1**: Original data
  - **Panel 2**: Pixel geometry and grid
## ⚡ Performance Optimization

This project uses **multiprocessing** to significantly speed up data processing:

- **Automatic CPU detection**: Automatically uses all available CPU cores
- **Parallel file processing**: Multiple files processed simultaneously
- **Expected speedup**: 3-8x faster on multi-core machines (depends on CPU cores)

### Parallel Processing Details

| Script | Parallelization | Speedup |
|--------|-----------------|---------|
| `main.py` | File processing within each Site/Variable | 3-8x |
| `extract_to_csv.py` | Raster data extraction | 3-8x |
| `plot_results.py` | Plot generation | 2-7x |

For detailed configuration options, see `MULTIPROCESSING_GUIDE.md`

## 🔬 Methods**: Coverage fraction (diagnosis)
  - **Panel 4**: Final result (mean with threshold)
- Saves to `Plots_Validacao_Final/`
- **✨ Uses parallel processing**: Plots are generated simultaneously

## 🔬 Methods

### Regridding: SUM / COUNT Method

To ensure robustness in calculating the mean on large-scale pixels with many missing data (NaN):

1. **Numerator (Sum)**: Sum of all valid values within the large pixel
2. **Denominator (Count)**: Number of valid small (70m) pixels
3. **Mean**: Sum / Count
4. **Coverage Fraction**: Real Count / Maximum Possible Count
5. **Final Filter**: Keeps only pixels with coverage ≥ 50%

This method avoids NaN propagation problems and provides more reliable calculations.

### Forest Mask

Data is filtered using MapBiomas forest classes:
- Class 3: Planted Forest
- Class 4: Natural Forest
- Class 5: Atlantic Forest
- Class 6: Transition Forest

With automatic fallback to the previous year if the requested year is not available.

## 📊 Output Format - CSVs

Generated CSVs contain the following columns:

| Column | Description |
|--------|-----------|
| `date` | Date calculated from year and DOY |
| `year` | Acquisition year |
| `doy` | Day of year (1-366) |
| `latitude` | Coordinate in Lat/Lon |
| `longitude` | Coordinate in Lat/Lon |
| `LST` / `NDVI` / `Rg` / `SM` | Variable value |
| `pixel_id` | Unique pixel ID (X_Y in UTM) |
| `x` | X coordinate (UTM 21S) |
| `y` | Y coordinate (UTM 21S) |

## 📁 Expected Input Data

### Raw Data Structure
```
Rasters_buffers_data/
├── LST_ATTO_ECOSTRESS/
│   ├── doy2018***.tif
│   └── ...
├── NDVI_K34_ECOSTRESS/
│   └── ...
└── ... (more combinations)
```

### MapBiomas
```
Coverage_mapbiomas/
├── 2018_coverage_*.tif
├── 2019_coverage_*.tif
├── 2020_coverage_*.tif
└── ...
```
## 📝 Important Notes

1. **Memory**: Processing uses multiprocessing which creates multiple processes
   - Memory usage scales with number of workers
   - Reduce workers if you have limited RAM
   - See `MULTIPROCESSING_GUIDE.md` for configuration

2. **Year Fallback**: If the requested year doesn't exist in MapBiomas, the script automatically uses the previous year

3. **Validation**: Always check the validation plots in `Plots_Validacao_Final/` to ensure regridding quality

4. **Coverage Threshold**: Default 50% - adjust in `config.py` if needed

5. **Parallel Processing**: All scripts automatically detect CPU cores. To customize:
   - Edit the `num_workers` variable in the script
   - See `MULTIPROCESSING_GUIDE.md` for advanced configuration

## 📚 Additional Documentation

- `MULTIPROCESSING_GUIDE.md`: Detailed guide on parallel processing configuration and troubleshooting
- **geopandas**: Geospatial operations
- **rasterio**: Raster data reading/writing
- **matplotlib**: Visualization
- **pandas**: DataFrame manipulation
- **pyproj**: Coordinate transformations

## ⚙️ Projection Used

- **Input**: WGS 84 (EPSG:4326) / Native Raster
- **Processing**: UTM Zone 21 South (EPSG:32721)
- **Output CSV**: Lat/Lon (EPSG:4326)

## 📝 Important Notes

1. **Memory**: Processing uses chunking to optimize memory usage
2. **Year Fallback**: If the requested year doesn't exist in MapBiomas, the script automatically uses the previous year
3. **Validation**: Always check the validation plots in `Plots_Validacao_Final/` to ensure regridding quality
4. **Coverage Threshold**: Default 50% - adjust in `config.py` if needed

## 🔍 Troubleshooting

### Error: "Shapefile not found"
- Check the paths in `config.py`
- Make sure all .shp, .shx, .dbf files are present

### Error: "MapBiomas for year not found"
- Check file existence in `Coverage_mapbiomas/`
- The script will automatically use the previous year as fallback

### Error: "Data folder not found"
- Check the structure in `Rasters_buffers_data/`
- Folder names must follow the pattern: `{VARIABLE}_{SITE}_ECOSTRESS`

## 📧 Authors and Contact

Remote sensing data processing project for Amazon research.

## 📜 License

[Specify your project's license]

---

**Last update**: December 2025
