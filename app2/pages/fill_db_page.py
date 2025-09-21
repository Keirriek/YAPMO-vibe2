"""Fill Database Page voor YAPMO applicatie."""

import asyncio
import atexit
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from globals import abort_button_manager, logging_service
from local_directory_picker import pick_directory
from media_processing import MediaProcessing
from nicegui import ui
from shutdown_manager import handle_exit_click
from theme import YAPMOTheme
from config import read_config, get_param


class FillDBPage:
    """Database vullen pagina van de YAPMO applicatie."""

    def __init__(self) -> None:
        """Initialize the database fill page."""
        # Get the path to config.json (same directory as main.py)
        self.config_path = Path(__file__).parent.parent / "config.json"

        # Initialize MediaProcessing (will be created during processing)
        self.media_processor: Any = None

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
        self.export_log_button: Any = None
        self.clear_log_button: Any = None
        self.scan_status_label: Any = None
        self.progress_info_label: Any = None
        self.details_button: Any = None

        self.test_output_area: Any = None

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
        self.processing_status_label: Any = None
        self.processed_files_label: Any = None
        self.json_records_label: Any = None
        self.json_output_column: Any = None
        self.export_json_button: Any = None
        self.clear_json_button: Any = None
        self.start_process_button: Any = None

        self.current_config: Any = None

        self._create_page()

        # Register abort handler for this page
        abort_button_manager.register_abort_handler("fill_db", self._abort_scan)

        # Cleanup when page is destroyed
        def cleanup() -> None:
            abort_button_manager.unregister_abort_handler("fill_db")

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
            self._create_test_output_panel()

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
        Progress and Log Panel (Hele breedte - Wit met Donkere Blauwe Rand)
        progress_card_classes = (
            "w-full bg-white border-2 border-blue-800 rounded-lg shadow-lg"
        )
        with ui.card().classes(progress_card_classes), \
             ui.card_section().classes("w-full p-6"):
            ui.label("Progress and Log").classes(
                "text-xl font-semibold text-gray-800 mb-4")

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
            ui.label("Log info:").classes("text-grey-700 font-medium mb-2")

            # Log display area (volledige breedte en hoogte)
            log_area_classes = "h-64 bg-gray-100 rounded-lg p-4 mb-4"
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

    def _create_test_output_panel(self) -> None:
        """Create the test output panel."""
        # Test Output Panel (Hele breedte - Wit met Groene Rand)
        test_card_classes = (
            "w-full bg-white border-2 border-green-500 rounded-lg shadow-lg"
        )
        with ui.card().classes(test_card_classes), \
             ui.card_section().classes("w-full p-6"):
            ui.label("Test Output - JSON Data").classes(
                "text-xl font-semibold text-gray-800 mb-4")

            # Processing status row
            with ui.row().classes("w-full items-center gap-4 mb-4"):
                status_text = "Ready for processing"
                self.processing_status_label = ui.label(status_text).classes(
                    "text-gray-700 font-medium")

                with ui.column().classes("items-center"):
                    self.processed_files_label = ui.label("0").classes(
                        "text-green-600 text-2xl font-bold")
                    ui.label("Processed Files").classes(
                        "text-gray-600 text-sm")

                with ui.column().classes("items-center"):
                    self.json_records_label = ui.label("0").classes(
                        "text-green-600 text-2xl font-bold")
                    ui.label("JSON Records").classes(
                        "text-gray-600 text-sm")

            # JSON Output Area
            ui.label("Generated JSON Data:").classes(
                "text-gray-700 font-medium mb-2")

            test_area_classes = "w-full h-96 bg-gray-100 rounded-lg p-4 mb-4"
            self.test_output_area = ui.scroll_area().classes(test_area_classes)
            with self.test_output_area:
                self.json_output_column = ui.column().classes("w-full")

            # Export and Clear buttons
            with ui.row().classes("w-full items-center gap-4"):
                self.export_json_button = YAPMOTheme.create_button(
                    "EXPORT JSON",
                    self._export_json,
                    "secondary",
                    "md",
                )
                # Disable initially
                self.export_json_button.disable()

                self.clear_json_button = YAPMOTheme.create_button(
                    "CLEAR JSON",
                    self._clear_json,
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

    def _load_config_parameters(self) -> dict[str, Any]:
        """Load configuration parameters for processing."""
        config = read_config()
        processing_config = config.get("processing", {})
        extensions_config = config.get("extensions", {})

        return {
            "nicegui_update_interval": processing_config.get("nicegui_update_interval"),
            "ui_update": processing_config.get("ui_update"),
            "log_extensive": config.get("logging", {}).get("log_extensive"),
            "max_workers": processing_config.get("max_workers"),
            "log_files_count_update": config.get("logging", {}).get("log_files_count_update"),
            "image_extensions": extensions_config.get("image_extensions"),
            "video_extensions": extensions_config.get("video_extensions"),
            "sidecar_extensions": extensions_config.get("sidecar_extensions"),
        }

    def _show_details(self) -> None:
        """Show file type details in a popup."""
        by_extension = self.scan_results.get("by_extension")
        if not self.scan_results or not isinstance(by_extension, dict):
            notify_msg = "No scan data available. Please scan a directory first."
            ui.notify(notify_msg, type="info")
            return

        # Get config for relevant extensions
        config = self._load_config_parameters()
        image_exts = config["image_extensions"]
        video_exts = config["video_extensions"]
        sidecar_exts = config["sidecar_extensions"]
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
        #DEBUG_scan_start
        logging_service.log("DEBUG", "Starting scan process") #DEBUG_scan_process_start

        if self.scan_running:
            return

        # Validate directory
        directory = self._validate_scan_directory()
        if not directory:
            return

        # Initialize scan
        self._initialize_scan_state(directory)

        # Start scan using NiceGUI's run_in_executor
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, self._scan_directory_sync, directory, self.current_config,
        )
        await self._on_scan_complete(result)

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
        # Load config parameters
        config = self._load_config_parameters()
        self.current_config = config

        # Start scan process
        self.scan_running = True
        self.scan_aborted = False
        self.scan_start_time = time.time()

        # Update UI elements
        self._update_scan_ui_elements()

        # Log scan start
        self._add_log_message(f"Starting scan of directory: {directory}", "PROCESS")
        logging_service.log("DEBUG", "Test INFO log from fill_db_page") #DEBUG_test_log

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
        self._setup_ui_updates(config["nicegui_update_interval"], config["ui_update"])

        # Enable abort button
        abort_button_manager.set_processing_active(active=True)

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

    def _scan_directory_sync(self, directory: str, config: dict) -> dict:
        """Scan directory synchronously for io_bound."""
        try:
            return self._perform_directory_scan(directory, config)
        except OSError as e:
            logging_service.log("ERROR", f"Scan error: {e}")
            return {"error": str(e)}

    def _perform_directory_scan(self, directory: str, config: dict) -> dict:
        """Perform the actual directory scanning."""
        # Initialize counters
        total_files = 0
        media_files = 0
        sidecars = 0
        directories = 0
        by_extension: dict[str, int] = {}

        # Initialize file list for processing phase
        file_list = []

        # Get supported extensions
        image_exts = config["image_extensions"]
        video_exts = config["video_extensions"]
        supported_extensions = image_exts + video_exts
        sidecar_extensions = config["sidecar_extensions"]

        # Scan directory recursively
        for root, dirs, files in os.walk(directory):
            if self.scan_aborted or not abort_button_manager.is_processing_active():
                break

            # Count directories
            directories += len(dirs)

            # Process files in this directory
            for file in files:
                is_aborted = self.scan_aborted
                is_processing = abort_button_manager.is_processing_active()
                if is_aborted or not is_processing:
                    break

                file_ext = Path(file).suffix.lower()

                total_files += 1

                # Count by extension
                if file_ext in by_extension:
                    by_extension[file_ext] += 1
                else:
                    by_extension[file_ext] = 1

                # Count media files
                if file_ext in supported_extensions:
                    media_files += 1
                    # Add to file list for processing phase
                    file_list.append(str(Path(root) / file))

                # Count sidecars
                if file_ext in sidecar_extensions:
                    sidecars += 1

                # Update progress
                self.scan_progress = total_files

            # Extensive logging if enabled
            if config["log_extensive"] and files:
                self._log_directory_summary(
                    root, files, supported_extensions, sidecar_extensions,
                )

        # Return final results
        return {
            "total_files": total_files,
            "media_files": media_files,
            "sidecars": sidecars,
            "directories": directories,
            "by_extension": by_extension,
            "file_list": file_list,  # Add file list for processing phase
        }

    def _count_valid_sidecars(self, _root: str, files: list[str],
                              supported_extensions: list[str],
                              sidecar_extensions: list[str]) -> int:
        """Count valid sidecars that belong to media files in this directory."""
        valid_sidecars = 0

        # Get all media files in this directory
        media_files = [
            f for f in files
            if Path(f).suffix.lower() in supported_extensions
        ]

        # For each media file, check if sidecars exist
        for media_file in media_files:
            media_name = Path(media_file).stem  # Name without extension

            # Check each sidecar extension
            for sidecar_ext in sidecar_extensions:
                sidecar_name = media_name + sidecar_ext
                if sidecar_name in files:
                    valid_sidecars += 1

        return valid_sidecars

    def _log_directory_summary(self, root: str, files: list[str],
                              supported_extensions: list[str],
                              sidecar_extensions: list[str]) -> None:
        """Log summary for a directory."""
        media_count = sum(
            1 for f in files if Path(f).suffix.lower() in supported_extensions
        )
        sidecar_count = self._count_valid_sidecars(
            root, files, supported_extensions, sidecar_extensions,
        )
        if media_count > 0 or sidecar_count > 0:
            log_msg = (
                f"Directory {root}: {media_count} media files, "
                f"{sidecar_count} sidecars"
            )
            logging_service.log("DEBUG", f"Directory summary: {log_msg}")

    async def _on_scan_complete(self, result: dict) -> None:
        """Handle scan completion callback."""
        if result and "error" in result:
            self._add_log_message(f'Scan error: {result["error"]}', "ERROR")
        else:
            # Update scan results with final values
            if hasattr(self, "scan_results"):
                self.scan_results.update(result)

            # Store file list for processing phase
            if "file_list" in result:
                self.scan_file_list = result["file_list"]

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

    def _setup_ui_updates(
        self, nicegui_interval_ms: int, ui_update_interval_ms: int,
    ) -> None:
        """Set up UI updates and NiceGUI connection alive."""

        # NiceGUI connection alive timer (technical, keeps connection alive)
        def keep_nicegui_alive() -> None:
            if self.scan_running and not self.scan_aborted:
                ui.timer(nicegui_interval_ms / 1000.0, keep_nicegui_alive, once=True)

        # UI update timer (user interface updates)
        def update_ui() -> None:
            #DEBUG
            processed_files = 0
            if hasattr(self, "media_processor") and self.media_processor is not None:
                processed_files = self.media_processor.files_processed
            logging_service.log(
                "DEBUG",
                f"UI update timer fired - scan_running={self.scan_running}, "
                f"processing_running={self.processing_running}, "
                f"scan_progress={self.scan_progress}, "
                f"processed_files={processed_files}",
            )

            if self.scan_aborted and self.processing_aborted:
                return

            # Check if scan is complete and finalize if needed
            if self.scan_complete and self.scan_running:
                self._finalize_scan()
                return

            try:
                self._update_progress_display()
                logging_service.log(
                    "DEBUG", "About to call _update_processing_progress_display",
                )
                self._update_processing_progress_display()

                # Only show estimated counters during scan, not after
                if self.scan_running:
                    self._update_counters_display()
                else:
                    # After scan, show final counters
                    self._update_final_counters()

                self._display_log_queue()

                # Schedule next update if still running or if we need to show final logs
                logging_service.log(
                    "DEBUG",
                    f"Scheduling next timer - scan_running={self.scan_running}, "
                    f"scan_aborted={self.scan_aborted}, "
                    f"processing_running={self.processing_running}, "
                    f"processing_aborted={self.processing_aborted}",
                )
                if ((self.scan_running and not self.scan_aborted) or
                     (self.processing_running and not self.processing_aborted)):
                    ui.timer(ui_update_interval_ms / 1000.0, update_ui, once=True)
                    logging_service.log("DEBUG", "Next timer scheduled")
                else:
                    logging_service.log("DEBUG", "No next timer scheduled")

            except OSError as e:
                logging_service.log("WARNING", f"UI update error: {e}")
                # Don't schedule next update on error

        # Start both timers
        logging_service.log(
            "DEBUG",
            f"Starting UI timers - "
            f"nicegui_interval_ms={nicegui_interval_ms}, "
            f"ui_update_interval_ms={ui_update_interval_ms}",
        )
        ui.timer(
            nicegui_interval_ms / 1000.0, keep_nicegui_alive, once=True,
        )  # Keep connection alive
        ui.timer(ui_update_interval_ms / 1000.0, update_ui, once=True)  # UI updates
        logging_service.log("DEBUG", "UI timers started successfully")

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
        #DEBUG
        logging_service.log(
            "DEBUG",
            f"Checking processing_running: {self.processing_running}",
        )

        if not self.processing_running:
            return

        #DEBUG
        processed_files = 0
        if hasattr(self, "media_processor") and self.media_processor is not None:
            processed_files = self.media_processor.files_processed
        logging_service.log(
            "DEBUG",
            f"Updating processing progress - "
            f"total_media_files={self.scan_results.get('media_files', 0)}, "
            f"processed_files={processed_files}",
        )

        # Get processing data - use media_files count from scan results
        value = self.scan_results.get("media_files", 0)
        total_media_files = int(str(value)) if value is not None else 0
        # processed_files is already set above

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
                #DEBUG
                logging_service.log(
                    "DEBUG",
                    f"Updated progress bar to {progress_percentage}% "
                    f"({processed_files}/{total_media_files})",
                )

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
                    #DEBUG
                    logging_service.log(
                        "DEBUG", f"Updated progress info to: {progress_text}",
                    )

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
        abort_button_manager.set_processing_active(active=False)



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
        abort_button_manager.set_processing_active(active=False)

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
        if (self.processing_status_label and
            hasattr(self.processing_status_label, "text")):
            self.processing_status_label.text = "Ready to start"

        # Log abort message
        self._add_log_message("Processing aborted by user", "PROCESS")
        self._add_message_to_display("Processing aborted by user", "PROCESS")

    def _add_log_message(self, message: str, level: str = "INFO") -> None:
        """Add a log message to the queue - UI update happens via timer."""
        # Gebruik de globale logging service
        logging_service.log(level, message)

    def _display_log_queue(self) -> None:
        """Display all messages from queue in UI."""
        try:
            new_messages = logging_service.get_ui_messages()  # Get and clear queue



            if new_messages and self.log_column:
                # Add new messages to display queue (let op volgorde)
                if not hasattr(self, "log_messages"):
                    self.log_messages = []

                for msg_data in new_messages:
                    timestamp = msg_data["timestamp"].split(" ")[1]
                    formatted_message = (
                        f"[{timestamp}] {msg_data['level']}: {msg_data['message']}"
                    )
                    self.log_messages.insert(0, formatted_message)  # Nieuwste bovenaan

                # Redraw all messages
                self.log_column.clear()
                with self.log_column:
                    for msg in self.log_messages:
                        ui.label(msg).classes("text-sm text-gray-700 font-mono")

        except OSError as e:
            logging_service.log("WARNING", f"Log display error: {e}")

    def _add_message_to_display(self, message: str, level: str = "INFO") -> None:
        """Add a single message to display without using queue."""
        try:
            if self.log_column:
                # Add message to display queue
                if not hasattr(self, "log_messages"):
                    self.log_messages = []

                timestamp = datetime.now().strftime("%H:%M:%S")  # noqa: DTZ005
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
            logging_service.log("WARNING", f"Log display error: {e}")

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
            logging_service.log("WARNING", f"Log clear error: {e}")

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

        # Clear JSON output
        if self.json_output_column:
            self.json_output_column.clear()

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
        if (
            self.processing_status_label
            and hasattr(self.processing_status_label, "text")
        ):
            self.processing_status_label.text = "Ready for processing"

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
        if self.processed_files_label and hasattr(self.processed_files_label, "text"):
            self.processed_files_label.text = "0"
        if self.json_records_label and hasattr(self.json_records_label, "text"):
            self.json_records_label.text = "0"





    def _reset_buttons(self) -> None:
        """Reset button states."""
        if self.details_button and hasattr(self.details_button, "disable"):
            self.details_button.disable()

        if self.export_json_button and hasattr(self.export_json_button, "disable"):
            self.export_json_button.disable()

    async def _start_processing(self) -> None:
        """Start MediaProcessing voor de geselecteerde directory."""
        #DEBUG
        logging_service.log(
            "DEBUG", "Processing button pressed - starting _start_processing",
        )

        # DEBUG: Processing start
        logging_service.log("DEBUG", "Starting processing process")

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

        #DEBUG
        logging_service.log(
            "DEBUG", f"Set processing_running = {self.processing_running}",
        )

        # Show spinner during processing
        if self.spinner:
            self.spinner.visible = True

        # Show progress bar during processing
        if self.progress_bar:
            self.progress_bar.visible = True
            self.progress_bar.value = 0.0  # Reset to 0%
        if self.progress_info_label:
            self.progress_info_label.visible = True


        if self.processing_status_label:
            self.processing_status_label.text = "Processing files..."

        # Keep START PROCESS button disabled during processing
        if self.start_process_button and hasattr(self.start_process_button, "disable"):
            self.start_process_button.disable()

        # Log processing start
        self._add_log_message(
            f"Starting processing for directory: {directory_path}", "PROCESS",
        )

        # Create MediaProcessing instance with current config
        config = self._load_config_parameters()
        log_files_count_update = config.get("log_files_count_update")
        self.media_processor = MediaProcessing(log_files_count_update=log_files_count_update)
        

        
        # Start UI update timer for processing phase
        logging_service.log(
            "DEBUG", f"About to call _setup_ui_updates with config: {config}",
        )
        self._setup_ui_updates(config["nicegui_update_interval"], config["ui_update"])
        logging_service.log("DEBUG", "_setup_ui_updates completed")

        # Enable abort button
        abort_button_manager.set_processing_active(active=True)

        # Start processing in background with UI updates
        logging_service.log(
            "DEBUG", "About to start batch processing - UI should remain responsive",
        )  # DEBUG

        # Process in batches to allow UI updates
        await self._process_directory_in_batches(directory_path)

        logging_service.log(
            "DEBUG", "Batch processing completed - UI should have remained responsive",
        )  # DEBUG

        # Update UI after processing is complete
        self._on_processing_complete()

    async def _process_directory_in_batches(self, directory_path: str) -> None:
        """Process directory in batches to allow UI updates."""

        try:
            # Reset processing results
            self.processing_results = {
                "total_files": 0,
                "processed_files": 0,
                "errors": [],
                "start_time": None,
                "end_time": None,
            }

            # Set processing state
            self.processing_aborted = False
            self.processing_results["start_time"] = datetime.now(UTC)

            # Start MediaProcessing
            logging_service.log(
                "DEBUG", "About to call media_processor.process_directory",
            )

            # Use file list from scan phase instead of directory scan
            logging_service.log("DEBUG", "Using file list from scan phase")
            if hasattr(self, "scan_file_list") and self.scan_file_list:
                file_list = self.scan_file_list
                logging_service.log(
                    "DEBUG", f"Found {len(file_list)} files from scan phase",
                )

                # Process files directly using the file list
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, self.media_processor.process_files_from_list, file_list,
                )
                logging_service.log("DEBUG", "run_in_executor completed")
            else:
                # Fallback to original method if file list not available
                logging_service.log(
                    "DEBUG", "No file list found, using original method",
                )
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, self.media_processor.process_directory, directory_path,
                )
                logging_service.log("DEBUG", "run_in_executor completed")

            logging_service.log("DEBUG", "media_processor.process_directory completed")

            # Update processing results (database writes now happen in _process_single_file)
            self.processing_results = result

            # Log completion
            log_msg = (
                f"Processing completed: {result['processed_count']} files, "
                f"{result['error_count']} errors, "
                f"time: {result['processing_time']:.2f}s"
            )
            logging_service.log("PROCESS", log_msg)

        except (OSError, ValueError, RuntimeError) as e:
            logging_service.log("ERROR", f"Processing error: {e}")
            self.processing_results = {
                "processed_count": 0,
                "error_count": 1,
                "processing_time": 0,
                "results": [],
            }

    def _on_processing_complete(self) -> None:
        """Handle processing completion in UI."""
        self.processing_running = False

        # Hide spinner
        if self.spinner:
            self.spinner.visible = False

        self._update_processing_completion_ui()
        self._update_processing_buttons()
        self._update_processing_counters()
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
        processed_files = 0
        if hasattr(self, "media_processor") and self.media_processor is not None:
            processed_files = self.media_processor.files_processed

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
        if self.processing_status_label and hasattr(
            self.processing_status_label, "text",
        ):
            self.processing_status_label.text = "Processing completed"

    def _update_processing_counters(self) -> None:
        """Update counter displays after processing completion."""
        processed_files = 0
        if hasattr(self, "media_processor") and self.media_processor is not None:
            processed_files = self.media_processor.files_processed
        if self.processed_files_label and hasattr(self.processed_files_label, "text"):
            self.processed_files_label.text = str(processed_files)
        if self.json_records_label and hasattr(self.json_records_label, "text"):
            self.json_records_label.text = str(processed_files)

    def _finalize_processing(self) -> None:
        """Finalize processing and enable export."""
        if self.export_json_button and hasattr(self.export_json_button, "enable"):
            self.export_json_button.enable()

        self._update_json_display()
        abort_button_manager.set_processing_active(active=False)

    def _update_json_display(self) -> None:
        """Update JSON output display."""
        if not self.json_output_column:
            return

        # Clear existing content
        self.json_output_column.clear()

        # Get results from MediaProcessing
        results = self.processing_results.get("results", [])

        if not results:
            with self.json_output_column:
                ui.label("No JSON data generated").classes("text-gray-500 italic")
            return

        # Display first 10 records as sample
        sample_size = min(10, len(results))

        with self.json_output_column:
            ui.label(
                f"Showing {sample_size} of {len(results)} records:",
            ).classes(
                "text-sm text-gray-600 mb-2",
            )

            for i, record in enumerate(results[:sample_size]):
                record_label = f"Record {i+1}:"
                ui.label(record_label).classes("text-sm font-medium text-gray-700 mt-2")
                ui.code(
                    json.dumps(record, indent=2, ensure_ascii=False),
                ).classes(
                    "text-xs bg-gray-200 p-2 rounded w-full",
                )

    def _export_json(self) -> None:
        """Export JSON data to file."""
        if not self.processing_results:
            ui.notify("No JSON data to export", type="warning")
            return

        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # noqa: DTZ005
            filename = (
                f"yapmo_processing_results_{timestamp}.json"
            )

            # Export results
            with Path(filename).open("w", encoding="utf-8") as f:
                json.dump(self.processing_results, f, indent=2, ensure_ascii=False)

            ui.notify(f"JSON data exported to {filename}", type="positive")

        except OSError as e:
            ui.notify(f"Error exporting JSON: {e}", type="negative")

    def _clear_json(self) -> None:
        """Clear JSON output display."""
        self.processing_results = {}

        if self.json_output_column and hasattr(self.json_output_column, "clear"):
            self.json_output_column.clear()

        if self.processed_files_label and hasattr(
            self.processed_files_label, "text",
        ):
            self.processed_files_label.text = "0"
        if self.json_records_label and hasattr(self.json_records_label, "text"):
            self.json_records_label.text = "0"
        if self.export_json_button and hasattr(self.export_json_button, "disable"):
            self.export_json_button.disable()
        if self.processing_status_label and hasattr(
            self.processing_status_label, "text",
        ):
            self.processing_status_label.text = "Ready for processing"

        ui.notify("JSON data cleared", type="info")


def create_fill_db_page() -> FillDBPage:
    """Maak de database vullen pagina."""
    return FillDBPage()


if __name__ == "__main__":
    create_fill_db_page()
    ui.run(title="Fill Database Page", port=8082)
