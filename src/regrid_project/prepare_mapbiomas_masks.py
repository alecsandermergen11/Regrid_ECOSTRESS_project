"""
prepare_mapbiomas_masks.py

Utility script to pre-cut MapBiomas coverage rasters per buffer/site and year.
The output will be saved under `Coverage_mapbiomas_cut/<SITE>/<year>_coverage_*.tif`.

Usage:
    python prepare_mapbiomas_masks.py

This script will:
- Scan `config.PATH_MAPBIOMAS_DIR` for MapBiomas coverage files
- For each site defined in `config.SITES`, it will clip the MapBiomas to the buffer
  extent and save the result in `config.PATH_MAPBIOMAS_CUT/<SITE>/`.

Next pipeline runs will use these pre-cut files when available.
"""
import os
import glob
import rioxarray as rxr
import geopandas as gpd
import config


def prepare_all_masks(verbose=True):
    # Find all MapBiomas files (pattern: YEAR_coverage_*.tif)
    pattern = os.path.join(config.PATH_MAPBIOMAS_DIR, "*_coverage_*.tif")
    mb_files = glob.glob(pattern)
    if not mb_files:
        print(f"No MapBiomas files found in {config.PATH_MAPBIOMAS_DIR}")
        return

    # Load site buffers once
    site_buffers = {}
    for site, shp in config.SITES.items():
        if not os.path.exists(shp):
            print(f"[WARNING] Buffer shapefile not found for {site}: {shp}")
            continue
        gdf = gpd.read_file(shp)
        if len(gdf) > 1:
            gdf = gdf.iloc[[0]]
        # ensure consistent CRS
        site_buffers[site] = gdf

    if not site_buffers:
        print("No valid site buffers available. Exiting.")
        return

    # Create output folders per site
    for site in site_buffers.keys():
        out_dir = os.path.join(config.PATH_MAPBIOMAS_CUT, site)
        os.makedirs(out_dir, exist_ok=True)

    # Process each MapBiomas file
    for mb_path in mb_files:
        try:
            # Extract year from filename
            basename = os.path.basename(mb_path)
            # Expected pattern: <year>_coverage_....tif
            year = None
            parts = basename.split("_")
            if parts and parts[0].isdigit():
                year = int(parts[0])
            if year is None:
                print(f"[SKIP] Could not determine year for {basename}")
                continue

            if verbose:
                print(f"Processing MapBiomas {basename} (year {year})")

            # Open MapBiomas (lazy) once
            mb_da = rxr.open_rasterio(mb_path, masked=True)
            if not mb_da.rio.crs:
                mb_da.rio.write_crs("EPSG:4326", inplace=True)

            # For each site, crop and save
            for site, gdf in site_buffers.items():
                out_dir = os.path.join(config.PATH_MAPBIOMAS_CUT, site)
                out_pattern = os.path.join(out_dir, f"{year}_coverage_*.tif")
                existing = glob.glob(out_pattern)
                if existing:
                    if verbose:
                        print(f"  [SKIP] Pre-cut exists for {site} year {year}")
                    continue

                # Reproject buffer to MapBiomas CRS
                buf_proj = gdf.to_crs(mb_da.rio.crs)
                try:
                    minx, miny, maxx, maxy = buf_proj.total_bounds
                    mb_box = mb_da.rio.clip_box(minx, miny, maxx, maxy, auto_expand=True)
                except Exception as e:
                    print(f"  [ERROR] Box crop failed for {site}/{year}: {e}")
                    continue

                try:
                    mb_clipped = mb_box.rio.clip(buf_proj.geometry)
                except Exception as e:
                    print(f"  [ERROR] Fine clip failed for {site}/{year}: {e}")
                    continue

                # Build output filename and save
                out_fn = os.path.join(out_dir, f"{year}_coverage_{site}.tif")
                try:
                    mb_clipped.rio.to_raster(out_fn)
                    print(f"  [SAVED] {out_fn}")
                except Exception as e:
                    print(f"  [ERROR] Saving failed for {site}/{year}: {e}")

        except Exception as e:
            print(f"[ERROR] Processing failed for {mb_path}: {e}")


if __name__ == "__main__":
    prepare_all_masks()
