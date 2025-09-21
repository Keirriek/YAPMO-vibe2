"""Database Manager voor YAPMO - Queue-based processing."""

import asyncio
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, Optional
from threading import Lock

from config import get_param
from queues.result_queue import ResultQueue, MetadataResult


class DatabaseManager:
    """Database manager voor YAPMO met queue-based processing."""
    
    def __init__(self, result_queue: ResultQueue) -> None:
        """Initialize DatabaseManager met ResultQueue."""
        self.result_queue = result_queue
        
        # Load configuratie parameters
        self.db_name = get_param("database", "database_name")
        self.db_table_media = get_param("database", "database_table_media")
        self.database_clean = get_param("database", "database_clean")
        self.batch_size = get_param("database", "database_write_batch_size")
        
        # Database paths
        self.db_path = Path(self.db_name)
        
        # Database state
        self.connection: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None
        
        # Thread safety
        self.db_lock = Lock()
        
        # Processing state
        self.batch = []
        self.processed_count = 0
        
        # Initialize database
        self._initialize_database()
        
        print("DEBUG: DatabaseManager initialized successfully")
    
    def _initialize_database(self) -> None:
        """Initialize database en tabellen."""
        try:
            print("DEBUG: Starting database initialization")
            
            # Clean database indien gewenst
            if self.database_clean and self.db_path.exists():
                self.db_path.unlink()
                print(f"DEBUG: Removed existing database: {self.db_path}")
            
            # Connect to database
            self._connect()
            
            # Initialize tables
            self._initialize_tables()
            
            print("DEBUG: Database initialization completed successfully")
            
        except Exception as e:
            error_msg = f"Database initialization failed: {e}"
            print(f"ERROR: {error_msg}")
            raise
    
    def _connect(self) -> None:
        """Connect to SQLite database met timeout."""
        try:
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database met 30 seconden timeout
            self.connection = sqlite3.connect(str(self.db_path), timeout=30.0)
            self.cursor = self.connection.cursor()
            
            print(f"DEBUG: Connected to database: {self.db_path}")
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                error_msg = "Database connection timeout ERROR - Check database, maybe in use by other programs"
                print(f"ERROR: {error_msg}")
            else:
                error_msg = f"Database connection error: {e}"
                print(f"ERROR: {error_msg}")
            raise
        except Exception as e:
            error_msg = f"Unexpected database connection error: {e}"
            print(f"ERROR: {error_msg}")
            raise
    
    def _initialize_tables(self) -> None:
        """Initialize alle benodigde tabellen."""
        try:
            # Create media table
            self._create_media_table()
            
            print("DEBUG: All tables initialized successfully")
            
        except Exception as e:
            error_msg = f"Error initializing tables: {e}"
            print(f"ERROR: {error_msg}")
            raise
    
    def _create_media_table(self) -> None:
        """Create media table met basic fields."""
        try:
            # Basic fields for now - will be extended later
            fields = [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "file_path TEXT UNIQUE NOT NULL",
                "hash_value TEXT",
                "file_size INTEGER",
                "timestamp REAL",
                "exif_data TEXT",  # JSON string
                "file_info TEXT"   # JSON string
            ]
            
            # Create table
            create_sql = f"""
                CREATE TABLE IF NOT EXISTS {self.db_table_media} (
                    {', '.join(fields)}
                )
            """
            
            self.cursor.execute(create_sql)
            
            # Create indexes for performance
            self.cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_file_path ON {self.db_table_media}(file_path)")
            self.cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_hash ON {self.db_table_media}(hash_value)")
            
            self.connection.commit()
            print(f"DEBUG: Media table '{self.db_table_media}' created/verified")
            
        except sqlite3.Error as e:
            error_msg = f"Error creating media table: {e}"
            print(f"ERROR: {error_msg}")
            raise
    
    async def start_consumer(self) -> None:
        """Start consuming results from queue and writing to database."""
        print("DEBUG: Starting database consumer")
        
        while True:
            if self.result_queue.is_aborted():
                print("DEBUG: Database consumer stopped due to abort")
                break
            
            # Get result from queue
            result = await self.result_queue.get_result()
            
            if result:
                # Check for end_of_results signal
                if hasattr(result, 'is_end_signal') and result.is_end_signal:
                    print("DEBUG: Received end_of_results signal")
                    break
                
                # Add to batch
                self.batch.append(result)
                
                # Write batch if full
                if len(self.batch) >= self.batch_size:
                    await self._write_batch()
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.01)
        
        # Write remaining batch
        if self.batch:
            await self._write_batch()
        
        print("DEBUG: Database consumer finished")
    
    async def _write_batch(self) -> None:
        """Write batch of results to database."""
        if not self.batch:
            return
        
        try:
            with self.db_lock:
                # Prepare batch data
                batch_data = []
                for result in self.batch:
                    # Convert to database format
                    import json
                    data = (
                        result.file_path,
                        result.hash_value,
                        result.file_size,
                        result.timestamp,
                        json.dumps(result.exif_data),
                        json.dumps(result.file_info)
                    )
                    batch_data.append(data)
                
                # Insert batch
                insert_sql = f"""
                    INSERT OR REPLACE INTO {self.db_table_media} 
                    (file_path, hash_value, file_size, timestamp, exif_data, file_info)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                
                self.cursor.executemany(insert_sql, batch_data)
                self.connection.commit()
                
                # Update counters
                self.processed_count += len(self.batch)
                print(f"DEBUG: Wrote batch of {len(self.batch)} records to database (total: {self.processed_count})")
                
                # Clear batch
                self.batch.clear()
                
        except Exception as e:
            error_msg = f"Error writing batch to database: {e}"
            print(f"ERROR: {error_msg}")
            # Clear batch to prevent infinite retry
            self.batch.clear()
    
    def get_processed_count(self) -> int:
        """Get number of processed records."""
        return self.processed_count
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            try:
                self.connection.close()
                print("DEBUG: Database connection closed")
            except sqlite3.Error as e:
                error_msg = f"Error closing database: {e}"
                print(f"ERROR: {error_msg}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
