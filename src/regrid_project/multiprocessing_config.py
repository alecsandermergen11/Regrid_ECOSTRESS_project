"""
Advanced Multiprocessing Configuration Module

This module provides utilities for configuring and optimizing multiprocessing
behavior in the Regrid project.
"""

import os
import psutil
from typing import Optional

class MultiprocessingConfig:
    """Configuration for multiprocessing parameters"""
    
    # CPU core allocation
    MAX_WORKERS = None  # Auto-detect if None
    RESERVE_CORES = 1   # Cores to reserve for system
    
    # Memory management
    MAX_MEMORY_PER_WORKER_MB = 1024  # MB per worker
    WARN_MEMORY_THRESHOLD = 0.85      # Warn if memory > 85%
    ERROR_MEMORY_THRESHOLD = 0.95     # Error if memory > 95%
    
    # Timeout settings
    TASK_TIMEOUT_SECONDS = 300  # 5 minutes
    POOL_TIMEOUT_SECONDS = 3600  # 1 hour
    
    # Batch processing
    BATCH_SIZE = None  # Auto-calculate if None
    
    @classmethod
    def get_optimal_workers(cls, task_type='io') -> int:
        """
        Calculate optimal number of workers based on system resources
        
        Args:
            task_type (str): 'io' for I/O bound, 'cpu' for CPU bound
        
        Returns:
            int: Optimal number of workers
        """
        cpu_count = os.cpu_count() or 4
        
        if task_type == 'io':
            # I/O bound: can use more workers than CPU count
            optimal = min(cpu_count * 2, 16)
        else:
            # CPU bound: typically limited to CPU count
            optimal = max(1, cpu_count - cls.RESERVE_CORES)
        
        # Respect maximum if set
        if cls.MAX_WORKERS is not None:
            optimal = min(optimal, cls.MAX_WORKERS)
        
        return optimal
    
    @classmethod
    def check_memory_availability(cls, required_workers: int) -> bool:
        """
        Check if sufficient memory is available for requested workers
        
        Args:
            required_workers (int): Number of workers needed
        
        Returns:
            bool: True if sufficient memory, False otherwise
        """
        try:
            memory = psutil.virtual_memory()
            available_mb = memory.available / (1024 * 1024)
            required_mb = required_workers * cls.MAX_MEMORY_PER_WORKER_MB
            
            if memory.percent > cls.ERROR_MEMORY_THRESHOLD:
                print(f"[ERROR] Memory usage critical: {memory.percent:.1f}%")
                return False
            
            if memory.percent > cls.WARN_MEMORY_THRESHOLD:
                print(f"[WARNING] High memory usage: {memory.percent:.1f}%")
            
            if available_mb < required_mb:
                print(f"[WARNING] Limited memory. Available: {available_mb:.0f}MB, "
                      f"Required: {required_mb:.0f}MB")
                return False
            
            return True
        except:
            # If psutil not available, assume memory is OK
            return True
    
    @classmethod
    def get_batch_size(cls, total_files: int, workers: int) -> int:
        """
        Calculate optimal batch size for processing
        
        Args:
            total_files (int): Total number of files to process
            workers (int): Number of available workers
        
        Returns:
            int: Optimal batch size
        """
        if cls.BATCH_SIZE is not None:
            return cls.BATCH_SIZE
        
        # Default: give each worker at least 2 tasks
        min_batch = max(1, total_files // (workers * 2))
        return min_batch


class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self, name: str, total_tasks: int):
        """
        Initialize performance monitor
        
        Args:
            name (str): Name of the task being monitored
            total_tasks (int): Total number of tasks
        """
        self.name = name
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start monitoring"""
        import time
        self.start_time = time.time()
    
    def update(self, completed: int = 1):
        """Update progress"""
        self.completed_tasks += completed
        self.log_progress()
    
    def stop(self):
        """Stop monitoring"""
        import time
        self.end_time = time.time()
        self.log_summary()
    
    def log_progress(self):
        """Log current progress"""
        if self.start_time:
            import time
            elapsed = time.time() - self.start_time
            rate = self.completed_tasks / elapsed if elapsed > 0 else 0
            remaining = (self.total_tasks - self.completed_tasks) / rate if rate > 0 else 0
            
            print(f"[{self.name}] Progress: {self.completed_tasks}/{self.total_tasks} "
                  f"({100*self.completed_tasks/self.total_tasks:.1f}%) "
                  f"| Rate: {rate:.2f} tasks/sec "
                  f"| ETA: {remaining/60:.1f}m")
    
    def log_summary(self):
        """Log execution summary"""
        if self.start_time and self.end_time:
            total_time = self.end_time - self.start_time
            rate = self.total_tasks / total_time if total_time > 0 else 0
            minutes, seconds = divmod(total_time, 60)
            
            print(f"\n[{self.name}] Summary:")
            print(f"  Total tasks: {self.total_tasks}")
            print(f"  Time elapsed: {minutes:.0f}m {seconds:.1f}s")
            print(f"  Average rate: {rate:.2f} tasks/sec")


def suggest_configuration(verbose: bool = False) -> dict:
    """
    Analyze system and suggest optimal configuration
    
    Args:
        verbose (bool): Print detailed analysis
    
    Returns:
        dict: Suggested configuration
    """
    config = {
        'workers': MultiprocessingConfig.get_optimal_workers('io'),
        'memory_available': False,
        'recommendations': []
    }
    
    try:
        memory = psutil.virtual_memory()
        config['memory_available'] = True
        config['memory_percent'] = memory.percent
        config['memory_available_mb'] = memory.available / (1024 * 1024)
        
        if verbose:
            print("\n=== System Analysis ===")
            print(f"CPU Cores: {os.cpu_count()}")
            print(f"Memory: {memory.total / (1024**3):.1f} GB total, "
                  f"{memory.available / (1024**3):.1f} GB available")
            print(f"Memory Usage: {memory.percent:.1f}%")
        
        # Memory-based recommendations
        if memory.percent > 80:
            config['recommendations'].append("High memory usage. Consider reducing workers.")
            config['workers'] = max(1, config['workers'] // 2)
        elif memory.percent < 30:
            config['recommendations'].append("Low memory usage. Can potentially increase workers.")
    
    except ImportError:
        if verbose:
            print("[WARNING] psutil not installed. Cannot analyze system memory.")
        config['recommendations'].append("Install psutil for better resource management: pip install psutil")
    
    if verbose:
        print(f"\n=== Recommendations ===")
        print(f"Suggested workers: {config['workers']}")
        for rec in config['recommendations']:
            print(f"  - {rec}")
    
    return config


# Example usage
if __name__ == "__main__":
    print("Multiprocessing Configuration Module")
    print("====================================\n")
    
    # Suggest configuration
    config = suggest_configuration(verbose=True)
    
    # Check memory
    print(f"\nMemory check for {config['workers']} workers: ", end="")
    if MultiprocessingConfig.check_memory_availability(config['workers']):
        print("OK ✓")
    else:
        print("FAILED ✗")
