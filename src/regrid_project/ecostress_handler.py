import numpy as np
import xarray as xr
import rioxarray as rxr
from rasterio.enums import Resampling
from . import config

# Define the standard metric projection for the region (UTM Zone 21 South)
CRS_METRICO = "EPSG:32721"

def create_centered_template(gdf_buffer):
    """
    Create an empty grid (template) in UTM 21S centered on the buffer.
    """
    buffer_utm = gdf_buffer.to_crs(CRS_METRICO)
    center_point = buffer_utm.geometry.centroid.iloc[0]
    cx, cy = center_point.x, center_point.y
    
    radius_m = 35000 
    steps_x = int(np.ceil(radius_m / config.TARGET_RES_X))
    steps_y = int(np.ceil(radius_m / config.TARGET_RES_Y))
    
    x_coords = [cx + i * config.TARGET_RES_X for i in range(-steps_x, steps_x + 1)]
    y_coords = [cy + i * config.TARGET_RES_Y for i in range(-steps_y, steps_y + 1)]
    
    coords = {'y': y_coords, 'x': x_coords}
    
    template = xr.DataArray(
        data=np.full((len(y_coords), len(x_coords)), np.nan),
        coords=coords,
        dims=('y', 'x'),
        name="template_oco3"
    )
    
    template.rio.write_crs(CRS_METRICO, inplace=True)
    template.rio.set_spatial_dims(x_dim="x", y_dim="y", inplace=True)
    
    return template

def load_ecostress(filepath, gdf_buffer):
    da = rxr.open_rasterio(filepath, masked=True).squeeze()
    if da.rio.crs is None:
        try:
            da.rio.write_crs(CRS_METRICO, inplace=True)
        except: pass 
        
    try:
        raster_crs = da.rio.crs if da.rio.crs else CRS_METRICO
        buffer_proj = gdf_buffer.to_crs(raster_crs)
        da_clipped = da.rio.clip(buffer_proj.geometry, buffer_proj.crs)
        return da_clipped
    except Exception as e:
        print(f"[WARNING] Could not crop initial buffer: {e}")
        return None

def apply_mask_and_regrid_centered(eco_da, forest_mask, gdf_buffer, coverage_threshold=0.50):
    """
    Performs regridding using the robust method: SUM / COUNT.
    This ensures that the average is calculated even with many NaNs.
    """
    
    # 1. Apply forest mask
    eco_filtered = eco_da.where(forest_mask)
    template_da = create_centered_template(gdf_buffer)
    
    # =========================================================================
    # ROBUST METHOD: (Sum of Values) / (Sum of Weights)
    # =========================================================================
    
    # A. PREPARE DATA (Numerator)
    # Fill NaNs with 0 to sum without propagating error
    data_filled = eco_filtered.fillna(0.0)
    data_filled.rio.write_nodata(None, inplace=True) # Important: 0 is value, not nodata here
    
    # B. PREPARE WEIGHTS (Denominator)
    # Create a mask where 1 = Valid Data, 0 = NaN
    valid_weights = eco_filtered.notnull().astype(np.float32)
    valid_weights.rio.write_nodata(None, inplace=True)

    # C. REGRID (USING SUM)
    # Sum of all values within the large pixel
    print("   -> Calculating Sum of Values...")
    sum_grid = data_filled.rio.reproject_match(
        template_da,
        resampling=Resampling.sum,
        nodata=np.nan
    )
    
    # Sum of weights (How many 70m pixels are valid here?)
    print("   -> Calculating Valid Pixel Count...")
    count_grid = valid_weights.rio.reproject_match(
        template_da,
        resampling=Resampling.sum,
        nodata=np.nan
    )
    
    # D. MEAN CALCULATION
    # Mean = Sum / Count
    # Where count is 0, it becomes NaN (division by zero)
    mean_grid = sum_grid / count_grid.where(count_grid > 0)
    
    # =========================================================================
    # COVERAGE CALCULATION (FRACTION) FOR THRESHOLD
    # =========================================================================
    
    # We need to know what the MAXIMUM possible count would be (if pixel was full)
    # Create a dummy grid full of 1s
    dummy_full = xr.ones_like(eco_filtered).astype(np.float32)
    dummy_full.rio.write_nodata(None, inplace=True)
    
    max_count_grid = dummy_full.rio.reproject_match(
        template_da,
        resampling=Resampling.sum,
        nodata=np.nan
    )
    
    # Fraction = Real Count / Maximum Possible Count
    fraction_grid = count_grid / max_count_grid
    
    # =========================================================================
    # FINAL FILTERING
    # =========================================================================
    
    print(f"   -> Applying filter: Keep if coverage >= {coverage_threshold*100}%")
    oco3_final = mean_grid.where(fraction_grid >= coverage_threshold)
    
    # Final clipping
    buffer_utm = gdf_buffer.to_crs(CRS_METRICO)
    oco3_final = oco3_final.rio.clip(buffer_utm.geometry)
    
    return oco3_final
