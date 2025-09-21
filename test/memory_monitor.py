#!/usr/bin/env python3
"""
Real-time Memory Monitor voor Fill Database V2

Monitort memory usage tijdens app gebruik
"""

import gc
import psutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add app directory to Python path
sys.path.insert(0, '/workspaces')

class MemoryMonitor:
    """Real-time memory monitoring for Fill Database V2 app."""
    
    def __init__(self, log_file: str = "/workspaces/test/memory_log.txt"):
        """Initialize memory monitor."""
        self.log_file = Path(log_file)
        self.monitoring = False
        self.data_points = []
        self.start_time = None
        
        # Create log file
        self.log_file.parent.mkdir(exist_ok=True)
        self.log_file.write_text("Memory Monitor Started\n")
        
    def start_monitoring(self) -> None:
        """Start real-time memory monitoring."""
        print("🔍 Starting Memory Monitor")
        print("=" * 30)
        print(f"📁 Log file: {self.log_file}")
        print("📊 Monitoring every 1 second...")
        print("⏹️  Press Ctrl+C to stop")
        print()
        
        self.monitoring = True
        self.start_time = datetime.now()
        
        try:
            while self.monitoring:
                self._collect_memory_data()
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
            self.stop_monitoring()
            
    def stop_monitoring(self) -> None:
        """Stop memory monitoring and generate report."""
        self.monitoring = False
        
        print("\n📊 Generating Memory Report...")
        self._generate_report()
        
    def _collect_memory_data(self) -> None:
        """Collect current memory data."""
        try:
            # Get process info
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # Get system info
            system_memory = psutil.virtual_memory()
            
            # Create data point
            data_point = {
                'timestamp': datetime.now(),
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'memory_percent': process.memory_percent(),
                'num_threads': process.num_threads(),
                'num_fds': process.num_fds() if hasattr(process, 'num_fds') else 0,
                'system_memory_percent': system_memory.percent,
                'total_processes': len(psutil.pids())
            }
            
            # Store data point
            self.data_points.append(data_point)
            
            # Log to file
            self._log_data_point(data_point)
            
            # Print current status
            elapsed = (datetime.now() - self.start_time).total_seconds()
            print(f"⏱️  {elapsed:6.1f}s | "
                  f"Memory: {data_point['rss_mb']:6.1f} MB | "
                  f"Threads: {data_point['num_threads']:2d} | "
                  f"Processes: {data_point['total_processes']:3d}")
            
        except Exception as e:
            print(f"❌ Error collecting memory data: {e}")
            
    def _log_data_point(self, data_point: Dict[str, Any]) -> None:
        """Log data point to file."""
        timestamp = data_point['timestamp'].strftime("%H:%M:%S")
        log_line = (f"{timestamp} | "
                   f"RSS: {data_point['rss_mb']:6.1f} MB | "
                   f"VMS: {data_point['vms_mb']:6.1f} MB | "
                   f"Mem%: {data_point['memory_percent']:5.1f}% | "
                   f"Threads: {data_point['num_threads']:2d} | "
                   f"FDs: {data_point['num_fds']:3d} | "
                   f"SysMem%: {data_point['system_memory_percent']:5.1f}% | "
                   f"Procs: {data_point['total_processes']:3d}\n")
        
        with self.log_file.open("a") as f:
            f.write(log_line)
            
    def _generate_report(self) -> None:
        """Generate memory analysis report."""
        if not self.data_points:
            print("❌ No data points collected")
            return
            
        print(f"\n📈 Memory Analysis Report")
        print("=" * 30)
        
        # Basic statistics
        rss_values = [dp['rss_mb'] for dp in self.data_points]
        thread_values = [dp['num_threads'] for dp in self.data_points]
        process_values = [dp['total_processes'] for dp in self.data_points]
        
        print(f"📊 Data Points Collected: {len(self.data_points)}")
        print(f"⏱️  Monitoring Duration: {(self.data_points[-1]['timestamp'] - self.data_points[0]['timestamp']).total_seconds():.1f} seconds")
        print()
        
        print(f"💾 Memory Usage (RSS):")
        print(f"   Min: {min(rss_values):.1f} MB")
        print(f"   Max: {max(rss_values):.1f} MB")
        print(f"   Avg: {sum(rss_values) / len(rss_values):.1f} MB")
        print(f"   Range: {max(rss_values) - min(rss_values):.1f} MB")
        print()
        
        print(f"🧵 Threads:")
        print(f"   Min: {min(thread_values)}")
        print(f"   Max: {max(thread_values)}")
        print(f"   Avg: {sum(thread_values) / len(thread_values):.1f}")
        print()
        
        print(f"🔄 Processes:")
        print(f"   Min: {min(process_values)}")
        print(f"   Max: {max(process_values)}")
        print(f"   Avg: {sum(process_values) / len(process_values):.1f}")
        print()
        
        # Leak detection
        self._detect_memory_leaks()
        
        # Save detailed report
        self._save_detailed_report()
        
    def _detect_memory_leaks(self) -> None:
        """Detect potential memory leaks."""
        print(f"🔍 Memory Leak Detection:")
        
        rss_values = [dp['rss_mb'] for dp in self.data_points]
        
        # Check for overall trend
        if len(rss_values) > 10:
            # Calculate trend over last 10% of data
            trend_start = int(len(rss_values) * 0.9)
            trend_values = rss_values[trend_start:]
            
            if len(trend_values) > 1:
                trend_slope = (trend_values[-1] - trend_values[0]) / len(trend_values)
                
                if trend_slope > 0.5:  # More than 0.5MB per second increase
                    print(f"   ⚠️  POTENTIAL MEMORY LEAK: {trend_slope:.2f} MB/s increase")
                elif trend_slope > 0.1:
                    print(f"   ⚠️  SLIGHT INCREASE: {trend_slope:.2f} MB/s")
                else:
                    print(f"   ✅ STABLE: {trend_slope:.2f} MB/s")
        
        # Check for sudden spikes
        if len(rss_values) > 5:
            for i in range(5, len(rss_values)):
                spike = rss_values[i] - rss_values[i-5]
                if spike > 20:  # More than 20MB increase in 5 seconds
                    print(f"   ⚠️  MEMORY SPIKE: +{spike:.1f} MB at {self.data_points[i]['timestamp'].strftime('%H:%M:%S')}")
        
        # Check for thread leaks
        thread_values = [dp['num_threads'] for dp in self.data_points]
        if len(thread_values) > 10:
            thread_trend = thread_values[-1] - thread_values[0]
            if thread_trend > 5:  # More than 5 threads increase
                print(f"   ⚠️  THREAD LEAK: +{thread_trend} threads")
            else:
                print(f"   ✅ THREADS STABLE: {thread_trend:+d} threads")
                
    def _save_detailed_report(self) -> None:
        """Save detailed report to file."""
        report_file = self.log_file.parent / "memory_report.txt"
        
        with report_file.open("w") as f:
            f.write("Fill Database V2 - Memory Analysis Report\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Data Points: {len(self.data_points)}\n")
            f.write(f"Duration: {(self.data_points[-1]['timestamp'] - self.data_points[0]['timestamp']).total_seconds():.1f} seconds\n\n")
            
            f.write("Memory Usage (RSS MB):\n")
            for dp in self.data_points:
                f.write(f"{dp['timestamp'].strftime('%H:%M:%S')} | {dp['rss_mb']:6.1f} MB\n")
            
            f.write("\nThread Count:\n")
            for dp in self.data_points:
                f.write(f"{dp['timestamp'].strftime('%H:%M:%S')} | {dp['num_threads']:2d} threads\n")
        
        print(f"📁 Detailed report saved: {report_file}")

def main() -> None:
    """Run memory monitor."""
    print("🧪 Fill Database V2 - Real-time Memory Monitor")
    print("=" * 50)
    
    monitor = MemoryMonitor()
    
    try:
        monitor.start_monitoring()
    except Exception as e:
        print(f"❌ Monitor failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
