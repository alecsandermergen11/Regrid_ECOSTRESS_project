# Performance Optimization Summary

## What Was Changed

### Multiprocessing Implementation

The project has been optimized with multiprocessing to enable parallel execution of CPU-intensive tasks.

## Files Modified

### 1. **main.py**
**Optimization**: Parallel file processing

**Changes**:
- Added `multiprocessing.Pool` import
- Created `process_single_file()` function for worker processes
- Modified main loop to collect tasks and process them in parallel
- Automatic CPU core detection

**Performance Impact**:
- Sequential: 1 file at a time
- Parallel: N files simultaneously (N = number of CPU cores)
- **Expected speedup: 3-8x** on multi-core machines

**Example** (8-core machine):
```
Before: 10 files × 2 seconds each = 20 seconds
After:  10 files in parallel ≈ 2-3 seconds
```

### 2. **extract_to_csv.py**
**Optimization**: Parallel raster file extraction

**Changes**:
- Added `multiprocessing.Pool` import
- Created `process_raster_file()` function for worker processes
- Modified to extract data from all files in parallel
- Results are combined after parallel execution

**Performance Impact**:
- Sequential: Extract files one-by-one
- Parallel: Extract N files simultaneously
- **Expected speedup: 3-8x**

### 3. **plot_results.py**
**Optimization**: Parallel plot generation

**Changes**:
- Added `multiprocessing.Pool` import
- Created `process_plot_task()` function for worker processes
- Collects all plot tasks first
- Generates plots in parallel (uses CPU cores - 1 to keep system responsive)

**Performance Impact**:
- Sequential: Generate plots one-by-one
- Parallel: Generate N plots simultaneously
- **Expected speedup: 2-7x** (uses 1 less core to maintain system responsiveness)

## Benchmarking

### How to Run Benchmarks

```bash
python benchmark.py
```

This will run all three main scripts and measure execution time.

### Expected Results

| CPU Cores | Expected Speedup |
|-----------|-----------------|
| 2-core | 1.5-2x |
| 4-core | 3-4x |
| 8-core | 6-8x |
| 16-core | 12-15x |

**Note**: Actual speedup depends on:
- File sizes
- Disk I/O speed
- Available RAM
- System load during execution

## Configuration

### Default Behavior

All scripts automatically:
1. Detect available CPU cores using `os.cpu_count()`
2. Create worker pool with detected core count
3. Distribute tasks across workers
4. Combine results

### Custom Configuration

To use a specific number of workers, edit the script:

```python
# Default (auto-detection):
num_workers = os.cpu_count() or 4

# Custom (example - use 4 workers):
num_workers = 4

# Or limit to half the cores:
num_workers = max(1, os.cpu_count() // 2)
```

## Memory Considerations

### Memory Usage

Multiprocessing creates separate Python processes. Memory usage scales approximately:

```
Total Memory ≈ (Base Memory) × (Number of Workers)
```

Example:
- Base memory: 500 MB
- Workers: 8
- Total: ~4 GB RAM

### For Limited Memory Systems

If your machine has limited RAM:

```python
# Reduce workers to save memory
num_workers = 2
```

Or modify to limit workers:

```python
num_workers = min(os.cpu_count() or 4, 4)  # Max 4 workers
```

## Thread Safety

All multiprocessing operations are thread-safe:
- ✓ File I/O operations
- ✓ Output files have unique names
- ✓ No shared data structures
- ✓ No race conditions

## Error Handling

All scripts include error handling:
- Failed tasks report status
- Other tasks continue processing
- Results show which tasks failed

Example output:
```
[OK] file1.tif
[OK] file2.tif
[ERROR] file3.tif: Could not load ECOSTRESS
[OK] file4.tif
```

## Troubleshooting

### Issue: High Memory Usage

**Solution**: Reduce number of workers
```python
num_workers = 2
```

### Issue: Slow Execution (Disk I/O Bound)

**Cause**: Disk speed is bottleneck, not CPU
**Solution**: 
- Use faster storage (SSD)
- Reduce workers
- Process in batches

### Issue: Process Crashes

**Cause**: Out of memory or system resource limits
**Solution**:
- Reduce number of workers
- Increase available disk space
- Close other applications

## Monitoring

### Windows

```powershell
# Open Task Manager to monitor CPU and RAM usage
taskmgr.exe
```

### Linux/macOS

```bash
# Real-time monitoring of processes
watch -n 1 'ps aux | grep python'

# Or use htop
htop
```

## Next Steps

### Potential Future Optimizations

1. **Dask Arrays**: Out-of-core processing for very large files
2. **Ray**: Distributed computing across multiple machines
3. **GPU Acceleration**: Use GPU for regridding operations
4. **Caching**: Store intermediate results to avoid recomputation
5. **Batch Processing**: Process multiple sites/variables in parallel

## Reverting Changes

To revert to sequential (non-parallel) processing:

**In main.py:**
```python
# Replace this:
with Pool(processes=num_workers) as pool:
    results = pool.map(process_single_file, task_args)

# With this:
results = [process_single_file(args) for args in task_args]
```

## Documentation

For detailed information on multiprocessing configuration and troubleshooting, see:
- `MULTIPROCESSING_GUIDE.md` - Complete guide
- `README.md` - Main documentation

---

**Optimization Date**: December 2025
**Python Version**: 3.8+
**Multiprocessing Backend**: Python standard library `multiprocessing`
