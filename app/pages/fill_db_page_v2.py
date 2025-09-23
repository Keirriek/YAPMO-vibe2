"""Fill Database V2 Page - Gestructureerde scan process pagina voor YAPMO applicatie."""

import os
import asyncio
import threading
import queue
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from nicegui import ui
from shutdown_manager import handle_exit_click
from local_directory_picker import pick_directory
from theme import YAPMOTheme
from config import get_param, set_param
import yapmo_globals
from pages.debug.fill_db_page_v2_debug import FillDbPageV2Debug
from core.logging_service_v2 import logging_service
from core.result_processor import ResultProcessor
from worker_functions import process_media_file, process_media_files_batch


class UIUpdateManager:
    """Simple UI update manager for real-time progress tracking."""
    
    def __init__(self, update_interval: float, state_provider=None) -> None:
        """Initialize the UI update manager."""
        self.update_interval = update_interval
        self.timer_active = False
        self.update_callbacks = []
        self.shared_data = {}
        self.lock = threading.Lock()
        self.state_provider = state_provider  # Function to get current state
    
    def register_callback(self, callback_func, data_key: str = None) -> None:
        """Register a callback function for UI updates."""
        self.update_callbacks.append({
            'callback': callback_func,
            'data_key': data_key
        })
    
    def update_shared_data(self, key: str, value) -> None:
        """Thread-safe update of shared data."""
        with self.lock:
            self.shared_data[key] = value
    
    def get_shared_data(self, key: str = None):
        """Thread-safe get of shared data."""
        with self.lock:
            if key is None:
                return self.shared_data.copy()
            return self.shared_data.get(key)
    
    def start_updates(self) -> None:
        """Start UI updates."""
        if not self.timer_active:
            self.timer_active = True
            self._schedule_update()
    
    def stop_updates(self) -> None:
        """Stop UI updates."""
        self.timer_active = False
    
    def _schedule_update(self) -> None:
        """Schedule the next UI update."""
        def update_ui():
                
            # if not self.timer_active:#JM De restart wel/niet gebeurt toch al
            #     return
            # Call all registered callbacks
            for callback_info in self.update_callbacks:
                try:
                    data_key = callback_info.get('data_key')
                    if data_key:
                        data = self.get_shared_data(data_key)
                        if data is not None:
                            callback_info['callback'](data)
                    else:
                        callback_info['callback']()
                except Exception as e:
                    print(f"Error in UI update callback: {e}")
            
            # Schedule next update
            if self.timer_active:
                ui.timer(self.update_interval, update_ui, once=True)
        
        ui.timer(self.update_interval, update_ui, once=True)


class ParallelWorkerManager:
    """Manager for parallel file processing workers."""
    
    def __init__(self, max_workers: int, progress_callback: Optional[Callable] = None) -> None:
        """Initialize the parallel worker manager."""
        self.max_workers = max_workers
        self.progress_callback = progress_callback
        self.executor = ProcessPoolExecutor(max_workers=max_workers)
        self.result_queue = queue.Queue()  # Worker resultaten
        self.logging_queue = queue.Queue()  # Log messages
        self.pending_futures = []
        self.worker_stats = {}  # Per worker statistieken
        self.lock = threading.Lock()
        self.is_running = False
        self.total_files = 0
        self.files_processed = 0
        self.directories_processed = 0
        self.start_time = None
        
    def start_workers(self) -> None:
        """Start the worker processes."""
        self.is_running = True
        self.start_time = time.time()
        # logging_service.log("DEBUG", f"Started parallel worker manager with {self.max_workers} workers")#DEBUG_OFF Started parallel worker manager with 20 workers
    
    def stop_workers(self) -> None:
        """Stop the worker processes."""
        self.is_running = False
        # Cancel pending futures
        for future in self.pending_futures:
            future.cancel()
        self.pending_futures.clear()
        self.executor.shutdown(wait=True)  # Wait for cleanup to prevent semaphore leaks
        # logging_service.log("DEBUG", "Stopped parallel worker manager")#DEBUG_OFF Stopped parallel worker manager
    
    def submit_file(self, file_path: str, worker_id: int) -> None:
        """Submit file to worker process."""
        if not self.is_running:
            return
            
        future = self.executor.submit(process_media_file, file_path, worker_id)
        self.pending_futures.append(future)
    
    def submit_files_batch(self, file_paths: List[str], worker_id: int) -> None:
        """Submit multiple files to worker process (batch processing for better ExifTool performance)."""
        if not self.is_running or not file_paths:
            return
            
        future = self.executor.submit(process_media_files_batch, file_paths, worker_id)
        self.pending_futures.append(future)
        
    def process_completed_workers(self) -> None:
        """Process completed worker results."""
        completed_futures = []
        
        for future in self.pending_futures[:]:
            if future.done():
                try:
                    result = future.result()
                    self._process_worker_result(result)
                    completed_futures.append(future)
                except Exception as e:
                    logging_service.log("ERROR", f"Worker failed: {str(e)}")
                    completed_futures.append(future)
        
        # Remove completed futures
        for future in completed_futures:
            self.pending_futures.remove(future)
    
    def _process_worker_result(self, result) -> None:
        """Process a single worker result or batch of results."""
        # Handle both single results and batch results
        if isinstance(result, list):
            # Batch result - process each result in the batch
            for single_result in result:
                self._process_single_result(single_result)
        else:
            # Single result - process directly
            self._process_single_result(result)
    
    def _process_single_result(self, result: Dict[str, Any]) -> None:
        """Process a single worker result."""
        with self.lock:
            self.files_processed += 1
            if result.get('success', False):
                self.directories_processed += 1
            
            # Update worker stats
            worker_id = result.get('worker_id', 0)
            if worker_id not in self.worker_stats:
                self.worker_stats[worker_id] = {
                    'files_processed': 0,
                    'success_count': 0,
                    'total_time': 0.0
                }
            
            self.worker_stats[worker_id]['files_processed'] += 1
            if result.get('success', False):
                self.worker_stats[worker_id]['success_count'] += 1
            self.worker_stats[worker_id]['total_time'] += result.get('processing_time', 0.0)
            
            # Process log messages
            for log_msg in result.get('log_messages', []):
                self.logging_queue.put(log_msg)
            
            # Add result to result queue for ResultProcessor
            self.result_queue.put(result)
            
            # Update progress
            if self.progress_callback:
                progress_data = self._get_progress_data()
                self.progress_callback(progress_data)
    
    def _get_progress_data(self) -> Dict[str, Any]:
        """Get current progress data."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        progress = (self.files_processed / self.total_files * 100) if self.total_files > 0 else 0
        files_per_sec = self.files_processed / elapsed if elapsed > 0 else 0
        dirs_per_sec = self.directories_processed / elapsed if elapsed > 0 else 0
        time_to_finish = (self.total_files - self.files_processed) / files_per_sec if files_per_sec > 0 else 0
        
        return {
            'progress': progress,
            'files_processed': self.files_processed,
            'directories_processed': self.directories_processed,
            'files_per_sec': files_per_sec,
            'directories_per_sec': dirs_per_sec,
            'time_to_finish': time_to_finish
        }
    
    def is_complete(self) -> bool:
        """Check if all workers are complete."""
        return len(self.pending_futures) == 0
    
    def get_final_stats(self) -> Dict[str, Any]:
        """Get final processing statistics."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        return {
            'files_processed': self.files_processed,
            'directories_processed': self.directories_processed,
            'files_per_sec': self.files_processed / elapsed if elapsed > 0 else 0,
            'directories_per_sec': self.directories_processed / elapsed if elapsed > 0 else 0,
            'elapsed_time': elapsed,
            'worker_stats': self.worker_stats
        }


# dummy_worker_process moved to worker_functions.py


class ApplicationState(Enum):
    """Application state enum for UI state machine."""
    INITIALISATION = "initialisation"
    IDLE = "idle"
    SCANNING = "scanning"
    IDLE_SCAN_DONE = "idle_scan_done"
    PROCESSING = "processing"
    IDLE_ACTION_DONE = "idle_action_done"
    ABORTED = "aborted"
    EXIT_PAGE = "exit_page"


