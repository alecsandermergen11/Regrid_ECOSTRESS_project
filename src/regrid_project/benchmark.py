#!/usr/bin/env python3
"""
Performance Benchmark Script
Measures execution time and efficiency of multiprocessing
"""

import os
import time
import sys

def benchmark_main_processing():
    """Benchmark main.py execution"""
    print("\n" + "="*60)
    print("BENCHMARKING: main.py (Regridding)")
    print("="*60)
    
    start_time = time.time()
    exit_code = os.system("python main.py")
    end_time = time.time()
    
    elapsed_time = end_time - start_time
    print(f"\nExecution time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    
    return elapsed_time, exit_code == 0

def benchmark_csv_extraction():
    """Benchmark extract_to_csv.py execution"""
    print("\n" + "="*60)
    print("BENCHMARKING: extract_to_csv.py (CSV Extraction)")
    print("="*60)
    
    start_time = time.time()
    exit_code = os.system("python extract_to_csv.py")
    end_time = time.time()
    
    elapsed_time = end_time - start_time
    print(f"\nExecution time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    
    return elapsed_time, exit_code == 0

def benchmark_plot_generation():
    """Benchmark plot_results.py execution"""
    print("\n" + "="*60)
    print("BENCHMARKING: plot_results.py (Plot Generation)")
    print("="*60)
    
    start_time = time.time()
    exit_code = os.system("python plot_results.py")
    end_time = time.time()
    
    elapsed_time = end_time - start_time
    print(f"\nExecution time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    
    return elapsed_time, exit_code == 0

def print_summary(results):
    """Print benchmark summary"""
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)
    
    total_time = 0
    for i, (name, elapsed, success) in enumerate(results, 1):
        status = "✓ SUCCESS" if success else "✗ FAILED"
        minutes, seconds = divmod(elapsed, 60)
        print(f"{i}. {name}")
        print(f"   Time: {minutes:.0f}m {seconds:.1f}s ({elapsed:.2f}s)")
        print(f"   Status: {status}\n")
        total_time += elapsed
    
    minutes, seconds = divmod(total_time, 60)
    print(f"Total execution time: {minutes:.0f}m {seconds:.1f}s ({total_time:.2f}s)")
    print(f"CPU cores available: {os.cpu_count()}")
    print("="*60)

def main():
    print("\n" + "="*60)
    print("REGRID PROJECT - PERFORMANCE BENCHMARK")
    print("="*60)
    print(f"System CPU cores: {os.cpu_count()}")
    print(f"Current directory: {os.getcwd()}")
    
    results = []
    
    # Run benchmarks
    try:
        elapsed, success = benchmark_main_processing()
        results.append(("main.py (Regridding)", elapsed, success))
    except Exception as e:
        print(f"Error running benchmark: {e}")
        results.append(("main.py (Regridding)", 0, False))
    
    try:
        elapsed, success = benchmark_csv_extraction()
        results.append(("extract_to_csv.py (CSV Extraction)", elapsed, success))
    except Exception as e:
        print(f"Error running benchmark: {e}")
        results.append(("extract_to_csv.py (CSV Extraction)", 0, False))
    
    try:
        elapsed, success = benchmark_plot_generation()
        results.append(("plot_results.py (Plot Generation)", elapsed, success))
    except Exception as e:
        print(f"Error running benchmark: {e}")
        results.append(("plot_results.py (Plot Generation)", 0, False))
    
    # Print summary
    print_summary(results)
    
    # Determine exit code
    all_success = all(success for _, _, success in results)
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())
