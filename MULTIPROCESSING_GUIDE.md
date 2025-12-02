# Multiprocessing Optimization Guide

## Overview

This project has been optimized with multiprocessing to significantly speed up data processing. The parallel processing is automatically enabled in three main scripts:

- **main.py**: Parallel processing of ECOSTRESS files
- **extract_to_csv.py**: Parallel extraction of raster data
- **plot_results.py**: Parallel generation of validation plots

## How It Works

### Automatic CPU Core Detection

All scripts automatically detect the number of available CPU cores using `os.cpu_count()`:

```python
num_workers = os.cpu_count() or 4
```

This means:
- If your machine has 8 cores, it will use 8 workers
- If detection fails, it defaults to 4 workers
- For plot generation, it uses `(num_workers - 1)` to keep 1 core free for system tasks

### Processing Strategy

#### main.py - File Processing
```
Original approach: Sequential processing of files
├── Site 1
│   ├── Variable 1
│   │   ├── File 1 (process)
│   │   ├── File 2 (process)
│   │   └── File 3 (process)
│   └── Variable 2
│       ├── File 1 (process)
│       └── File 2 (process)

Optimized approach: Parallel processing within each Site/Variable combination
├── Site 1
│   ├── Variable 1
│   │   ├── File 1 (worker 1)
│   │   ├── File 2 (worker 2)
│   │   └── File 3 (worker 3) [parallel execution]
```

#### extract_to_csv.py - Raster Extraction
All raster files for a Site/Variable combination are processed in parallel:
- Each worker loads and extracts data from one raster file
- Results are combined after all workers finish
- Coordinate transformation happens serially but on combined data

#### plot_results.py - Plot Generation
All validation plots are generated in parallel:
- Each worker generates one plot
- Uses (num_cores - 1) to reserve resources for main process

## Performance Expectations

### Expected Speed-Up

| Scenario | Speed-up |
|----------|----------|
| 4-core machine | 3-4x faster |
| 8-core machine | 6-8x faster |
| 16-core machine | 12-15x faster |

**Note**: Actual speed-up depends on:
- File sizes and complexity
- I/O speed (disk read/write)
- Available RAM
- System load

### Memory Usage

Multiprocessing creates separate Python processes, so:
- Memory usage ≈ (Base memory) × (Number of workers)
- Example: If base memory is 500MB and 8 workers, expect ~4GB RAM

To limit workers, modify the script:
```python
num_workers = min(os.cpu_count() or 4, 4)  # Max 4 workers
```

## Configuration

### Adjusting Number of Workers

To customize the number of workers, edit the relevant script:

#### main.py
```python
# Around line 19
num_workers = os.cpu_count() or 4
# Change to:
num_workers = 4  # Or any number you prefer
```

#### extract_to_csv.py
```python
# Around line 35
num_workers = os.cpu_count() or 4
# Change to:
num_workers = 2  # Reduce for lower memory machines
```

#### plot_results.py
```python
# Around line 21
num_workers = max(1, os.cpu_count() - 1) if os.cpu_count() else 2
# Change to:
num_workers = 2  # Or any number you prefer
```

## Troubleshooting

### Issue: Process pool exceeds memory limits

**Solution**: Reduce the number of workers
```python
num_workers = max(1, os.cpu_count() // 2)  # Use half the cores
```

### Issue: Slow disk I/O becomes bottleneck

**Solution**: 
- Consider using SSD instead of HDD
- Reduce number of workers to 2-4
- Process data in batches instead of all at once

### Issue: Some processes appear to hang

**Solution**:
- Increase timeout or add progress bars
- Check system resources (RAM, CPU)
- Restart the process

### Issue: Process crashes with "No space left on device"

**Solution**:
- Clear temporary files
- Reduce number of workers to lower RAM usage
- Process fewer files at once

## Technical Details

### Process Communication

The multiprocessing uses Pool.map() which:
1. Sends task arguments to worker processes
2. Workers process independently
3. Returns results to main process
4. Main process collects and processes results

### Thread Safety

All I/O operations are:
- File-based (no shared file handles)
- Safe for concurrent access
- Output files have unique names (no conflicts)

### Pickling

For multiprocessing to work, all objects must be pickleable:
- Numpy arrays ✓
- Pandas DataFrames ✓
- Rasterio datasets ✓
- File paths (strings) ✓

## Performance Tips

1. **Use SSD**: Significantly faster I/O than HDD
2. **Optimize file formats**: Compressed TIFs may be slower to process
3. **Monitor resources**: Use `Task Manager` (Windows) or `htop` (Linux)
4. **Process in batches**: For very large datasets, process subsets

## Monitoring Execution

### Windows
```powershell
# Watch CPU usage in Task Manager
Start-Process taskmgr
```

### Linux/Mac
```bash
# Monitor processes
watch -n 1 'ps aux | grep python'

# Or use htop
htop
```

## Reverting to Sequential Processing

If you need to disable multiprocessing for debugging, modify the scripts:

```python
# Replace:
with Pool(processes=num_workers) as pool:
    results = pool.map(process_function, task_list)

# With:
results = [process_function(task) for task in task_list]
```

## Future Optimizations

Potential improvements for future versions:
1. **Dask arrays**: For out-of-core processing
2. **Ray**: For distributed computing across machines
3. **GPU acceleration**: For regridding operations
4. **Caching**: Store intermediate results
5. **Batch processing**: Process multiple sites/variables in parallel

---

**Last update**: December 2025