class FillDbPageV2:
    """Fill Database V2 pagina van de YAPMO applicatie."""

    def __init__(self) -> None:
        """Initialize the fill database v2 page."""
        # Initialize application state
        self.current_state = ApplicationState.INITIALISATION
        
        # Initialize debug helper
        self.debug_helper = FillDbPageV2Debug(self)
        
        # Initialize UI update manager
        update_interval = get_param("processing", "ui_update") / 1000.0  # Convert ms to seconds
        self.ui_update_manager = UIUpdateManager(update_interval)
        
        # Initialize extension counts for details popup
        self.extension_counts = {}
        
        # Initialize parallel worker manager
        self.worker_manager: Optional[ParallelWorkerManager] = None
        self.result_processor: Optional[ResultProcessor] = None
        
        # Initialize timer tracking
        self.active_timers = []
        
        # Register cleanup on exit
        import atexit
        atexit.register(self._cleanup_on_exit)
        
        # Initialize UI elements as None
        # Logging section
        self.log_area: ui.scroll_area | None = None
        self.log_column: ui.column | None = None
        self.log_clear_button: ui.button | None = None
        
        # Scan section
        self.scan_select_directory: ui.button | None = None
        self.scan_search_directory_input: ui.input | None = None
        self.scan_start_button: ui.button | None = None
        self.scan_spinner: ui.spinner | None = None
        self.scan_state_label: ui.label | None = None
        self.scan_total_files_label: ui.label | None = None
        self.scan_media_files_label: ui.label | None = None
        self.scan_sidecars_label: ui.label | None = None
        self.scan_total_directories_label: ui.label | None = None
        self.scan_details_button: ui.button | None = None
        
        # Processing section
        self.processing_start_button: ui.button | None = None
        self.processing_progressbar: ui.linear_progress | None = None
        self.processing_progress_label: ui.label | None = None
        self.processing_files_processed_label: ui.label | None = None
        self.processing_directories_processed_label: ui.label | None = None
        self.processing_files_sec_label: ui.label | None = None
        self.processing_directories_sec_label: ui.label | None = None
        self.processing_time_to_finish_label: ui.label | None = None
        
        # Debug section
        self.debug_current_state_label: ui.label | None = None
        self.debug_start_ui_btn: ui.button | None = None
        self.debug_stop_ui_btn: ui.button | None = None
        self.debug_status_ui_label: ui.label | None = None
        self.debug_log_input: ui.input | None = None
        self.debug_add_log_btn: ui.button | None = None
        self.debug_show_queue_btn: ui.button | None = None
        self.debug_queue_count_label: ui.label | None = None
        self.debug_direct_update_btn: ui.button | None = None
        self.debug_counter_label: ui.label | None = None
        # Flag status labels
        self.debug_ui_update_timer_label: ui.label | None = None
        self.debug_ui_update_finished_label: ui.label | None = None
        self.debug_action_finished_label: ui.label | None = None
        self.debug_ui_finished_label: ui.label | None = None
        
        # Create the page
        self._create_page()

    def _create_page(self) -> None:
        """Create the fill database v2 page."""

        @ui.page("/fill-db-page-v2")
        def fill_db_page_v2() -> None:
            with YAPMOTheme.page_frame(
                "Fill Database V2",
                exit_handler=handle_exit_click,
            ):
                self._create_content()
                # Configure UI for initial state after UI elements are created
                self._set_state(self.current_state)
                
                # Simulate initialization process and transition to IDLE
                timer = ui.timer(0.5, self._initialize_page, once=True)
                self.active_timers.append(timer)

    def _create_content(self) -> None:
        """Create the content of the fill database v2 page."""
        self._create_logging_section()
        self._create_scan_section()
        self._create_debug_section()

    def _create_logging_section(self) -> None:
        """Create the logging section with log area and clear button."""
        with ui.card().classes("w-full bg-white rounded-lg mb-6"), ui.card_section().classes("w-full p-6"):
            ui.label("Progress and Log").classes("text-xl font-semibold text-gray-800 mb-4")
            
            # Log section
            ui.label("Log info:").classes("text-grey-700 font-medium mb-2")
            
            # Log display area
            log_area_classes = "h-64 bg-gray-100 rounded-lg p-4 mb-4"
            self.log_area = ui.scroll_area().classes(log_area_classes)
            with self.log_area:
                self.log_column = ui.column().classes("w-full")
            
            # Control buttons
            with ui.row().classes("w-full items-center gap-4"):
                self.log_clear_button = YAPMOTheme.create_button(
                    "CLEAR LOG",
                    self._clear_log,
                    "secondary",
                    "md",
                )

    def _create_scan_section(self) -> None:
        """Create the scanning section with directory input and scan results."""
        with ui.card().classes("w-full bg-white rounded-lg mb-6"), ui.card_section():
            ui.label("Scanning").classes("text-xl font-bold mb-4")
            
            with ui.row().classes("gap-6"):
                # Left side - Buttons (like Test Directory Traverse)
                with ui.column().classes("gap-4"):
                    self.scan_select_directory = YAPMOTheme.create_button(
                        "SELECT DIRECTORY",
                        self._select_directory,
                        "secondary",
                        "lg",
                    )
                    
                    self.scan_start_button = YAPMOTheme.create_button(
                        "START Scanning",
                        self._start_scanning,
                        "primary",
                        "lg",
                    )
                
                # Right side - Content
                # Search Directory section
                with ui.row().classes("flex-1 gap-4"):
                    with ui.column().classes("flex-1"):
                        ui.label("Search Directory").classes("text-lg font-bold mb-2")
                        self.scan_search_directory_input = ui.input(
                            placeholder="Enter directory path...",
                            value=get_param("paths", "search_path")
                        ).classes("w-full").on('change', self._on_directory_input_changed)
                    
                    # Hourglass spinner
                    with ui.column().classes("items-center justify-center"):
                        with ui.row().classes("justify-end w-full"):
                            self.scan_spinner = ui.spinner("hourglass", size="xl", color="red")
                            self.scan_spinner.set_visibility(False)
                
                # Horizontal line separator
                ui.separator().classes("my-4")
                
                # Scan Complete section
                with ui.row().classes("gap-6"):
                    # Left column - Details button (same width as START Scanning)
                    with ui.column().classes("w-48 gap-4"):
                        self.scan_details_button = YAPMOTheme.create_button(
                            "DETAILS",
                            self._show_details,
                            "secondary",
                            "lg",
                        )
                        # Disable details button initially
                        self.scan_details_button.disable()
                    
                    # Right column - Scan Complete content
                    with ui.column().classes("flex-1"):
                        with ui.row().classes("w-full gap-2 mb-2"):
                            ui.label("Scan status").classes("text-lg font-bold")
                            self.scan_state_label = ui.label("not active").classes("text-lg font-bold")
                        
                        # File count labels in one row
                        with ui.row().classes("gap-4"):
                            self.scan_total_files_label = ui.label("0").classes("text-4xl font-bold text-blue-600")
                            ui.label("Total Files").classes("text-sm")
                            
                            self.scan_media_files_label = ui.label("0").classes("text-4xl font-bold text-blue-600")
                            ui.label("Media Files").classes("text-sm")
                            
                            self.scan_sidecars_label = ui.label("0").classes("text-4xl font-bold text-blue-600")
                            ui.label("Sidecars").classes("text-sm")
                            
                            self.scan_total_directories_label = ui.label("0").classes("text-4xl font-bold text-blue-600")
                            ui.label("Directories").classes("text-sm")

                # Processing section (UI elements only, no functionality)
                ui.separator().classes("my-4")
            ui.label("File Processing").classes("text-xl font-bold mb-4")
            with ui.row().classes("gap-4"):
                # Start Processing button
                self.processing_start_button = YAPMOTheme.create_button(
                    "START PROCESSING",
                    self._start_processing,
                    "primary",
                    "lg",
                )
                
                # Processing Progress section
                with ui.column().classes("flex-1"):
                    ui.label("Processing Progress").classes("text-lg font-bold mb-2")
                    
                    # Progress bar
                    self.processing_progressbar = ui.linear_progress(
                        value=0.0,
                        show_value=False,
                        size="20px",
                        color="blue",
                    ).classes("w-full mb-2")
                    
                    # Progress info
                    self.processing_progress_label = ui.label(
                            "Processing: 0%"
                    ).classes("text-gray-700 font-medium")
                    
                    # File processing count labels in one row
                    with ui.row().classes("gap-4"):
                        with ui.column():
                            ui.label("Files Processed").classes("text-sm")
                            self.processing_files_processed_label = ui.label("0").classes("text-4xl font-bold text-blue-600")
                        with ui.column():
                            ui.label("Directories Processed").classes("text-sm")
                            self.processing_directories_processed_label = ui.label("0").classes("text-4xl font-bold text-blue-600")
                        with ui.column():
                            ui.label("Files/sec").classes("text-sm")
                            self.processing_files_sec_label = ui.label("0").classes("text-4xl font-bold text-blue-600")
                        with ui.column():
                            ui.label("Directories/sec").classes("text-sm")
                            self.processing_directories_sec_label = ui.label("0").classes("text-4xl font-bold text-blue-600")
                        with ui.column():
                            ui.label("Estimated time to finish").classes("text-sm")
                            self.processing_time_to_finish_label = ui.label("0").classes("text-4xl font-bold text-blue-600")

    def _create_debug_section(self) -> None:
        """Create the debug section using debug helper."""
        self.debug_helper.create_debug_section()
        

    def _set_state(self, new_state: ApplicationState) -> None:
        """Set application state and configure all UI elements."""
        self.current_state = new_state
        self._configure_ui_for_state(new_state)
        
        # Update debug state label and flags
        self.debug_helper.update_debug_state_label()
        self.debug_helper.update_debug_flags()

    def _configure_ui_for_state(self, state: ApplicationState) -> None:
        """Configure UI elements for the given state.
        
        IMPORTANT: NiceGUI button enabling vereist specifieke aanpak!
        - Eerst props(remove="disabled") om disabled property te verwijderen
        - Dan enable() aanroepen
        - Dan props("color=...") voor kleur
        - NiceGUI slaat disabled op als string 'false', niet boolean False
        - Dit geldt voor alle states - houd volgorde consistent!
        """
        if state == ApplicationState.INITIALISATION:
            # All buttons disabled
            if self.scan_select_directory:
                self.scan_select_directory.disable()
            if self.scan_start_button:
                self.scan_start_button.disable()
            if self.scan_details_button:
                self.scan_details_button.disable()
            if self.processing_start_button:
                self.processing_start_button.disable()
            if self.log_clear_button:
                self.log_clear_button.disable()
            
            # Input disabled
            if self.scan_search_directory_input:
                self.scan_search_directory_input.disable()
            
            # Spinner visible but inactive (black) for testing
            if self.scan_spinner:
                self.scan_spinner.set_visibility(True)
                # Note: NiceGUI spinner doesn't have direct color control, 
                # but it will be visible and inactive
            
            # State label
            if self.scan_state_label:
                self.scan_state_label.text = "Initializing..."
            
            # All counters reset to 0
            if self.scan_total_files_label:
                self.scan_total_files_label.text = "0"
            if self.scan_media_files_label:
                self.scan_media_files_label.text = "0"
            if self.scan_sidecars_label:
                self.scan_sidecars_label.text = "0"
            if self.scan_total_directories_label:
                self.scan_total_directories_label.text = "0"
            
            # Processing section reset
            if self.processing_progressbar:
                self.processing_progressbar.value = 0.0
                self.processing_progressbar.set_visibility(False)
            if self.processing_progress_label:
                self.processing_progress_label.text = "Processing: 0%"
            if self.processing_files_processed_label:
                self.processing_files_processed_label.text = "0"
            if self.processing_directories_processed_label:
                self.processing_directories_processed_label.text = "0"
            if self.processing_files_sec_label:
                self.processing_files_sec_label.text = "0"
            if self.processing_directories_sec_label:
                self.processing_directories_sec_label.text = "0"
            if self.processing_time_to_finish_label:
                self.processing_time_to_finish_label.text = "0"
            
            # Register abort handler (available from start)
            from yapmo_globals import abort_manager
            abort_manager.register_abort_handler("fill_db_page_v2", self._handle_abort)
            
            # Disable ABORT button (no process running yet)
            from theme import YAPMOTheme
            if hasattr(YAPMOTheme, 'abort_button') and YAPMOTheme.abort_button:
                YAPMOTheme.abort_button.disable()
                
        elif state == ApplicationState.SCANNING:
            # All controls disabled during scanning
            if self.scan_select_directory:
                self.scan_select_directory.disable()
                self.scan_select_directory.props("color=secondary disabled")
            if self.scan_start_button:
                self.scan_start_button.disable()
                self.scan_start_button.text = "SCANNING"
                self.scan_start_button.props("color=negative disabled")
            if self.scan_details_button:
                self.scan_details_button.disable()
            if self.processing_start_button:
                self.processing_start_button.disable()
            if self.log_clear_button:
                self.log_clear_button.disable()
            
            # Input disabled
            if self.scan_search_directory_input:
                self.scan_search_directory_input.disable()
            
            # Spinner visible and active (red color)
            if self.scan_spinner:
                self.scan_spinner.set_visibility(True)
                # Note: NiceGUI spinner doesn't have direct color control,
                # but it will be visible and active during scanning
            
            # State label
            if self.scan_state_label:
                self.scan_state_label.text = "scanning active"
            
            # ABORT button enabled and orange during scanning
            # Note: ABORT button is in header, configured by theme
            # We need to register our abort handler with the global abort manager
            from yapmo_globals import abort_manager
            abort_manager.register_abort_handler("fill_db_page_v2", self._handle_abort)
            
            # Enable ABORT button
            from theme import YAPMOTheme
            if hasattr(YAPMOTheme, 'abort_button') and YAPMOTheme.abort_button:
                YAPMOTheme.abort_button.enable()
                YAPMOTheme.abort_button.props("color=warning")
                
        elif state == ApplicationState.PROCESSING:
            # All scan controls disabled during processing
            if self.scan_select_directory:
                self.scan_select_directory.disable()
                self.scan_select_directory.props("color=secondary disabled")
            if self.scan_start_button:
                self.scan_start_button.disable()
                self.scan_start_button.props("color=primary disabled")
            if self.scan_details_button:
                self.scan_details_button.disable()
                self.scan_details_button.props("color=secondary disabled")
            if self.scan_search_directory_input:
                self.scan_search_directory_input.disable()
            
            # Processing controls active
            if self.processing_start_button:
                self.processing_start_button.disable()
                self.processing_start_button.text = "PROCESSING"
                self.processing_start_button.props("color=negative disabled")
            if self.processing_progressbar:
                self.processing_progressbar.set_visibility(True)
            
            # State label
            if self.scan_state_label:
                self.scan_state_label.text = "processing active"
            
            # ABORT button enabled and orange during processing
            from yapmo_globals import abort_manager
            abort_manager.register_abort_handler("fill_db_page_v2", self._handle_abort)
            
            # Enable ABORT button
            from theme import YAPMOTheme
            if hasattr(YAPMOTheme, 'abort_button') and YAPMOTheme.abort_button:
                YAPMOTheme.abort_button.enable()
                YAPMOTheme.abort_button.props("color=warning")
                
        elif state == ApplicationState.IDLE:
            # Stop UI update timer
            self._stop_ui_update()
            
            # Clean up all active timers
            self._cleanup_timers()
            
            # Clear all callbacks to prevent race conditions
            self.ui_update_manager.update_callbacks.clear()
            
            # Clear scan data (fresh start)
            if hasattr(self, 'scanned_files'):
                self.scanned_files = []
            if hasattr(self, 'last_scanned_directory'):
                self.last_scanned_directory = ""
            
            # Reset ALL flags
            yapmo_globals.action_finished_flag = False
            yapmo_globals.ui_update_finished = False
            yapmo_globals.abort_requested = False
            yapmo_globals.stop_processing_flag = False
            
            # Unregister abort handler
            from yapmo_globals import abort_manager
            abort_manager.unregister_abort_handler("fill_db_page_v2")
            
            # Disable ABORT button
            from theme import YAPMOTheme
            if hasattr(YAPMOTheme, 'abort_button') and YAPMOTheme.abort_button:
                YAPMOTheme.abort_button.disable()
            
            # Scan controls enabled
            if self.scan_select_directory:
                self.scan_select_directory.props(remove="disabled")
                self.scan_select_directory.enable()
                self.scan_select_directory.props("color=secondary")
            if self.scan_start_button:
                self.scan_start_button.props(remove="disabled")
                self.scan_start_button.enable()
                self.scan_start_button.text = "START Scanning"
                self.scan_start_button.props("color=primary")
            if self.scan_search_directory_input:
                self.scan_search_directory_input.enable()
            
            # Scan details always enabled
            if self.scan_details_button:
                self.scan_details_button.props(remove="disabled")
                self.scan_details_button.enable()
                self.scan_details_button.props("color=secondary")
            
            # Processing controls DISABLED (no scan data available)
            if self.processing_start_button:
                self.processing_start_button.disable()
                self.processing_start_button.text = "START PROCESSING"
                self.processing_start_button.props("color=primary")
            
            # Log controls enabled
            if self.log_clear_button:
                self.log_clear_button.enable()
            
            # Spinner hidden
            if self.scan_spinner:
                self.scan_spinner.set_visibility(False)
            
            # State label
            if self.scan_state_label:
                self.scan_state_label.text = "not active"
            
            # Keep counter values from previous scan (don't reset to 0)
            # Counters will show the last scan results
            
            # Processing section - behoud resultaten (don't reset to 0)
            # Progress bar en labels behouden hun waarden van laatste processing
            # Alleen visibility van progress bar aanpassen
            if self.processing_progressbar:
                self.processing_progressbar.set_visibility(False)  # Verberg progress bar
            # Alle andere processing labels behouden hun waarden
                
        elif state == ApplicationState.IDLE_SCAN_DONE:
            # Scan completed - processing enabled, scan data available
            # Stop UI update timer
            self._stop_ui_update()
            
            # Clean up all active timers
            self._cleanup_timers()
            
            # Clear all callbacks to prevent race conditions
            self.ui_update_manager.update_callbacks.clear()
            
            # Reset ALL flags
            yapmo_globals.action_finished_flag = False
            yapmo_globals.ui_update_finished = False
            yapmo_globals.abort_requested = False
            yapmo_globals.stop_processing_flag = False
            
            # Unregister abort handler
            from yapmo_globals import abort_manager
            abort_manager.unregister_abort_handler("fill_db_page_v2")
            
            # Disable ABORT button
            from theme import YAPMOTheme
            if hasattr(YAPMOTheme, 'abort_button') and YAPMOTheme.abort_button:
                YAPMOTheme.abort_button.disable()
            
            # Scan controls enabled
            if self.scan_select_directory:
                self.scan_select_directory.props(remove="disabled")
                self.scan_select_directory.enable()
                self.scan_select_directory.props("color=secondary")
            if self.scan_start_button:
                self.scan_start_button.props(remove="disabled")
                self.scan_start_button.enable()
                self.scan_start_button.text = "START Scanning"
                self.scan_start_button.props("color=primary")
            if self.scan_search_directory_input:
                self.scan_search_directory_input.enable()
            
            # Scan details enabled (scan data available)
            if self.scan_details_button:
                self.scan_details_button.props(remove="disabled")
                self.scan_details_button.enable()
                self.scan_details_button.props("color=secondary")
            
            # Processing controls ENABLED (scan data available!)
            if self.processing_start_button:
                self.processing_start_button.props(remove="disabled")
                self.processing_start_button.enable()
                self.processing_start_button.text = "START PROCESSING"
                self.processing_start_button.props("color=primary")
            
            # Log controls enabled
            if self.log_clear_button:
                self.log_clear_button.enable()
            
            # Spinner hidden
            if self.scan_spinner:
                self.scan_spinner.set_visibility(False)
            
            # State label
            if self.scan_state_label:
                self.scan_state_label.text = "scan complete"
            
            # Keep counter values from scan (show scan results)
            # Counters will show the scan results
            
            # Processing section - behoud resultaten (don't reset to 0)
            # Progress bar en labels behouden hun waarden van laatste processing
            # Alleen visibility van progress bar aanpassen
            if self.processing_progressbar:
                self.processing_progressbar.set_visibility(False)  # Verberg progress bar
            # Alle andere processing labels behouden hun waarden
                
        elif state == ApplicationState.IDLE_ACTION_DONE:
            # Unified action completion state
            # This state waits for ui_update_finished = True
            # Then resets flags and transitions to IDLE
            
            # All controls disabled during action completion
            if self.scan_select_directory:
                self.scan_select_directory.disable()
                self.scan_select_directory.props("color=secondary disabled")
            if self.scan_start_button:
                self.scan_start_button.disable()
            if self.processing_start_button:
                self.processing_start_button.disable()
            if self.log_clear_button:
                self.log_clear_button.disable()
            
            # Input disabled
            if self.scan_search_directory_input:
                self.scan_search_directory_input.disable()
            
            # State label
            if self.scan_state_label:
                self.scan_state_label.text = "Action completed"
            
            # Enable details button if scan data is available
            if self.scan_details_button and self.extension_counts:
                self.scan_details_button.props(remove="disabled")
                self.scan_details_button.enable()
                self.scan_details_button.props("color=secondary")
            
            # Register flag transition checker for this state only
            self.ui_update_manager.register_callback(
                self._check_action_flag_transition
            )
            
            # Keep abort handler registered (user can still abort)
            from yapmo_globals import abort_manager
            abort_manager.register_abort_handler("fill_db_page_v2", self._handle_abort)
            
            # Enable ABORT button (user can abort to reset)
            from theme import YAPMOTheme
            if hasattr(YAPMOTheme, 'abort_button') and YAPMOTheme.abort_button:
                YAPMOTheme.abort_button.enable()
                YAPMOTheme.abort_button.props("color=warning")
                
        elif state == ApplicationState.ABORTED:
            # Clean up all active timers first
            self._cleanup_timers()
            
            # All controls disabled
            if self.scan_select_directory:
                self.scan_select_directory.disable()
                self.scan_select_directory.props("color=secondary disabled")
            if self.scan_start_button:
                self.scan_start_button.disable()
                self.scan_start_button.text = "START Scanning"
                self.scan_start_button.props("color=primary disabled")
            if self.scan_details_button:
                self.scan_details_button.disable()
                self.scan_details_button.props("color=secondary disabled")
            if self.processing_start_button:
                self.processing_start_button.disable()
            if self.log_clear_button:
                self.log_clear_button.disable()
            if self.scan_search_directory_input:
                self.scan_search_directory_input.disable()
            
            # Spinner hidden
            if self.scan_spinner:
                self.scan_spinner.set_visibility(False)
            
            # State label - show abort message
            if self.scan_state_label:
                self.scan_state_label.text = "Aborting..."
            
            # Labels behouden hun waarden (niet resetten)
            
            # Register flag transition checker for this state only
            self.ui_update_manager.register_callback(
                self._check_action_flag_transition
            )
            
            # Start UI update timer for ABORTED state
            self._start_ui_update()
            
            # Unregister abort handler (abort is complete)
            from yapmo_globals import abort_manager
            abort_manager.unregister_abort_handler("fill_db_page_v2")
            
            # Disable ABORT button
            from theme import YAPMOTheme
            if hasattr(YAPMOTheme, 'abort_button') and YAPMOTheme.abort_button:
                YAPMOTheme.abort_button.disable()
                
        elif state == ApplicationState.EXIT_PAGE:
            # All controls disabled
            if self.scan_select_directory:
                self.scan_select_directory.disable()
            if self.scan_start_button:
                self.scan_start_button.disable()
            if self.scan_details_button:
                self.scan_details_button.disable()
            if self.processing_start_button:
                self.processing_start_button.disable()
            if self.log_clear_button:
                self.log_clear_button.disable()
            if self.scan_search_directory_input:
                self.scan_search_directory_input.disable()
            
            # Spinner hidden
            if self.scan_spinner:
                self.scan_spinner.set_visibility(False)
            
            # State label
            if self.scan_state_label:
                self.scan_state_label.text = "Saving state..."
            
            # All counters reset to 0
            if self.scan_total_files_label:
                self.scan_total_files_label.text = "0"
            if self.scan_media_files_label:
                self.scan_media_files_label.text = "0"
            if self.scan_sidecars_label:
                self.scan_sidecars_label.text = "0"
            if self.scan_total_directories_label:
                self.scan_total_directories_label.text = "0"
            
            # Processing section reset
            if self.processing_progressbar:
                self.processing_progressbar.value = 0.0
                self.processing_progressbar.set_visibility(False)
            if self.processing_progress_label:
                self.processing_progress_label.text = "Processing: 0%"
            if self.processing_files_processed_label:
                self.processing_files_processed_label.text = "0"
            if self.processing_directories_processed_label:
                self.processing_directories_processed_label.text = "0"
            if self.processing_files_sec_label:
                self.processing_files_sec_label.text = "0"
            if self.processing_directories_sec_label:
                self.processing_directories_sec_label.text = "0"
            if self.processing_time_to_finish_label:
                self.processing_time_to_finish_label.text = "0"
            
            # Unregister abort handler (exit page)
            from yapmo_globals import abort_manager
            abort_manager.unregister_abort_handler("fill_db_page_v2")
            
            # Disable ABORT button
            from theme import YAPMOTheme
            if hasattr(YAPMOTheme, 'abort_button') and YAPMOTheme.abort_button:
                YAPMOTheme.abort_button.disable()


    # Placeholder methods for button handlers
    def _clear_log(self) -> None:
        """Clear the log area."""
        try:
            if self.log_column:
                # Clear local log messages
                if hasattr(self, "log_messages"):
                    self.log_messages = []
                
                # Clear UI display
                self.log_column.clear()
        except Exception as e:
            ui.notify(f"Log clear error: {str(e)}", type="error")

    async def _select_directory(self) -> None:
        """Select directory for scanning."""
        selected_path = await pick_directory()
        if selected_path and self.scan_search_directory_input:
            self.scan_search_directory_input.value = selected_path
            # Save to config.json
            set_param("paths", "search_path", selected_path)
            # Trigger directory change detection
            self._on_directory_input_changed(None)

    def _start_scanning(self) -> None:
        """Start the scanning process."""
        # Reset extension counts for new scan
        self.extension_counts = {}
        
        # 1. EERSTE ACTIE: ExifTool check (VOOR directory validatie)
        if not self._check_exiftool_availability():
            return  # ExifTool not available, stay in IDLE state
        
        # 2. DAN: Transitie naar SCANNING state
        self._set_state(ApplicationState.SCANNING)
        
        # 3. DAN: Directory validatie
        current_path = self.scan_search_directory_input.value if self.scan_search_directory_input else ""
        is_valid, error_msg = self._validate_directory_path(current_path)
        
        if not is_valid:
            # UI message + waarde ONGEWIJZIGD + terug naar IDLE
            ui.notify(f"Directory validation failed: {error_msg}", type="error")
            # Clear flags on validation failure
            yapmo_globals.action_finished_flag = False
            yapmo_globals.ui_update_finished = False
            yapmo_globals.abort_requested = False  # Reset abort flag
            # GEEN reset van input waarde - blijft ongewijzigd!
            self._set_state(ApplicationState.IDLE)  # SCANNING → IDLE
            return  # IDLE state zorgt voor UI update stop!
        
        # 3. Validatie OK → clear flags and start UI update timer
        yapmo_globals.action_finished_flag = False
        yapmo_globals.abort_requested = False  # Reset abort flag for new scan
        self._start_ui_update()
        
        # 4. Start scanning proces
        # Save to config
        set_param("paths", "search_path", current_path)
        ui.notify("Scanning started", type="info")
        
        # Process any initial log messages
        self._display_log_queue()
        
        # Start async directory scanning
        timer = ui.timer(0.1, lambda: asyncio.create_task(self._run_scan_process(current_path)), once=True)
        self.active_timers.append(timer)

    def _on_directory_input_changed(self, event) -> None:
        """Called when directory input changes."""
        # Get the new directory value from the input field
        new_directory = self.scan_search_directory_input.value if self.scan_search_directory_input else ""
        #logging_service.log("DEBUG", f"Directory input changed to: {new_directory}")#DEBUG_OFF Directory input changed
        
        # Check if we have scan data and directory changed
        if hasattr(self, 'scanned_files') and self.scanned_files:
            if hasattr(self, 'last_scanned_directory') and self.last_scanned_directory != new_directory:
                logging_service.log("INFO", "Directory changed - clearing scan data")
                self.scanned_files = []
                self.last_scanned_directory = ""
                
                # Transition to IDLE if we were in IDLE_SCAN_DONE
                if self.current_state == ApplicationState.IDLE_SCAN_DONE:
                    self._set_state(ApplicationState.IDLE)
                    ui.notify("Directory changed - please scan again", type="info")

    def _start_processing(self) -> None:
        """Start the file processing process."""
        # Log processing start attempt
        
        # Log ExifTool support status
        from worker_functions import check_exiftool_availability
        is_available = check_exiftool_availability()
        use_exiftool = get_param("processing", "use_exiftool")
        
        if use_exiftool and is_available:
            logging_service.log("INFO_EXTRA", "Start Processing with exiftool support")
        else:
            logging_service.log("INFO_EXTRA", "Start Processing WITHOUT exiftool support")
        
        # 1. EERSTE ACTIE: Directory validatie
        current_path = self.scan_search_directory_input.value if self.scan_search_directory_input else ""
        # logging_service.log("DEBUG", f"Validating directory path: {current_path}")#DEBUG_OFF Validating directory path       
        is_valid, error_msg = self._validate_directory_path(current_path)
        
        if not is_valid:
            # Validation faalt: UI message + config waarde in input
            logging_service.log("ERROR", f"Directory validation failed: {error_msg}")
            ui.notify(f"Directory validation failed: {error_msg}", type="error")
            # Reset input to config value
            self.scan_search_directory_input.value = get_param("paths", "search_path")
            logging_service.log("INFO", "Reset directory input to config value")
            return
        
        # Validation successful
        logging_service.log("INFO_EXTRA", f"Directory validation successful: {current_path}")
        
        # 2. Check if we're in correct state (IDLE_SCAN_DONE)  #TODO Dit kan volgens mij weg
        if self.current_state != ApplicationState.IDLE_SCAN_DONE:
            logging_service.log("WARNING", "Processing can only start from IDLE_SCAN_DONE state")
            ui.notify("No Scanninng done", type="warning")
            return
        
        # 3. Get files to process (guaranteed to exist in IDLE_SCAN_DONE state)
        files_to_process = self._scan_files_for_processing("")
        
        # 4. Validation lukt: Reset flags en transition naar PROCESSING
        yapmo_globals.action_finished_flag = False
        yapmo_globals.stop_processing_flag = False
        # logging_service.log("DEBUG", "Reset processing flags")#DEBUG_OFF Reset processing flags
        
        # 5. Transition naar PROCESSING state
        # logging_service.log("DEBUG", "Transitioning to PROCESSING state")#DEBUG_OFF Transitioning to PROCESSING state
        self._set_state(ApplicationState.PROCESSING)
        
        # 6. Start UI update
        # logging_service.log("DEBUG", "Starting UI update timer")#DEBUG_OFF Starting UI update timer
        self._start_ui_update()
        
        # 7. Start processing process (dummy voor nu)
        # logging_service.log("DEBUG", "Starting background processing task")#DEBUG_OFF Starting background processing task
        timer = ui.timer(0.1, lambda: asyncio.create_task(self._run_processing_process(current_path)), once=True)
        self.active_timers.append(timer)

    def _show_details(self) -> None:
        
        # Get config for relevant extensions
        from config import get_param
        image_exts = get_param("extensions", "image_extensions")
        video_exts = get_param("extensions", "video_extensions")
        sidecar_exts = get_param("extensions", "sidecar_extensions")
        relevant_extensions = image_exts + video_exts + sidecar_exts
        
        dialog = ui.dialog()
        with dialog:
            with ui.card().classes("w-96 p-4 bg-white"):
                ui.label("FILETYPES FOUND").classes("text-xl font-bold mb-4 text-black")

                # Table with file types
                with ui.scroll_area().classes("w-full h-64"), \
                     ui.column().classes("w-full"):
                    # Header row
                    with ui.row().classes("w-full font-bold text-white bg-blue-500 p-2 rounded"):
                        ui.label("File type").classes("flex-1 text-white")
                        ui.label("Found").classes("w-20 text-right text-white")

                    # Data rows - only relevant extensions, sorted by file type
                    relevant_items = [
                        (ext, count) for ext, count in self.extension_counts.items()
                        if ext.lower() in relevant_extensions
                    ]
                    sorted_items = sorted(relevant_items)

                    if sorted_items:
                        for ext, count in sorted_items:
                            with ui.row().classes("w-full p-2 border-b border-gray-300"):
                                ui.label(str(ext)).classes("flex-1 text-black")
                                ui.label(str(count)).classes("w-20 text-right text-blue-600")
                    else:
                        # Show empty state when no relevant extensions found
                        with ui.row().classes("w-full p-4 text-center"):
                            ui.label("No relevant file types found").classes("text-gray-500")

                # Close button
                ui.button("CLOSE", on_click=dialog.close).classes(
                    "bg-blue-500 text-white px-4 py-2 rounded mt-4").props("color=primary")

        dialog.open()

    def _check_exiftool_availability(self) -> bool:
        """Check ExifTool availability. Returns True to continue, False to stay in IDLE."""
        from worker_functions import check_exiftool_availability
        from config import get_param
        
        # Check ExifTool status
        is_available = check_exiftool_availability()
        use_exiftool = get_param("processing", "use_exiftool")
        
        # Log status
        if use_exiftool and is_available:
            logging_service.log("INFO_EXTRA", "Start Scanning with exiftool support")
        else:
            logging_service.log("INFO_EXTRA", "Start Scanning WITHOUT exiftool support")
        
        # Show dialog if ExifTool is enabled but not available
        if use_exiftool and not is_available:
            self._show_exiftool_unavailable_dialog()
            return False  # Stay in IDLE state
        
        return True  # Continue normally

    def _show_exiftool_unavailable_dialog(self) -> None:
        """Show ExifTool unavailable dialog."""
        def _close_dialog(dialog: ui.dialog) -> None:
            """Close dialog and stay in IDLE."""
            dialog.close()
            logging_service.log("INFO_EXTRA", "User acknowledged ExifTool unavailability")
        
        # Create dialog with same styling as exit/abort dialogs
        dialog = ui.dialog()
        with dialog, YAPMOTheme.create_dialog_card():
            YAPMOTheme.create_dialog_title("ExifTool Not Available")
            
            YAPMOTheme.create_dialog_content(
                "Sorry, ExifTool is not available.\n\n"
                "You can change your config to proceed without ExifTool. Or make ExifTool available."
            )
            
            with YAPMOTheme.create_dialog_buttons():
                YAPMOTheme.create_dialog_button_confirm(
                    "OK",
                    lambda: _close_dialog(dialog)
                )
        
        dialog.open()

    def _handle_abort(self) -> None:
        """Handle abort button click."""
        if self.current_state in [ApplicationState.SCANNING, ApplicationState.PROCESSING]:
            # Direct abort - no second dialog needed
            self._confirm_abort(None)
    
    def _confirm_abort(self, dialog) -> None:
        """Confirm abort and transition to IDLE_ACTION_DONE state."""
        if dialog:
            dialog.close()
        
        # Set abort flag
        yapmo_globals.abort_requested = True
        
        # Set stop processing flag if we're in processing state
        if self.current_state == ApplicationState.PROCESSING:
            yapmo_globals.stop_processing_flag = True
            
            # Stop worker manager if running (no more results will be added)
            if self.worker_manager:
                self.worker_manager.stop_workers()
                
                # Wait for all workers to be completely stopped
                while self.worker_manager and not self.worker_manager.is_complete():
                    time.sleep(0.1)
                
                # Now all workers are stopped, no more results will be added
                self.worker_manager = None
            
            # Wait for result processor to finish processing remaining results
            if self.result_processor:
                # Wait for all remaining results to be processed
                self.result_processor.wait_for_completion(timeout=5.0)
                self.result_processor.stop()
                self.result_processor = None
        
        # Clear scan data on abort
        if hasattr(self, 'scanned_files'):
            self.scanned_files = []
        if hasattr(self, 'last_scanned_directory'):
            self.last_scanned_directory = ""
        
        # Set action_finished_flag (unified flag for all actions including abort)
        yapmo_globals.action_finished_flag = True
        # Note: ui_update_finished is NOT set here - only UI update functions can set this
        
        # Show notification
        ui.notify("User ABORTED", type="negative")
        
        # Transition to IDLE_ACTION_DONE state (unified completion state)
        self._set_state(ApplicationState.IDLE_ACTION_DONE)
        
        # Process any abort log messages
        self._display_log_queue()

    def _start_ui_update(self) -> None:
        """Start UI update timer."""
        try:
            # Register callback for scan progress updates
            self.ui_update_manager.register_callback(
                self._update_scan_progress_ui, 
                'scan_progress'
            )
            # Register callback for processing progress updates
            self.ui_update_manager.register_callback(
                self._update_processing_progress_ui, 
                'processing_progress'
            )
            # Register callback for log queue processing
            self.ui_update_manager.register_callback(
                self._display_log_queue
            )
            # Register flag transition check for all states
            self.ui_update_manager.register_callback(
                self._check_action_flag_transition
            )
            self.ui_update_manager.start_updates()
        except Exception as e:
            ui.notify(f"Failed to start UI update: {str(e)}", type="error")

    def _stop_ui_update(self) -> None:
        """Stop UI update timer."""
        self.ui_update_manager.stop_updates()
    
    def _cleanup_timers(self) -> None:
        """Clean up all active timers."""
        for timer in self.active_timers:
            try:
                timer.cancel()
            except Exception:
                pass  # Timer might already be cancelled
        self.active_timers.clear()
    
    def _cleanup_on_exit(self) -> None:
        """Clean up resources on application exit."""
        try:
            # Stop worker manager if active
            if self.worker_manager:
                self.worker_manager.stop_workers()
            
            # Clean up timers
            self._cleanup_timers()
        except Exception:
            pass  # Ignore errors during exit cleanup

    def _display_log_queue(self) -> None:
        """Display all messages from logging service queue in UI."""
        try:
            new_messages = logging_service.get_ui_messages()  # Get and clear queue
            
            if new_messages and self.log_column:
                # Add new messages to display queue (let op volgorde)
                if not hasattr(self, "log_messages"):
                    self.log_messages = []

                for msg_data in new_messages:
                    # Handle timestamp format safely
                    timestamp_parts = msg_data["timestamp"].split(" ")
                    if len(timestamp_parts) >= 2:
                        timestamp = timestamp_parts[1]
                    else:
                        timestamp = msg_data["timestamp"]
                    formatted_message = (
                        f"[{timestamp}] {msg_data['level']}: {msg_data['message']}"
                    )
                    self.log_messages.insert(0, formatted_message)  # Nieuwste bovenaan

                # Redraw all messages
                self.log_column.clear()
                
                with self.log_column:
                    for msg in self.log_messages:
                        ui.label(msg).classes("text-sm text-gray-700 font-mono")
                
                # Scroll to top to show latest messages (newest at top)
                self.log_area.scroll_to(percent=0)
                        
        except Exception as e:
            logging_service.log("WARNING", f"Log display error: {e}")

    def _format_time_estimate(self, seconds: float) -> str:
        """Format time estimate in hh:mm:ss.ss format."""
        if seconds <= 0:
            return "00:00:00.00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"

    def _update_scan_progress_ui(self, scan_data: dict) -> None:
        """Update UI elements from scan progress data."""
        try:
            # Update scan counters
            if hasattr(self, 'scan_total_files_label') and self.scan_total_files_label:
                self.scan_total_files_label.text = str(scan_data.get('total_files', 0))
            if hasattr(self, 'scan_media_files_label') and self.scan_media_files_label:
                self.scan_media_files_label.text = str(scan_data.get('media_files', 0))
            if hasattr(self, 'scan_sidecars_label') and self.scan_sidecars_label:
                self.scan_sidecars_label.text = str(scan_data.get('sidecars', 0))
            if hasattr(self, 'scan_total_directories_label') and self.scan_total_directories_label:
                self.scan_total_directories_label.text = str(scan_data.get('directories', 0))
            
            # Always display log messages (allowed in all states)
            self._display_log_queue()
            
            # Update debug flags
            self.debug_helper.update_debug_flags()
            
            # Check if action is finished and we're in IDLE_ACTION_DONE state
            if (yapmo_globals.action_finished_flag and 
                self.current_state == ApplicationState.IDLE_ACTION_DONE):
                # Check if both queues are empty before setting ui_update_finished
                messages = logging_service.get_ui_messages()
                log_queue_empty = len(messages) == 0
                
                # Check result queue if worker manager exists
                result_queue_empty = True
                if self.worker_manager:
                    result_queue_empty = self.worker_manager.result_queue.empty()
                
                if log_queue_empty and result_queue_empty:
                    # Both queues are empty, set ui_update_finished flag
                    yapmo_globals.ui_update_finished = True
                    # Update debug flags after flag change
                    self.debug_helper.update_debug_flags()
            
            # Abort now goes directly to IDLE_ACTION_DONE, no special handling needed here
                
        except Exception as e:
            # Silent error handling - UI update should not crash the app
            pass

    def _update_processing_progress_ui(self, processing_data: dict) -> None:
        """Update UI elements from processing progress data."""
        try:
            # Update processing progress bar
            if hasattr(self, 'processing_progressbar') and self.processing_progressbar:
                self.processing_progressbar.value = processing_data.get('progress', 0) / 100.0
            
            # Update processing progress label
            if hasattr(self, 'processing_progress_label') and self.processing_progress_label:
                progress = processing_data.get('progress', 0)
                self.processing_progress_label.text = f"Processing: {progress:.1f}%"
            
            # Update processing counters
            if hasattr(self, 'processing_files_processed_label') and self.processing_files_processed_label:
                self.processing_files_processed_label.text = str(processing_data.get('files_processed', 0))
            if hasattr(self, 'processing_directories_processed_label') and self.processing_directories_processed_label:
                self.processing_directories_processed_label.text = str(processing_data.get('directories_processed', 0))
            if hasattr(self, 'processing_files_sec_label') and self.processing_files_sec_label:
                self.processing_files_sec_label.text = f"{processing_data.get('files_per_sec', 0):.1f}"
            if hasattr(self, 'processing_directories_sec_label') and self.processing_directories_sec_label:
                self.processing_directories_sec_label.text = f"{processing_data.get('directories_per_sec', 0):.1f}"
            if hasattr(self, 'processing_time_to_finish_label') and self.processing_time_to_finish_label:
                time_to_finish = processing_data.get('time_to_finish', 0)
                if time_to_finish > 0:
                    self.processing_time_to_finish_label.text = self._format_time_estimate(time_to_finish)
                else:
                    self.processing_time_to_finish_label.text = "00:00:00.00"
            
            # Always display log messages (allowed in all states)
            self._display_log_queue()
            
            # Update debug flags
            self.debug_helper.update_debug_flags()
            
            # Check if action is finished and we're in IDLE_ACTION_DONE state
            if (yapmo_globals.action_finished_flag and 
                self.current_state == ApplicationState.IDLE_ACTION_DONE):
                # Check if both queues are empty before setting ui_update_finished
                messages = logging_service.get_ui_messages()
                log_queue_empty = len(messages) == 0
                
                # Check result queue if worker manager exists
                result_queue_empty = True
                if self.worker_manager:
                    result_queue_empty = self.worker_manager.result_queue.empty()
                
                if log_queue_empty and result_queue_empty:
                    # Both queues are empty, set ui_update_finished flag
                    yapmo_globals.ui_update_finished = True
                    # Update debug flags after flag change
                    self.debug_helper.update_debug_flags()
            
        except Exception as e:
            # Silent error handling - UI update should not crash the app
            pass


    def _check_action_flag_transition(self) -> None:
        """Check if action is finished and transition to appropriate state."""
        try:
            # Check if we're in IDLE_ACTION_DONE state
            if self.current_state == ApplicationState.IDLE_ACTION_DONE:
                # Check if both flags are set
                if (yapmo_globals.action_finished_flag and 
                    yapmo_globals.ui_update_finished):
                    
                    # Clear both flags
                    yapmo_globals.action_finished_flag = False
                    yapmo_globals.ui_update_finished = False
                    
                    # Update debug flags after flag clearing
                    self.debug_helper.update_debug_flags()
                    
                    # Determine next state based on what was completed
                    if hasattr(self, 'scanned_files') and self.scanned_files:
                        # Scan completed - go to IDLE_SCAN_DONE
                        self._set_state(ApplicationState.IDLE_SCAN_DONE)
                    else:
                        # Processing completed - go to IDLE
                        self._set_state(ApplicationState.IDLE)
            
        except Exception as e:
            # Silent error handling - flag check should not crash the app
            pass


    async def _run_scan_process(self, directory: str) -> None:
        """Run the scan process with real-time updates."""
        try:
            # Run scan in background thread
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._scan_directory_sync_with_updates, directory
            )
            
            # Update UI with final results
            self._update_final_results(result)
            
            # Set action_finished_flag (unified flag for all actions)
            yapmo_globals.action_finished_flag = True
            
            # Transition to IDLE_SCAN_DONE state after scanning
            self._set_state(ApplicationState.IDLE_SCAN_DONE)
            
            # Process any remaining log messages
            self._display_log_queue()
            
        except Exception as e:
            # Log error instead of UI notify (background thread)
            logging_service.log("ERROR", f"Scan failed: {str(e)}")
            # Clear flags on error
            yapmo_globals.action_finished_flag = False
            yapmo_globals.ui_update_finished = False
            # Clean up timers on error
            self._cleanup_timers()
            self._set_state(ApplicationState.IDLE)

    async def _run_processing_process(self, directory: str) -> None:
        """Run the processing process with real-time updates."""
        try:
            # Run parallel processing in background thread
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._process_files_parallel, directory
            )
            
            # Update UI with final results
            self._update_processing_final_results(result)
            
            # Set action_finished_flag (unified flag for all actions)
            yapmo_globals.action_finished_flag = True
            
            # Transition to IDLE_ACTION_DONE state after processing
            self._set_state(ApplicationState.IDLE_ACTION_DONE)
            
            # Process any remaining log messages
            self._display_log_queue()
            
        except Exception as e:
            # Log error instead of UI notify (background thread)
            logging_service.log("ERROR", f"Processing failed: {str(e)}")
            # Clear flags on error
            yapmo_globals.action_finished_flag = False
            yapmo_globals.stop_processing_flag = False
            
            # Stop result processor on error (after workers are stopped)
            if self.result_processor:
                # Wait for any remaining results to be processed
                self.result_processor.wait_for_completion(timeout=5.0)
                self.result_processor.stop()
                self.result_processor = None
            
            self._set_state(ApplicationState.IDLE)

    def _scan_directory_sync_with_updates(self, directory: str) -> dict:
        """Scan directory with real-time UI updates."""
        import time
        
        # Record start time for elapsed time calculation
        start_time = time.time()
        
        files_count = 0
        directories_count = 0
        media_files_count = 0
        sidecars_count = 0
        
        # List to collect media files for processing
        files_to_process = []
        
        # Load extensions from config and create lookup dictionary
        image_exts = set(get_param("extensions", "image_extensions"))
        video_exts = set(get_param("extensions", "video_extensions"))
        sidecar_exts = set(get_param("extensions", "sidecar_extensions"))
        
        #DEBUG_OFF Block start - Extension mapping debug
        #logging_service.log("DEBUG", f"Image extensions loaded: {sorted(image_exts)}")
        #logging_service.log("DEBUG", f"Video extensions loaded: {sorted(video_exts)}")
        #logging_service.log("DEBUG", f"Sidecar extensions loaded: {sorted(sidecar_exts)}")
        #DEBUG_OFF Block end - Extension mapping debug
        
        # Create extension lookup dictionary for efficient file categorization
        extension_map = {}
        for ext in image_exts:
            extension_map[ext] = 'media'
        for ext in video_exts:
            extension_map[ext] = 'media'
        for ext in sidecar_exts:
            extension_map[ext] = 'sidecar'
        
        #DEBUG_OFF Block start - Extension map debug
        #logging_service.log("DEBUG", f"Extension map created: {extension_map}")
        #DEBUG_OFF Block end - Extension map debug
        
        # Use os.walk() for recursive directory traversal
        for root, dirs, files in os.walk(directory):
            # Check for abort request
            if yapmo_globals.abort_requested:
                break
                
            # Count directories
            directories_count += 1
            
            #DEBUG_OFF Block start - Directory scan debug
            #logging_service.log("DEBUG", f"Scanning directory: {root}")
            #logging_service.log("DEBUG", f"Found {len(files)} files: {files}")
            #DEBUG_OFF Block end - Directory scan debug
            
            # Count files and categorize them
            for file in files:
                if yapmo_globals.abort_requested:
                    files_to_process.clear()  #JM reset list om naar IDLE te gaan
                    break
                files_count += 1
                file_ext = Path(file).suffix.lower()
                
                #DEBUG_OFF Block start - File processing debug
                #logging_service.log("DEBUG", f"Processing file: {file} -> extension: {file_ext}")
                #DEBUG_OFF Block end - File processing debug
                
                # Track file extension counts for details popup
                if file_ext in self.extension_counts:
                    self.extension_counts[file_ext] += 1
                else:
                    self.extension_counts[file_ext] = 1
                
                # Use dictionary lookup for efficient categorization
                file_type = extension_map.get(file_ext, 'other')
                
                #DEBUG_OFF Block start - File categorization debug
                #logging_service.log("DEBUG", f"File {file}: ext={file_ext}, type={file_type}, mapped_from={extension_map.get(file_ext, 'NOT_FOUND')}")
                #DEBUG_OFF Block end - File categorization debug
                
                if file_type == 'media':
                    media_files_count += 1
                    # Add media files to processing list
                    files_to_process.append(os.path.join(root, file))
                    
                    #DEBUG_OFF Block start - Media file found debug
                    #logging_service.log("DEBUG", f"MEDIA FILE FOUND: {file} -> {os.path.join(root, file)}")
                    #DEBUG_OFF Block end - Media file found debug
                elif file_type == 'sidecar':
                    sidecars_count += 1
            
            # Update shared data for UI updates
            scan_data = {
                'total_files': files_count,
                'media_files': media_files_count,
                'sidecars': sidecars_count,
                'directories': directories_count
            }
            # Update shared data for UI updates
            self.ui_update_manager.update_shared_data('scan_progress', scan_data)
            # Process log messages immediately during scanning
            self._display_log_queue()
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Calculate files per second
        files_per_sec = files_count / elapsed_time if elapsed_time > 0 else 0
        
        # Format elapsed time for display
        if elapsed_time < 60:
            elapsed_str = f"{elapsed_time:.2f} seconds"
        elif elapsed_time < 3600:
            minutes = int(elapsed_time // 60)
            seconds = elapsed_time % 60
            elapsed_str = f"{minutes}m {seconds:.1f}s"
        else:
            hours = int(elapsed_time // 3600)
            minutes = int((elapsed_time % 3600) // 60)
            elapsed_str = f"{hours}h {minutes}m"
        
        logging_service.log("INFO", f"Scanning summary: {files_count} files, {media_files_count} \
media files, {sidecars_count} sidecars, {directories_count} directories - Elapsed time: {elapsed_str} ({files_per_sec:.2f} files/sec)")
        
        # Store files for later use in processing
        self.scanned_files = files_to_process
        self.last_scanned_directory = directory
        
        #DEBUG_OFF Block start - Final scan results debug
        #logging_service.log("DEBUG", f"FINAL SCAN RESULTS:")
        #logging_service.log("DEBUG", f"  - Total files found: {files_count}")
        #logging_service.log("DEBUG", f"  - Media files found: {media_files_count}")
        #logging_service.log("DEBUG", f"  - Sidecars found: {sidecars_count}")
        #logging_service.log("DEBUG", f"  - Files to process: {len(files_to_process)}")
        #logging_service.log("DEBUG", f"  - Files list: {files_to_process}")
        #DEBUG_OFF Block end - Final scan results debug
        
        return {
            "files": files_count,
            "directories": directories_count,
            "media_files": media_files_count,
            "sidecars": sidecars_count,
        }

    def _update_final_results(self, result: dict) -> None:
        """Update UI with final scan results."""
        # Update global scan counters
        yapmo_globals.scan_total_files = result.get("files", 0)
        yapmo_globals.scan_media_files = result.get("media_files", 0)
        yapmo_globals.scan_sidecars = result.get("sidecars", 0)
        yapmo_globals.scan_total_directories = result.get("directories", 0)
        
        
        # Update all count labels
        if hasattr(self, 'scan_total_files_label') and self.scan_total_files_label:
            self.scan_total_files_label.text = str(result.get("files", 0))
        if hasattr(self, 'scan_media_files_label') and self.scan_media_files_label:
            self.scan_media_files_label.text = str(result.get("media_files", 0))
        if hasattr(self, 'scan_sidecars_label') and self.scan_sidecars_label:
            self.scan_sidecars_label.text = str(result.get("sidecars", 0))
        if hasattr(self, 'scan_total_directories_label') and self.scan_total_directories_label:
            self.scan_total_directories_label.text = str(result.get("directories", 0))

    def _update_processing_final_results(self, result: dict) -> None:
        """Update UI with final processing results."""
        # Update processing labels with final results
        if hasattr(self, 'processing_files_processed_label') and self.processing_files_processed_label:
            self.processing_files_processed_label.text = str(result.get("files_processed", 0))
        if hasattr(self, 'processing_directories_processed_label') and self.processing_directories_processed_label:
            self.processing_directories_processed_label.text = str(result.get("directories_processed", 0))
        if hasattr(self, 'processing_files_sec_label') and self.processing_files_sec_label:
            self.processing_files_sec_label.text = f"{result.get('files_per_sec', 0):.1f}"
        if hasattr(self, 'processing_directories_sec_label') and self.processing_directories_sec_label:
            self.processing_directories_sec_label.text = f"{result.get('directories_per_sec', 0):.1f}"
        if hasattr(self, 'processing_time_to_finish_label') and self.processing_time_to_finish_label:
            self.processing_time_to_finish_label.text = "Complete"


    def _process_files_parallel(self, directory: str) -> dict:
        """Process files using parallel workers."""
        # Log processing start
        # logging_service.log("DEBUG", f"Starting parallel file processing in directory: {directory}")#DEBUG_OFF Starting parallel file processing in directory:
        
        # Scan directory for files to process
        files_to_process = self._scan_files_for_processing(directory)
        # logging_service.log("INFO", f"Found {len(files_to_process)} files to process")#DEGUB_OFF Found XX files to process
        
        total_files = len(files_to_process)
        
        if total_files == 0:
            logging_service.log("WARNING", "No files found to process")
            return {
                "files_processed": 0,
                "directories_processed": 0,
                "files_per_sec": 0,
                "directories_per_sec": 0,
                "elapsed_time": 0
            }
        
        # Initialize parallel worker manager
        max_workers = get_param("processing", "max_workers") or 4
        self.worker_manager = ParallelWorkerManager(
            max_workers=max_workers,
            progress_callback=self._update_processing_progress_ui
        )
        
        # Set total files for progress calculation
        self.worker_manager.total_files = total_files
        
        # Start workers
        self.worker_manager.start_workers()
        
        # Start result processor to consume results from the queue
        self.result_processor = ResultProcessor(
            result_queue=self.worker_manager.result_queue,
            logging_queue=self.worker_manager.logging_queue
        )
        self.result_processor.start()
        
        # Submit files to workers using batch processing for better ExifTool performance
        batch_size = get_param("processing", "read_batch_size")  # Get read batch size from config
        
        for i in range(0, len(files_to_process), batch_size):
            if yapmo_globals.stop_processing_flag:
                logging_service.log("INFO", "Processing aborted by user")
                break
                
            # Get batch of files
            batch_files = files_to_process[i:i + batch_size]
            worker_id = (i // batch_size) % max_workers
            
            # Submit batch to worker
            self.worker_manager.submit_files_batch(batch_files, worker_id)
        
        # Process results from workers
        while not self.worker_manager.is_complete():
            if yapmo_globals.stop_processing_flag:
                logging_service.log("INFO", "Processing aborted by user")
                break
                
            # Process completed workers
            self.worker_manager.process_completed_workers()
            
            # Update UI with current progress
            progress_data = self.worker_manager._get_progress_data()
            self.ui_update_manager.update_shared_data('processing_progress', progress_data)
            
            # Process worker log messages
            self._process_worker_logs()
            
            # Small delay to prevent busy waiting
            time.sleep(0.1)
        
        # Get final statistics
        final_stats = self.worker_manager.get_final_stats()
        
        # Stop workers first (no more results will be added to queue)
        self.worker_manager.stop_workers()
        
        # Wait for all workers to be completely stopped
        while not self.worker_manager.is_complete():
            time.sleep(0.1)
        
        # Now all workers are stopped, no more results will be added
        self.worker_manager = None
        
        # Wait for result processor to finish processing remaining results
        if self.result_processor:
            # Wait for all remaining results to be processed
            self.result_processor.wait_for_completion(timeout=10.0)
            self.result_processor.stop()
            self.result_processor = None
        
        # Log processing completion
        # logging_service.log("INFO", f"Parallel processing completed successfully!")
        logging_service.log("INFO", f"Final summary: {final_stats['files_processed']} files, {final_stats['directories_processed']} directories processed in {final_stats['elapsed_time']:.2f}s")
        logging_service.log("INFO_EXTRA", f"Average performance: {final_stats['files_per_sec']:.1f} files/sec, {final_stats['directories_per_sec']:.1f} dirs/sec")
        
        return final_stats
    
    def _scan_files_for_processing(self, directory: str) -> List[str]:
        """Get files to process from previous scan."""
        return getattr(self, 'scanned_files', [])
    
    def _process_worker_logs(self) -> None:
        """Process worker log messages from logging queue."""
        if not self.worker_manager:
            return
            
        # Process worker logs
        while not self.worker_manager.logging_queue.empty():
            try:
                log_msg = self.worker_manager.logging_queue.get_nowait()
                
                # Handle both dictionary and string log messages
                if isinstance(log_msg, dict):
                    logging_service.log(log_msg['level'], log_msg['message'])
                elif isinstance(log_msg, str):
                    # Parse string log message (format: "LEVEL: message")
                    if ':' in log_msg:
                        level, message = log_msg.split(':', 1)
                        logging_service.log(level.strip(), message.strip())
                    else:
                        logging_service.log("INFO", log_msg)
                else:
                    logging_service.log("WARNING", f"Unknown log message type: {type(log_msg)}")
                    
            except queue.Empty:
                break
            except Exception as e:
                logging_service.log("ERROR", f"Error processing worker log: {str(e)}")
        
        # Process regular logs
        self._display_log_queue()

    def _validate_directory_path(self, path: str) -> tuple[bool, str]:
        """
        Validate directory path.
        Returns: (is_valid, error_message)
        """
        import os
        
        if not path:
            return False, "No directory path provided"
        
        if not os.path.exists(path):
            return False, "Directory does not exist"
        
        if not os.path.isdir(path):
            return False, "Path is not a directory"
        
        if not os.access(path, os.R_OK):
            return False, "No read permission for directory"
        
        return True, ""

    def _initialize_page(self) -> None:
        """Initialize the page and transition to IDLE state."""
        try:
            # Initialize logging service
            logging_service.reload_config()
            
            # Check for any critical errors during initialization
            # For now, we assume initialization is always successful
            
            # Clear flags on initialization
            yapmo_globals.action_finished_flag = False
            yapmo_globals.ui_update_finished = False
            
            # Clean up initialization timers before transitioning to IDLE
            self._cleanup_timers()
            
            # Transition to IDLE state
            self._set_state(ApplicationState.IDLE)
                
        except Exception as e:
            # If initialization fails, show error but stay in IDLE
            ui.notify(f"Initialization failed: {str(e)}", type="error")
            # Clear flags on initialization error
            yapmo_globals.action_finished_flag = False
            yapmo_globals.ui_update_finished = False
            # Clean up timers on error
            self._cleanup_timers()
            self._set_state(ApplicationState.IDLE)






    def _cleanup_timers(self) -> None:
        """Clean up all active timers."""
        try:
            for timer in self.active_timers:
                if hasattr(timer, 'cancel'):
                    timer.cancel()
            self.active_timers.clear()
        except Exception as e:
            # Silent error handling - timer cleanup should not crash the app
            pass

    def _cleanup_on_exit(self) -> None:
        """Cleanup function called on application exit."""
        try:
            # Stop worker manager if active
            if self.worker_manager:
                self.worker_manager.stop_workers()
            
            # Clean up all timers
            self._cleanup_timers()
        except Exception as e:
            # Silent error handling - exit cleanup should not crash the app
            pass


def create_fill_db_page_v2() -> FillDbPageV2:
    """Create the fill database v2 page."""
    return FillDbPageV2()


if __name__ == "__main__":
    create_fill_db_page_v2()
    ui.run(title="YAPMO Fill Database V2", port=8080)
