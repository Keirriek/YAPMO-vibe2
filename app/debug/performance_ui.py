"""Performance UI - Creates and manages UI elements for performance monitoring.

This module provides UI components for displaying performance data
in the debug section of the YAPMO application.

Key Features:
- Real-time statistics display
- Performance charts (line, histogram, bar)
- Performance log with filtering
- Integration with existing debug section
"""

from typing import Any, Dict, List, Optional
from nicegui import ui
from debug.performance_monitor import get_performance_monitor


class PerformanceUI:
    """UI components for performance monitoring in debug section."""
    
    def __init__(self, parent_page: Any) -> None:
        """Initialize performance UI with reference to parent page.
        
        Args:
            parent_page: Reference to the parent FillDbPageV2 instance
        """
        self.parent_page = parent_page
        self.performance_monitor = get_performance_monitor()
        
        # UI element references
        self.stats_labels: Dict[str, Any] = {}
        self.charts: Dict[str, Any] = {}
        self.log_elements: Dict[str, Any] = {}
        
        # Data storage for charts
        self.files_per_sec_history: List[float] = []
        self.processing_times: List[float] = []
        self.bottleneck_data: Dict[str, float] = {}
        
        # Filtering state
        self.selected_worker: str = "All"
        self.selected_component: str = "All"
    
    def create_performance_section(self) -> None:
        """Create the performance monitoring section in debug card."""
        with ui.card().classes("w-full bg-gray-50 rounded-lg mb-4"), ui.card_section():
            ui.label("Performance Monitoring").classes("text-lg font-bold mb-4")
            
            # Real-time Statistics
            self._create_statistics_section()
            
            # Performance Charts
            self._create_charts_section()
            
            # Performance Log
            self._create_log_section()
    
    def _create_statistics_section(self) -> None:
        """Create real-time statistics display."""
        ui.label("Real-time Statistics").classes("text-md font-bold mb-2")
        
        # Main statistics row
        with ui.row().classes("gap-4 mb-2"):
            self.stats_labels['files_per_sec'] = ui.label("Files/sec: 0.0").classes("font-bold text-blue-600")
            self.stats_labels['peak_files_per_sec'] = ui.label("Peak: 0.0").classes("text-green-600")
            self.stats_labels['min_files_per_sec'] = ui.label("Min: 0.0").classes("text-red-600")
        
        # Secondary statistics row
        with ui.row().classes("gap-4 mb-2"):
            self.stats_labels['active_workers'] = ui.label("Active: 0").classes("text-purple-600")
            self.stats_labels['completed_files'] = ui.label("Completed: 0").classes("text-indigo-600")
            self.stats_labels['bottleneck'] = ui.label("Bottleneck: unknown").classes("text-orange-600")
        
        # Consistency indicator
        with ui.row().classes("gap-2 items-center"):
            ui.label("Consistency:").classes("text-sm")
            self.stats_labels['consistency_progress'] = ui.linear_progress().classes("flex-1").props("value=0")
            self.stats_labels['consistency_value'] = ui.label("0.00").classes("text-sm font-mono")
    
    def _create_charts_section(self) -> None:
        """Create performance charts section."""
        ui.label("Performance Charts").classes("text-md font-bold mb-2")
        
        # Add Chart.js library and initialization script to body
        self._add_chart_js_library()
        
        with ui.row().classes("gap-4 mb-2"):
            # Files per second trend chart
            with ui.column().classes("flex-1"):
                ui.label("Files/sec Trend (60s)").classes("text-sm font-medium mb-1")
                self.charts['files_per_sec_chart'] = ui.html(self._create_canvas_html("files-per-sec-chart")).classes("w-full h-32 border rounded")
            
            # Processing time distribution chart
            with ui.column().classes("flex-1"):
                ui.label("Processing Time Distribution").classes("text-sm font-medium mb-1")
                self.charts['processing_time_chart'] = ui.html(self._create_canvas_html("processing-time-chart")).classes("w-full h-32 border rounded")
        
        # Bottleneck components chart
        with ui.column().classes("w-full"):
            ui.label("Bottleneck Components").classes("text-sm font-medium mb-1")
            self.charts['bottleneck_chart'] = ui.html(self._create_canvas_html("bottleneck-chart")).classes("w-full h-24 border rounded")
    
    def _create_log_section(self) -> None:
        """Create performance log section."""
        ui.label("Performance Log").classes("text-md font-bold mb-2")
        
        # Filter controls
        with ui.row().classes("gap-2 mb-2"):
            ui.label("Filter:").classes("text-sm")
            
            self.log_elements['worker_filter'] = ui.select(
                options=["All", "Worker 1", "Worker 2", "Worker 3", "Worker 4"],
                value="All"
            ).classes("w-32").on("change", self._on_worker_filter_change)
            
            self.log_elements['component_filter'] = ui.select(
                options=["All", "Database", "ExifTool", "I/O"],
                value="All"
            ).classes("w-32").on("change", self._on_component_filter_change)
            
            ui.button("Clear Log", on_click=self._clear_log).classes("text-xs")
        
        # Log display
        self.log_elements['log_display'] = ui.log().classes("h-48 w-full border rounded")
    
    def update_performance_display(self) -> None:
        """Update all performance UI elements with current data."""
        try:
            # Get current performance status
            status = self.performance_monitor.get_current_status()
            
            # Debug: Print status to see what data we have
            print(f"Performance UI Update - Status: {status}")  # DEBUG_ON Performance UI status debug
            
            # Update statistics labels
            self._update_statistics_labels(status)
            
            # Update charts
            self._update_charts(status)
            
            # Update log display
            self._update_log_display()
            
        except Exception as e:
            print(f"Error updating performance display: {e}")  # DEBUG_ON Performance UI update error
    
    def _update_statistics_labels(self, status: Dict[str, Any]) -> None:
        """Update statistics labels with current data."""
        try:
            # Update main statistics
            if 'files_per_sec' in self.stats_labels:
                self.stats_labels['files_per_sec'].text = f"Files/sec: {status.get('current_files_per_second', 0.0):.1f}"
            
            if 'peak_files_per_sec' in self.stats_labels:
                self.stats_labels['peak_files_per_sec'].text = f"Peak: {status.get('peak_files_per_second', 0.0):.1f}"
            
            if 'min_files_per_sec' in self.stats_labels:
                min_val = status.get('min_files_per_second', 0.0)
                if min_val == float('inf'):
                    min_val = 0.0
                self.stats_labels['min_files_per_sec'].text = f"Min: {min_val:.1f}"
            
            # Update secondary statistics
            if 'active_workers' in self.stats_labels:
                self.stats_labels['active_workers'].text = f"Active: {status.get('active_workers', 0)}"
            
            if 'completed_files' in self.stats_labels:
                self.stats_labels['completed_files'].text = f"Completed: {status.get('completed_files', 0)}"
            
            if 'bottleneck' in self.stats_labels:
                bottleneck = status.get('bottleneck_component', 'unknown')
                self.stats_labels['bottleneck'].text = f"Bottleneck: {bottleneck}"
            
            # Update consistency indicator
            consistency = status.get('performance_consistency', 0.0)
            if 'consistency_progress' in self.stats_labels:
                self.stats_labels['consistency_progress'].props(f"value={consistency}")
            
            if 'consistency_value' in self.stats_labels:
                self.stats_labels['consistency_value'].text = f"{consistency:.2f}"
                
        except Exception as e:
            print(f"Error updating statistics labels: {e}")  # DEBUG_ON Statistics update error
    
    def _update_charts(self, status: Dict[str, Any]) -> None:
        """Update performance charts with current data."""
        try:
            # Update files per second chart with real-time data
            files_per_sec_data = status.get('files_per_sec_history', [])
            if files_per_sec_data:
                self.files_per_sec_history = files_per_sec_data[-30:]  # Keep last 30 data points
                self._update_files_per_sec_chart()
            
            # Update processing time chart with real-time data
            processing_times = status.get('processing_times', [])
            if processing_times:
                self.processing_times = processing_times[-50:]  # Keep last 50 data points
                self._update_processing_time_chart()
            
            # Update bottleneck chart with real-time data
            bottleneck_data = status.get('bottleneck_data', {})
            if bottleneck_data:
                self.bottleneck_data = bottleneck_data
                self._update_bottleneck_chart()
            
        except Exception as e:
            print(f"Error updating charts: {e}")  # DEBUG_ON Charts update error
    
    def _update_files_per_sec_chart(self) -> None:
        """Update files per second trend chart."""
        try:
            if 'files_per_sec_chart' not in self.charts:
                return
            
            # Get performance history from monitor
            history = getattr(self.performance_monitor, 'performance_history', [])
            
            if not history:
                return
            
            # Extract data for chart
            timestamps = [h.get('timestamp', 0) for h in history]
            files_per_sec = [h.get('files_per_second', 0) for h in history]
            
            # Keep only last 12 data points (60 seconds at 5-second intervals)
            if len(timestamps) > 12:
                timestamps = timestamps[-12:]
                files_per_sec = files_per_sec[-12:]
            
            # Create time labels (relative to start)
            if timestamps:
                start_time = timestamps[0]
                time_labels = [f"{(t - start_time):.0f}s" for t in timestamps]
            else:
                time_labels = []
            
            # Update chart via JavaScript
            ui.run_javascript(f"updateFilesPerSecChart({time_labels}, {files_per_sec})")
            print(f"Files/sec chart data: {list(zip(time_labels, files_per_sec))}")  # DEBUG_ON Files per sec chart data
            
        except Exception as e:
            print(f"Error updating files per sec chart: {e}")  # DEBUG_ON Files per sec chart error
    
    def _update_processing_time_chart(self) -> None:
        """Update processing time distribution chart."""
        try:
            if 'processing_time_chart' not in self.charts:
                return
            
            # Get processing times from completed operations
            completed_ops = getattr(self.performance_monitor, 'completed_operations', [])
            
            if not completed_ops:
                return
            
            # Extract processing times
            processing_times = []
            for op in completed_ops:
                if hasattr(op, 'end_time') and hasattr(op, 'start_time') and op.end_time and op.start_time:
                    processing_times.append(op.end_time - op.start_time)
            
            # Keep only last 100 files
            if len(processing_times) > 100:
                processing_times = processing_times[-100:]
            
            if not processing_times:
                return
            
            # Create histogram bins (simplified)
            min_time = min(processing_times)
            max_time = max(processing_times)
            bin_size = (max_time - min_time) / 10 if max_time > min_time else 0.1
            
            bins = []
            bin_labels = []
            for i in range(10):
                bin_start = min_time + i * bin_size
                bin_end = min_time + (i + 1) * bin_size
                bin_count = sum(1 for t in processing_times if bin_start <= t < bin_end)
                bins.append(bin_count)
                bin_labels.append(f"{bin_start:.2f}-{bin_end:.2f}s")
            
            # Update chart via JavaScript
            ui.run_javascript(f"updateProcessingTimeChart({bin_labels}, {bins})")
            print(f"Processing time chart data: {list(zip(bin_labels, bins))}")  # DEBUG_ON Processing time chart data
            
        except Exception as e:
            print(f"Error updating processing time chart: {e}")  # DEBUG_ON Processing time chart error
    
    def _update_bottleneck_chart(self) -> None:
        """Update bottleneck components chart."""
        try:
            if 'bottleneck_chart' not in self.charts:
                return
            
            # Get bottleneck data from monitor
            db_times = getattr(self.performance_monitor, 'database_wait_times', [])
            exiftool_times = getattr(self.performance_monitor, 'exiftool_wait_times', [])
            io_times = getattr(self.performance_monitor, 'io_wait_times', [])
            
            # Calculate average wait times
            avg_db = sum(db_times) / len(db_times) if db_times else 0
            avg_exiftool = sum(exiftool_times) / len(exiftool_times) if exiftool_times else 0
            avg_io = sum(io_times) / len(io_times) if io_times else 0
            
            # Update chart via JavaScript
            ui.run_javascript(f"updateBottleneckChart([{avg_db}, {avg_exiftool}, {avg_io}])")
            print(f"Bottleneck chart data: Database={avg_db:.3f}s, ExifTool={avg_exiftool:.3f}s, I/O={avg_io:.3f}s")  # DEBUG_ON Bottleneck chart data
            
        except Exception as e:
            print(f"Error updating bottleneck chart: {e}")  # DEBUG_ON Bottleneck chart error
    
    def _update_log_display(self) -> None:
        """Update performance log display."""
        try:
            if 'log_display' not in self.log_elements:
                # print("🔍 UI DEBUG: log_display element not found")  # DEBUG_OFF UI debug - log_display element not found
                return
            
            # Get recent performance logs
            recent_logs = self.performance_monitor.get_recent_logs(limit=20)
            # print(f"🔍 UI DEBUG: Recent logs count: {len(recent_logs)}")  # DEBUG_OFF UI debug - Recent logs count
            
            if recent_logs:
                # Update log display with performance logs
                log_text = "\n".join(recent_logs)
                self.log_elements['log_display'].text = log_text
                # print(f"🔍 UI DEBUG: Updated log display with {len(recent_logs)} logs")  # DEBUG_OFF UI debug - Updated log display
            else:
                # Show current status if no logs available
                status = self.performance_monitor.get_current_status()
                status_text = f"Files/sec: {status.get('current_files_per_second', 0.0):.1f}\n"
                status_text += f"Active workers: {status.get('active_workers', 0)}\n"
                status_text += f"Completed files: {status.get('completed_files', 0)}\n"
                status_text += f"Bottleneck: {status.get('bottleneck_component', 'Unknown')}"
                self.log_elements['log_display'].text = status_text
                # print("🔍 UI DEBUG: Updated log display with status (no recent logs)")  # DEBUG_OFF UI debug - Updated log display with status
            
        except Exception as e:
            print(f"Error updating log display: {e}")  # DEBUG_ON Log display update error
    
    def _filter_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter messages based on current filter settings."""
        filtered = []
        
        for message in messages:
            # Check worker filter
            if self.selected_worker != "All":
                worker_id = message.get('worker_id', 0)
                if f"Worker {worker_id}" != self.selected_worker:
                    continue
            
            # Check component filter
            if self.selected_component != "All":
                level = message.get('level', '')
                if not self._matches_component_filter(level, self.selected_component):
                    continue
            
            filtered.append(message)
        
        return filtered
    
    def _matches_component_filter(self, level: str, component: str) -> bool:
        """Check if log level matches component filter."""
        component_mapping = {
            'Database': ['TEST4', 'TEST5'],
            'ExifTool': ['TEST2', 'TEST3'],
            'I/O': ['TEST7']
        }
        
        if component in component_mapping:
            return level in component_mapping[component]
        
        return True
    
    def _add_log_message(self, message: Dict[str, Any]) -> None:
        """Add a single message to the log display."""
        try:
            if 'log_display' not in self.log_elements:
                return
            
            # Format message for display
            timestamp = message.get('timestamp', '')
            level = message.get('level', '')
            worker_id = message.get('worker_id', '')
            msg_text = message.get('message', '')
            
            # Create formatted log entry
            worker_str = f"Worker {worker_id}" if worker_id is not None else "Main"
            formatted_msg = f"{timestamp} {worker_str} {level}: {msg_text}"
            
            # Add to log display (simplified - would need proper ui.log integration)
            # For now, just print to console
            print(f"PERF_LOG: {formatted_msg}")  # DEBUG_ON Performance log message
            
        except Exception as e:
            print(f"Error adding log message: {e}")  # DEBUG_ON Log message add error
    
    def _on_worker_filter_change(self, event: Any) -> None:
        """Handle worker filter change."""
        try:
            self.selected_worker = event.value
            self._update_log_display()
        except Exception as e:
            print(f"Error handling worker filter change: {e}")  # DEBUG_ON Worker filter change error
    
    def _on_component_filter_change(self, event: Any) -> None:
        """Handle component filter change."""
        try:
            self.selected_component = event.value
            self._update_log_display()
        except Exception as e:
            print(f"Error handling component filter change: {e}")  # DEBUG_ON Component filter change error
    
    def _clear_log(self) -> None:
        """Clear the performance log display."""
        try:
            if 'log_display' in self.log_elements:
                # Clear log display (simplified - would need proper ui.log integration)
                print("PERF_LOG: Log cleared")  # DEBUG_ON Performance log cleared
        except Exception as e:
            print(f"Error clearing log: {e}")  # DEBUG_ON Log clear error
    
    def _add_chart_js_library(self) -> None:
        """Add Chart.js library and initialization script to body."""
        ui.add_body_html("""
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            // Global chart references
            window.performanceCharts = {};
            
            // Initialize charts when DOM is ready
            document.addEventListener('DOMContentLoaded', function() {
                initializePerformanceCharts();
            });
            
            function initializePerformanceCharts() {
                // Files per second line chart
                var ctx1 = document.getElementById('files-per-sec-chart');
                if (ctx1) {
                    window.performanceCharts.filesPerSec = new Chart(ctx1, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'Files/sec',
                                data: [],
                                borderColor: 'rgb(75, 192, 192)',
                                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                                tension: 0.1,
                                fill: true
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    title: {
                                        display: true,
                                        text: 'Files per Second'
                                    }
                                },
                                x: {
                                    title: {
                                        display: true,
                                        text: 'Time (seconds)'
                                    }
                                }
                            },
                            plugins: {
                                legend: {
                                    display: false
                                }
                            }
                        }
                    });
                }
                
                // Processing time histogram
                var ctx2 = document.getElementById('processing-time-chart');
                if (ctx2) {
                    window.performanceCharts.processingTime = new Chart(ctx2, {
                        type: 'bar',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'Processing Time (s)',
                                data: [],
                                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                                borderColor: 'rgba(54, 162, 235, 1)',
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    title: {
                                        display: true,
                                        text: 'Frequency'
                                    }
                                },
                                x: {
                                    title: {
                                        display: true,
                                        text: 'Processing Time (s)'
                                    }
                                }
                            },
                            plugins: {
                                legend: {
                                    display: false
                                }
                            }
                        }
                    });
                }
                
                // Bottleneck components bar chart
                var ctx3 = document.getElementById('bottleneck-chart');
                if (ctx3) {
                    window.performanceCharts.bottleneck = new Chart(ctx3, {
                        type: 'bar',
                        data: {
                            labels: ['Database', 'ExifTool', 'I/O'],
                            datasets: [{
                                label: 'Wait Time (s)',
                                data: [0, 0, 0],
                                backgroundColor: [
                                    'rgba(255, 99, 132, 0.6)',
                                    'rgba(54, 162, 235, 0.6)',
                                    'rgba(255, 205, 86, 0.6)'
                                ],
                                borderColor: [
                                    'rgba(255, 99, 132, 1)',
                                    'rgba(54, 162, 235, 1)',
                                    'rgba(255, 205, 86, 1)'
                                ],
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    title: {
                                        display: true,
                                        text: 'Wait Time (seconds)'
                                    }
                                },
                                x: {
                                    title: {
                                        display: true,
                                        text: 'Component'
                                    }
                                }
                            },
                            plugins: {
                                legend: {
                                    display: false
                                }
                            }
                        }
                    });
                }
            }
            
            // Global functions for updating charts
            window.updateFilesPerSecChart = function(labels, data) {
                if (window.performanceCharts.filesPerSec) {
                    window.performanceCharts.filesPerSec.data.labels = labels;
                    window.performanceCharts.filesPerSec.data.datasets[0].data = data;
                    window.performanceCharts.filesPerSec.update();
                }
            };
            
            window.updateProcessingTimeChart = function(labels, data) {
                if (window.performanceCharts.processingTime) {
                    window.performanceCharts.processingTime.data.labels = labels;
                    window.performanceCharts.processingTime.data.datasets[0].data = data;
                    window.performanceCharts.processingTime.update();
                }
            };
            
            window.updateBottleneckChart = function(data) {
                if (window.performanceCharts.bottleneck) {
                    window.performanceCharts.bottleneck.data.datasets[0].data = data;
                    window.performanceCharts.bottleneck.update();
                }
            };
        </script>
        """)
    
    def _create_canvas_html(self, chart_id: str) -> str:
        """Create HTML for canvas element only."""
        return f'<canvas id="{chart_id}" width="400" height="200"></canvas>'
    
