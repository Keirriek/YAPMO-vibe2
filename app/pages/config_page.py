"""Configuration Page voor YAPMO applicatie."""

from typing import Any

from config import get_param, set_param
from local_directory_picker import pick_directory
from nicegui import ui
from shutdown_manager import handle_exit_click
from theme import YAPMOTheme
from core.logging_service_v2 import logging_service


class ConfigPage:
    """Configuratie pagina van de YAPMO applicatie."""

    def __init__(self) -> None:
        """Initialize the configuration page."""
        self.ui_elements: dict[str, Any] = {}
        self._create_page()

    def _create_page(self) -> None:
        """Maak de configuratie pagina."""

        @ui.page("/config")
        def config_page() -> None:
            with YAPMOTheme.page_frame("Configuration", exit_handler=handle_exit_click):
                self._create_content()

    def _create_content(self) -> None:
        """Maak de content van de configuratie pagina."""
        # Header met action buttons
        with ui.card().classes("w-full mb-6"), ui.row().classes(
            "w-full items-center justify-between",
        ):
                ui.label("YAPMO Configuration").classes("text-h4")

                with ui.row().classes("gap-2"):
                    YAPMOTheme.create_button(
                        "Reset to Defaults",
                        on_click=self.reset_to_defaults,
                        color="warning",
                    )

                    YAPMOTheme.create_button(
                        "Save Configuration",
                        on_click=self.save_config,
                        color="positive",
                    )

        # Main content met tabs
        with ui.tabs().classes("w-full") as tabs:
            general_tab = ui.tab("General", icon="settings")
            database_tab = ui.tab("Database", icon="database")
            logging_tab = ui.tab("Logging", icon="info")
            paths_tab = ui.tab("Paths", icon="folder")
            extensions_tab = ui.tab("File Types", icon="description")
            metadata_tab = ui.tab("Metadata", icon="info")
            advanced_tab = ui.tab("Advanced", icon="tune")

        with ui.tab_panels(tabs, value=general_tab).classes("w-full"):

            # General Settings Tab
            with ui.tab_panel(general_tab):
                self._create_general_settings()

            # Database Tab
            with ui.tab_panel(database_tab):
                self._create_database_settings()

            # Logging Tab
            with ui.tab_panel(logging_tab):
                self._create_logging_settings()

            # Paths Tab
            with ui.tab_panel(paths_tab):
                self._create_paths_settings()

            # File Types Tab
            with ui.tab_panel(extensions_tab):
                self._create_extensions_settings()

            # Metadata Tab
            with ui.tab_panel(metadata_tab):
                self._create_metadata_settings()

            # Advanced Tab
            with ui.tab_panel(advanced_tab):
                self._create_advanced_settings()

    def _create_general_settings(self) -> None:
        """Maak general settings sectie."""
        with ui.card().classes("w-full mb-4"):
            ui.label("General Application Settings").classes("text-h6 q-mb-md")

            with ui.grid(columns=2).classes("w-full gap-4"):
                self.ui_elements["app_name"] = ui.input(
                    "Application Name",
                    value=get_param("general", "app_name"),
                    placeholder="YAPMO",
                ).classes("w-full")

                self.ui_elements["app_version"] = ui.input(
                    "Application Version",
                    value=get_param("general", "app_version"),
                    placeholder="2.0.0",
                ).classes("w-full")

                self.ui_elements["app_description"] = ui.textarea(
                    "Application Description",
                    value=get_param("general", "app_description"),
                    placeholder="Yet Another Photo Manager and Organizer",
                ).classes("w-full")

    def _create_logging_settings(self) -> None:
        """Maak logging settings sectie."""
        with ui.card().classes("w-full mb-4"):
            ui.label("Logging Settings").classes("text-h6 q-mb-md")

            # File paths
            with ui.grid(columns=2).classes("w-full gap-4 mb-4"):
                self.ui_elements["log_file_path"] = ui.input(
                    "Log File Path",
                    value=get_param("logging", "log_file_path"),
                    placeholder="./log/yapmo_log.log",
                ).classes("w-full")

                self.ui_elements["debug_file_path"] = ui.input(
                    "Debug File Path",
                    value=get_param("logging", "debug_file_path"),
                    placeholder="./log/yapmo_debug.log",
                ).classes("w-full")

            # Keep existing clean log setting
            self.ui_elements["log_clean"] = ui.checkbox(
                "Clean Log File Before Start",
                value=get_param("logging", "log_clean"),
            ).classes("w-full mb-4")

            # Log levels matrix
            ui.label("Log Level Routing").classes("text-h6 mb-2")
            
            # Get current levels config
            levels_config = get_param("logging", "levels")
            levels = ["ERROR", "WARNING", "INFO", "INFO_EXTRA", "DEBUG", "TEST_AI", "TEST1", "TEST2", "TEST3", "TEST4"]
            routes = ["t", "ui", "df"]
            route_labels = {"t": "Terminal", "ui": "UI", "df": "Debug File"}
            
            # Create matrix using grid layout instead of table
            with ui.grid(columns=4).classes("w-full gap-2"):
                # Header row
                ui.label("Level").classes("font-bold p-2")
                ui.label("Terminal").classes("font-bold text-center p-2")
                ui.label("UI").classes("font-bold text-center p-2")
                ui.label("Debug File").classes("font-bold text-center p-2")
                
                # Data rows
                for level in levels:
                    ui.label(level).classes("font-medium p-2")
                    
                    # Terminal checkbox
                    self.ui_elements[f"log_{level}_t"] = ui.checkbox(
                        "",
                        value="t" in levels_config.get(level, []),
                    ).classes("mx-auto")
                    
                    # UI checkbox
                    self.ui_elements[f"log_{level}_ui"] = ui.checkbox(
                        "",
                        value="ui" in levels_config.get(level, []),
                    ).classes("mx-auto")
                    
                    # Debug file checkbox
                    self.ui_elements[f"log_{level}_df"] = ui.checkbox(
                        "",
                        value="df" in levels_config.get(level, []),
                    ).classes("mx-auto")

    def _create_paths_settings(self) -> None:
        """Maak paths settings sectie."""
        with ui.card().classes("w-full"):
            ui.label("Directory Paths").classes("text-h6 q-mb-md")

            with ui.column().classes("w-full gap-4"):
                # Source Path
                with ui.row().classes("w-full items-center"):
                    self.ui_elements["source_path"] = ui.input(
                        "Source Path",
                        value=get_param("paths", "source_path"),
                        placeholder="/workspaces",
                    ).classes("flex-grow")

                    YAPMOTheme.create_button(
                        "Browse",
                        on_click=lambda: self._browse_folder("source_path"),
                        color="secondary",
                    )

                # Search Path
                with ui.row().classes("w-full items-center"):
                    self.ui_elements["search_path"] = ui.input(
                        "Search Path",
                        value=get_param("paths", "search_path"),
                        placeholder="/Pictures-test",
                    ).classes("flex-grow")

                    YAPMOTheme.create_button(
                        "Browse",
                        on_click=lambda: self._browse_folder("search_path"),
                        color="secondary",
                    )

                # Browse Path
                with ui.row().classes("w-full items-center"):
                    self.ui_elements["browse_path"] = ui.input(
                        "Browse Path",
                        value=get_param("paths", "browse_path"),
                        placeholder="/",
                    ).classes("flex-grow")

                    YAPMOTheme.create_button(
                        "Browse",
                        on_click=lambda: self._browse_folder("browse_path"),
                        color="secondary",
                    )

    def _create_extensions_settings(self) -> None:
        """Maak file extensions settings sectie."""
        with ui.grid(columns=3).classes("w-full gap-4"):
            # Image Extensions
            with ui.card().classes("w-full"):
                ui.label("Image Extensions (read only)").classes("text-h6 q-mb-md")

                with ui.column().classes("w-full"):
                    self.ui_elements["image_extensions"] = ui.textarea(
                        placeholder="Enter extensions, one per line",
                        value="\n".join(get_param("extensions", "image_extensions")),
                    ).classes("w-full h-32")

                    ui.label(
                        "Supported: .jpg, .jpeg, .png, .tiff, .raw, .arw, etc.",
                    ).classes("text-sm text-gray-600")

            # Video Extensions
            with ui.card().classes("w-full"):
                ui.label("Video Extensions (read only)").classes("text-h6 q-mb-md")

                with ui.column().classes("w-full"):
                    self.ui_elements["video_extensions"] = ui.textarea(
                        placeholder="Enter extensions, one per line",
                        value="\n".join(get_param("extensions", "video_extensions")),
                    ).classes("w-full h-32")

                    ui.label("Supported: .mp4, .mov, .avi, .mkv, .wmv, etc.").classes(
                        "text-sm text-gray-600")

            # Sidecar Extensions
            with ui.card().classes("w-full"):
                ui.label("Sidecar Extensions (read only)").classes("text-h6 q-mb-md")

                with ui.column().classes("w-full"):
                    self.ui_elements["sidecar_extensions"] = ui.textarea(
                        placeholder="Enter extensions, one per line",
                        value="\n".join(get_param("extensions", "sidecar_extensions")),
                    ).classes("w-full h-32")

                    ui.label("Supported: .aae, .xmp, .acr, .on1, .dop, .pp3").classes(
                        "text-sm text-gray-600")

    def _create_metadata_settings(self) -> None:
        """Maak metadata settings sectie."""
        with ui.card().classes("w-full"):
            ui.label("Metadata Settings").classes("text-h6 q-mb-md")

            with ui.column().classes("w-full gap-4"):
                # Placeholder voor metadata instellingen
                self.ui_elements["metadata_enabled"] = ui.checkbox(
                    "Enable Metadata Extraction",
                    value=True,
                )

                ui.label("Metadata field mappings will be displayed here when config system is implemented.").classes("text-sm text-gray-600")

    def _create_advanced_settings(self) -> None:
        """Maak advanced settings sectie."""
        with ui.card().classes("w-full"):
            ui.label("Advanced Settings").classes("text-h6 q-mb-md")

            with ui.column().classes("w-full gap-4"):
                # Processing Settings
                ui.label("Processing Settings").classes("text-h5 q-mb-md")

                with ui.grid(columns=2).classes("w-full gap-4"):
                    # Max Workers
                    self.ui_elements["max_workers"] = ui.number(
                        "Max Workers",
                        value=get_param("processing", "max_workers"),
                        min=1,
                        max=32,
                        format="%i",
                    ).classes("w-full")

                    # NiceGUI Update Interval
                    self.ui_elements["nicegui_update_interval"] = ui.number(
                        "NiceGUI Update Interval (ms)",
                        value=get_param("processing", "nicegui_update_interval"),
                        min=10,
                        max=60000,
                        format="%i",
                    ).classes("w-full")

                    # UI Update Interval
                    self.ui_elements["ui_update"] = ui.number(
                        "UI Update Interval (ms) > NiceGUI Update interval",
                        value=get_param("processing", "ui_update"),
                        min=20,
                        max=60000,
                        format="%i",
                    ).classes("w-full text-red-600 font-bold")

                    # Use ExifTool
                    self.ui_elements["use_exiftool"] = ui.checkbox(
                        "Use ExifTool",
                        value=get_param("processing", "use_exiftool"),
                    ).classes("w-full")

                    # ExifTool Timeout
                    self.ui_elements["exiftool_timeout"] = ui.number(
                        "ExifTool Timeout (milliseconds)",
                        value=get_param("processing", "exiftool_timeout"),
                        min=1,
                        max=500000,
                        format="%i",
                    ).classes("w-full")

                    # Processing Times Barchart
                    self.ui_elements["processing_array"] = ui.input(
                        "Processing times barchart",
                        value=get_param("processing", "processing_array"),
                        placeholder="1,10,50,100,200,300,500,1000",
                    ).classes("w-full")

                    # Worker Timeout
                    self.ui_elements["worker_timeout"] = ui.number(
                        "Worker Timeout (milliseconds)",
                        value=get_param("processing", "worker_timeout"),
                        min=1,
                        max=60000,
                        format="%i",
                    ).classes("w-full")

                    # Read Batch Size - ExifTool Performance Optimization
                    self.ui_elements["read_batch_size"] = ui.number(
                        "read_batch_size (for ExifTool optimalisation)",
                        value=get_param("processing", "read_batch_size"),
                        min=1,
                        max=1000,
                        format="%i",
                    ).classes("w-full")
                    
                    # Add help text for batch size
                    ui.label(
                        "Controls how many files are processed together in one ExifTool call. "
                        "Higher values = faster processing but more memory usage. "
                        "Recommended: 5-15 for optimal performance."
                    ).classes("text-sm text-gray-600 mt-2")

    def _create_database_settings(self) -> None:
        """Maak database settings sectie."""
        with ui.card().classes("w-full mb-4"):
            ui.label("Database Settings").classes("text-h6 q-mb-md")

            with ui.grid(columns=2).classes("w-full gap-4"):
                self.ui_elements["database_name"] = ui.input(
                    "Database Name",
                    value=get_param("database", "database_name"),
                    placeholder="./images_auto_field.db",
                ).classes("w-full")

                self.ui_elements["database_table_media"] = ui.input(
                    value=get_param("database", "database_table_media"),
                    placeholder="Media",
                    label="Database Table Media",
                ).classes("w-full")

                self.ui_elements["database_table_media_new"] = ui.input(
                    value=get_param("database", "database_table_media_new"),
                    placeholder="Media_New",
                    label="Database Table Media New",
                ).classes("w-full")

                self.ui_elements["database_table_dirs"] = ui.input(
                    value=get_param("database", "database_table_dirs"),
                    placeholder="Directories",
                    label="Database Table Directories",
                ).classes("w-full")

                self.ui_elements["database_clean"] = ui.switch(
                    value=get_param("database", "database_clean"),
                    text="Database Clean",
                )

                self.ui_elements["database_write_retry"] = ui.number(
                    "Database Write Retry",
                    value=get_param("database", "database_write_retry"),
                    min=1,
                    max=30,
                    format="%i",
                ).classes("w-full")

                self.ui_elements["database_max_retry_files"] = ui.number(
                    "Database Max Retry Files",
                    value=get_param("database", "database_max_retry_files"),
                    min=1,
                    max=30,
                    format="%i",
                ).classes("w-full")

                self.ui_elements["database_write_batch_size"] = ui.number(
                    "Database Write Batch Size",
                    value=get_param("database", "database_write_batch_size"),
                    min=1,
                    max=100000,
                    format="%i",
                ).classes("w-full")

    async def _browse_folder(self, field_name: str) -> None:
        """Browse voor folder selectie."""
        try:
            # Get current value as starting directory
            current_path = self.ui_elements[field_name].value or "/"
            
            # Open directory picker
            selected_path = await pick_directory(
                directory=current_path,
                show_hidden_files=False
            )
            
            if selected_path:
                # Update the input field with selected path
                self.ui_elements[field_name].value = selected_path
                ui.notify(f"Selected directory: {selected_path}", type="positive")
            else:
                ui.notify("No directory selected", type="info")
                
        except Exception as e:
            ui.notify(f"Error browsing directory: {e}", type="negative")

    def reset_to_defaults(self) -> None:
        """Reset naar default instellingen."""
        try:
            # Reset general values
            self.ui_elements["app_name"].value = "YAPMO"
            self.ui_elements["app_version"].value = "2.0.0"
            self.ui_elements["app_description"].value = "Yet Another Photo Manager and Organizer"
            
            # Reset to new default values
            self.ui_elements["max_workers"].value = 20
            self.ui_elements["nicegui_update_interval"].value = 100
            self.ui_elements["ui_update"].value = 500
            self.ui_elements["database_write_retry"].value = 3
            self.ui_elements["database_max_retry_files"].value = 10
            self.ui_elements["read_batch_size"].value = 5
            
            ui.notify("Configuration reset to new default values", type="positive")
        except Exception as e:
            ui.notify(f"Error resetting to defaults: {e}", type="negative")

    def save_config(self) -> None:
        """Sla configuratie op."""
        try:
            # Save general parameters
            set_param("general", "app_name", self.ui_elements["app_name"].value)
            set_param("general", "app_version", self.ui_elements["app_version"].value)
            set_param("general", "app_description", self.ui_elements["app_description"].value)

            # Save database parameters
            set_param("database", "database_name", self.ui_elements["database_name"].value)
            set_param("database", "database_table_media", self.ui_elements["database_table_media"].value)
            set_param("database", "database_table_media_new", self.ui_elements["database_table_media_new"].value)
            set_param("database", "database_table_dirs", self.ui_elements["database_table_dirs"].value)
            set_param("database", "database_clean", self.ui_elements["database_clean"].value)
            set_param("database", "database_write_retry", int(self.ui_elements["database_write_retry"].value))
            set_param("database", "database_max_retry_files", int(self.ui_elements["database_max_retry_files"].value))
            set_param("database", "database_write_batch_size", int(self.ui_elements["database_write_batch_size"].value))

            # Save logging parameters
            set_param("logging", "log_clean", self.ui_elements["log_clean"].value)
            set_param("logging", "log_file_path", self.ui_elements["log_file_path"].value)
            set_param("logging", "debug_file_path", self.ui_elements["debug_file_path"].value)
            
            # Save log levels matrix
            levels = ["ERROR", "WARNING", "INFO", "INFO_EXTRA", "DEBUG", "TEST_AI", "TEST1", "TEST2", "TEST3", "TEST4"]
            routes = ["t", "ui", "df"]
            levels_config = {}
            
            for level in levels:
                level_routes = []
                for route in routes:
                    if self.ui_elements[f"log_{level}_{route}"].value:
                        level_routes.append(route)
                levels_config[level] = level_routes
            
            set_param("logging", "levels", levels_config)

            # Save processing parameters
            set_param("processing", "max_workers", int(self.ui_elements["max_workers"].value))
            set_param("processing", "use_exiftool", self.ui_elements["use_exiftool"].value)
            set_param("processing", "exiftool_timeout", int(self.ui_elements["exiftool_timeout"].value))
            set_param("processing", "nicegui_update_interval", int(self.ui_elements["nicegui_update_interval"].value))
            set_param("processing", "ui_update", int(self.ui_elements["ui_update"].value))
            set_param("processing", "processing_array", self.ui_elements["processing_array"].value)
            set_param("processing", "worker_timeout", int(self.ui_elements["worker_timeout"].value))
            set_param("processing", "read_batch_size", int(self.ui_elements["read_batch_size"].value))

            # Save paths parameters
            set_param("paths", "source_path", self.ui_elements["source_path"].value)
            set_param("paths", "search_path", self.ui_elements["search_path"].value)
            set_param("paths", "browse_path", self.ui_elements["browse_path"].value)

            # DO NOT call logging_service.reload_config() - it hangs the UI thread!
            # The reload_config() method uses threading locks that can block the UI,
            # causing the menu and other UI elements to become unresponsive.
            # Instead, we navigate to main page for a fresh UI context.

            ui.notify("Configuration saved successfully!", type="positive")
            
            # Navigate to main page to avoid UI hanging issues
            # This provides a fresh UI context and prevents threading conflicts
            ui.navigate.to("/")
        except Exception as e:
            ui.notify(f"Error saving configuration: {e}", type="negative")


def create_config_page() -> ConfigPage:
    """Maak de configuratie pagina."""
    return ConfigPage()


if __name__ == "__main__":
    create_config_page()
    ui.run(title="Config Page", port=8081)