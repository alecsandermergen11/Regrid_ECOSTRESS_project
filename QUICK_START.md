# Quick Start Guide - Regrid Project with Multiprocessing

## 🚀 TL;DR (Too Long; Didn't Read)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Edit config.py if needed (optional)
nano config.py

# 3. Run the processing scripts
python main.py              # Process and regrid data
python extract_to_csv.py    # Extract time series
python plot_results.py      # Generate validation plots

# 4. Check results
# - Output files in: Output_Regrid_OCO3_Multi/
# - CSV files in: Tabelas_CSVs/
# - Plots in: Plots_Validacao_Final/

# Optional: Benchmark your system
python benchmark.py
```

## Step-by-Step Setup

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

**Optional** (for advanced monitoring):
```bash
pip install psutil
```

### 2️⃣ Configure the Project

Edit `config.py`:
```python
# Change these paths to match your setup:
BASE_PATH = r"D:\your\project\path"
SITES = {
    "ATTO": r"D:\your\buffers\ATTO.shp",
    "K34":  r"D:\your\buffers\K34.shp",
    "K67":  r"D:\your\buffers\K67.shp"
}
```

### 3️⃣ Run Main Processing
```bash
python main.py
```

**What it does**:
- ✓ Reads ECOSTRESS data
- ✓ Applies forest mask
- ✓ Regrid to OCO-3 resolution
- ✓ **Uses all your CPU cores automatically**

**Expected output**:
```
=== STARTING BATCH PROCESSING (MULTI-SITES / MULTI-VARS) ===
Using 8 CPU cores for parallel processing

### SITE: ATTO
   >>> Processing Variable: LST
   Files found: 150
   Starting parallel processing with 8 workers...
      [OK] file1.tif
      [OK] file2.tif
      ...
```

### 4️⃣ Extract Time Series
```bash
python extract_to_csv.py
```

**What it does**:
- ✓ Loads processed rasters
- ✓ Extracts pixel values
- ✓ Converts coordinates
- ✓ **Extracts all files in parallel**

**Output**: CSV files in `Tabelas_CSVs/`
```
ATTO_LST.csv
ATTO_NDVI.csv
K34_LST.csv
...
```

### 5️⃣ Generate Plots
```bash
python plot_results.py
```

**What it does**:
- ✓ Generates validation plots
- ✓ 4-panel visualization per file
- ✓ **Generates plots in parallel**

**Output**: PNG files in `Plots_Validacao_Final/`

## 📊 Performance Expectations

| Your System | Time Saved |
|-------------|-----------|
| 2-core | 1.5-2x faster |
| 4-core | 3-4x faster |
| 8-core | **6-8x faster** ⚡ |
| 16-core | 12-15x faster ⚡⚡ |

**Example**: 8-core system processes 10 files in ~3 seconds instead of 20!

## 🔧 Customization

### Limit Workers (for memory-constrained systems)

Edit `main.py`, `extract_to_csv.py`, or `plot_results.py`:

```python
# Current line:
num_workers = os.cpu_count() or 4

# Change to (example - 4 workers max):
num_workers = min(os.cpu_count() or 4, 4)
```

### Change Output Paths

Edit `config.py`:
```python
OUTPUT_ROOT = r"D:\my\output\path\Output_Regrid_OCO3_Multi"
```

## 📈 Benchmark Your System

```bash
python benchmark.py
```

This will:
1. Run all three scripts sequentially
2. Measure execution time for each
3. Report total time and speedup

**Output example**:
```
============================================================
BENCHMARK SUMMARY
============================================================
1. main.py (Regridding)
   Time: 0m 5.2s (5.20s)
   Status: ✓ SUCCESS

2. extract_to_csv.py (CSV Extraction)
   Time: 0m 8.7s (8.70s)
   Status: ✓ SUCCESS

3. plot_results.py (Plot Generation)
   Time: 0m 2.3s (2.30s)
   Status: ✓ SUCCESS

Total execution time: 0m 16.2s
CPU cores available: 8
============================================================
```

## 🐛 Troubleshooting

### Issue: Script runs slowly

**Check**:
```bash
# Windows: Open Task Manager and check CPU usage
# Linux: Run: htop
```

**Solution**: 
- If not all cores are used, multiprocessing may not be working
- If all cores at 100%, this is normal! ✓

### Issue: Out of memory error

**Solution**: Reduce workers
```python
num_workers = 2  # Use 2 workers instead of all cores
```

### Issue: No output files

**Check**:
- Input files exist in `Rasters_buffers_data/`?
- Buffer shapefiles exist?
- MapBiomas files in `Coverage_mapbiomas/`?

**Solution**: Review output messages for [ERROR] tags

## 📚 More Information

- **Detailed Guide**: See `MULTIPROCESSING_GUIDE.md`
- **Technical Details**: See `OPTIMIZATION_REPORT.md`
- **Full Overview**: See `IMPLEMENTATION_SUMMARY.md`
- **Main Documentation**: See `README.md`

## ✅ Verification

### Check if multiprocessing is working

```bash
python -c "import os; print(f'CPU cores: {os.cpu_count()}')"
```

Should output: `CPU cores: X` (where X is your number of cores)

### Check if output files are created

```bash
ls Output_Regrid_OCO3_Multi/ATTO/LST/  # Check for .tif files
ls Tabelas_CSVs/                       # Check for .csv files
ls Plots_Validacao_Final/              # Check for .png files
```

## 🎯 Common Workflows

### Process single site only

Edit `config.py`:
```python
SITES = {
    "ATTO": os.path.join(BASE_PATH, r"Buffers\ATTO_buffer_30km\buffer_30km_ATTO.shp"),
}
```

### Process single variable only

Edit `config.py`:
```python
VARIABLES = ["LST"]  # Only process LST
```

### Process single file for testing

Modify `main.py` line ~75:
```python
eco_files = glob.glob(os.path.join(input_dir, "*.tif"))[:1]  # Only first file
```

## 📞 Getting Help

1. **Check for [ERROR] messages** in output
2. **Review MULTIPROCESSING_GUIDE.md** for detailed help
3. **Run benchmark.py** to analyze your system
4. **Check system resources** (memory, disk space, CPU)

## 🎓 Key Concepts

### What is Multiprocessing?

- Uses multiple CPU cores simultaneously
- Each core processes one task independently
- Results are combined automatically
- Your computer does N things at once!

### Why is it faster?

```
Before: 1 file processed at a time (1 core)
        File 1 → File 2 → File 3 → File 4
        Time: 8 seconds

After:  4 files processed at a time (4 cores)
        File 1
        File 2 } in parallel
        File 3
        File 4
        Time: 2 seconds
```

## 🎉 Next Steps

1. ✅ Install dependencies
2. ✅ Configure paths
3. ✅ Run `main.py`
4. ✅ Run `extract_to_csv.py`
5. ✅ Run `plot_results.py`
6. ✅ Enjoy the speedup! 🚀

---

**Need help?** See the documentation files:
- Quick answers → `IMPLEMENTATION_SUMMARY.md`
- Detailed help → `MULTIPROCESSING_GUIDE.md`
- Technical info → `OPTIMIZATION_REPORT.md`

**Last Updated**: December 2025
