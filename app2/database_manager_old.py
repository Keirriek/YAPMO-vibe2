"""Database Manager voor YAPMO (Yet Another Photo Management Organizer)

Moderne SQLite database manager met:
- Dynamic field mapping vanuit configuratie
- Proper error handling en logging
- Support voor toevoegen en updaten van records
- Handelt complexe metadata structuren af
- Thread-safe design voor parallelle processen
"""

import sqlite3
import logging
import os
import json
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime
from threading import Lock

from config import get_param
from globals import logging_service


class DatabaseManager:
    """Moderne database manager voor YAPMO met dynamic field mapping"""
    
    def __init__(self):
        """Initialize DatabaseManager met configuratie."""
        # DEBUG: Test if DatabaseManager is created
        logging_service.log("INFO", "=== DatabaseManager.__init__ CALLED ===")
        
        # Load configuratie parameters
        self.db_name = get_param("database", "database_name")
        self.db_table_media = get_param("database", "database_table_media")
        self.db_table_dirs = get_param("database", "database_table_dirs")
        self.database_clean = get_param("database", "database_clean")
        self.database_write_retry = get_param("database", "database_write_retry")
        self.database_max_retry_files = get_param("database", "database_max_retry_files")
        
        logging_service.log("INFO", f"Database config: clean={self.database_clean}, name={self.db_name}")
        
        # Database paths
        self.db_path = Path(self.db_name)
        
        # Database state
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        
        # Thread safety
        self.db_lock = Lock()
        
        # Failed files tracking
        self.failed_files_count = 0
        
        # Initialize database
        self._initialize_database()
        
        logging_service.log("INFO", "=== DatabaseManager.__init__ COMPLETED ===")
        
        # Log initialisatie
        logging_service.log(
            "INFO",
            f"DatabaseManager initialized: {self.db_path}, "
            f"write_retry={self.database_write_retry}, "
            f"max_retry_files={self.database_max_retry_files}"
        )
    
    def _initialize_database(self) -> None:
        """Initialize database en tabellen."""
        try:
            logging_service.log("INFO", "=== _initialize_database STARTED ===")
            
            # Clean database indien gewenst
            if self.database_clean and self.db_path.exists():
                self.db_path.unlink()
                logging_service.log("INFO", f"Removed existing database: {self.db_path}")
            
            # Connect to database
            self._connect()
            
            # Initialize tables
            self._initialize_tables()
            
            logging_service.log("INFO", "Database initialization completed successfully")
            logging_service.log("INFO", "=== _initialize_database COMPLETED ===")
            
        except Exception as e:
            logging_service.log("ERROR", f"Database initialization failed: {e}")
            raise
    
    def _connect(self) -> None:
        """Connect to SQLite database."""
        try:
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database
            self.connection = sqlite3.connect(str(self.db_path), timeout=30.0)
            self.cursor = self.connection.cursor()
            
            # Enable foreign keys and WAL mode for better performance
            self.cursor.execute("PRAGMA foreign_keys = ON")
            self.cursor.execute("PRAGMA journal_mode = WAL")
            self.cursor.execute("PRAGMA busy_timeout = 30000")  # 30 second timeout
            
            logging_service.log("INFO", f"Connected to database: {self.db_path}")
            
        except sqlite3.Error as e:
            logging_service.log("ERROR", f"Error connecting to database: {e}")
            raise
    
    def _initialize_tables(self) -> None:
        """Initialize alle benodigde tabellen."""
        try:
            # Create media table
            self._create_media_table()
            
            # Create directories table
            self._create_directories_table()
            
            logging_service.log("INFO", "All tables initialized successfully")
            
        except Exception as e:
            logging_service.log("ERROR", f"Error initializing tables: {e}")
            raise
    
    def _create_media_table(self) -> None:
        """Create media table met dynamic fields vanuit config."""
        try:
            # Get field mappings from config
            field_mappings = self._get_field_mappings()
            
            # Base fields
            fields = [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "YAPMO_FQPN TEXT UNIQUE NOT NULL",  # Fully Qualified Path Name
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
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
            logging_service.log("ERROR", f"Error creating media table: {e}")
            raise
    
    def _create_directories_table(self) -> None:
        """Create directories table voor tracking scanned directories."""
        try:
            create_sql = f"""
                CREATE TABLE IF NOT EXISTS {self.db_table_dirs} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dirname TEXT NOT NULL,
                    dirpath TEXT UNIQUE NOT NULL,
                    filecount INTEGER DEFAULT 0,
                    fully_searched INTEGER DEFAULT 0,
                    last_scan TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            
            self.cursor.execute(create_sql)
            self.cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_dirpath ON {self.db_table_dirs}(dirpath)")
            
            self.connection.commit()
            logging_service.log("INFO", f"Directories table '{self.db_table_dirs}' created/verified")
            
        except sqlite3.Error as e:
            logging_service.log("ERROR", f"Error creating directories table: {e}")
            raise
    
    def _get_field_mappings(self) -> Dict[str, str]:
        """Get combined field mappings vanuit config."""
        mappings = {}
        
        # Combine all field mappings from config
        file_fields = get_param("metadata_fields_file")
        image_fields = get_param("metadata_fields_image")
        video_fields = get_param("metadata_fields_video")
        
        # Convert lists to key-value mappings where key = value
        for field in file_fields:
            mappings[field] = field
        for field in image_fields:
            mappings[field] = field
        for field in video_fields:
            mappings[field] = field
        
        return mappings
    
    def reset_failed_files_counter(self) -> None:
        """Reset failed files counter bij start van nieuwe directory processing."""
        with self.db_lock:
            self.failed_files_count = 0
            logging_service.log("INFO", "Failed files counter reset")
    
    def add_media_record(self, metadata: Dict[str, Any]) -> bool:
        """Add of update media record in database (thread-safe)."""
        with self.db_lock:
            try:
                # DEBUG: Test if function is called
                logging_service.log("INFO", "=== add_media_record CALLED ===")
                logging_service.log("INFO", f"Metadata keys: {list(metadata.keys())}")
                
                # Get FQPN (Fully Qualified Path Name) as primary key
                fqpn = metadata.get('SourceFile') or metadata.get('YAPMO:FQPN') or metadata.get('YAPMO_FQPN')
                if not fqpn:
                    logging_service.log("WARNING", "No FQPN found in metadata, skipping record")
                    return False
                
                # Check if we've exceeded max retry files
                if self.failed_files_count >= self.database_max_retry_files:
                    logging_service.log("ERROR", f"Maximum failed files ({self.database_max_retry_files}) reached, stopping processing")
                    raise RuntimeError("Maximum failed files reached")
                
                # Try to add/update record with retry logic
                success = self._add_record_with_retry(metadata, fqpn)
                
                if success:
                    return True
                else:
                    # Increment failed files counter
                    self.failed_files_count += 1
                    logging_service.log("WARNING", f"Failed to add record for {fqpn} after all retries. Failed files: {self.failed_files_count}")
                    return False
                
            except Exception as e:
                logging_service.log("ERROR", f"Error adding media record: {e}")
                raise
    
    def _add_record_with_retry(self, metadata: Dict[str, Any], fqpn: str) -> bool:
        """Add record with retry logic."""
        for attempt in range(self.database_write_retry + 1):  # +1 for initial attempt
            try:
                if attempt == 0:
                    # First attempt
                    return self._insert_or_replace_record(metadata, fqpn)
                else:
                    # Retry attempt
                    logging_service.log("INFO", f"Retry attempt {attempt} for {fqpn}")
                    return self._insert_or_replace_record(metadata, fqpn)
                    
            except sqlite3.Error as e:
                if attempt < self.database_write_retry:
                    logging_service.log("WARNING", f"Database write attempt {attempt + 1} failed for {fqpn}: {e}")
                    continue
                else:
                    # Final attempt failed
                    logging_service.log("WARNING", f"All database write attempts failed for {fqpn}: {e}")
                    return False
        
        return False
    
    def _insert_or_replace_record(self, metadata: Dict[str, Any], fqpn: str) -> bool:
        """Insert or replace record in database."""
        try:
            # DEBUG: Print received JSON
            logging_service.log("INFO", f"=== RECEIVED JSON ===")
            for key, value in metadata.items():
                logging_service.log("INFO", f"JSON: {key} = {value}")
            logging_service.log("INFO", f"FQPN: {fqpn}")
            logging_service.log("INFO", f"=====================")
            
            # Prepare data for database - start with FQPN
            data = {'YAPMO_FQPN': fqpn}
            
            # Add ALL metadata fields directly to database
            for key, value in metadata.items():
                # Skip FQPN as it's already set
                if key == 'YAPMO_FQPN':
                    continue
                
                # Convert lists to comma-separated strings
                if isinstance(value, list):
                    value = ', '.join(str(x) for x in value)
                
                # Store value directly - no mapping needed
                data[key] = str(value) if value is not None else None
            
            # DEBUG: Print prepared data
            logging_service.log("INFO", f"=== PREPARED DATA ===")
            for key, value in data.items():
                logging_service.log("INFO", f"DATA: {key} = {value}")
            logging_service.log("INFO", f"=====================")
            
            # Use INSERT OR REPLACE for UPSERT functionality
            fields = list(data.keys())
            placeholders = ', '.join(['?' for _ in fields])
            values = list(data.values())
            
            sql = f"""
                INSERT OR REPLACE INTO {self.db_table_media} ({', '.join(fields)})
                VALUES ({placeholders})
            """
            
            # DEBUG: Print SQL statement
            logging_service.log("INFO", f"=== SQL STATEMENT ===")
            logging_service.log("INFO", f"SQL: {sql}")
            logging_service.log("INFO", f"VALUES: {values}")
            logging_service.log("INFO", f"=====================")
            
            self.cursor.execute(sql, values)
            self.connection.commit()
            
            logging_service.log("INFO", f"=== RECORD INSERTED SUCCESSFULLY ===")
            
            return True
            
        except sqlite3.Error as e:
            logging_service.log("ERROR", f"Database error in _insert_or_replace_record: {e}")
            raise
    
    def close(self) -> None:
        """Close database connection."""
        with self.db_lock:
            if self.connection:
                try:
                    self.connection.close()
                    logging_service.log("INFO", "Database connection closed")
                except sqlite3.Error as e:
                    logging_service.log("ERROR", f"Error closing database: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
