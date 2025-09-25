"""Configuration management for YAPMO application."""

import json
import os
from typing import Any


class ConfigManager:
    """Simple configuration manager for YAPMO."""
    
    def __init__(self, config_file: str = "config.json") -> None:
        """Initialize the config manager."""
        self.config_file = config_file
        self.config: dict[str, Any] = {}
        self.json_error = False
        self.validation_error = False
        self.error_details = []
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                # Validate config but don't fix yet - let user decide
                self._validate_config()
            else:
                # Create default config if file doesn't exist
                self._create_default_config()
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in config file: {e}")
            # Set flag and details for later dialog
            self.json_error = True
            self.error_details = [f"Corrupted JSON: {str(e)}"]
            # Create minimal config to prevent crashes, but don't save it yet
            self._create_minimal_config()
        except IOError as e:
            print(f"ERROR: Error reading config file: {e}")
            # Set flag and details for later dialog
            self.json_error = True
            self.error_details = [f"File not readable: {str(e)}"]
            # Create minimal config to prevent crashes, but don't save it yet
            self._create_minimal_config()
    
    def _create_default_config(self) -> None:
        """Create default configuration."""
        self.config = {
            "version": "YAPMO v2.0.0",
            "general": {
                "app_name": "YAPMO",
                "app_version": "2.0.0",
                "app_description": "Yet Another Photo Manager and Organizer",
                "default_config": True
            },
            "logging": {
                "log_enabled": True,
                "log_clean": True,
                "log_file_path": "./log/yapmo_log.log",
                "debug_file_path": "./log/yapmo_debug.log",
                "log_files_count_update": 1000,
                "levels": {
                    "ERROR": ["ui", "t", "df"],
                    "WARNING": ["ui", "t", "df"],
                    "INFO": ["ui"],
                    "INFO_EXTRA": ["df"],
                    "DEBUG": ["df"],
                    "TEST_AI": [],
                    "TEST1": [],
                    "TEST2": [],
                    "TEST3": [],
                    "TEST4": []
                }
            },
            "processing": {
                "max_workers": 20,
                "use_exiftool": True,
                "exiftool_timeout": 30000,
                "nicegui_update_interval": 100,
                "ui_update": 500,
                "worker_timeout": 30000,
                "read_batch_size": 5
            },
            "processing_queues": {
                "result_queue_depth": 32,
                "get_result_timeout": 500,
                "logging_queue_depth": 200,
                "get_log_timeout": 100
            },
            "database": {
                "database_path": "./images_auto_field.db",
                "database_table_media": "Media",
                "database_table_media_new": "Media_New",
                "database_table_dirs": "Directories",
                "database_write_retry": 3,
                "database_max_retry_files": 10,
                "database_write_batch_size": 1000,
                "database_timeout": 30,
                "database_encoding": "UTF-8",
                "database_journal_mode": "WAL",
                "database_synchronous": "NORMAL",
                "database_cache_size": -64000,
                "database_temp_store": "MEMORY"
            },
            "paths": {
                "source_path": "/workspaces",
                "search_path": "/Pictures-test",
                "browse_path": "/"
            },
            "extensions": {
                "image_extensions": [".jpg", ".jpeg", ".png", ".tiff", ".raw", ".arw"],
                "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"],
                "sidecar_extensions": [".aae", ".xmp", ".acr", ".on1", ".dop", ".pp3"]
            }
        }
        self.save_config()
    
    def _create_minimal_config(self) -> None:
        """Create minimal configuration in memory only (not saved to file)."""
        self.config = {
            "version": "YAPMO v2.0.0",
            "general": {
                "app_name": "YAPMO",
                "app_version": "2.0.0",
                "app_description": "Yet Another Photo Manager and Organizer",
                "default_config": False
            },
            "logging": {
                "log_enabled": True,
                "log_clean": True,
                "log_file_path": "./log/yapmo_log.log",
                "debug_file_path": "./log/yapmo_debug.log",
                "log_files_count_update": 1000,
                "levels": {
                    "ERROR": ["ui", "t", "df"],
                    "WARNING": ["ui", "t", "df"],
                    "INFO": ["ui"],
                    "INFO_EXTRA": ["df"],
                    "DEBUG": ["df"],
                    "TEST_AI": [],
                    "TEST1": [],
                    "TEST2": [],
                    "TEST3": [],
                    "TEST4": []
                }
            },
            "processing": {
                "max_workers": 20,
                "use_exiftool": True,
                "exiftool_timeout": 30000,
                "nicegui_update_interval": 100,
                "ui_update": 500,
                "worker_timeout": 30000,
                "read_batch_size": 5
            },
            "processing_queues": {
                "result_queue_depth": 32,
                "get_result_timeout": 500,
                "logging_queue_depth": 200,
                "get_log_timeout": 100
            },
            "database": {
                "database_path": "./images_auto_field.db",
                "database_table_media": "Media",
                "database_table_media_new": "Media_New",
                "database_table_dirs": "Directories",
                "database_write_retry": 3,
                "database_max_retry_files": 10,
                "database_write_batch_size": 1000,
                "database_timeout": 30,
                "database_encoding": "UTF-8",
                "database_journal_mode": "WAL",
                "database_synchronous": "NORMAL",
                "database_cache_size": -64000,
                "database_temp_store": "MEMORY"
            },
            "paths": {
                "source_path": "/workspaces",
                "search_path": "/Pictures-test",
                "browse_path": "/"
            },
            "extensions": {
                "image_extensions": [".jpg", ".jpeg", ".png", ".tiff", ".raw", ".arw"],
                "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"],
                "sidecar_extensions": [".aae", ".xmp", ".acr", ".on1", ".dop", ".pp3"]
            }
        }
        # Note: NOT saving to file - only in memory
    
    def was_config_created(self) -> bool:
        """Check if config.json was just created (has default_config = True)."""
        return self.config.get("general", {}).get("default_config", False)
    
    def has_json_error(self) -> bool:
        """Check if there was a JSON error during config loading."""
        return self.json_error
    
    def has_validation_error(self) -> bool:
        """Check if there were validation errors during config loading."""
        return self.validation_error
    
    def get_error_details(self) -> list[str]:
        """Get detailed error information."""
        return self.error_details
    
    def _show_json_error_dialog(self) -> None:
        """Show dialog for JSON error and handle user choice."""
        from nicegui import ui
        
        def _create_new_config(dialog: ui.dialog) -> None:
            """Create new default config."""
            dialog.close()
            self._create_default_config()
            ui.notify("New default configuration created", type="positive")
        
        def _exit_action(dialog: ui.dialog) -> None:
            """Exit application."""
            dialog.close()
            ui.notify("Application will exit", type="negative")
            from nicegui import app
            app.shutdown()
        
        # Create dialog
        dialog = ui.dialog()
        with dialog, ui.card().classes("w-[500px] p-6"):
            ui.label("Configuration File Corrupted").classes("text-xl font-bold mb-4")
            ui.label("The config.json file contains invalid JSON.").classes("text-base mb-2")
            ui.label("Create new default configuration?").classes("text-base mb-6")
            
            with ui.row().classes("w-full justify-end gap-3"):
                ui.button("NO - Exit", on_click=lambda: _exit_action(dialog)).props("color=negative")
                ui.button("YES - Create New", on_click=lambda: _create_new_config(dialog)).props("color=positive")
        
        dialog.open()
    
    def _show_validation_error_dialog(self) -> None:
        """Show dialog for validation errors and handle user choice."""
        from nicegui import ui
        
        def _fix_config(dialog: ui.dialog) -> None:
            """Fix config values and continue."""
            dialog.close()
            ui.notify("Configuration values fixed", type="positive")
        
        def _exit_action(dialog: ui.dialog) -> None:
            """Exit application."""
            dialog.close()
            ui.notify("Application will exit", type="negative")
            from nicegui import app
            app.shutdown()
        
        # Create dialog
        dialog = ui.dialog()
        with dialog, ui.card().classes("w-[500px] p-6"):
            ui.label("Invalid Configuration Values").classes("text-xl font-bold mb-4")
            ui.label("Some configuration values are invalid or out of range.").classes("text-base mb-2")
            ui.label("Fix automatically with default values?").classes("text-base mb-6")
            
            with ui.row().classes("w-full justify-end gap-3"):
                ui.button("NO - Exit", on_click=lambda: _exit_action(dialog)).props("color=negative")
                ui.button("YES - Fix Values", on_click=lambda: _fix_config(dialog)).props("color=positive")
        
        dialog.open()
    

    
    def get_param(self, section: str, key: str) -> Any:
        """Get a parameter value from config."""
        return self.config.get(section, {}).get(key)
    
    def set_param(self, section: str, key: str, value: Any) -> None:
        """Set a parameter value in config."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        #TEST_AI FIX: Save config after setting parameter to ensure changes are persisted
        self.save_config()
    
    def get_section(self, section: str) -> dict[str, Any]:
        """Get entire section from config."""
        return self.config.get(section, {})
    
    def save_config(self) -> None:
        """Save configuration to JSON file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving config: {e}")
    
    def get_version(self) -> str:
        """Get application version."""
        return self.config.get("version", "YAPMO v2.0.0")
    
    def _validate_config(self) -> None:
        """Validate config parameters and collect errors without fixing."""
        validation_errors = []
        
        # Validation rules
        validations = {
            "processing": {
                "max_workers": {"min": 1, "max": 32, "default": 20},
                "nicegui_update_interval": {"min": 10, "max": 60000, "default": 100},
                "ui_update": {"min": 20, "max": 60000, "default": 500},
                "read_batch_size": {"min": 1, "max": 1000, "default": 5},
            },
            "processing_queues": {
                "result_queue_depth": {"min": 5, "max": 64, "default": 32},
                "get_result_timeout": {"min": 1, "max": 6000, "default": 500},
                "logging_queue_depth": {"min": 1, "max": 200000, "default": 200},
                "get_log_timeout": {"min": 1, "max": 60000, "default": 100},
            },
            "database": {
                "database_write_retry": {"min": 1, "max": 30, "default": 3},
                "database_max_retry_files": {"min": 1, "max": 30, "default": 10},
            },
            "logging": {
                "log_files_count_update": {"min": 1, "max": 100000, "default": 1000},
            }
        }
        
        # Text fields that cannot be empty
        text_fields = {
            "database": ["database_path", "database_table_media", "database_table_media_new", "database_table_dirs"],
            "logging": ["log_file_path", "debug_file_path"],
            "paths": ["source_path", "search_path", "browse_path"]
        }
        
        # Validate without fixing
        for section, params in validations.items():
            if section not in self.config:
                validation_errors.append(f"Missing section '{section}'")
            else:
                for param, rules in params.items():
                    if param not in self.config[section]:
                        validation_errors.append(f"Missing parameter '{section}.{param}'")
                    else:
                        value = self.config[section][param]
                        if not isinstance(value, (int, float)) or value < rules["min"] or value > rules["max"]:
                            validation_errors.append(f"Invalid value for '{section}.{param}' ({value})")
        
        # Validate text fields
        for section, fields in text_fields.items():
            if section not in self.config:
                validation_errors.append(f"Missing section '{section}'")
            else:
                for field in fields:
                    if field not in self.config[section] or not self.config[section][field]:
                        validation_errors.append(f"Empty or missing text field '{section}.{field}'")
        
        # Set validation error flag if there were any errors
        if validation_errors:
            self.validation_error = True
            self.error_details = validation_errors

    def _validate_and_fix_config(self) -> None:
        """Validate config parameters and fix invalid values."""
        validation_errors = []
        
        # Validation rules
        validations = {
            "processing": {
                "max_workers": {"min": 1, "max": 32, "default": 20},
                "nicegui_update_interval": {"min": 10, "max": 60000, "default": 100},
                "ui_update": {"min": 20, "max": 60000, "default": 500},
                "read_batch_size": {"min": 1, "max": 1000, "default": 5},
            },
            "processing_queues": {
                "result_queue_depth": {"min": 5, "max": 64, "default": 32},
                "get_result_timeout": {"min": 1, "max": 6000, "default": 500},
                "logging_queue_depth": {"min": 1, "max": 200000, "default": 200},
                "get_log_timeout": {"min": 1, "max": 60000, "default": 100},
            },
            "database": {
                "database_write_retry": {"min": 1, "max": 30, "default": 3},
                "database_max_retry_files": {"min": 1, "max": 30, "default": 10},
            },
            "logging": {
                "log_files_count_update": {"min": 1, "max": 100000, "default": 1000},
            }
        }
        
        # Text fields that cannot be empty
        text_fields = {
            "database": ["database_path", "database_table_media", "database_table_media_new", "database_table_dirs"],
            "logging": ["log_file_path", "debug_file_path"],
            "paths": ["source_path", "search_path", "browse_path"]
        }
        
        # Validate and fix
        for section, params in validations.items():
            if section not in self.config:
                self.config[section] = {}
                validation_errors.append(f"Missing section '{section}'")
            
            for param, rules in params.items():
                if param not in self.config[section]:
                    self.config[section][param] = rules["default"]
                    validation_errors.append(f"Missing parameter '{section}.{param}'")
                else:
                    value = self.config[section][param]
                    if not isinstance(value, (int, float)) or value < rules["min"] or value > rules["max"]:
                        self.config[section][param] = rules["default"]
                        validation_errors.append(f"Invalid value for '{section}.{param}' ({value})")
        
        # Validate text fields
        for section, fields in text_fields.items():
            if section not in self.config:
                self.config[section] = {}
                validation_errors.append(f"Missing section '{section}'")
            
            for field in fields:
                if field not in self.config[section] or not self.config[section][field]:
                    # Set default values for missing text fields
                    defaults = {
                        "database": {
                            "database_path": "./images_auto_field.db",
                            "database_table_media": "Media",
                            "database_table_media_new": "Media_New",
                            "database_table_dirs": "Directories",
                        },
                        "logging": {
                            "log_file_path": "./log/yapmo_log.log",
                            "debug_file_path": "./log/yapmo_debug.log",
                        },
                        "paths": {
                            "source_path": "/workspaces",
                            "search_path": "/Pictures-test",
                            "browse_path": "/"
                        }
                    }
                    self.config[section][field] = defaults[section][field]
                    validation_errors.append(f"Empty or missing text field '{section}.{field}'")
        
        # Always set validation error flag if there were any errors
        if validation_errors:
            self.validation_error = True
            self.error_details = validation_errors
            #TEST_AI FIX: Save config after validation fixes to ensure changes are persisted
            self.save_config()
    

    



