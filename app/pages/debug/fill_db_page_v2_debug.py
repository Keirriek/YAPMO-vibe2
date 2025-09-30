"""Debug functionality for Fill Database V2 Page."""

from typing import Any
from nicegui import ui


class FillDbPageV2Debug:
    """Debug helper class for FillDbPageV2."""
    
    def __init__(self, parent_page: Any) -> None:
        """Initialize debug helper with reference to parent page."""
        self.parent_page = parent_page
        
    def create_debug_section(self) -> None:
        """Create the debug section with performance UI elements."""
        with ui.card().classes("w-full bg-white rounded-lg mb-6"), ui.card_section():
            ui.label("DEBUG").classes("text-xl font-bold mb-4")
            
            # Current State Display
            ui.label("Current State").classes("text-lg font-bold mb-2")
            self.parent_page.debug_current_state_label = ui.label(
                f"State: {self.parent_page.current_state.value}"
            ).classes("text-xl font-bold text-blue-600")
            
            # Performance Monitoring Section
            ui.label("Performance Monitoring").classes("text-lg font-bold mb-2 mt-4")
            
            # Real-time Statistics
            ui.label("Real-time Statistics").classes("text-md font-semibold mb-2")
            with ui.row().classes("gap-4 mb-2"):
                self.parent_page.files_per_sec_label = ui.label("Files/sec: 0.0").classes("text-sm")
                self.parent_page.peak_label = ui.label("Peak: 0.0").classes("text-sm")
                self.parent_page.min_label = ui.label("Min: 0.0").classes("text-sm")
                self.parent_page.active_label = ui.label("Active: 0").classes("text-sm")
                self.parent_page.completed_label = ui.label("Completed: 0").classes("text-sm")
                self.parent_page.bottleneck_label = ui.label("Bottleneck: unknown").classes("text-sm")
            
            # Consistency row
            with ui.row().classes("gap-2 mb-4"):
                ui.label("Consistency:").classes("text-sm font-medium")
                self.parent_page.consistency_input = ui.input("Consistency").classes("w-32")
                self.parent_page.consistency_input.value = "0.00"
            
            # Performance Charts Section
            ui.label("Performance Charts").classes("text-md font-semibold mb-2")
            
            # Files/sec Trend Chart (full width)
            ui.label("Files/sec Trend (60s)").classes("text-sm font-medium mb-1")
            self.parent_page.files_per_sec_chart = ui.html('<canvas id="files-per-sec-chart" width="800" height="250"></canvas>')
            
            # Charts row (side by side)
            with ui.row().classes("gap-4 mt-4"):
                with ui.column().classes("flex-1"):
                    # Processing Time Distribution Chart
                    ui.label("Processing Time Distribution").classes("text-sm font-medium mb-1")
                    self.parent_page.processing_time_chart = ui.html('<canvas id="processing-time-chart" width="400" height="250"></canvas>')
                with ui.column().classes("flex-1"):
                    # Bottleneck Components Chart
                    ui.label("Bottleneck Components").classes("text-sm font-medium mb-1")
                    self.parent_page.bottleneck_chart = ui.html('<canvas id="bottleneck-chart" width="400" height="250"></canvas>')
            
            # Performance Log Section
            ui.label("Performance Log").classes("text-md font-semibold mb-2 mt-6")
            
            # Filter row
            with ui.row().classes("gap-2 mb-3"):
                self.parent_page.level_filter = ui.select(["All", "TEST1", "TEST2", "TEST3", "TEST4", "TEST5", "TEST6", "TEST7", "TEST8", "TEST9", "TEST10"], value="All").classes("w-24")
                # Dynamic worker filter based on max_workers
                worker_options = ["All"] + [f"Worker {i+1}" for i in range(32)]
                self.parent_page.worker_filter = ui.select(worker_options, value="All").classes("w-24")
                self.parent_page.clear_log_btn = ui.button("CLEAR LOG").classes("text-xs")
            
            # Log display
            self.parent_page.log_display = ui.textarea("Performance logs will appear here...").classes("w-full h-40 text-xs font-mono")
            self.parent_page.log_display.readonly = True
            
            # Add Chart.js and initialize charts
            ui.add_body_html("""
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            // Initialize charts when page loads
            window.addEventListener('DOMContentLoaded', function() {
                // Files/sec Trend Chart
                const filesPerSecCtx = document.getElementById('files-per-sec-chart');
                if (filesPerSecCtx) {
                    window.performanceCharts = window.performanceCharts || {};
                    window.performanceCharts.filesPerSec = new Chart(filesPerSecCtx, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'Files/sec',
                                data: [],
                                borderColor: 'rgb(75, 192, 192)',
                                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                tension: 0.1
                            }]
                        },
                        options: {
                            responsive: true,
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
                            }
                        }
                    });
                }
                
                // Processing Time Distribution Chart
                const processingTimeCtx = document.getElementById('processing-time-chart');
                if (processingTimeCtx) {
                    window.performanceCharts.processingTime = new Chart(processingTimeCtx, {
                        type: 'bar',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'Frequency',
                                data: [],
                                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                                borderColor: 'rgba(54, 162, 235, 1)',
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
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
                            }
                        }
                    });
                }
                
                // Bottleneck Components Chart
                const bottleneckCtx = document.getElementById('bottleneck-chart');
                if (bottleneckCtx) {
                    window.performanceCharts.bottleneck = new Chart(bottleneckCtx, {
                        type: 'bar',
                        data: {
                            labels: ['Database', 'ExifTool Component', 'I/O'],
                            datasets: [{
                                label: 'Wait Time',
                                data: [0, 0, 0],
                                backgroundColor: [
                                    'rgba(255, 99, 132, 0.2)',
                                    'rgba(255, 205, 86, 0.2)',
                                    'rgba(75, 192, 192, 0.2)'
                                ],
                                borderColor: [
                                    'rgba(255, 99, 132, 1)',
                                    'rgba(255, 205, 86, 1)',
                                    'rgba(75, 192, 192, 1)'
                                ],
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    title: {
                                        display: true,
                                        text: 'Wait Time (sec)'
                                    }
                                }
                            }
                        }
                    });
                }
            });
        </script>
        """)
    
    def update_debug_state_label(self) -> None:
        """Update debug state label."""
        if hasattr(self.parent_page, 'debug_current_state_label') and self.parent_page.debug_current_state_label:
            self.parent_page.debug_current_state_label.text = f"State: {self.parent_page.current_state.value}"
    
    def update_files_per_sec_label(self, files_per_sec: float) -> None:
        """Update files per sec label."""
        if hasattr(self.parent_page, 'files_per_sec_label') and self.parent_page.files_per_sec_label:
            self.parent_page.files_per_sec_label.text = f"Files/sec: {files_per_sec:.1f}"
