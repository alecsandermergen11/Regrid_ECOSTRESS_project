import os
import glob
import re
from multiprocessing import Pool, Manager
import geopandas as gpd
from src.regrid_project import config
from src.regrid_project import mapbiomas_handler as mb_h
from src.regrid_project import ecostress_handler as eco_h
def extract_year(filename):
    """Extract year from filename pattern 'doy2018...'"""
    match = re.search(r"doy(\d{4})", filename)
    if match:
        return int(match.group(1))
    return None

def process_single_file(args=None):
    """Dual-mode function:
    - If called with no arguments, act as the orchestrator that discovers sites/variables
      and dispatches worker tasks to the process pool.
    - If called with a single `args` tuple (filepath, output_dir, gdf_buffer), process
      that single file and return the output path or an error message.
    """
    # Worker mode: process a single file (used by Pool.map)
    if args is not None:
        try:
            filepath, output_dir, gdf_buffer = args
        except Exception as e:
            return f"[ERROR] Invalid args for worker: {e}"

        filename = os.path.basename(filepath)
        out_path = os.path.join(output_dir, f"Regrid_{filename}")

        # Skip if already processed
        if os.path.exists(out_path):
            return f"[SKIP] {filename} (already exists)"

        year = extract_year(filename)
        if not year:
            return f"[SKIP] {filename} (year not identified)"

        eco_da = eco_h.load_ecostress(filepath, gdf_buffer)
        if eco_da is None:
            return f"[ERROR] {filename} (failed to load ECOSTRESS)"

        mask = mb_h.create_forest_mask(eco_da, year, gdf_buffer)
        if mask is None:
            return f"[ERROR] {filename} (failed to create mask)"

        result_da = eco_h.apply_mask_and_regrid_centered(eco_da, mask, gdf_buffer)
        if result_da is None:
            return f"[ERROR] {filename} (regrid failed)"

        try:
            result_da.rio.to_raster(out_path)
            return f"[OK] {filename} -> {out_path}"
        except Exception as e:
            return f"[ERROR] {filename} (saving failed: {e})"

    # Orchestrator mode: no args provided
    print("=== STARTING BATCH PROCESSING (MULTI-SITES / MULTI-VARS) ===")

    # Get number of CPU cores available
    num_workers = os.cpu_count() or 4
    print(f"Using {num_workers} CPU cores for parallel processing")

    # 1. Loop through SITES
    for site_name, buffer_path in config.SITES.items():
        print(f"\n##################################################")
        print(f"### SITE: {site_name}")
        print(f"##################################################")

        # Load Site Buffer
        if not os.path.exists(buffer_path):
            print(f"[ERROR] Shapefile not found: {buffer_path}")
            continue

        print(f"Loading Buffer: {os.path.basename(buffer_path)}")
        gdf_buffer = gpd.read_file(buffer_path)

        # Ensure only 1 geometry (first) to avoid list problems
        if len(gdf_buffer) > 1:
            gdf_buffer = gdf_buffer.iloc[[0]]

        # 2. Loop through VARIABLES
        for var_name in config.VARIABLES:
            print(f"\n   >>> Processing Variable: {var_name}")

            # -----------------------------------------------------------
            # INTELLIGENT PATH CONSTRUCTION
            # Guesses folder name: e.g., "SM_ATTO_ECOSTRESS"
            # If folder structure is different, adjust this line:
            folder_name = f"{var_name}_{site_name}_ECOSTRESS"
            input_dir = os.path.join(config.BASE_PATH, "Rasters_buffers_data", folder_name)
            # -----------------------------------------------------------

            if not os.path.exists(input_dir):
                print(f"   [WARNING] Data folder not found: {input_dir}")
                continue

            # Create output folder: Output/ATTO/SM
            output_dir = os.path.join(config.OUTPUT_ROOT, site_name, var_name)
            os.makedirs(output_dir, exist_ok=True)

            # List Files
            eco_files = glob.glob(os.path.join(input_dir, "*.tif"))
            print(f"   Files found: {len(eco_files)}")

            if len(eco_files) == 0:
                continue

            # 3. Prepare arguments for parallel processing
            # Create list of tuples (filepath, output_dir, gdf_buffer) for each file
            task_args = [(filepath, output_dir, gdf_buffer) for filepath in eco_files]

            # 4. Process files in parallel
            print(f"   Starting parallel processing with {num_workers} workers...")
            with Pool(processes=num_workers) as pool:
                results = pool.map(process_single_file, task_args)

            # 5. Display results
            for result in results:
                print(f"      {result}")

    print("\n=== PROCESSING COMPLETED SUCCESSFULLY ===")
    print("\n=== To extract time series, run the extraction code: extract_to_csv.py ===")

if __name__ == "__main__":
    process_single_file()