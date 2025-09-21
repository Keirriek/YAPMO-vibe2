"""Test Directory Traverse Page voor YAPMO applicatie."""

import asyncio
import json
import os
import time
import threading
from pathlib import Path
from typing import Any, Dict, Union, Optional
from multiprocessing import Value, Manager
from multiprocessing.queues import Queue as MPQueue

from nicegui import ui, run
from shutdown_manager import handle_exit_click
from theme import YAPMOTheme
from local_directory_picker import pick_directory
from config import get_param
from core.process_media_files import process_media_files
from core.logging_service import logging_service
import yapmo_globals as global_vars


class TestTraversePage:
    """Test directory traverse pagina van de YAPMO applicatie."""

    def __init__(self) -> None:
        """Initialize the test traverse page."""
        # Get the path to config.json (same directory as main.py)
        self.config_path = Path(__file__).parent.parent / "config.json"
        
        # Initialize UI element variables
        self.dir_input: Any = None
        self.start_scan_button: Any = None
        self.start_processing_button: Any = None
        self.total_files_label: Any = None
        self.media_files_label: Any = None
        self.sidecars_label: Any = None
        self.directories_label: Any = None
        self.details_button: Any = None
        self.scan_results = {
            "total_files": 0,
            "media_files": 0,
            "sidecars": 0,
            "directories": 0
        }
        
        # Define type for shared resources
        ThreadDict = Dict[str, Optional[threading.Thread]]
        SharedResources = Dict[str, Union[Optional[Value], Optional[ThreadDict]]]
        
        # Global variables for cleanup - using shared memory like app3
        self.shared_resources: SharedResources = {
            'progress': None,
            'running': None,
            'threads': {'ui': None, 'process': None}
        }
        
        # Traversal state
        self.traversing = False
        self.processing = False
        self.aborted = False
        
        # Processing timers
        self.scan_timer: Any = None
        self.processing_timer: Any = None
        
        # UI update interval will be loaded dynamically from config
        
        # Load file extensions from config for tracking
        self.image_extensions = get_param("extensions", "image_extensions")
        self.video_extensions = get_param("extensions", "video_extensions")
        self.sidecar_extensions = get_param("extensions", "sidecar_extensions")
        self.relevant_extensions = self.image_extensions + self.video_extensions + self.sidecar_extensions
        
        # File extension tracking
        self.file_extension_counts = {}
        
        # Initialize log messages
        self.log_messages: list[str] = []
        
        
        # Register abort handler
        global_vars.abort_manager.register_abort_handler("test_traverse", self._abort_processing)
        
        self._create_page()

    def _reset_progress_bars(self) -> None:
        """Reset progress bars and labels to initial state."""
        # Reset scan progress
        if hasattr(self, 'scan_spinner') and self.scan_spinner:
            self.scan_spinner.visible = False
        if hasattr(self, 'scan_progress_label') and self.scan_progress_label:
            self.scan_progress_label.text = "Ready to scan..."
        
        # Reset processing progress
        if hasattr(self, 'processing_progress_bar') and self.processing_progress_bar:
            self.processing_progress_bar.value = 0.0
        if hasattr(self, 'processing_progress_label') and self.processing_progress_label:
            self.processing_progress_label.text = "Processing: 0% (0/0 files processed)"

    def _cleanup_resources(self) -> None:
        """Cleanup function to handle shared resources - based on app3 implementation."""
        try:
            # First stop the running flag to signal threads to stop
            if self.shared_resources['running']:
                try:
                    self.shared_resources['running'].value = False
                except:
                    pass
            
            # Wait for threads to finish
            for thread_name, thread in self.shared_resources['threads'].items():
                try:
                    if thread and thread.is_alive():
                        thread.join(timeout=0.5)
                except:
                    pass
                finally:
                    self.shared_resources['threads'][thread_name] = None
            
            # Clean up shared progress
            if self.shared_resources['progress']:
                try:
                    self.shared_resources['progress'].value = 0
                    self.shared_resources['progress'] = None
                except:
                    pass
                
            # Ensure running flag is cleaned up
            self.shared_resources['running'] = None
            
            # Clear the shared resources
            self.shared_resources['threads'] = {'ui': None, 'process': None}
            self.shared_resources['progress'] = None
            self.shared_resources['running'] = None
            
            # Give a small delay to ensure cleanup is complete
            time.sleep(0.1)
        except Exception as e:
            ui.notify(f"Error during cleanup: {e}", type='negative')

    def _create_page(self) -> None:
        """Maak de test traverse pagina."""

        @ui.page("/test-traverse")
        def test_traverse_page() -> None:
            with YAPMOTheme.page_frame("Test Directory Traverse", exit_handler=handle_exit_click):
                self._create_content()

    def _load_search_path_from_config(self) -> str:
        """Load search_path from config.json."""
        try:
            with self.config_path.open(encoding="utf-8") as f:
                config = json.load(f)
            
            return str(config.get("paths", {}).get("search_path", ""))
            
        except FileNotFoundError:
            return get_param("paths", "search_path")
        except json.JSONDecodeError:
            return get_param("paths", "search_path")
        except KeyError:
            return get_param("paths", "search_path")

    def _create_content(self) -> None:
        """Maak de content van de test traverse pagina."""
        # Initialize page state
        self._initialize_page_state()

    def _initialize_page_state(self) -> None:
        """Initialize page state when page loads."""
        # Create the main UI card
        with ui.card().classes("w-full mb-6"):
            ui.label("Test Directory Traverse").classes("text-2xl font-bold mb-6")
            
            # Main content row
            with ui.row().classes("w-full gap-6"):
                # Left column - buttons and input
                with ui.column().classes("gap-4"):
                    # SELECT DIRECTORY button
                    YAPMOTheme.create_button(
                        "SELECT DIRECTORY",
                        self._select_directory,
                        "primary",
                        "lg"
                    )
                    
                    # START SCAN button
                    self.start_scan_button = YAPMOTheme.create_button(
                        "START SCAN",
                        self._start_scan,
                        "primary",
                        "lg"
                    )
                    
                    # START PROCESSING button
                    self.start_processing_button = YAPMOTheme.create_button(
                        "START PROCESSING",
                        self._start_processing,
                        "secondary",
                        "lg"
                    )
                    self.start_processing_button.disable()  # Disabled until scan is complete
                    
                
                # Right column - input field and results
                with ui.column().classes("gap-4 flex-1"):
                    # Search Directory input
                    with ui.column().classes("w-full gap-2"):
                        ui.label("Search Directory").classes("text-lg font-semibold")
                        # Load search path from config
                        search_path = self._load_search_path_from_config()
                        
                        self.dir_input = ui.input(
                            placeholder="Select directory...",
                            value=search_path
                        ).classes("w-full")
                        ui.separator()
                    
                    # Scan Complete results
                    with ui.column().classes("gap-2"):
                        ui.label("Scan Complete").classes("text-lg font-semibold")
                        with ui.row().classes("gap-6"):
                            # Total Files
                            with ui.column().classes("items-center"):
                                self.total_files_label = ui.label(str(self.scan_results["total_files"])).classes("text-3xl font-bold text-blue-600")
                                ui.label("Total Files").classes("text-sm")
                            
                            # Media Files
                            with ui.column().classes("items-center"):
                                self.media_files_label = ui.label(str(self.scan_results["media_files"])).classes("text-3xl font-bold text-blue-600")
                                ui.label("Media Files").classes("text-sm")
                            
                            # Sidecars
                            with ui.column().classes("items-center"):
                                self.sidecars_label = ui.label(str(self.scan_results["sidecars"])).classes("text-3xl font-bold text-blue-600")
                                ui.label("Sidecars").classes("text-sm")
                            
                            # Directories
                            with ui.column().classes("items-center"):
                                self.directories_label = ui.label(str(self.scan_results["directories"])).classes("text-3xl font-bold text-blue-600")
                                ui.label("Directories").classes("text-sm")
                        
                        # DETAILS button
                        self.details_button = YAPMOTheme.create_button(
                            "DETAILS",
                            self._show_details,
                            "info",
                            "lg"
                        )
                        # Disable details button initially
                        self.details_button.disable()
        
        # Create Progress and Log panel
        self._create_progress_log_panel()
        
        # Reset progress bars after UI is created
        self._reset_progress_bars()

    def _create_progress_log_panel(self) -> None:
        """Create the progress and log panel."""
        # Progress and Log Panel (Hele breedte - Wit met Donkere Blauwe Rand)
        progress_card_classes = (
            "w-full bg-white border-2 border-blue-800 rounded-lg shadow-lg"
        )
        with ui.card().classes(progress_card_classes), \
             ui.card_section().classes("w-full p-6"):
            ui.label("Progress and Log").classes(
                "text-xl font-semibold text-gray-800 mb-4")

            
            # Scan Progress Section
            with ui.column().classes("w-full mb-4"):
                ui.label("Scan Progress").classes("text-lg font-semibold text-gray-800 mb-2")
                self.scan_spinner = ui.spinner("Hourglass", size="lg").classes("mb-2")
                self.scan_progress_label = ui.label("Scanning files...").classes(
                    "text-sm text-gray-600 font-medium"
                )

            # Processing Progress Section
            with ui.column().classes("w-full mb-4"):
                ui.label("Processing Progress").classes("text-lg font-semibold text-gray-800 mb-2")
                self.processing_progress_bar = ui.linear_progress(
                    value=0.0,
                    show_value=False,
                    size="15px",
                    color="green",
                ).classes("w-full mb-2")
                self.processing_progress_label = ui.label("Processing: 0% (0/0 files processed)").classes(
                    "text-sm text-gray-600 font-medium"
                )
            

            # Log section
            ui.label("Log info:").classes(
                "text-gray-700 font-medium mb-2")

            # Log display area (volledige breedte en hoogte)
            log_area_classes = "w-full h-64 bg-gray-100 rounded-lg p-4 mb-4"
            self.log_scroll_area = ui.scroll_area().classes(log_area_classes)
            with self.log_scroll_area:
                self.log_column = ui.column().classes("w-full")

            # Control buttons
            with ui.row().classes("w-full items-center gap-4"):
                self.clear_log_button = YAPMOTheme.create_button(
                    "CLEAR LOG",
                    self._clear_log,
                    "secondary",
                    "md",
                )

    async def _select_directory(self) -> None:
        """Handle directory selection."""
        directory = await pick_directory()
        if directory and self.dir_input:
            self.dir_input.value = directory
            # Update config.json with new search path
            self._update_config_search_path(directory)
    
    def _update_config_search_path(self, new_path: str) -> None:
        """Update the search_path in config.json."""
        try:
            # Read current config
            with self.config_path.open(encoding="utf-8") as f:
                config = json.load(f)
            
            # Update search_path
            config["paths"]["search_path"] = new_path
            
            # Write back to config file
            with self.config_path.open("w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except FileNotFoundError:
            ui.notify(f"Config file not found: {self.config_path}", type="negative")
        except json.JSONDecodeError as e:
            ui.notify(f"Error reading config.json: {e}", type="negative")
        except KeyError:
            ui.notify("Error updating config.json: Key not found", type="negative")
    

    def _start_scan(self) -> None:
        """Handle start scan - directory traversal only."""
        if self.traversing:
            return  # Already traversing
        
        # Get directory from input
        directory = self.dir_input.value if self.dir_input else ""
        if not directory:
            ui.notify("Please select a directory first", type="negative")
            return
        
        # Check if directory exists
        if not os.path.exists(directory):
            ui.notify("Directory does not exist", type="negative")
            return
        
        # Start scanning process
        self._start_scanning_process(directory)
    
    def _start_scanning_process(self, directory: str) -> None:
        """Start directory scanning process using shared memory - based on app3 implementation."""
        # First clean up any existing resources
        self._cleanup_resources()
        
        # Set traversing state
        self.traversing = True
        
        ## DEBUG_OFF Log traversal start
        # logging_service.log("INFO", f"Starting file scan of directory: {directory}")
        
        # Initialize shared resources
        self.shared_resources['progress'] = Value('i', 0)
        self.shared_resources['running'] = Value('b', True)
        self.shared_resources['threads'] = {'ui': None, 'process': None}
        
        # Update button states
        if self.start_scan_button:
            self.start_scan_button.props("color=negative")
            self.start_scan_button.text = "Scanning..."
            self.start_scan_button.disable()
        if self.start_processing_button:
            self.start_processing_button.disable()
        
        # Enable abort button
        global_vars.abort_manager.set_processing_active(active=True)
        
        # Disable details button during traversal
        if self.details_button:
            self.details_button.disable()
        
        # Reset counters
        self.scan_results["total_files"] = 0
        self.scan_results["media_files"] = 0
        self.scan_results["sidecars"] = 0
        self.scan_results["directories"] = 0
        self.traverse_progress = 0
        self.traverse_media_files = 0
        self.traverse_sidecars = 0
        self.traverse_directories = 0
        
        # Reset file extension counts
        self.file_extension_counts = {}
        
        # Update UI labels
        if self.total_files_label:
            self.total_files_label.text = "0"
        if self.media_files_label:
            self.media_files_label.text = "0"
        if self.sidecars_label:
            self.sidecars_label.text = "0"
        if self.directories_label:
            self.directories_label.text = "0"
        
        # Reset progress bars before starting
        self._reset_progress_bars()
        
        # Start scan timer in main thread
        self._start_scan_timer()
        
        # Start traversal using run_in_executor for background thread
        asyncio.create_task(self._run_traversal_async(directory))
        # Processing
    def _start_processing(self) -> None:
        """Handle start processing - process scanned files."""
        if self.processing:
            return  # Already processing
        
        # Check if we have scan results
        if not self.scan_results.get("media_files", 0):
            ui.notify("Please scan a directory first", type="warning")
            return
        
        # Start processing process
        asyncio.create_task(self._start_processing_process())
    
    async def _start_processing_process(self) -> None:
        """Start media processing after scan completion using shared memory."""
        # Check for abort
        logging_service.log("DEBUG", "Starting processing process")#DEBUG_ON
        print("Starting processing process")#DEBUG_ON
        # Update UI immediately to show the DEBUG message
        self._display_log_queue()#DEBUG die moet eigenlijk niet nodig zijn.
        if self.aborted:
            return
            
        # Get directory from input
        directory = self.dir_input.value if self.dir_input else ""
        if not directory:
            return
        
        # Initialize shared resources if needed
        if not self.shared_resources['progress']:
            self.shared_resources['progress'] = Value('i', 0)
        if not self.shared_resources['running']:
            self.shared_resources['running'] = Value('b', True)
        if not self.shared_resources['threads']:
            self.shared_resources['threads'] = {'ui': None, 'process': None}
        
        # Reset progress variables for real processing
        global_vars.progress_current = 0
        global_vars.progress_total_files = self.scan_results.get("media_files", 0)
        
        # Set processing state and progress total
        self.processing = True
        self.traverse_progress = self.scan_results.get("media_files", 0)
        
        # Update button states
        if self.start_scan_button:
            self.start_scan_button.disable()
        if self.start_processing_button:
            self.start_processing_button.props("color=negative")
            self.start_processing_button.text = "Processing..."
            self.start_processing_button.disable()
        
        # Sync global vars for processing
        global_vars.progress_current = 0
        global_vars.progress_total_files = self.traverse_progress
        
        # Update shared progress for media processing
        if self.shared_resources['progress']:
            with self.shared_resources['progress'].get_lock():
                self.shared_resources['progress'].value = 0
        
        # Reset processing progress bar
        if self.processing_progress_bar:
            self.processing_progress_bar.value = 0.0
        if self.processing_progress_label:
            self.processing_progress_label.text = f"Processing: 0% (0/{self.traverse_progress} files processed)"
        
        # Log media processing start with total files found
        total_files = self.scan_results.get("total_files", 0)
        logging_service.log("INFO", f"Starting file processing: {total_files} media files to process")
        
        # Start processing timer
        self._start_processing_timer()
        
        # Start processing using run_in_executor for background thread
        # This will print to terminal via the workers
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, process_media_files, directory
        )
        
        # Check for abort after processing using shared memory
        if self.shared_resources['running'] and not self.shared_resources['running'].value:
            return
        
        # Log results and print to console
        processed = result.get("processed_files", 0)
        successful = result.get("successful_files", 0)
        failed = result.get("failed_files", 0)
        total_time = result.get("total_processing_time", 0.0)
        
        # Calculate files per second
        files_per_second = processed / total_time if total_time > 0 else 0.0
        
        # Log completion
        logging_service.log("INFO", 
            f"File processing completed - Processed: {processed}, Successful: {successful}, "
            f"Failed: {failed}, Total time: {total_time:.4f}s, Files/sec: {files_per_second:.4f}")
        
        # Update final processing progress
        if self.processing_progress_bar:
            self.processing_progress_bar.value = 1.0  # 100%
        if self.processing_progress_label:
            self.processing_progress_label.text = f"Processing: Completed: 100% ({processed}/{processed} files processed)"
        
        # Reset processing state
        self.processing = False
        
        # Stop timers
        self._stop_scan_timer()
        self._stop_processing_timer()
        
        # Reset button states
        if self.start_scan_button:
            self.start_scan_button.enable()
        if self.start_processing_button:
            self.start_processing_button.enable()
            self.start_processing_button.props("color=primary")
            self.start_processing_button.text = "START PROCESSING"
        
        # Disable abort button
        global_vars.abort_manager.set_processing_active(active=False)
        
        # Clean up shared resources
        self._cleanup_resources()
    
    async def _run_traversal_async(self, directory: str) -> None:
        """Run traversal in background thread and handle completion."""
        # Start traversal using run_in_executor for background thread
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, self._traverse_directory_sync, directory
        )
        await self._on_traversal_complete(result)
    
    def _start_scan_timer(self) -> None:
        """Start UI update thread for scanning phase."""
        def update_scan_ui():
            """Update the UI elements during scanning using shared memory"""
            try:
                last_value = 0
                while self.traversing and not self.aborted:
                    try:
                        # Use shared_resources for consistent progress tracking
                        current_count = self.shared_resources['progress'].value if self.shared_resources['progress'] else 0
                            
                        if current_count != last_value:
                            # Update UI labels with current progress
                            if self.total_files_label:
                                self.total_files_label.text = str(current_count)
                            if self.media_files_label:
                                self.media_files_label.text = str(self.traverse_media_files)
                            if self.sidecars_label:
                                self.sidecars_label.text = str(self.traverse_sidecars)
                            if self.directories_label:
                                self.directories_label.text = str(self.traverse_directories)
                            
                            # Show scan spinner and update label
                            if self.scan_spinner:
                                self.scan_spinner.visible = True
                            if self.scan_progress_label:
                                self.scan_progress_label.text = f"Scanning... {current_count} files found"
                            
                            # Display log messages from queue
                            self._display_log_queue()
                            
                            last_value = current_count
                        
                        time.sleep(get_param("processing", "ui_update") / 1000.0)  # Convert to seconds
                    except AttributeError:
                        # Resources have been cleaned up, exit thread
                        break
                    except Exception as e:
                        logging_service.log("WARNING", f"Error in scan UI update: {e}")
                        break
                
                # Final update when scan completes
                try:
                    time.sleep(0.5)  # Give time for final messages
                    
                    final_count = self.shared_resources['progress'].value if self.shared_resources['progress'] else 0
                    
                    # Final scan progress
                    if self.scan_spinner:
                        self.scan_spinner.visible = False
                    if self.scan_progress_label:
                        if self.aborted:
                            self.scan_progress_label.text = f"Scan: Aborted - {final_count} files found"
                        else:
                            self.scan_progress_label.text = f"Scan: Completed - {final_count} files found"
                    
                    self._display_log_queue()
                except Exception as e:
                    logging_service.log("WARNING", f"Error in final scan update: {e}")
                    
            except Exception as e:
                logging_service.log("WARNING", f"Error in scan UI update thread: {e}")
        
        # Start the scan UI update thread
        self.scan_timer = threading.Thread(target=update_scan_ui, daemon=True)
        self.scan_timer.start()
    
    def _start_processing_timer(self) -> None:
        """Start UI update thread for processing phase."""
        def update_processing_ui():
            """Update the UI elements during processing using shared memory"""
            try:
                last_value = 0
                while self.processing and not self.aborted:
                    try:
                        # Use shared_resources for consistent progress tracking
                        current_count = self.shared_resources['progress'].value if self.shared_resources['progress'] else 0
                        # Use scan results for total count
                        total_count = self.scan_results.get("media_files", 0)
                            
                        if current_count != last_value:
                            # Update UI labels with current progress
                            if self.total_files_label:
                                self.total_files_label.text = str(current_count)
                            if self.media_files_label:
                                self.media_files_label.text = str(self.traverse_media_files)
                            if self.sidecars_label:
                                self.sidecars_label.text = str(self.traverse_sidecars)
                            if self.directories_label:
                                self.directories_label.text = str(self.traverse_directories)
                            
                            # Update processing progress
                            if total_count > 0:
                                progress_value = current_count / total_count
                                percentage = int(progress_value * 100)
                                
                                if self.processing_progress_bar:
                                    self.processing_progress_bar.value = progress_value
                                if self.processing_progress_label:
                                    self.processing_progress_label.text = f"Processing: {percentage}% ({current_count}/{total_count} files processed)"
                            
                            # Display log messages from queue
                            self._display_log_queue()
                            
                            last_value = current_count
                        
                        time.sleep(get_param("processing", "ui_update") / 1000.0)  # Convert to seconds
                    except AttributeError:
                        # Resources have been cleaned up, exit thread
                        break
                    except Exception as e:
                        logging_service.log("WARNING", f"Error in processing UI update: {e}")
                        break
                
                # Final update when processing completes
                try:
                    time.sleep(0.5)  # Give time for final messages
                    
                    final_count = self.shared_resources['progress'].value if self.shared_resources['progress'] else 0
                    total_count = self.scan_results.get("media_files", 0)
                    
                    if total_count > 0:
                        progress_value = final_count / total_count
                        percentage = int(progress_value * 100)
                        
                        # Final processing progress
                        if self.processing_progress_bar:
                            self.processing_progress_bar.value = progress_value
                        if self.processing_progress_label:
                            if self.aborted:
                                self.processing_progress_label.text = f"Processing: Aborted: {percentage}% ({final_count}/{total_count} files processed)"
                            else:
                                self.processing_progress_label.text = f"Processing: Completed: {percentage}% ({final_count}/{total_count} files processed)"
                    
                    self._display_log_queue()
                except Exception as e:
                    logging_service.log("WARNING", f"Error in final processing update: {e}")
                    
            except Exception as e:
                logging_service.log("WARNING", f"Error in processing UI update thread: {e}")
        
        # Start the processing UI update thread
        self.processing_timer = threading.Thread(target=update_processing_ui, daemon=True)
        self.processing_timer.start()
    
    def _stop_scan_timer(self) -> None:
        """Stop the scan timer."""
        if hasattr(self, 'scan_timer') and self.scan_timer:
            # Thread will stop automatically when traversing becomes False
            self.scan_timer = None
    
    def _stop_processing_timer(self) -> None:
        """Stop the processing timer."""
        if hasattr(self, 'processing_timer') and self.processing_timer:
            # Thread will stop automatically when processing becomes False
            self.processing_timer = None
    
    
    def _abort_processing(self) -> None:
        """Abort current processing - based on app3 implementation."""
        # Set the global abort flag
        self.aborted = True
        self.traversing = False
        self.processing = False
        
        # Stop the running flag to signal threads to stop
        if self.shared_resources['running'] and self.shared_resources['running'].value:
            self.shared_resources['running'].value = False
        
        # Stop timers
        self._stop_scan_timer()
        self._stop_processing_timer()
        
        # Disable abort button
        global_vars.abort_manager.set_processing_active(active=False)
        
        # Log abort
        logging_service.log("WARNING", "Processing aborted by user")

        
        
        # Reset progress bars
        self._reset_progress_bars()
        
        # Reset button states
        if self.start_scan_button:
            self.start_scan_button.props("color=primary")
            self.start_scan_button.text = "START SCAN"
            self.start_scan_button.enable()
        if self.start_processing_button:
            self.start_processing_button.disable()
            self.start_processing_button.props("color=secondary")
            self.start_processing_button.text = "START PROCESSING"
    
    def _traverse_directory_sync(self, directory: str) -> dict:
        """Traverse directory synchronously in background thread using shared memory."""
        try:
            # Get file extensions from config
            image_extensions = get_param("extensions", "image_extensions")
            video_extensions = get_param("extensions", "video_extensions")
            sidecar_extensions = get_param("extensions", "sidecar_extensions")
            
            # Initialize counters
            total_files = 0
            media_files = 0
            sidecars = 0
            directories = 0
            scanned_files = 0  # Counter for real-time progress
            
            # Use os.walk() for recursive directory traversal
            for root, dirs, files in os.walk(directory):
                # Check for abort using shared memory
                if self.shared_resources['running'] and not self.shared_resources['running'].value:
                    break
                    
                try:
                    # Update counters
                    total_files += len(files)
                    directories += 1
                    
                    # Count media files and sidecars
                    for file in files:
                        # Check for abort using shared memory
                        if self.shared_resources['running'] and not self.shared_resources['running'].value:
                            break
                            
                        file_ext = os.path.splitext(file)[1].lower()
                        
                        # Track file extension counts (only relevant extensions)
                        if file_ext in self.relevant_extensions:
                            if file_ext in self.file_extension_counts:
                                self.file_extension_counts[file_ext] += 1
                            else:
                                self.file_extension_counts[file_ext] = 1
                        
                        # Check if it's a media file (image or video)
                        if file_ext in image_extensions or file_ext in video_extensions:
                            media_files += 1
                        
                        # Check if it's a sidecar file
                        elif file_ext in sidecar_extensions:
                            sidecars += 1
                        
                        # Increment scanned files counter and update progress
                        scanned_files += 1
                        if self.shared_resources['progress']:
                            with self.shared_resources['progress'].get_lock():
                                self.shared_resources['progress'].value = scanned_files
                    
                    # Update instance variables for other UI elements
                    self.traverse_progress = total_files
                    self.traverse_media_files = media_files
                    self.traverse_sidecars = sidecars
                    self.traverse_directories = directories
                    
                except (PermissionError, OSError):
                    # Skip directories that can't be accessed
                    continue
            
            # Return final results
            return {
                "total_files": total_files,
                "media_files": media_files,
                "sidecars": sidecars,
                "directories": directories,
            }
            
        except Exception as e:
            return {"error": str(e)}

    async def _on_traversal_complete(self, result: dict) -> None:
        """Handle traversal completion - based on app3 implementation."""
        # Stop the running flag
        if self.shared_resources['running']:
            self.shared_resources['running'].value = False
        
        if result and "error" in result:
            logging_service.log("ERROR", f"Error during traversal: {result['error']}")
            ui.notify(f"Error during traversal: {result['error']}", type="negative")
        else:
            # Update scan results with final values
            self.scan_results.update(result)
            
            # Log completion with summary
            total_files = result.get("total_files", 0)
            media_files = result.get("media_files", 0)
            sidecars = result.get("sidecars", 0)
            directories = result.get("directories", 0)
            logging_service.log("INFO", 
                f"File scan completed - Total files: {total_files}, Media files: {media_files}, "
                f"Sidecars: {sidecars}, Directories: {directories}")
        
        # Reset traversing state
        self.traversing = False
        
        # Final UI update
        self._update_final_results()
        
        # Update button states - enable processing button if scan was successful
        if self.start_scan_button:
            self.start_scan_button.props("color=primary")
            self.start_scan_button.text = "START SCAN"
            self.start_scan_button.enable()
        
        if self.start_processing_button and result and not result.get("error"):
            self.start_processing_button.enable()
            self.start_processing_button.props("color=primary")
            self.start_processing_button.text = "START PROCESSING"
        
        # Disable abort button
        global_vars.abort_manager.set_processing_active(active=False)
        
        # Enable details button when scan data is available
        if self.details_button and self.file_extension_counts:
            self.details_button.enable()
        
        # Scan is complete, processing button is now enabled


    def _update_final_results(self) -> None:
        """Update UI with final results (no traversing check)."""
        # Update UI labels with final counter values
        if self.total_files_label:
            self.total_files_label.text = str(self.scan_results["total_files"])
        if self.media_files_label:
            self.media_files_label.text = str(self.scan_results["media_files"])
        if self.sidecars_label:
            self.sidecars_label.text = str(self.scan_results["sidecars"])
        if self.directories_label:
            self.directories_label.text = str(self.scan_results["directories"])
        
        # Update scan progress with final values
        total_files = self.scan_results["total_files"]
        if self.scan_spinner:
            self.scan_spinner.visible = False
        if self.scan_progress_label and total_files > 0:
            self.scan_progress_label.text = f"Scan: Completed - {total_files} files found"

    def _show_details(self) -> None:
        """Show file type details in a popup."""
        if not self.file_extension_counts:
            ui.notify("No scan data available. Please scan a directory first.", type="info")
            return

        with ui.dialog() as dialog, ui.card().classes("w-96 h-96"):
            ui.label("FILETYPES FOUND").classes("text-xl font-bold text-white mb-4")

            # Table with file types
            with ui.scroll_area().classes("w-full h-64"), \
                 ui.column().classes("w-full"):
                # Header row
                row_classes = "w-full font-bold text-white bg-blue-400 p-2"
                with ui.row().classes(row_classes):
                    ui.label("File type").classes("flex-1")
                    ui.label("Found").classes("w-20 text-right")

                # Data rows - only relevant extensions, sorted alphabetically
                relevant_items = [
                    (ext, count) for ext, count in self.file_extension_counts.items()
                    if ext.lower() in self.relevant_extensions
                ]
                sorted_items = sorted(relevant_items)

                for ext, count in sorted_items:
                    data_row_classes = "w-full p-2 border-b border-gray-600"
                    with ui.row().classes(data_row_classes):
                        ui.label(str(ext)).classes("flex-1 text-black-400")
                        ui.label(str(count)).classes("w-20 text-right text-blue-400")

            # Close button
            ui.button("CLOSE", on_click=dialog.close).classes(
                "bg-gray-600 text-white px-4 py-2 rounded-lg mt-4")

        dialog.open()

    def _clear_log(self) -> None:
        """Clear the log display."""
        try:
            if self.log_column:
                # Clear local log messages
                if hasattr(self, "log_messages"):
                    self.log_messages = []
                
                # Clear UI display
                self.log_column.clear()
        except Exception as e:
            logging_service.log("WARNING", f"Log clear error: {e}")

    def _display_log_queue(self) -> None:
        """Display all messages from logging service queue in UI."""
        try:
            new_messages = logging_service.get_ui_messages()  # Get and clear queue
            
            if new_messages and self.log_column:
                # Add new messages to display queue
                if not hasattr(self, "log_messages"):
                    self.log_messages = []
                
                for msg_data in new_messages:
                    # Safe timestamp extraction
                    timestamp = msg_data.get("timestamp", "")
                    if " " in timestamp:
                        timestamp = timestamp.split(" ")[1]
                    else:
                        timestamp = timestamp
                    
                    formatted_message = (
                        f"[{timestamp}] {msg_data.get('level', 'INFO')}: {msg_data.get('message', '')}"
                    )
                    self.log_messages.insert(0, formatted_message)  # Newest on top
                
                # Redraw all messages
                self.log_column.clear()
                with self.log_column:
                    for msg in self.log_messages:
                        ui.label(msg).classes("text-sm text-gray-700 font-mono")
                        
        except Exception as e:
            logging_service.log("WARNING", f"Log display error: {e}")



def create_test_traverse_page() -> TestTraversePage:
    """Maak de test traverse pagina."""
    return TestTraversePage()
