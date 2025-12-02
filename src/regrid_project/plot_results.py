import os
import glob
import re
from multiprocessing import Pool
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import rioxarray as rxr
import xarray as xr
from src.regrid_project import config
from src.regrid_project import ecostress_handler as eco_h
from src.regrid_project import mapbiomas_handler as mb_h

# Style configuration
plt.style.use('seaborn-v0_8-whitegrid')

def extract_year(filename):
    match = re.search(r"doy(\d{4})", filename)
    if match:
        return int(match.group(1))
    return 2018 # Fallback

def generate_plot(site_name, var_name, filepath, buffer_path, output_folder):
    """
    Generate 4-panel plot for detailed validation.
    """
    filename = os.path.basename(filepath)
    print(f"   -> Generating plot for: {filename} ...")
    
    year = extract_year(filename)
    
    # 1. Load Buffer
    gdf_buffer = gpd.read_file(buffer_path)
    if len(gdf_buffer) > 1: gdf_buffer = gdf_buffer.iloc[[0]]

    # 2. Load and Mask Data
    try:
        da_raw = eco_h.load_ecostress(filepath, gdf_buffer)
        if da_raw is None: return
        
        mask = mb_h.create_forest_mask(da_raw, year, gdf_buffer)
        if mask is None: return
        da_masked = da_raw.where(mask)
        
        # 3. Generate Template
        template_da = eco_h.create_centered_template(gdf_buffer)
        target_crs = template_da.rio.crs
        
        # --- MANUAL MATHEMATICAL CALCULATION (To display in plots 3 and 4) ---
        
        # A. Prepare Numerator (Sum) and Denominator (Count)
        data_filled = da_masked.fillna(0.0)
        data_filled.rio.write_nodata(None, inplace=True)
        
        valid_weights = da_masked.notnull().astype(np.float32)
        valid_weights.rio.write_nodata(None, inplace=True)
        
        # B. Reproject using SUM
        sum_grid = data_filled.rio.reproject_match(template_da, resampling=eco_h.Resampling.sum, nodata=np.nan)
        count_grid = valid_weights.rio.reproject_match(template_da, resampling=eco_h.Resampling.sum, nodata=np.nan)
        
        # C. Calculate Maximum Possible for Fraction
        # --- CORRECTION HERE: Use xr.ones_like instead of rxr.ones_like ---
        dummy_full = xr.ones_like(da_masked).astype(np.float32) 
        dummy_full.rio.write_nodata(None, inplace=True)
        max_count_grid = dummy_full.rio.reproject_match(template_da, resampling=eco_h.Resampling.sum, nodata=np.nan)
        
        # D. Results
        mean_grid = sum_grid / count_grid.where(count_grid > 0) # Pure Mean
        fraction_grid = count_grid / max_count_grid # Coverage Percentage

        # E. Apply Thresholds for visualization
        THRESHOLD_TEST = 0.50 # 1%
        da_final_thresh = mean_grid.where(fraction_grid >= THRESHOLD_TEST)
        
        # Clippings for plotting
        buffer_utm = gdf_buffer.to_crs(target_crs)
        mean_grid = mean_grid.rio.clip(buffer_utm.geometry)
        da_final_thresh = da_final_thresh.rio.clip(buffer_utm.geometry)
        fraction_grid = fraction_grid.rio.clip(buffer_utm.geometry)

    except Exception as e:
        print(f"      [ERROR] Failed to process {filename}: {e}")
        return

    # ================= PLOTTING =================
    fig, axes = plt.subplots(1, 4, figsize=(30, 10), constrained_layout=True)
    
    # --- PLOT 1: ORIGINAL ---
    ax1 = axes[0]
    da_masked.rio.reproject(target_crs).plot(
        ax=ax1, cmap='viridis', add_colorbar=True, 
        cbar_kwargs={'label': var_name, 'shrink': 0.6}
    )
    buffer_utm.boundary.plot(ax=ax1, color='white', linewidth=1, linestyle='--')
    ax1.set_title(f"1. Original ({site_name})", fontsize=14)
    ax1.set_aspect('equal')

    # --- PLOT 2: GEOMETRY ---
    ax2 = axes[1]
    # Points
    da_for_scatter = da_masked.rio.reproject(target_crs, resampling=eco_h.Resampling.nearest)
    values = da_for_scatter.values.flatten()
    xs, ys = np.meshgrid(da_for_scatter.x.values, da_for_scatter.y.values)
    valid = ~np.isnan(values)
    ax2.scatter(xs.flatten()[valid], ys.flatten()[valid], c='dimgray', s=2, marker='s')
    
    # Buffer/Center
    buffer_utm.boundary.plot(ax=ax2, color='black', linewidth=2)
    c = buffer_utm.geometry.centroid.iloc[0]
    ax2.scatter(c.x, c.y, c='black', s=150, marker='o')
    ax2.scatter(c.x, c.y, c='cyan', s=50, marker='+')

    # Grid
    x_g, y_g = mean_grid.x.values, mean_grid.y.values
    for x in x_g: ax2.axvline(x - config.TARGET_RES_X/2, color='red', lw=1, alpha=0.6)
    for y in y_g: ax2.axhline(y - config.TARGET_RES_Y/2, color='red', lw=1, alpha=0.6)
    

    ax2.set_title("2. Geometry (pixel 2.20x1.66km)", fontsize=14)
    ax2.set_aspect('equal')
    ax2.set_ylim(y_g.min() - config.TARGET_RES_Y, y_g.max() + config.TARGET_RES_Y)
    ax2.set_xlim(x_g.min() - config.TARGET_RES_X, x_g.max() + config.TARGET_RES_X)

    # --- PLOT 3: COVERAGE FRACTION (DIAGNOSIS) ---
    ax3 = axes[2]
    fraction_grid.plot(
        ax=ax3, cmap='jet_r', add_colorbar=True, vmin=0, vmax=1,
        cbar_kwargs={'label': 'Fraction (0–1)', 'shrink': 0.6}
    )
    buffer_utm.boundary.plot(ax=ax3, color='black')
    ax3.set_title(f"3. Coverage Fraction\n(Cells where fraction > {THRESHOLD_TEST})", fontsize=14)
    ax3.set_aspect('equal')
    ax3.set_ylim(y_g.min() - config.TARGET_RES_Y, y_g.max() + config.TARGET_RES_Y)
    ax3.set_xlim(x_g.min() - config.TARGET_RES_X, x_g.max() + config.TARGET_RES_X)

    # --- PLOT 4: FINAL RESULT (THRESHOLD 1%) ---
    ax4 = axes[3]
    da_final_thresh.plot(
        ax=ax4, cmap='viridis', add_colorbar=True, 
        cbar_kwargs={'label': f'Mean {var_name}', 'shrink': 0.6}
    )
    buffer_utm.boundary.plot(ax=ax4, color='black')
    ax4.set_title(
    f"4. Final Result (> {THRESHOLD_TEST*100}%)\n(Mean)", fontsize=14)
    ax4.set_aspect('equal')
    ax4.set_ylim(y_g.min() - config.TARGET_RES_Y, y_g.max() + config.TARGET_RES_Y)
    ax4.set_xlim(x_g.min() - config.TARGET_RES_X, x_g.max() + config.TARGET_RES_X)

    # Save
    out_name = f"Validation_{site_name}_{var_name}.png"
    out_path = os.path.join(output_folder, out_name)
    plt.savefig(out_path, dpi=150)
    plt.close()
    return f"[OK] Saved: {out_path}"

