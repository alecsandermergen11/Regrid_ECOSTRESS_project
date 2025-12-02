import os
import glob
import rioxarray as rxr
from rasterio.enums import Resampling
from . import config
import geopandas as gpd
import os
import glob

def get_mapbiomas_file(year):
    """
    Find the MapBiomas .tif file.
    Fallback Logic: If year is 2025, use 2024.
    """
    # === FALLBACK LOGIC ===
    if year >= 2025:
        print(f"   -> [WARNING] MapBiomas {year} not available. Using MapBiomas 2024 as reference.")
        target_year = 2024
    else:
        target_year = year

    pattern = os.path.join(config.PATH_MAPBIOMAS_DIR, f"{target_year}_coverage_*.tif")
    files = glob.glob(pattern)
    
    if not files:
        print(f"[CRITICAL ERROR] MapBiomas for year {target_year} not found.")
        return None
    return files[0]

def create_forest_mask(ecostress_data_array, year, gdf_buffer):
    """
    1. Open MapBiomas (With year fallback if necessary).
    2. Box Clipping (Memory Optimized).
    3. Fine Clipping + Reprojection.
    """
    # First: check if there is a pre-cut MapBiomas file for this site/year
    # Expected location: PATH_MAPBIOMAS_CUT/<SITE>/<year>_coverage_*.tif
    try:
        site_name = None
        # Attempt to infer site name from buffer if possible
        if hasattr(gdf_buffer, 'name') and gdf_buffer.name:
            site_name = gdf_buffer.name
    except:
        site_name = None

    # If caller provided a GeoDataFrame without name, attempt to match by spatial intersection
    # We'll check any pre-cut files per site and load the first matching site folder
    precut_path = None
    if os.path.isdir(config.PATH_MAPBIOMAS_CUT):
        # If site_name known, look there first
        if site_name:
            candidate_dir = os.path.join(config.PATH_MAPBIOMAS_CUT, site_name)
            pattern = os.path.join(candidate_dir, f"{year}_coverage_*.tif")
            files = glob.glob(pattern) if os.path.isdir(candidate_dir) else []
            if files:
                precut_path = files[0]

        # If not found, check each site folder and test intersection with buffer
        if precut_path is None:
            for site, shp in config.SITES.items():
                candidate_dir = os.path.join(config.PATH_MAPBIOMAS_CUT, site)
                pattern = os.path.join(candidate_dir, f"{year}_coverage_*.tif")
                files = glob.glob(pattern)
                if not files:
                    continue
                # Quick spatial test: open the first file's bounds and compare to buffer bounds
                try:
                    mb_test = rxr.open_rasterio(files[0], masked=True)
                    mb_bounds = mb_test.rio.bounds()
                    minx, miny, maxx, maxy = mb_bounds
                    buf_minx, buf_miny, buf_maxx, buf_maxy = gdf_buffer.total_bounds
                    # If bounding boxes intersect, assume it's the right pre-cut file
                    if not (maxx < buf_minx or minx > buf_maxx or maxy < buf_miny or miny > buf_maxy):
                        precut_path = files[0]
                        break
                except Exception:
                    continue

    if precut_path:
        try:
            mb_da = rxr.open_rasterio(precut_path, masked=True).squeeze()
        except Exception as e:
            print(f"[WARNING] Failed to open pre-cut MapBiomas {precut_path}: {e}")
            precut_path = None

    # If no pre-cut available, fall back to original behavior
    if not precut_path:
        mb_path = get_mapbiomas_file(year)
        if mb_path is None:
            return None

        # 1. Open MapBiomas with chunks
        mb_da = rxr.open_rasterio(mb_path, masked=True, chunks={'x': 2048, 'y': 2048}).squeeze()

    # If we have a full MapBiomas (either precut or original), ensure CRS and align
    if not mb_da.rio.crs:
        mb_da.rio.write_crs("EPSG:4326", inplace=True)

    buffer_mb = gdf_buffer.to_crs(mb_da.rio.crs)

    try:
        # If the data covers a broader area than the buffer, do a box crop to reduce memory
        minx, miny, maxx, maxy = buffer_mb.total_bounds
        try:
            mb_box = mb_da.rio.clip_box(minx, miny, maxx, maxy, auto_expand=True)
            mb_box.load()
        except Exception:
            mb_box = mb_da

        # Fine clipping and reprojection / alignment with ECOSTRESS
        mb_clipped = mb_box.rio.clip(buffer_mb.geometry) if mb_box is not None else mb_da.rio.clip(buffer_mb.geometry)
        mb_reprojected = mb_clipped.rio.reproject_match(
            ecostress_data_array,
            resampling=Resampling.nearest
        )
    except Exception as e:
        print(f"[ERROR] Failed in geometric processing: {e}")
        return None
    
    # 4. Create the mask
    mask = mb_reprojected.isin(config.FOREST_CLASSES)
    return mask
