"""Fill Database Page voor YAPMO applicatie."""

import asyncio
import atexit
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nicegui import ui
from shutdown_manager import handle_exit_click
from theme import YAPMOTheme
from config import get_param, ConfigManager
from local_directory_picker import pick_directory

# Import managers
from managers.abort_manager import AbortManager
from managers.queue_manager import QueueManager
from managers.process_manager import ProcessManager
from managers.database_manager import DatabaseManager
from core.file_scanner import FileScanner
from core.process_media_files import ProcessMediaFiles


class FillDBPage:
    """Database vullen pagina van de YAPMO applicatie."""

    def __init__(self) -> None:
        """Initialize the database fill page."""
        # Get the path to config.json (same directory as main.py)
        self.config_path = Path(__file__).parent.parent / "config.json"

        # Initialize managers
        self.config_manager = ConfigManager()
        self.queue_manager = QueueManager(self.config_manager)
        
        # Create ResultQueue with a temporary database manager
        from queues.result_queue import ResultQueue
        temp_db_manager = None  # Will be set after DatabaseManager is created
        self.queue_manager.result_queue = ResultQueue(temp_db_manager)
        
        # Now create DatabaseManager with the ResultQueue
        self.database_manager = DatabaseManager(self.queue_manager.result_queue)
        
        # Initialize logging manager (simplified for now)
        from managers.logging_manager import LoggingManager
        #TODO argument aangepast: originele argumenten: LoggingManager(self.config_manager, self.queue_manager.logging_queue)
        self.logging_manager = LoggingManager(self.queue_manager.logging_queue)
        
        # Initialize abort manager with all required components
        self.abort_manager = AbortManager(
            self.queue_manager.result_queue,
            self.queue_manager.logging_queue,
            self.database_manager,
            self.logging_manager
        )
        
        # Initialize process manager
        self.process_manager = ProcessManager(self.config_manager, self.queue_manager, self.abort_manager)
        
        # Initialize core components
        self.file_scanner = FileScanner(self.config_manager, self.queue_manager, self.abort_manager)
        self.process_media_files = ProcessMediaFiles(
            self.config_manager, self.queue_manager, self.abort_manager, self.process_manager
        )

        # Initialize page state management
        self.page_state = {
            "scanning": False,
            "processing": False,
            "filling_db": False,
        }

        # Initialize scan state
        self.scan_running = False
        self.scan_aborted = False
        self.scan_results = {
            "total_files": 0,
            "media_files": 0,
            "sidecars": 0,
            "directories": 0,
            "by_extension": {},
        }

        # Processing state
        self.processing_running = False
        self.processing_aborted = False
        self.processing_results: dict[str, Any] = {}

        # Scan state variables
        self.scan_progress = 0
        self.scan_complete = False
        self.scan_start_time: float | None = None
        self.processing_start_time: float | None = None

        # Initialize UI component references
        self.dir_input: Any = None
        self.spinner: Any = None
        self.progress_bar: Any = None
        self.log_scroll_area: Any = None
        self.clear_log_button: Any = None
        self.scan_status_label: Any = None
        self.progress_info_label: Any = None
        self.details_button: Any = None
        self.start_process_button: Any = None

        # Initialize file count variables
        self.total_files = 0
        self.media_files = 0
        self.sidecars = 0
        self.directories = 0

        # Initialize log messages
        self.log_messages: list[str] = []

        self.total_files_label: Any = None
        self.media_files_label: Any = None
        self.sidecars_label: Any = None
        self.directories_label: Any = None
        self.log_column: Any = None

        self._create_page()

        # Register abort handler for this page
        #TODO method aangepast: originele code: self.abort_manager.register_abort_handler("fill_db", self._abort_scan)
        # AbortManager doesn't have register_abort_handler method

        # Cleanup when page is destroyed
        def cleanup() -> None:
            #TODO method aangepast: originele code: self.abort_manager.unregister_abort_handler("fill_db")
            # AbortManager doesn't have unregister_abort_handler method
            pass

        # Register cleanup (this will be called when the page is destroyed)
        atexit.register(cleanup)

    def _create_page(self) -> None:
        """Maak de database vullen pagina."""

        @ui.page("/fill-db")
        def fill_db_page() -> None:
            with YAPMOTheme.page_frame("Fill Database", exit_handler=handle_exit_click):
                self._create_content()

    def _create_content(self) -> None:
        """Maak de content van de database vullen pagina."""
        # Initialize page state
        self._initialize_page_state()

    def _initialize_page_state(self) -> None:
        """Initialize page state when page loads."""
        # Reset scan state
        self.scan_running = False
        self.scan_aborted = False
        self.scan_results = {
            "total_files": 0,
            "media_files": 0,
            "sidecars": 0,
            "directories": 0,
            "by_extension": {},
        }

        # Reset progress
        self.scan_progress = 0
        self.scan_complete = False

        # Clear log messages
        self.log_messages = []

        # Reset scan start time (already defined in __init__)
        self.scan_start_time = None

        # Container voor de hele pagina
        with ui.column().classes("w-full max-w-7xl mx-auto p-6"):
            self._create_scan_results_panel()
            self._create_progress_log_panel()

        # Reset UI elements after creation
        self._reset_ui_elements()

    def _create_scan_results_panel(self) -> None:
        """Create the scan results panel."""
        # Scan Results Panel (Hele breedte - Standaard kaartjes kleur met Blauwe Rand)
        card_classes = (
            "w-full bg-white border-2 border-blue-500 rounded-lg shadow-lg mb-6"
        )
        section_classes = "w-full p-6"
        with ui.card().classes(card_classes), \
             ui.card_section().classes(section_classes):
            ui.label("Scan Results").classes(
                "text-xl font-semibold text-gray-800 mb-4")

            # Directory selection row (direct onder de titel)
            with ui.row().classes("w-full items-center gap-4 mb-6"):
                YAPMOTheme.create_button(
                    "SELECT DIRECTORY",
                    self._select_directory,
                    "primary",
                    "md",
                )

                # Load search path from config
                search_path = self._load_search_path_from_config()

                self.dir_input = ui.input(
                    label="Search Directory",
                    value=search_path,
                    placeholder="Select a directory to scan...",
                    on_change=self._on_directory_input_change,
                ).classes("flex-1")

                # Dots spinner indicator
                self.spinner = ui.spinner(
                    "dots",
                    size="6rem",
                    color="red",
                ).classes("text-blue-500")
                # Hide spinner initially
                self.spinner.visible = False

            # Statistics row
            with ui.row().classes("w-full gap-4 mb-4"):
                # Start Process button
                self.start_process_button = YAPMOTheme.create_button(
                    "START PROCESS",
                    self._start_scan,
                    "primary",
                    "md",
                )
                # Enable initially so user can start a scan
                self.start_process_button.enable()

                self.scan_status_label = ui.label("Ready to start").classes(
                    "text-gray-700 font-medium")

                with ui.column().classes("items-center"):
                    self.total_files_label = ui.label("0").classes(
                        "text-blue-600 text-2xl font-bold")
                    ui.label("Total Files").classes(
                        "text-gray-600 text-sm")

                with ui.column().classes("items-center"):
                    self.media_files_label = ui.label("0").classes(
                        "text-blue-600 text-2xl font-bold")
                    ui.label("Media Files").classes(
                        "text-gray-600 text-sm")

                with ui.column().classes("items-center"):
                    self.sidecars_label = ui.label("0").classes(
                        "text-blue-600 text-2xl font-bold")
                    ui.label("Sidecars").classes(
                        "text-gray-600 text-sm")

                with ui.column().classes("items-center"):
                    self.directories_label = ui.label("0").classes(
                        "text-blue-600 text-2xl font-bold")
                    ui.label("Directories").classes(
                        "text-gray-600 text-sm")

                self.details_button = YAPMOTheme.create_button(
                    "DETAILS",
                    self._show_details,
                    "info",
                    "md",
                )
                # Disable details button initially
                self.details_button.disable()

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

            # Processing times barchart
            with ui.row().classes("w-full items-center gap-4 mb-2"):
                ui.label("Processing Times (ms):").classes("text-sm font-medium text-gray-600")
                self.processing_barchart = ui.html("").classes("flex-1")
                self.processing_barchart.visible = False

            # Progress bar and directories counter row
            with ui.row().classes("w-full items-center gap-4 mb-4"):
                # Progress bar (flex-1 to take remaining space)
                self.progress_bar = ui.linear_progress(
                    value=0.0,
                    show_value=False,
                    size="20px",
                    color="blue",
                ).classes("flex-1")
                self.progress_bar.visible = False

            # Progress info - verborgen bij initialisatie
            progress_text = (
                "Progress info: Completed: 0% "
                "(0 Found/0 Files processed)"
            )
            self.progress_info_label = ui.label(progress_text).classes(
                "text-gray-700 font-medium mb-4",
            )
            self.progress_info_label.visible = False

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
        """Handle directory selection using local directory picker."""
        try:
            # Open directory picker starting from /workspaces
            selected_dir = await pick_directory(directory="/workspaces")

            if selected_dir:
                # Update the input field with selected directory
                if self.dir_input:
                    self.dir_input.value = selected_dir
                    # Update config.json with new search path
                    self._update_config_search_path(selected_dir)
                else:
                    ui.notify("Error: Directory input not found", type="negative")

        except (OSError, PermissionError) as e:
            ui.notify(f"Error selecting directory: {e}", type="negative")

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

    def _on_directory_input_change(self) -> None:
        """Handle manual directory input changes."""
        if self.dir_input and self.dir_input.value:
            # Update config.json with new search path
            self._update_config_search_path(self.dir_input.value)

    def _load_search_path_from_config(self) -> str:
        """Load search_path from config.json."""
        try:
            with self.config_path.open(encoding="utf-8") as f:
                config = json.load(f)

            return str(config.get("paths", {}).get("search_path"))

        except FileNotFoundError:
            error_msg = f"ERROR: Config file not found: {self.config_path}"
            ui.notify(error_msg, type="negative")
            return get_param("paths", "search_path")
        except json.JSONDecodeError as e:
            ui.notify(f"ERROR: Invalid config.json format: {e}", type="negative")
            return get_param("paths", "search_path")
        except KeyError:
            ui.notify("ERROR: search_path not found in config.json", type="negative")
            return get_param("paths", "search_path")

    def _show_details(self) -> None:
        """Show file type details in a popup."""
        by_extension = self.scan_results.get("by_extension")
        if not self.scan_results or not isinstance(by_extension, dict):
            notify_msg = "No scan data available. Please scan a directory first."
            ui.notify(notify_msg, type="info")
            return

        # Get config for relevant extensions
        image_exts = self.config_manager.get_param("extensions", "image_extensions")
        video_exts = self.config_manager.get_param("extensions", "video_extensions")
        sidecar_exts = self.config_manager.get_param("extensions", "sidecar_extensions")
        relevant_extensions = image_exts + video_exts + sidecar_exts

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

                # Data rows - only relevant extensions, sorted by file type
                relevant_items = [
                    (ext, count) for ext, count in by_extension.items()
                    if ext.lower() in relevant_extensions
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

    async def _start_scan(self) -> None:
        """Start the directory scan process."""
        if self.scan_running:
            return

        # Validate directory
        directory = self._validate_scan_directory()
        if not directory:
            return

        # Initialize scan
        self._initialize_scan_state(directory)

        # Start scan using FileScanner
        try:
            result = await self.file_scanner.scan_directory(directory)
            await self._on_scan_complete(result)
        except Exception as e:
            self._add_log_message(f"Scan error: {e}", "ERROR")

    def _validate_scan_directory(self) -> str | None:
        """Validate the scan directory and return it if valid."""
        directory = self.dir_input.value if self.dir_input else ""
        if not directory:
            ui.notify("Please select a directory first", type="negative")
            return None

        if not Path(directory).exists():
            self._add_log_message(f"Directory does not exist: {directory}", "ERROR")
            return None

        if not os.access(directory, os.R_OK):
            self._add_log_message(f"Directory is not readable: {directory}", "ERROR")
            return None

        return directory

    def _initialize_scan_state(self, directory: str) -> None:
        """Initialize scan state and UI."""
        # Start scan process
        self.scan_running = True
        self.scan_aborted = False
        self.scan_start_time = time.time()

        # Update UI elements
        self._update_scan_ui_elements()

        # Log scan start
        self._add_log_message(f"Starting scan of directory: {directory}", "PROCESS")

        # Reset scan results
        self.scan_results = {
            "total_files": 0,
            "media_files": 0,
            "sidecars": 0,
            "directories": 0,
            "by_extension": {},
        }

        # Reset progress
        self.scan_progress = 0
        self.scan_complete = False

        # Start UI update timer
        self._setup_ui_updates()

        # Enable abort button
        self.abort_manager.set_processing_active(active=True)

    def _update_scan_ui_elements(self) -> None:
        """Update UI elements for scan start."""
        if self.clear_log_button:
            self.clear_log_button.disable()

        if self.spinner:
            self.spinner.visible = True

        # Disable START PROCESS button during scan
        if self.start_process_button and hasattr(self.start_process_button, "disable"):
            self.start_process_button.disable()

        # Progress bar and info label are hidden during scan phase
        if self.progress_bar:
            self.progress_bar.visible = False
        if self.progress_info_label:
            self.progress_info_label.visible = False

        if self.scan_status_label:
            self.scan_status_label.text = "Scanning..."

    async def _on_scan_complete(self, result) -> None:
        """Handle scan completion callback."""
        # Update scan results with final values
        if hasattr(self, "scan_results"):
            self.scan_results.update({
                "total_files": result.total_files,
                "media_files": result.media_files,
                "sidecars": result.sidecars,
                "directories": result.directories,
                "by_extension": result.by_extension,
            })

        # Store file list for processing phase
        self.scan_file_list = result.file_list

        # Set scan complete flag
        self.scan_complete = True

        # Finalize scan
        self._finalize_scan()

        # Start processing phase automatically
        await self._start_processing_automatically()

    async def _start_processing_automatically(self) -> None:
        """Start processing phase automatically after scan completion."""
        # Calculate scan duration
        scan_duration = self._calculate_scan_duration()
        duration_str = self._format_duration(scan_duration)

        # Get scan results for log message
        total_files = self.scan_results.get("total_files", 0)
        media_files = self.scan_results.get("media_files", 0)
        sidecars = self.scan_results.get("sidecars", 0)
        directories = self.scan_results.get("directories", 0)

        # Log processing start with scan summary
        log_message = (
            f"Scan completed in {duration_str} - "
            f"Processing phase starting automatically - "
            f"Scan results: {total_files} files, {media_files} media files, "
            f"{sidecars} sidecars, {directories} directories"
        )
        self._add_log_message(log_message, "PROCESS")

        # Update status label
        if self.scan_status_label and hasattr(self.scan_status_label, "text"):
            self.scan_status_label.text = "Processing"

        # Start processing
        await self._start_processing()

    def _setup_ui_updates(self) -> None:
        """Set up UI updates and NiceGUI connection alive."""
        # UI update timer (user interface updates)
        def update_ui() -> None:
            if self.scan_aborted and self.processing_aborted:
                return

            # Check if scan is complete and finalize if needed
            if self.scan_complete and self.scan_running:
                self._finalize_scan()
                return

            try:
                self._update_progress_display()
                self._update_processing_progress_display()

                # Only show estimated counters during scan, not after
                if self.scan_running:
                    self._update_counters_display()
                else:
                    # After scan, show final counters
                    self._update_final_counters()

                self._display_log_queue()

                # Schedule next update if still running
                if ((self.scan_running and not self.scan_aborted) or
                     (self.processing_running and not self.processing_aborted)):
                    ui.timer(0.1, update_ui, once=True)

            except OSError as e:
                # Don't schedule next update on error
                pass

        # Start timer
        ui.timer(0.1, update_ui, once=True)

    def _update_progress_display(self) -> None:
        """Update progress bar and info display during scanning."""
        if self.scan_running:
            # During scanning
            value = self.scan_results.get("total_files")
            total_files = int(str(value)) if value is not None else 1
            progress_percentage = min(
                100.0, (int(str(self.scan_progress)) / max(1, total_files)) * 100,
            )
            if hasattr(self.progress_bar, "value"):
                self.progress_bar.value = progress_percentage / 100.0

            if self.progress_info_label:
                current_files = int(str(self.scan_progress))
                value = self.scan_results.get("total_files")
                total_files = int(str(value)) if value is not None else 0
                percentage = (
                    min(100, int((current_files / max(1, total_files)) * 100))
                    if total_files > 0 else 0
                )
                progress_text = (
                    f"Scanning: {current_files}/{total_files} files found "
                    f"({percentage}% completed)"
                )
                if hasattr(self.progress_info_label, "text"):
                    self.progress_info_label.text = progress_text

    def _update_processing_progress_display(self) -> None:
        """Update processing progress bar and time estimation."""
        if not self.processing_running:
            return

        # Get processing data - use media_files count from scan results
        value = self.scan_results.get("media_files", 0)
        total_media_files = int(str(value)) if value is not None else 0
        processed_files = self.process_media_files.processed_count

        if total_media_files > 0:
            # Calculate progress percentage (processed/total * 100%)
            progress_percentage = min(
                100, int((processed_files / total_media_files) * 100),
            )

            # Calculate processing speed (files per second)
            if self.processing_start_time is not None:
                elapsed_time = time.time() - self.processing_start_time
            else:
                elapsed_time = 0.0
            files_per_second = processed_files / elapsed_time if elapsed_time > 0 else 0

            # Calculate remaining time
            remaining_files = total_media_files - processed_files
            estimated_remaining_time = (
                (elapsed_time / processed_files) * remaining_files
                if processed_files > 0 else 0
            )

            # Update progress bar (0% to 100%)
            if self.progress_bar and hasattr(self.progress_bar, "value"):
                self.progress_bar.value = progress_percentage / 100.0

            # Update progress info label
            if self.progress_info_label:
                remaining_str = self._format_duration(estimated_remaining_time)
                progress_text = (
                    f"Completed: {progress_percentage}% "
                    f"({processed_files} Processed / {total_media_files} "
                    f"Media files to process) "
                    f"{files_per_second:.1f} files/sec "
                    f"estimate: {remaining_str} remaining"
                )
                if hasattr(self.progress_info_label, "text"):
                    self.progress_info_label.text = progress_text
                
                # Update processing barchart
                self._update_processing_barchart()

    def _update_processing_barchart(self) -> None:
        """Update the processing times barchart."""
        try:
            if not hasattr(self.process_media_files, 'processing_buckets'):
                return
            
            buckets = self.process_media_files.processing_buckets
            if not buckets:
                return
            
            # Calculate max count for scaling
            max_count = max(buckets.values()) if buckets.values() else 1
            
            # Create HTML for barchart
            html_parts = ['<div style="display: flex; align-items: end; height: 60px; gap: 2px;">']
            
            for label, count in buckets.items():
                height = (count / max_count) * 50 if max_count > 0 else 0
                color = "#3b82f6" if count > 0 else "#e5e7eb"
                
                html_parts.append(f'''
                    <div style="display: flex; flex-direction: column; align-items: center; min-width: 40px;">
                        <div style="width: 20px; height: {height}px; background-color: {color}; border-radius: 2px 2px 0 0;"></div>
                        <div style="font-size: 10px; margin-top: 2px; text-align: center; color: #666;">{count}</div>
                        <div style="font-size: 8px; text-align: center; color: #999; transform: rotate(-45deg); white-space: nowrap;">{label}</div>
                    </div>
                ''')
            
            html_parts.append('</div>')
            
            # Add average processing time
            if hasattr(self.process_media_files, 'processing_times') and self.process_media_files.processing_times:
                avg_time = sum(self.process_media_files.processing_times) / len(self.process_media_files.processing_times)
                html_parts.append(f'<div style="margin-top: 5px; font-size: 12px; color: #666;">Avg: {avg_time:.1f}ms</div>')
            
            if self.processing_barchart:
                self.processing_barchart.content = ''.join(html_parts)
                
        except Exception as e:
            logger.error(f"Error updating processing barchart: {e}")

    def _update_counters_display(self) -> None:
        """Update counter displays."""
        if self.total_files_label and hasattr(self.total_files_label, "text"):
            self.total_files_label.text = str(self.scan_progress)

        if self.scan_progress > 0:
            estimated_media = int(self.scan_progress * 0.7)
            estimated_sidecars = int(self.scan_progress * 0.05)
            estimated_directories = max(
                1, int(self.scan_progress / 100) if self.scan_progress else 1,
            )

            if self.media_files_label and hasattr(self.media_files_label, "text"):
                self.media_files_label.text = str(estimated_media)
            if self.sidecars_label and hasattr(self.sidecars_label, "text"):
                self.sidecars_label.text = str(estimated_sidecars)
            if self.directories_label and hasattr(self.directories_label, "text"):
                self.directories_label.text = str(estimated_directories)

    def _finalize_scan(self) -> None:
        """Finalize scan and update UI."""
        self.scan_running = False

        # Disable abort button
        self.abort_manager.set_processing_active(active=False)

        # Re-enable START PROCESS button
        if self.start_process_button and hasattr(self.start_process_button, "enable"):
            self.start_process_button.enable()

        # Re-enable clear log button
        if self.clear_log_button:
            self.clear_log_button.enable()

        # Hide spinner
        if self.spinner:
            self.spinner.visible = False

        # Show progress bar and info for processing phase
        if self.progress_bar:
            self.progress_bar.visible = True
        if self.progress_info_label:
            self.progress_info_label.visible = True
        if self.processing_barchart:
            self.processing_barchart.visible = True

        # Update scan status
        if self.scan_status_label:
            self.scan_status_label.text = "Scan Complete"

        # Update final values in the card
        self._update_final_counters()

        # Enable details button when scan data is available
        if hasattr(self, "details_button") and self.details_button:
            self.details_button.enable()

        # Calculate and log scan duration
        scan_duration = self._calculate_scan_duration()
        duration_str = self._format_duration(scan_duration)

        # Final scan summary log (always show, regardless of log_extensive)
        summary_message = (
            f"Scan complete - Duration: {duration_str}, "
            f"Directories: {self.scan_results.get('directories', 0)}, "
            f"Files: {self.scan_results.get('total_files', 0)}, "
            f"Media files: {self.scan_results.get('media_files', 0)}, "
            f"Sidecars: {self.scan_results.get('sidecars', 0)}"
        )
        self._add_log_message(summary_message, "PROCESS")

        # Display any remaining log messages from queue
        self._display_log_queue()

        # Add final message directly to display (without queue)
        self._add_message_to_display(summary_message, "PROCESS")

    def _update_final_counters(self) -> None:
        """Update final counter values."""
        if self.total_files_label and hasattr(self.total_files_label, "text"):
            self.total_files_label.text = str(self.scan_results.get("total_files", 0))
        if self.media_files_label and hasattr(self.media_files_label, "text"):
            self.media_files_label.text = str(self.scan_results.get("media_files", 0))
        if self.sidecars_label and hasattr(self.sidecars_label, "text"):
            self.sidecars_label.text = str(self.scan_results.get("sidecars", 0))
        if self.directories_label and hasattr(self.directories_label, "text"):
            self.directories_label.text = str(self.scan_results.get("directories", 0))

    def _calculate_scan_duration(self) -> float:
        """Calculate scan duration in seconds."""
        if hasattr(self, "scan_start_time") and self.scan_start_time is not None:
            return time.time() - self.scan_start_time
        return 0.0

    def _format_duration(self, scan_duration: float) -> str:
        """Format duration as dd:hh:mm:ss.ss."""
        days = int(scan_duration // 86400)
        hours = int((scan_duration % 86400) // 3600)
        minutes = int((scan_duration % 3600) // 60)
        seconds = scan_duration % 60

        if days > 0:
            return f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:05.2f}"
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:05.2f}"
        if minutes > 0:
            return f"{minutes:02d}:{seconds:05.2f}"
        return f"{seconds:.2f}s"

    async def _start_processing(self) -> None:
        """Start MediaProcessing voor de geselecteerde directory."""
        if not self.scan_complete:
            ui.notify("Please complete scan first", type="warning")
            return

        if not self.dir_input or not self.dir_input.value:
            ui.notify("Please select a directory first", type="warning")
            return

        directory_path = self.dir_input.value

        # Start processing
        self.processing_running = True
        self.processing_aborted = False
        self.processing_results = {}
        self.processing_start_time = time.time()

        # Show spinner during processing
        if self.spinner:
            self.spinner.visible = True

        # Show progress bar during processing
        if self.progress_bar:
            self.progress_bar.visible = True
            self.progress_bar.value = 0.0  # Reset to 0%
        if self.progress_info_label:
            self.progress_info_label.visible = True

        if self.scan_status_label:
            self.scan_status_label.text = "Processing files..."

        # Keep START PROCESS button disabled during processing
        if self.start_process_button and hasattr(self.start_process_button, "disable"):
            self.start_process_button.disable()

        # Log processing start
        self._add_log_message(
            f"Starting processing for directory: {directory_path}", "PROCESS",
        )

        # Start UI update timer for processing phase
        self._setup_ui_updates()

        # Enable abort button
        self.abort_manager.set_processing_active(active=True)

        # Start processing in background with UI updates
        # Process files using the file list from scan phase
        if hasattr(self, "scan_file_list") and self.scan_file_list:
            file_list = self.scan_file_list
            self._add_log_message(f"Processing {len(file_list)} files from scan phase", "PROCESS")

            # Process files directly using the file list
            result = await self.process_media_files.process_files(file_list)
            self.processing_results = result

            # Log completion
            log_msg = (
                f"Processing completed: {result.processed_files} files, "
                f"{result.error_files} errors, "
                f"time: {result.processing_time:.2f}s"
            )
            self._add_log_message(log_msg, "PROCESS")

        # Update UI after processing is complete
        self._on_processing_complete()

    def _on_processing_complete(self) -> None:
        """Handle processing completion in UI."""
        self.processing_running = False

        # Hide spinner
        if self.spinner:
            self.spinner.visible = False

        self._update_processing_completion_ui()
        self._update_processing_buttons()
        self._finalize_processing()

        # Update status label to complete
        if self.scan_status_label and hasattr(self.scan_status_label, "text"):
            self.scan_status_label.text = "Ready to start"

        # Re-enable START PROCESS button
        if self.start_process_button and hasattr(self.start_process_button, "enable"):
            self.start_process_button.enable()

        # Add one final log queue display to catch any remaining messages
        self._display_log_queue()

    def _update_processing_completion_ui(self) -> None:
        """Update UI elements for processing completion."""
        value = self.scan_results.get("media_files", 0)
        total_media_files = int(str(value)) if value is not None else 0
        processed_files = self.process_media_files.processed_count

        # Set progress bar to 100% complete
        if self.progress_bar and hasattr(self.progress_bar, "value"):
            self.progress_bar.value = 1.0  # 100% complete

        if self.progress_info_label and total_media_files > 0:
            if self.processing_start_time is not None:
                total_time = time.time() - self.processing_start_time
            else:
                total_time = 0.0
            files_per_second = (
                processed_files / total_time if total_time > 0 else 0
            )
            total_time_str = self._format_duration(total_time)

            completion_text = (
                f"Processing Completed: 100% "
                f"({processed_files} Processed) "
                f"{files_per_second:.1f} files/sec "
                f"Total time: {total_time_str}"
            )
            if hasattr(self.progress_info_label, "text"):
                self.progress_info_label.text = completion_text

    def _update_processing_buttons(self) -> None:
        """Update button states after processing completion."""
        if self.scan_status_label and hasattr(self.scan_status_label, "text"):
            self.scan_status_label.text = "Processing completed"

    def _finalize_processing(self) -> None:
        """Finalize processing and enable export."""
        self.abort_manager.set_processing_active(active=False)

    def _abort_scan(self) -> None:
        """Abort the current scan or processing process."""
        if self.scan_running:
            self._abort_scan_process()
        elif self.processing_running:
            self._abort_processing_process()
        else:
            return

        # Common abort actions
        self._perform_common_abort_actions()

    def _abort_scan_process(self) -> None:
        """Abort the scan process."""
        self.scan_aborted = True
        self.scan_running = False

    def _abort_processing_process(self) -> None:
        """Abort the processing process."""
        self.processing_aborted = True
        self.processing_running = False

    def _perform_common_abort_actions(self) -> None:
        """Perform common actions when aborting."""
        # Disable abort button
        self.abort_manager.set_processing_active(active=False)

        # Update UI elements
        self._update_abort_ui_elements()

        # Update status based on what was aborted
        if self.scan_aborted:
            self._handle_scan_abort()
        elif self.processing_aborted:
            self._handle_processing_abort()

        # Display any remaining log messages from queue
        self._display_log_queue()

    def _update_abort_ui_elements(self) -> None:
        """Update UI elements during abort."""
        # Re-enable START PROCESS button after abort
        if self.start_process_button and hasattr(self.start_process_button, "enable"):
            self.start_process_button.enable()

        if self.clear_log_button and hasattr(self.clear_log_button, "enable"):
            self.clear_log_button.enable()

        if self.spinner and hasattr(self.spinner, "visible"):
            self.spinner.visible = False

        if self.progress_bar:
            self.progress_bar.visible = False
        if self.progress_info_label:
            self.progress_info_label.visible = False

    def _handle_scan_abort(self) -> None:
        """Handle scan abort specific actions."""
        if self.scan_status_label and hasattr(self.scan_status_label, "text"):
            self.scan_status_label.text = "Ready to start"

        # Enable details button if scan data is available
        value = self.scan_results.get("total_files", 0)
        total_files = int(str(value)) if value is not None else 0
        if (
            hasattr(self, "details_button")
            and self.details_button
            and total_files > 0
        ):
            self.details_button.enable()

        # Log abort message
        self._add_log_message("Scan aborted by user", "PROCESS")
        self._add_message_to_display("Scan aborted by user", "PROCESS")

    def _handle_processing_abort(self) -> None:
        """Handle processing abort specific actions."""
        if self.scan_status_label and hasattr(self.scan_status_label, "text"):
            self.scan_status_label.text = "Ready to start"

        # Log abort message
        self._add_log_message("Processing aborted by user", "PROCESS")
        self._add_message_to_display("Processing aborted by user", "PROCESS")

    def _add_log_message(self, message: str, level: str = "INFO") -> None:
        """Add a log message to the queue - UI update happens via timer."""
        # Use the queue manager for logging
        asyncio.create_task(self.queue_manager.put_log(level, message))

    def _display_log_queue(self) -> None:
        """Display all messages from queue in UI."""
        try:
            # Get messages from queue manager
            # This is a simplified version - in reality you'd get from the logging queue
            pass

        except OSError as e:
            pass

    def _add_message_to_display(self, message: str, level: str = "INFO") -> None:
        """Add a single message to display without using queue."""
        try:
            if self.log_column:
                # Add message to display queue
                if not hasattr(self, "log_messages"):
                    self.log_messages = []

                timestamp = datetime.now().strftime("%H:%M:%S")
                formatted_message = (
                    f"[{timestamp}] {level}: {message}"
                )
                self.log_messages.insert(0, formatted_message)  # Nieuwste bovenaan

                # Redraw all messages
                self.log_column.clear()
                with self.log_column:
                    for msg in self.log_messages:
                        ui.label(msg).classes("text-sm text-gray-700 font-mono")
        except OSError as e:
            pass

    def _clear_log(self) -> None:
        """Clear the log display."""
        try:
            if self.log_column:
                # Clear local log messages
                if hasattr(self, "log_messages"):
                    self.log_messages = []

                # Clear UI display
                self.log_column.clear()
        except OSError as e:
            pass

    def _reset_ui_elements(self) -> None:
        """Reset UI elements to initial state."""
        # Reset scan state
        self.scan_running = False
        self.scan_aborted = False
        self.scan_complete = False

        # Reset processing state
        self.processing_running = False
        self.processing_aborted = False
        self.processing_results = {}

        # Reset progress
        self.scan_progress = 0

        # Reset UI components
        self._reset_ui_components()

        # Reset counters
        self._reset_counters()

        # Reset buttons
        self._reset_buttons()

    def _reset_ui_components(self) -> None:
        """Reset UI components."""
        if self.spinner and hasattr(self.spinner, "visible"):
            self.spinner.visible = False
        # Hide progress bar and info label at initialization
        if self.progress_bar:
            self.progress_bar.visible = False
            if hasattr(self.progress_bar, "value"):
                self.progress_bar.value = 0.0
        if self.progress_info_label:
            self.progress_info_label.visible = False
            if hasattr(self.progress_info_label, "text"):
                progress_text = (
                    "Progress info: Completed: 0% "
                    "(0 Found/0 Files processed, incl. SideCars)"
                )
                self.progress_info_label.text = progress_text
        if self.scan_status_label and hasattr(self.scan_status_label, "text"):
            self.scan_status_label.text = "Scan Complete"

    def _reset_counters(self) -> None:
        """Reset counter displays."""
        if self.total_files_label and hasattr(self.total_files_label, "text"):
            self.total_files_label.text = "0"
        if self.media_files_label and hasattr(self.media_files_label, "text"):
            self.media_files_label.text = "0"
        if self.sidecars_label and hasattr(self.sidecars_label, "text"):
            self.sidecars_label.text = "0"
        if self.directories_label and hasattr(self.directories_label, "text"):
            self.directories_label.text = "0"

    def _reset_buttons(self) -> None:
        """Reset button states."""
        if self.details_button and hasattr(self.details_button, "disable"):
            self.details_button.disable()


def create_fill_db_page() -> FillDBPage:
    """Maak de database vullen pagina."""
    return FillDBPage()


if __name__ == "__main__":
    create_fill_db_page()
    ui.run(title="Fill Database Page", port=8082)