def process_plot_task(args):
    """Process a single plot generation task"""
    site_name, var_name, filepath, buffer_path, output_folder = args
    try:
        result = generate_plot(site_name, var_name, filepath, buffer_path, output_folder)
        return result if result else f"[ERROR] Failed to generate plot for {site_name} - {var_name}"
    except Exception as e:
        return f"[ERROR] {site_name} - {var_name}: {str(e)}"

def main():
    print("=== GENERATING VALIDATION PLOTS (4-PANEL METHOD - SUM) ===")
    plot_dir = os.path.join(config.BASE_PATH, "Validation_plots")
    os.makedirs(plot_dir, exist_ok=True)
    
    # Get number of CPU cores available
    num_workers = max(1, os.cpu_count() - 1) if os.cpu_count() else 2
    print(f"Using {num_workers} CPU cores for parallel plot generation")
    
    # Collect all plot tasks
    plot_tasks = []
    
    for site_name, buffer_path in config.SITES.items():
        print(f"\n--- Collecting tasks for Site: {site_name} ---")
        if not os.path.exists(buffer_path):
            continue

        for var_name in config.VARIABLES:
            folder_name = f"{var_name}_{site_name}_ECOSTRESS"
            input_dir = os.path.join(config.BASE_PATH, "Rasters_buffers_data", folder_name)
            if not os.path.exists(input_dir):
                continue
            
            files = glob.glob(os.path.join(input_dir, "*.tif"))
            if not files:
                continue
            
            # Add first file from each site/variable combination
            plot_tasks.append((site_name, var_name, files[0], buffer_path, plot_dir))
    
    print(f"\nTotal plot tasks: {len(plot_tasks)}")
    
    if plot_tasks:
        print(f"Starting parallel plot generation...")
        with Pool(processes=num_workers) as pool:
            results = pool.map(process_plot_task, plot_tasks)
        
        # Display results
        for result in results:
            print(f"   {result}")

if __name__ == "__main__":
    main()