# Global config instance
config_manager = ConfigManager()


def get_param(section: str, key: str) -> Any:
    """Get a parameter value from config."""
    return config_manager.get_param(section, key)


def set_param(section: str, key: str, value: Any) -> None:
    """Set a parameter value in config."""
    config_manager.set_param(section, key, value)
    config_manager.save_config()


def get_section(section: str) -> dict[str, Any]:
    """Get entire section from config."""
    return config_manager.get_section(section)


def get_version() -> str:
    """Get application version."""
    return config_manager.get_version()


def was_config_created() -> bool:
    """Check if config.json was just created."""
    return config_manager.was_config_created()


def has_json_error() -> bool:
    """Check if there was a JSON error during config loading."""
    return config_manager.has_json_error()


def has_validation_error() -> bool:
    """Check if there were validation errors during config loading."""
    return config_manager.has_validation_error()


def get_error_details() -> list[str]:
    """Get detailed error information."""
    return config_manager.get_error_details()


def show_json_error_dialog() -> None:
    """Show dialog for corrupted JSON config file."""
    from nicegui import ui
    
    def _create_new_config(dialog: ui.dialog) -> None:
        """Create new default config and continue."""
        dialog.close()
        # Clear the error flags
        config_manager.json_error = False
        config_manager.validation_error = False
        config_manager.error_details = []
        # Create and save the new config
        config_manager._create_default_config()
        ui.notify("New default configuration created and ready to use", type="positive")
    
    def _exit_action(dialog: ui.dialog) -> None:
        """Exit application."""
        dialog.close()
        ui.notify("Application will exit", type="negative")
        from nicegui import app
        app.shutdown()
    
    # Get error details
    error_details = get_error_details()
    
    # Create dialog
    dialog = ui.dialog()
    with dialog, ui.card().classes("w-[600px] p-6"):
        ui.label("Configuration File Problem").classes("text-xl font-bold mb-4")
        
        # Show specific error type
        if "Corrupted JSON" in str(error_details):
            ui.label("❌ Corrupted JSON file detected").classes("text-base mb-2 text-red-600")
        elif "File not readable" in str(error_details):
            ui.label("❌ Config file not found or not readable").classes("text-base mb-2 text-red-600")
        else:
            ui.label("❌ Configuration file problem").classes("text-base mb-2 text-red-600")
        
        # Show error details
        if error_details:
            ui.label("Error details:").classes("text-sm font-medium mb-2")
            with ui.column().classes("ml-4 mb-4"):
                for error in error_details:
                    ui.label(f"• {error}").classes("text-sm text-gray-600")
        
        ui.label("Create new default configuration and continue?").classes("text-base mb-6")
        
        with ui.row().classes("w-full justify-end gap-3"):
            ui.button("NO - Exit", on_click=lambda: _exit_action(dialog)).props("color=negative")
            ui.button("YES - Create & Continue", on_click=lambda: _create_new_config(dialog)).props("color=positive")
    
    dialog.open()


