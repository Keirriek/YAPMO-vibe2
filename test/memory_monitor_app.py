#!/usr/bin/env python3
"""
App Memory Monitor voor Fill Database V2

Monitort memory usage van de app process (niet van zichzelf)
"""

import gc
import psutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add app directory to Python path
sys.path.insert(0, '/workspaces')

class AppMemoryMonitor:
    """Memory monitoring for Fill Database V2 app process."""
    
    def __init__(self, log_file: str = "/workspaces/test/app_memory_log.txt"):
        """Initialize app memory monitor."""
        self.log_file = Path(log_file)
        self.monitoring = False
        self.data_points = []
        self.start_time = None
        self.app_process = None
        
        # Create log file
        self.log_file.parent.mkdir(exist_ok=True)
        self.log_file.write_text("App Memory Monitor Started\n")
        
    def find_app_process(self) -> Optional[psutil.Process]:
        """Find the Fill Database V2 app process."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and len(cmdline) > 1:
                        # Look for main.py in the command line
                        if 'main.py' in ' '.join(cmdline) and 'fill_db' in ' '.join(cmdline).lower():
                            return psutil.Process(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            print(f"Error finding app process: {e}")
        
        return None
    
    def start_monitoring(self) -> None:
        """Start real-time app memory monitoring."""
        print("🔍 Starting App Memory Monitor")
        print("=" * 35)
        print(f"📁 Log file: {self.log_file}")
        print("📊 Monitoring app process every 1 second...")
        print("⏹️  Press Ctrl+C to stop")
        print()
        
        self.monitoring = True
        self.start_time = datetime.now()
        
        try:
            while self.monitoring:
                # Find app process if not found yet
                if self.app_process is None:
                    self.app_process = self.find_app_process()
                    if self.app_process is None:
                        print("⏳ Waiting for app process...")
                        time.sleep(2)
                        continue
                    else:
                        print(f"✅ Found app process: PID {self.app_process.pid}")
                
                # Check if app process still exists
                try:
                    if not self.app_process.is_running():
                        print("❌ App process stopped")
                        self.app_process = None
                        continue
                except psutil.NoSuchProcess:
                    print("❌ App process not found")
                    self.app_process = None
                    continue
                
                self._collect_app_memory_data()
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
            self.stop_monitoring()
            
    def stop_monitoring(self) -> None:
        """Stop memory monitoring and generate report."""
        self.monitoring = False
        
        print("\n📊 Generating App Memory Report...")
        self._generate_report()
        
    def _collect_app_memory_data(self) -> None:
        """Collect current app memory data."""
        try:
            if self.app_process is None:
                return
                
            # Get app process info
            memory_info = self.app_process.memory_info()
            
            # Get system info
            system_memory = psutil.virtual_memory()
            
            # Create data point
            data_point = {
                'timestamp': datetime.now(),
                'pid': self.app_process.pid,
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'memory_percent': self.app_process.memory_percent(),
                'num_threads': self.app_process.num_threads(),
                'num_fds': self.app_process.num_fds() if hasattr(self.app_process, 'num_fds') else 0,
                'cpu_percent': self.app_process.cpu_percent(),
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
                  f"App Memory: {data_point['rss_mb']:6.1f} MB | "
                  f"Threads: {data_point['num_threads']:2d} | "
                  f"CPU: {data_point['cpu_percent']:5.1f}% | "
                  f"Processes: {data_point['total_processes']:3d}")
            
        except Exception as e:
            print(f"❌ Error collecting app memory data: {e}")
            
    def _log_data_point(self, data_point: Dict[str, Any]) -> None:
        """Log data point to file."""
        timestamp = data_point['timestamp'].strftime("%H:%M:%S")
        log_line = (f"{timestamp} | "
                   f"PID: {data_point['pid']} | "
                   f"RSS: {data_point['rss_mb']:6.1f} MB | "
                   f"VMS: {data_point['vms_mb']:6.1f} MB | "
                   f"Mem%: {data_point['memory_percent']:5.1f}% | "
                   f"Threads: {data_point['num_threads']:2d} | "
                   f"CPU: {data_point['cpu_percent']:5.1f}% | "
                   f"FDs: {data_point['num_fds']:3d} | "
                   f"SysMem%: {data_point['system_memory_percent']:5.1f}% | "
                   f"Procs: {data_point['total_processes']:3d}\n")
        
        with self.log_file.open("a") as f:
            f.write(log_line)
            
    def _generate_report(self) -> None:
        """Generate app memory analysis report."""
        if not self.data_points:
            print("❌ No data points collected")
            return
            
        print(f"\n📈 App Memory Analysis Report")
        print("=" * 35)
        
        # Basic statistics
        rss_values = [dp['rss_mb'] for dp in self.data_points]
        thread_values = [dp['num_threads'] for dp in self.data_points]
        cpu_values = [dp['cpu_percent'] for dp in self.data_points]
        
        print(f"📊 Data Points Collected: {len(self.data_points)}")
        print(f"⏱️  Monitoring Duration: {(self.data_points[-1]['timestamp'] - self.data_points[0]['timestamp']).total_seconds():.1f} seconds")
        print()
        
        print(f"💾 App Memory Usage (RSS):")
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
        
        print(f"⚡ CPU Usage:")
        print(f"   Min: {min(cpu_values):.1f}%")
        print(f"   Max: {max(cpu_values):.1f}%")
        print(f"   Avg: {sum(cpu_values) / len(cpu_values):.1f}%")
        print()
        
        # Leak detection
        self._detect_memory_leaks()
        
        # Save detailed report
        self._save_detailed_report()
        
    def _detect_memory_leaks(self) -> None:
        """Detect potential memory leaks in app process."""
        print(f"🔍 App Memory Leak Detection:")
        
        rss_values = [dp['rss_mb'] for dp in self.data_points]
        
        # Check for overall trend
        if len(rss_values) > 10:
            # Calculate trend over last 10% of data
            trend_start = int(len(rss_values) * 0.9)
            trend_values = rss_values[trend_start:]
            
            if len(trend_values) > 1:
                trend_slope = (trend_values[-1] - trend_values[0]) / len(trend_values)
                
                if trend_slope > 1.0:  # More than 1MB per second increase
                    print(f"   ⚠️  POTENTIAL MEMORY LEAK: {trend_slope:.2f} MB/s increase")
                elif trend_slope > 0.1:
                    print(f"   ⚠️  SLIGHT INCREASE: {trend_slope:.2f} MB/s")
                else:
                    print(f"   ✅ STABLE: {trend_slope:.2f} MB/s")
        
        # Check for sudden spikes
        if len(rss_values) > 5:
            for i in range(5, len(rss_values)):
                spike = rss_values[i] - rss_values[i-5]
                if spike > 50:  # More than 50MB increase in 5 seconds
                    print(f"   ⚠️  MEMORY SPIKE: +{spike:.1f} MB at {self.data_points[i]['timestamp'].strftime('%H:%M:%S')}")
        
        # Check for thread leaks
        thread_values = [dp['num_threads'] for dp in self.data_points]
        if len(thread_values) > 10:
            thread_trend = thread_values[-1] - thread_values[0]
            if thread_trend > 10:  # More than 10 threads increase
                print(f"   ⚠️  THREAD LEAK: +{thread_trend} threads")
            else:
                print(f"   ✅ THREADS STABLE: {thread_trend:+d} threads")
                
    def _save_detailed_report(self) -> None:
        """Save detailed report to file."""
        report_file = self.log_file.parent / "app_memory_report.txt"
        
        with report_file.open("w") as f:
            f.write("Fill Database V2 - App Memory Analysis Report\n")
            f.write("=" * 55 + "\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Data Points: {len(self.data_points)}\n")
            f.write(f"Duration: {(self.data_points[-1]['timestamp'] - self.data_points[0]['timestamp']).total_seconds():.1f} seconds\n\n")
            
            f.write("App Memory Usage (RSS MB):\n")
            for dp in self.data_points:
                f.write(f"{dp['timestamp'].strftime('%H:%M:%S')} | {dp['rss_mb']:6.1f} MB | Threads: {dp['num_threads']:2d} | CPU: {dp['cpu_percent']:5.1f}%\n")
            
            f.write("\nThread Count:\n")
            for dp in self.data_points:
                f.write(f"{dp['timestamp'].strftime('%H:%M:%S')} | {dp['num_threads']:2d} threads\n")
        
        print(f"📁 Detailed report saved: {report_file}")

def main() -> None:
    """Run app memory monitor."""
    print("🧪 Fill Database V2 - App Memory Monitor")
    print("=" * 50)
    
    monitor = AppMemoryMonitor()
    
    try:
        monitor.start_monitoring()
    except Exception as e:
        print(f"❌ Monitor failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
