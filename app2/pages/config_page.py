"""Configuration Page voor YAPMO applicatie."""

from typing import Any

from config import get_param, set_param
from nicegui import ui
from shutdown_manager import handle_exit_click
from theme import YAPMOTheme


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
        # Load logging configuration - direct individuele parameters ophalen
        # Load database configuration - direct individuele parameters ophalen



        # Database Settings
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
                    max=10,
                    format="%i",
                ).classes("w-full")

                self.ui_elements["database_max_retry_files"] = ui.number(
                    "Database Max Retry Files",
                    value=get_param("database", "database_max_retry_files"),
                    min=1,
                    max=100,
                    format="%i",
                ).classes("w-full")



        # Logging Settings
        with ui.card().classes("w-full mb-4"):
            ui.label("Logging Settings").classes("text-h6 q-mb-md")

            with ui.grid(columns=2).classes("w-full gap-4"):
                self.ui_elements["log_enabled"] = ui.checkbox(
                    "Enable Logging",
                    value=get_param("logging", "log_enabled"),
                ).classes("w-full")

                self.ui_elements["log_terminal"] = ui.checkbox(
                    "Show Logging in Terminal",
                    value=get_param("logging", "log_terminal"),
                ).classes("w-full")

                self.ui_elements["log_clean"] = ui.checkbox(
                    "Clean Log File Before Start",
                    value=get_param("logging", "log_clean"),
                ).classes("w-full")

                self.ui_elements["log_file"] = ui.input(
                    "Log File Name",
                    value=get_param("logging", "log_file"),
                    placeholder="yapmo.log",
                ).classes("w-full")

                self.ui_elements["log_extensive"] = ui.checkbox(
                    "Log Extensive",
                    value=get_param("logging", "log_extensive"),
                ).classes("w-full")

                self.ui_elements["debug_mode"] = ui.checkbox(
                    "Debug Mode",
                    value=get_param("logging", "debug_mode"),
                ).classes("w-full")

                self.ui_elements["log_path"] = ui.input(
                    "Log File Path",
                    value=get_param("logging", "log_path"),
                    placeholder="./logs",
                ).classes("w-full")

                self.ui_elements["log_files_count_update"] = ui.number(
                    "Log Files Count Update",
                    value=get_param("logging", "log_files_count_update"),
                    min=1,
                    max=50000,
                    format="%i",
                ).classes("w-full")



    def _create_paths_settings(self) -> None:
        """Maak paths settings sectie."""
        # Load paths configuration - direct individuele parameters ophalen

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
        # Load metadata configurations - direct individuele parameters ophalen

        with ui.card().classes("w-full"):
            ui.label("Metadata Settings").classes("text-h6 q-mb-md")

            with ui.column().classes("w-full gap-4"):
                # Metadata field mappings display
                with ui.expansion(
                    "File Metadata Fields", icon="description",
                ).classes("w-full"):
                    metadata_fields_file = get_param("metadata_fields_file")
                    for exif_key, db_field in metadata_fields_file.items():
                        ui.label(f"{exif_key} → {db_field}").classes("text-sm")

                with ui.expansion(
                    "Image Metadata Fields", icon="photo",
                ).classes("w-full"):
                    metadata_fields_image = get_param("metadata_fields_image")
                    for exif_key, db_field in metadata_fields_image.items():
                        ui.label(f"{exif_key} → {db_field}").classes("text-sm")

                with ui.expansion(
                    "Video Metadata Fields", icon="video_library",
                ).classes("w-full"):
                    metadata_fields_video = get_param("metadata_fields_video")
                    for exif_key, db_field in metadata_fields_video.items():
                        ui.label(f"{exif_key} → {db_field}").classes("text-sm")

                with ui.expansion(
                    "Image Write Permissions", icon="edit",
                ).classes("w-full"):
                    metadata_write_image = get_param("metadata_write_image")
                    for field, writable in metadata_write_image.items():
                        if writable:
                            ui.label(f"✓ {field}").classes(
                                "text-sm text-green-600 font-bold")
                        else:
                            ui.label(f"✗ {field}").classes(
                                "text-sm text-red-600")

                with ui.expansion(
                    "Video Write Permissions", icon="edit",
                ).classes("w-full"):
                    metadata_write_video = get_param("metadata_write_video")
                    for field, writable in metadata_write_video.items():
                        if writable:
                            ui.label(f"✓ {field}").classes(
                                "text-sm text-green-600 font-bold")
                        else:
                            ui.label(f"✗ {field}").classes(
                                "text-sm text-red-600")

                # Placeholder voor metadata instellingen #AI_attention
                self.ui_elements["metadata_enabled"] = ui.checkbox(
                    "Enable Metadata Extraction",
                    value=True,
                )

    def _create_advanced_settings(self) -> None:
        """Maak advanced settings sectie."""
        with ui.card().classes("w-full"):
            ui.label("Advanced Settings").classes("text-h6 q-mb-md")

            with ui.column().classes("w-full gap-4"):
                # Processing Settings
                ui.label("Processing Settings").classes("text-h5 q-mb-md")

                # Load processing configuration - direct individuele parameters ophalen
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
                        min=50,
                        max=2000,
                        format="%i",
                    ).classes("w-full")

                    # UI Update Interval
                    self.ui_elements["ui_update"] = ui.number(
                        "UI Update Interval (ms)",
                        value=get_param("processing", "ui_update"),
                        min=100,
                        max=5000,
                        format="%i",
                    ).classes("w-full")

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

                # Hash Settings (Read-Only)
                ui.label("Hash Settings (Read-Only)").classes("text-h5 q-mb-md")

                with ui.grid(columns=2).classes("w-full gap-4"):
                    # Hash Algorithm
                    hash_algorithm_input = ui.input(
                        "Hash Algorithm",
                        value=get_param("processing", "hash_algorithm"),
                    ).classes("w-full")
                    hash_algorithm_input.disable()

                    # Hash Chunk Size
                    hash_chunk_input = ui.input(
                        "Hash Chunk Size (bytes)",
                        value=str(get_param("processing", "hash_chunk_size")),
                    ).classes("w-full")
                    hash_chunk_input.disable()

                    # Video Header Size
                    video_header_input = ui.input(
                        "Video Header Size (bytes)",
                        value=str(get_param("processing", "video_header_size")),
                    ).classes("w-full")
                    video_header_input.disable()

                    # Hash Info
                    hash_info_input = ui.input(
                        "Hash Strategy",
                        value="SHA-256 for images, Hybrid for videos",
                    ).classes("w-full")
                    hash_info_input.disable()

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
                    max=10,
                    format="%i",
                ).classes("w-full")

                self.ui_elements["database_max_retry_files"] = ui.number(
                    "Database Max Retry Files",
                    value=get_param("database", "database_max_retry_files"),
                    min=1,
                    max=100,
                    format="%i",
                ).classes("w-full")

                self.ui_elements["database_write_batch_size"] = ui.number(
                    "Database Write Batch Size",
                    value=get_param("database", "database_write_batch_size"),
                    min=1,
                    max=100000,
                    format="%i",
                ).classes("w-full")

    def _browse_folder(self, field_name: str) -> None:
        """Browse voor folder selectie."""
        ui.notify(
            # AI_attention
            f"Browse functionality for {field_name} will be implemented")

    def reset_to_defaults(self) -> None:
        """Reset naar default instellingen."""
        try:
            # Reset database parameters to defaults
            set_param("database", "database_write_batch_size", 1000)
            
            # Update UI elements
            self.ui_elements["database_write_batch_size"].value = 1000
            
            ui.notify("Database batch size reset to default (1000)", type="positive")
        except Exception as e:
            ui.notify(f"Error resetting to defaults: {e}", type="negative")

    def save_config(self) -> None:
        """Sla configuratie op."""
        try:
            # Save logging parameters
            set_param("logging", "log_enabled", self.ui_elements["log_enabled"].value)
            set_param("logging", "log_terminal", self.ui_elements["log_terminal"].value)
            set_param("logging", "log_clean", self.ui_elements["log_clean"].value)
            set_param("logging", "log_file", self.ui_elements["log_file"].value)
            set_param("logging", "log_path", self.ui_elements["log_path"].value)

            # Save database parameters
            set_param("database", "database_name", self.ui_elements["database_name"].value)
            set_param("database", "database_table_media", self.ui_elements["database_table_media"].value)
            set_param("database", "database_table_media_new", self.ui_elements["database_table_media_new"].value)
            set_param("database", "database_table_dirs", self.ui_elements["database_table_dirs"].value)
            set_param("database", "database_clean", self.ui_elements["database_clean"].value)
            set_param("database", "database_write_retry", int(self.ui_elements["database_write_retry"].value))
            set_param("database", "database_max_retry_files", int(self.ui_elements["database_max_retry_files"].value))
            set_param("database", "database_write_batch_size", int(self.ui_elements["database_write_batch_size"].value))

            # Save processing parameters
            set_param("processing", "max_workers", int(self.ui_elements["max_workers"].value))
            set_param("processing", "use_exiftool", self.ui_elements["use_exiftool"].value)
            set_param("processing", "exiftool_timeout", int(self.ui_elements["exiftool_timeout"].value))
            set_param("processing", "nicegui_update_interval", int(self.ui_elements["nicegui_update_interval"].value))
            set_param("processing", "ui_update", int(self.ui_elements["ui_update"].value))
            set_param("logging", "log_extensive", self.ui_elements["log_extensive"].value)
            set_param("logging", "log_files_count_update", int(self.ui_elements["log_files_count_update"].value))

            # Save paths parameters
            set_param("paths", "source_path", self.ui_elements["source_path"].value)
            set_param("paths", "search_path", self.ui_elements["search_path"].value)
            set_param("paths", "browse_path", self.ui_elements["browse_path"].value)

            ui.notify("Configuration saved successfully!", type="positive")
        except (FileNotFoundError, KeyError, ValueError, OSError) as e:
            ui.notify(f"Error saving configuration: {e}", type="negative")


def create_config_page() -> ConfigPage:
    """Maak de configuratie pagina."""
    return ConfigPage()


if __name__ == "__main__":
    create_config_page()
    ui.run(title="Config Page", port=8081)
