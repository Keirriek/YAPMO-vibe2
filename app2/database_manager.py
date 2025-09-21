"""Database Manager voor YAPMO (Yet Another Photo Management Organizer)

VERSIE 2: Database initialisatie routine
- Database connectie en tabel creatie
- Config.json parsing voor metadata velden
- Error handling met logging service
- UI timeout meldingen
"""

import sqlite3
from pathlib import Path
from typing import Dict, Any
from threading import Lock

from config import get_param
from globals import logging_service
from nicegui import ui  # type: ignore[import]


class DatabaseManager:
    """Database manager voor YAPMO met initialisatie routine."""
    
    def __init__(self) -> None:
        """Initialize DatabaseManager met configuratie."""
        # Load configuratie parameters
        self.db_name = get_param("database", "database_name")
        self.db_table_media = get_param("database", "database_table_media")
        self.database_clean = get_param("database", "database_clean")
        
        # Database paths
        self.db_path = Path(self.db_name)
        
        # Database state
        self.connection: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None
        
        # Thread safety
        self.db_lock = Lock()
        
        # Initialize database
        self._initialize_database()
        
        logging_service.log("INFO", "DatabaseManager initialized successfully")
    
    def _initialize_database(self) -> None:
        """Initialize database en tabellen."""
        try:
            logging_service.log("INFO", "Starting database initialization")
            
            # Clean database indien gewenst
            if self.database_clean and self.db_path.exists():
                self.db_path.unlink()
                logging_service.log("INFO", f"Removed existing database: {self.db_path}")
            
            # Connect to database
            self._connect()
            
            # Initialize tables
            self._initialize_tables()
            
            logging_service.log("INFO", "Database initialization completed successfully")
            
        except Exception as e:
            error_msg = f"Database initialization failed: {e}"
            logging_service.log("ERROR", error_msg)
            # UI melding voor gebruiker
            ui.notify(
                "Database initialization failed - Check logs for details",
                type="negative",
                position="top-right"
            )
            raise
    
    def _connect(self) -> None:
        """Connect to SQLite database met timeout."""
        try:
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database met 30 seconden timeout
            self.connection = sqlite3.connect(str(self.db_path), timeout=30.0)
            self.cursor = self.connection.cursor()
            
            logging_service.log("INFO", f"Connected to database: {self.db_path}")
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                error_msg = "Database connection timeout ERROR - Check database, maybe in use by other programs"
                logging_service.log("ERROR", error_msg)
                ui.notify(error_msg, type="negative", position="top-right")
            else:
                error_msg = f"Database connection error: {e}"
                logging_service.log("ERROR", error_msg)
                ui.notify(error_msg, type="negative", position="top-right")
            raise
        except Exception as e:
            error_msg = f"Unexpected database connection error: {e}"
            logging_service.log("ERROR", error_msg)
            ui.notify(error_msg, type="negative", position="top-right")
            raise
    
    def _initialize_tables(self) -> None:
        """Initialize alle benodigde tabellen."""
        try:
            # Create media table
            self._create_media_table()
            
            logging_service.log("INFO", "All tables initialized successfully")
            
        except Exception as e:
            error_msg = f"Error initializing tables: {e}"
            logging_service.log("ERROR", error_msg)
            raise
    
    def _create_media_table(self) -> None:
        """Create media table met dynamic fields vanuit config."""
        try:
            # Get field mappings from config
            field_mappings = self._get_field_mappings()
            
            # Base fields
            fields = [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "YAPMO_FQPN TEXT UNIQUE NOT NULL"  # Fully Qualified Path Name
            ]
            
            # Add fields from config
            for exif_key, db_field in field_mappings.items():
                if db_field not in ['YAPMO_FQPN']:  # Skip if already defined
                    fields.append(f"{db_field} TEXT")
            
            # Create table
            create_sql = f"""
                CREATE TABLE IF NOT EXISTS {self.db_table_media} (
                    {', '.join(fields)}
                )
            """
            
            self.cursor.execute(create_sql)
            
            # Create indexes for performance
            self.cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_fqpn ON {self.db_table_media}(YAPMO_FQPN)")
            
            # Only create hash index if the hash field exists
            if 'YAPMO_hash' in [field.split()[0] for field in fields]:
                self.cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_hash ON {self.db_table_media}(YAPMO_hash)")
            
            self.connection.commit()
            logging_service.log("INFO", f"Media table '{self.db_table_media}' created/verified")
            
        except sqlite3.Error as e:
            error_msg = f"Error creating media table: {e}"
            logging_service.log("ERROR", error_msg)
            raise
    
    def _get_field_mappings(self) -> Dict[str, str]:
        """Get combined field mappings vanuit config."""
        mappings = {}
        
        try:
            # Combine all field mappings from config
            file_fields = get_param("metadata_fields_file")
            image_fields = get_param("metadata_fields_image")
            video_fields = get_param("metadata_fields_video")
            
            # Process file fields (dictionary format)
            if isinstance(file_fields, dict):
                for exif_key, db_field in file_fields.items():
                    mappings[exif_key] = db_field
            
            # Process image fields (dictionary format)
            if isinstance(image_fields, dict):
                for exif_key, db_field in image_fields.items():
                    mappings[exif_key] = db_field
            
            # Process video fields (dictionary format)
            if isinstance(video_fields, dict):
                for exif_key, db_field in video_fields.items():
                    mappings[exif_key] = db_field
            
            logging_service.log("INFO", f"Field mappings loaded: {len(mappings)} fields")
            
        except Exception as e:
            error_msg = f"Error loading field mappings: {e}"
            logging_service.log("ERROR", error_msg)
            raise
        
        return mappings
    
    def add_media_record(self, metadata: Dict[str, Any]) -> bool:
        """Add media record to database (thread-safe dummy routine voor testing).
        
        Args:
            metadata: Dictionary met file metadata van process_single_file
            
        Returns:
            True als record succesvol is verwerkt (dummy)
        """
        with self.db_lock:
            try:
                # Log alle ontvangen JSON data voor debugging
                logging_service.log("INFO", "=== RECEIVED MEDIA RECORD ===")
                logging_service.log("INFO", f"Number of fields: {len(metadata)}")
                
                # Log alle individuele velden
                for key, value in metadata.items():
                    if isinstance(value, list):
                        logging_service.log("INFO", f"Field: {key} = {value} (list with {len(value)} items)")
                    else:
                        logging_service.log("INFO", f"Field: {key} = {value}")
                
                # Log FQPN als die er is
                fqpn = metadata.get('YAPMO:FQPN') or metadata.get('SourceFile', 'UNKNOWN')
                logging_service.log("INFO", f"Processing file: {fqpn}")
                
                logging_service.log("INFO", "=== MEDIA RECORD PROCESSING COMPLETED ===")
                
                # Return True om succes te simuleren
                return True
                
            except Exception as e:
                error_msg = f"Error processing media record: {e}"
                logging_service.log("ERROR", error_msg)
                return False
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            try:
                self.connection.close()
                logging_service.log("INFO", "Database connection closed")
            except sqlite3.Error as e:
                error_msg = f"Error closing database: {e}"
                logging_service.log("ERROR", error_msg)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
