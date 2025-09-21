"""Configuration management for YAPMO application."""

import json
from pathlib import Path
from typing import Any

# Globale variabele voor app directory (nooit wijzigen!)
APP_DIR = Path(__file__).parent


class ConfigError(Exception):
    """Custom exception for configuration errors."""


def read_config(config_file: str | None = None) -> dict[str, Any]:
    """Read configuration from config.json file using JSON5.

    Args:
    ----
        config_file: Optional path to config file. If None, uses default location

    Returns:
    -------
        Dictionary containing configuration settings

    Raises:
    ------
        ConfigError: If config file cannot be read or parsed

    """
    # Gebruik APP_DIR voor config.json
    if config_file is None:
        config_path = APP_DIR / "config.json"
    else:
        config_path = Path(config_file)

    try:
        if not config_path.exists():
            msg = f"Configuration file not found: {config_path}"
            raise ConfigError(msg)  # noqa: TRY301

        with config_path.open(encoding="utf-8") as f:
            return json.load(f)


    except Exception as e:
        msg = f"Error reading config file {config_path}: {e}"
        raise ConfigError(
            msg) from e


def write_config(config_dict: dict[str, Any], config_file: str | None = None) -> None:
    """Write configuration to config.json file using JSON5.

    Args:
    ----
        config_dict: Configuration dictionary to write
        config_file: Optional path to config file. If None, uses default location

    Raises:
    ------
        ConfigError: If config file cannot be written

    """
    # Gebruik APP_DIR voor config.json
    if config_file is None:
        config_path = APP_DIR / "config.json"
    else:
        config_path = Path(config_file)

    try:
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with config_path.open("w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)

    except Exception as e:
        msg = f"Error writing config file {config_path}: {e}"
        raise ConfigError(
            msg) from e


def get_param(
    section: str, param_name: str | None = None,
) -> str | int | bool | list[str]:  # type: ignore[return-value]
    """Get a parameter from the configuration.

    Args:
    ----
        section: Section name (e.g., 'logging')
        param_name: Parameter name within section. If None, returns entire section

    Returns:
    -------
        Parameter value or entire section if param_name is None

    """
    import logging
    import sys
    
    config_data = read_config()

    if section not in config_data:
        # Try to get default section from config.py
        try:
            default_config = create_default_config()
            if section in default_config:
                # Add missing section to config.json
                config_data[section] = default_config[section]
                write_config(config_data)
                logging.warning(f"Section '{section}' not found in config.json, added with defaults from config.py")
                if param_name is None:
                    return config_data[section]
            else:
                # Section not found in defaults either
                logging.error(f"Section '{section}' not found in config.json or config.py defaults")
                sys.exit(1)
        except Exception as e:
            logging.error(f"Failed to retrieve default section '{section}': {e}")
            sys.exit(1)

    if param_name is None:
        return config_data[section]

    if param_name not in config_data[section]:
        # Try to get default parameter from config.py
        try:
            default_config = create_default_config()
            if section in default_config and param_name in default_config[section]:
                # Add missing parameter to config.json
                config_data[section][param_name] = default_config[section][param_name]
                write_config(config_data)
                logging.warning(f"Parameter '{param_name}' not found in section '{section}', added with default value {default_config[section][param_name]} from config.py")
                return config_data[section][param_name]
            else:
                # Parameter not found in defaults either
                logging.error(f"Parameter '{param_name}' not found in section '{section}' in config.json or config.py defaults")
                sys.exit(1)
        except Exception as e:
            logging.error(f"Failed to retrieve default parameter '{param_name}' from section '{section}': {e}")
            sys.exit(1)

    return config_data[section][param_name]


def set_param(
    section: str, param_name: str, value: str | int | bool | list[str],
) -> None:  # type: ignore[assignment]
    """Set a parameter in the configuration.

    Args:
    ----
        section: Section name (e.g., 'logging')
        param_name: Parameter name within section
        value: Value to set

    Raises:
    ------
        ConfigError: If config file cannot be read or written

    """
    config_data = read_config()

    if section not in config_data:
        config_data[section] = {}

    config_data[section][param_name] = value
    write_config(config_data)

# Version configuration functions
def get_version() -> str:
    """Get application version.

    Returns
    -------
        String containing application version

    """
    config = read_config()
    return config.get("version")


# All functions are now properly implemented above


def create_default_config() -> dict[str, Any]:
    """Create default configuration.

    Returns
    -------
        Dictionary containing default configuration

    """
    return {
        "version": "YAPMO v0.7",
        "logging": {
            "log_enabled": True,
            "log_terminal": True,
            "log_clean": True,
            "log_file": "yapmo.log",
            "dev_log_enabled": True,
            "dev_log_file": "yapmo_dev.log",
            "debug_mode": False,
            "debug_directory_logging": True,
            "debug_directory_log_interval": 500,
            "log_files_count_update": 500,
            "log_path": "./logs",
        },
        "database": {
            "database_clean": False,
            "database_name": "../YAPMO_db/images_auto_field.db",
            "database_table_media": "Media",
            "database_table_media_new": "Media_New",
            "database_table_dirs": "Directories",
            "database_write_retry": 3,
            "database_max_retry_files": 10,
            "database_write_batch_size": 1000,
        },
        "metadata_fields_file": {
            "YAPMO:Modify": "YAPMO_Modify",
            "YAPMO:FileName": "YAPMO_FILE_Name",
            "FILE:FileName": "FILE_Name",
            "YAPMO:Directory": "YAPMO_FILE_Path",
            "FILE:Directory": "FILE_Path",
            "YAPMO:FileSize": "YAPMO_FILE_Size",
            "FILE:FileSize": "FILE_Size",
            "YAPMO:FileType": "YAPMO_FILE_Type",
            "FILE:FileType": "FILE_Type",
            "YAPMO:Name_New": "YAPMO_FILE_Name_New",
            "YAPMO:Path_New": "YAPMO_FILE_Path_New",
            "YAPMO:Hash": "YAPMO_hash",
            "YAPMO:FileModifyDate": "YAPMO_FILE_Modify_Date",
            "YAPMO:Sidecars": "YAPMO_Sidecars",
            "File:FileModifyDate": "FILE_Modify_Date",
            "YAPMO:FQPN": "YAPMO_FQPN",
        },
        "metadata_fields_image": {
            "EXIF:DateTimeOriginal": "EXIF_DateTimeOriginal",
            "IPTC:DateCreated": "IPTC_DateCreated",
            "EXIF:GPSDateStamp": "EXIF_GPSDateStamp",
            "EXIF:GPSTimeStamp": "EXIF_GPSTimeStamp",
            "IPTC:Keywords": "IPTC_Keywords",
            "IPTC:TimeCreated": "IPTC_TimeCreated",
                    "XMP_CreateDate": "XMP_CreateDate",
        "XMP_ModifyDate": "XMP_ModifyDate",
        "XMP_Rating": "XMP_Rating",
        "XMP_Subject": "XMP_Subject",
        "XMP_HierarchicalSubject": "XMP_HierarchicalSubject",
        "XMP_RegionAreaH": "XMP_RegionAreaH",
        "XMP_RegionAreaW": "XMP_RegionAreaW",
        "XMP_RegionAreaX": "XMP_RegionAreaX",
        "XMP_RegionAreaY": "XMP_RegionAreaY",
        "XMP_RegionType": "XMP_RegionType",
        "XMP_RegionName": "XMP_RegionName",
        "XMP_Title": "XMP_Title",
        },
        "metadata_fields_video": {
            "QuickTime:CreateDate": "QuickTime_CreateDate",
            "QuickTime:Keywords": "QuickTime_Keywords",
            "QuickTime:Title": "QuickTime_Title",
            "QuickTime:Description": "QuickTime_Description",
            "Composite:Rating": "Composite_Rating",
            "QuickTime:GPSCoordinates": "QuickTime_GPSCoordinates",
            "Composite:ImageSize": "Composite_ImageSize",
            "Composite:Megapixels": "Composite_Megapixels",
            "Composite:Duration": "Composite_Duration",
        },
        "metadata_write_image": {
            "File:Name": False,
            "File:Directory": False,
            "File:FileModifyDate": False,
            "File:Size": False,
            "File:Type": False,
            "EXIF:DateTimeOriginal": False,
            "IPTC:DateCreated": False,
            "EXIF:GPSDateStamp": False,
            "EXIF:GPSTimeStamp": False,
            "IPTC:Keywords": True,
            "IPTC:TimeCreated": False,
                    "XMP_CreateDate": False,
        "XMP_ModifyDate": False,
        "XMP_Rating": False,
        "XMP_Subject": False,
        "XMP_HierarchicalSubject": True,
        "XMP_RegionAreaH": False,
        "XMP_RegionAreaW": False,
        "XMP_RegionAreaX": False,
        "XMP_RegionAreaY": False,
        "XMP_RegionType": True,
        "XMP_RegionName": False,
        "XMP_Title": False,
        },
        "metadata_write_video": {
            "File:Name": False,
            "File:Directory": False,
            "File:FileModifyDate": False,
            "File:Size": False,
            "File:Type": False,
            "EXIF:DateTimeOriginal": True,
            "QuickTime:CreateDate": False,
            "QuickTime:Keywords": True,
            "QuickTime:Title": True,
            "QuickTime:Description": True,
            "Composite:Rating": False,
            "QuickTime:GPSCoordinates": False,
        },
        "processing": {
            "max_workers": 4,
            "use_exiftool": True,
            "exiftool_timeout": 30000,
            "nicegui_update_interval": 500,
            "ui_update": 500,
        },
        "paths": {
            "source_path": "/workspaces",
            "search_path": "/Pictures-test",
            "browse_path": "/",
        },
        "extensions": {
            "image_extensions": [".jpg", ".jpeg", ".png", ".tiff", ".raw", ".arw"],
            "video_extensions": [
                ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm",
            ],
            "sidecar_extensions": [".aae", ".xmp", ".acr", ".on1", ".dop", ".pp3"],
        },
    }


def initialize_config() -> None:
    """Initialize configuration file with defaults if it doesn't exist."""
    try:
        read_config()
    except ConfigError:
        # Config file doesn't exist, create it with defaults
        default_config = create_default_config()
        write_config(default_config)
