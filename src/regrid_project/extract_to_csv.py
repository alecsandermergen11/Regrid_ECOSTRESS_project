import os
import glob
import re
from multiprocessing import Pool
import numpy as np
import pandas as pd
import rioxarray as rxr
from pyproj import Transformer
from src.regrid_project import config

def extract_date_info(filename):
    """Extract Year and DOY from filename."""
    match = re.search(r"doy(\d{4})(\d{3})", filename)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

def process_raster_file(filepath):
    """Process a single raster file and return dataframe"""
    try:
        filename = os.path.basename(filepath)
        year, doy = extract_date_info(filename)
        
        # Load Raster
        da = rxr.open_rasterio(filepath, masked=True).squeeze()
        
        # Convert to DataFrame
        df = da.to_dataframe(name='value').reset_index()
        
        # Remove NaNs and make an explicit copy to avoid SettingWithCopyWarning
        df_clean = df.dropna(subset=['value']).copy()
        
        if df_clean.empty:
            return None
        
        # Add metadata using .loc to avoid SettingWithCopyWarning
        df_clean.loc[:, 'year'] = year
        df_clean.loc[:, 'doy'] = doy

        # Create actual date
        if year and doy:
            df_clean.loc[:, 'date'] = pd.to_datetime(df_clean['year'] * 1000 + df_clean['doy'], format='%Y%j')

        # Store filename for reference
        df_clean.loc[:, 'filename'] = filename
        
        return df_clean
        
    except Exception as e:
        print(f"   Error reading {filepath}: {e}")
        return None

def main():
    print("=== EXTRACTING DATA TO INDIVIDUAL CSVs (BY BUFFER AND VARIABLE) ===")
    
    # Create a specific folder to store the tables
    csv_output_dir = os.path.join(config.BASE_PATH, "Tables_CSVs")
    os.makedirs(csv_output_dir, exist_ok=True)
    
    # Configure coordinate transformer (UTM 21S -> Lat/Lon)
    transformer = Transformer.from_crs("EPSG:32721", "EPSG:4326", always_xy=True)

    # 1. Loop through SITES (Buffers)
    for site_name in config.SITES.keys():
        
        # 2. Loop through VARIABLES
        for var_name in config.VARIABLES:
            
            # Build the path to the folder where processed TIFs are
            # Ex: .../Output_Regrid_OCO3_Multi/ATTO/LST
            target_folder = os.path.join(config.OUTPUT_ROOT, site_name, var_name)
            
            if not os.path.exists(target_folder):
                # If folder doesn't exist (perhaps NDVI for K34 hasn't been processed yet), skip
                continue

            print(f"\nProcessing: {site_name} - {var_name} ...")
            
            # List only TIF files from this specific folder
            files = glob.glob(os.path.join(target_folder, "*.tif"))
            
            if not files:
                print(f"   [WARNING] Empty folder: {target_folder}")
                continue

            # Temporary list to store data ONLY from this Site/Variable
            batch_data = []

            for filepath in files:
                filename = os.path.basename(filepath)
                year, doy = extract_date_info(filename)
                
                try:
                    # Load Raster
                    da = rxr.open_rasterio(filepath, masked=True).squeeze()
                except Exception as e:
                    print(f"   Erro ao ler {filename}: {e}")
                    continue

                # Convert to DataFrame
                df = da.to_dataframe(name='value').reset_index()
                
                # Remove NaNs (where there's no forest or outside buffer)
                # Make an explicit copy to avoid SettingWithCopyWarning when adding columns
                df_clean = df.dropna(subset=['value']).copy()
                
                if df_clean.empty:
                    continue

                # Add basic metadata using .loc to avoid SettingWithCopyWarning
                df_clean.loc[:, 'year'] = year
                df_clean.loc[:, 'doy'] = doy

                # Create actual date
                if year and doy:
                    df_clean.loc[:, 'date'] = pd.to_datetime(df_clean['year'] * 1000 + df_clean['doy'], format='%Y%j')

                # Convert Coordinates to Lat/Lon
                lons, lats = transformer.transform(df_clean['x'].values, df_clean['y'].values)
                df_clean.loc[:, 'longitude'] = lons
                df_clean.loc[:, 'latitude'] = lats

                # Create unique pixel ID
                # Note: No need for site name in ID here, as file is already separated by site
                df_clean.loc[:, 'pixel_id'] = (
                    df_clean['x'].astype(int).astype(str) + "_" + 
                    df_clean['y'].astype(int).astype(str)
                )

                batch_data.append(df_clean)

            # --- SAVE CSV FOR THIS PAIR (SITE + VARIABLE) ---
            if batch_data:
                final_df = pd.concat(batch_data, ignore_index=True)
                
                # Rename value column to variable name (e.g., 'LST', 'NDVI')
                # This helps a lot in later analysis
                final_df.rename(columns={'value': var_name}, inplace=True)
                
                # Organize columns
                cols = ['date', 'year', 'doy', 'latitude', 'longitude', var_name, 'pixel_id', 'x', 'y', 'filename']
                cols = [c for c in cols if c in final_df.columns]
                final_df = final_df[cols]
                
                # CSV filename: E.g., ATTO_LST.csv
                csv_filename = f"{site_name}_{var_name}.csv"
                output_path = os.path.join(csv_output_dir, csv_filename)
                
                final_df.to_csv(output_path, index=False)
                print(f"   -> SAVED: {csv_filename} ({len(final_df)} rows)")
            else:
                print(f"   -> No valid data found for {site_name}/{var_name}.")

    print("\n=== ALL CSVs HAVE BEEN GENERATED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()