def show_validation_error_dialog() -> None:
    """Show dialog for invalid config values."""
    from nicegui import ui
    
    def _fix_config(dialog: ui.dialog) -> None:
        """Fix config values and continue."""
        dialog.close()
        # Clear the error flags
        config_manager.validation_error = False
        config_manager.error_details = []
        # Fix the config values
        config_manager._validate_and_fix_config()
        # Save the corrected config
        config_manager.save_config()
        ui.notify("Configuration values fixed and saved", type="positive")
    
    def _exit_action(dialog: ui.dialog) -> None:
        """Exit application."""
        dialog.close()
        ui.notify("Application will exit", type="negative")
        from nicegui import app
        app.shutdown()
    
    # Get error details
    error_details = get_error_details()
    
    # Create dialog
    dialog = ui.dialog()
    with dialog, ui.card().classes("w-[600px] p-6"):
        ui.label("Invalid Configuration Values").classes("text-xl font-bold mb-4")
        ui.label("⚠️ Configuration structure or values are invalid").classes("text-base mb-2 text-orange-600")
        
        # Show error details
        if error_details:
            ui.label("Problems found:").classes("text-sm font-medium mb-2")
            with ui.column().classes("ml-4 mb-4 max-h-32 overflow-y-auto"):
                for error in error_details:
                    ui.label(f"• {error}").classes("text-sm text-gray-600")
        
        ui.label("Fix automatically with default values?").classes("text-base mb-6")
        
        with ui.row().classes("w-full justify-end gap-3"):
            ui.button("NO - Exit", on_click=lambda: _exit_action(dialog)).props("color=negative")
            ui.button("YES - Fix Values", on_click=lambda: _fix_config(dialog)).props("color=positive")
    
    dialog.open()


def show_default_config_dialog() -> None:
    """Show dialog for default configuration."""
    from nicegui import ui
    
    def _continue_action(dialog: ui.dialog) -> None:
        """Continue with default config."""
        dialog.close()
        # Set default_config to false
        set_param("general", "default_config", False)
        ui.notify("Continuing with default configuration", type="positive")
    
    def _exit_action(dialog: ui.dialog) -> None:
        """Exit application."""
        dialog.close()
        ui.notify("Application will exit", type="negative")
        # Use same shutdown method as exit dialog
        from nicegui import app
        app.shutdown()
    
    # Create dialog
    dialog = ui.dialog()
    with dialog, ui.card().classes("w-[500px] p-6"):
        ui.label("Default Configuration").classes("text-xl font-bold mb-4")
        ui.label("You are using default configuration values.").classes("text-base mb-2")
        ui.label("Continue with default configuration?").classes("text-base mb-6")
        
        with ui.row().classes("w-full justify-end gap-3"):
            ui.button("NO - Exit", on_click=lambda: _exit_action(dialog)).props("color=negative")
            ui.button("YES - Continue", on_click=lambda: _continue_action(dialog)).props("color=positive")
    
    dialog.open()



