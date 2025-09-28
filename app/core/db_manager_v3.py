"""Database manager v3 for file processing results - Clean implementation."""

import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from threading import Lock
from contextlib import contextmanager

from core.logging_service_v2 import logging_service
from config import get_param


class DatabaseManagerV3:
    """SQLite database manager with config-driven field mapping - Clean implementation."""
    
    def __init__(self) -> None:
        """Initialize database manager with config parameters."""
        # Load database config from config.json
        self.db_name = get_param("database", "database_path")
        self.db_table_media = get_param("database", "database_table_media")
        self.write_retry = get_param("database", "database_write_retry")
        self.max_retry_files = get_param("database", "database_max_retry_files")
        self.batch_size = get_param("database", "database_write_batch_size")
        self.database_timeout = get_param("database", "database_timeout")
        self.database_encoding = get_param("database", "database_encoding")
        self.database_journal_mode = get_param("database", "database_journal_mode")
        self.database_synchronous = get_param("database", "database_synchronous")
        self.database_cache_size = get_param("database", "database_cache_size")
        self.database_temp_store = get_param("database", "database_temp_store")
        
        # Database paths
        self.db_path = Path(self.db_name)
        
        # Thread safety
        self.db_lock = Lock()
        
        # Load field mappings once at initialization for efficiency
        self.field_mappings = self._get_field_mappings()
        self.db_fields = list(self.field_mappings.values()) + ['id']
        
        # Cache batch size for efficiency
        self.batch_size = get_param("database", "database_write_batch_size")
        self.transaction_batch_size = get_param("database", "database_transaction_batch_size")
        self.pending_batches = 0
        
        # Cache INSERT SQL statement for efficiency
        placeholders = ', '.join(['?' for _ in self.db_fields])
        self.insert_sql = f"INSERT INTO {self.db_table_media} ({', '.join(self.db_fields)}) VALUES ({placeholders})"
        
        # Initialize database
        self._initialize_database()
        
        logging_service.log("INFO", "DatabaseManagerV3 initialized successfully")
    
    def _initialize_database(self) -> None:
        """Initialize database and tables with UTF-8 support."""
        try:
            logging_service.log("INFO", "Starting database initialization")

            # Connect and create tables
            self._connect_and_create_tables()

            logging_service.log("INFO", "Database initialization completed successfully")

        except Exception as e:
            error_msg = f"Database initialization failed: {e}"
            logging_service.log("ERROR", error_msg)
            raise

    def clear_database(self) -> None:
        """Clear the database by deleting the database file."""
        try:
            if self.db_path.exists():
                self.db_path.unlink()
                logging_service.log("INFO", f"Database cleared: {self.db_path}")
            else:
                logging_service.log("INFO", "Database does not exist, nothing to clear")
        except Exception as e:
            error_msg = f"Error clearing database: {e}"
            logging_service.log("ERROR", error_msg)
            raise
    
    def _connect_and_create_tables(self) -> None:
        """Connect to database and create tables with optimal PRAGMA settings."""
        try:
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect with timeout from config
            conn = sqlite3.connect(str(self.db_path), timeout=self.database_timeout)
            
            # Essential PRAGMA's for your requirements
            conn.execute(f"PRAGMA encoding = '{self.database_encoding}'")  # Non-ASCII support
            conn.execute("PRAGMA foreign_keys = ON")   # Data integrity
            conn.execute(f"PRAGMA journal_mode = {self.database_journal_mode}")  # Performance
            conn.execute(f"PRAGMA synchronous = {self.database_synchronous}") # Speed vs safety
            
            # Performance PRAGMA's
            conn.execute(f"PRAGMA cache_size = {self.database_cache_size}")  # More cache
            conn.execute(f"PRAGMA temp_store = {self.database_temp_store}") # Temp in RAM
            
            # Create table
            self._create_media_table(conn)
            
            conn.close()
            logging_service.log("INFO", f"Database created successfully: {self.db_path}")
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                error_msg = "Database connection timeout - Check if database is in use"
                logging_service.log("ERROR", error_msg)
            else:
                error_msg = f"Database connection error: {e}"
                logging_service.log("ERROR", error_msg)
            raise
        except Exception as e:
            error_msg = f"Unexpected database error: {e}"
            logging_service.log("ERROR", error_msg)
            raise
    
    def _create_media_table(self, conn: sqlite3.Connection) -> None:
        """Create media table with dynamic fields from config."""
        try:
            # Use cached field mappings for efficiency
            field_mappings = self.field_mappings
            
            # Base fields
            fields = [
                "id INTEGER PRIMARY KEY AUTOINCREMENT"
            ]
            
            # Add fields from config
            added_fields = set()
            for exif_key, db_field in field_mappings.items():
                if db_field not in added_fields:
                    fields.append(f"{db_field} TEXT")
                    added_fields.add(db_field)
            
            # Create table
            create_sql = f"""
                CREATE TABLE IF NOT EXISTS {self.db_table_media} (
                    {', '.join(fields)}
                )
            """
            
            conn.execute(create_sql)
            
            # Create indexes for performance
            if 'YAPMO_hash' in added_fields:
                conn.execute(f"CREATE INDEX IF NOT EXISTS idx_hash ON {self.db_table_media}(YAPMO_hash)")
            
            if 'FILE_Path' in added_fields:
                conn.execute(f"CREATE INDEX IF NOT EXISTS idx_file_path ON {self.db_table_media}(FILE_Path)")
            
            conn.commit()
            logging_service.log("INFO", f"Media table '{self.db_table_media}' created/verified")
            
        except sqlite3.Error as e:
            error_msg = f"Error creating media table: {e}"
            logging_service.log("ERROR", error_msg)
            raise
    
    def _get_field_mappings(self) -> Dict[str, str]:
        """Get combined field mappings from config."""
        mappings = {}
        
        try:
            # Combine all field mappings from config
            from config import get_section
            yapmo_fields = get_section("metadata_fields_yapmo")
            file_fields = get_section("metadata_fields_file")
            image_fields = get_section("metadata_fields_image")
            video_fields = get_section("metadata_fields_video")
            
            # Ensure we have dictionaries
            if not isinstance(yapmo_fields, dict):
                yapmo_fields = {}
            if not isinstance(file_fields, dict):
                file_fields = {}
            if not isinstance(image_fields, dict):
                image_fields = {}
            if not isinstance(video_fields, dict):
                video_fields = {}
            
            # Process all field mappings
            for field_dict in [yapmo_fields, file_fields, image_fields, video_fields]:
                if isinstance(field_dict, dict):
                    mappings.update(field_dict)
            
            logging_service.log("INFO", f"Field mappings loaded: {len(mappings)} fields")
            
        except Exception as e:
            error_msg = f"Error loading field mappings: {e}"
            logging_service.log("ERROR", error_msg)
            raise
        
        return mappings
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling and PRAGMA settings."""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=self.database_timeout)
            
            # Apply PRAGMA settings for each connection
            conn.execute(f"PRAGMA encoding = '{self.database_encoding}'")
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(f"PRAGMA journal_mode = {self.database_journal_mode}")
            conn.execute(f"PRAGMA synchronous = {self.database_synchronous}")
            conn.execute(f"PRAGMA cache_size = {self.database_cache_size}")
            conn.execute(f"PRAGMA temp_store = {self.database_temp_store}")
            
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            error_msg = f"Database connection error: {e}"
            logging_service.log("ERROR", error_msg)
            raise
        finally:
            if conn:
                conn.close()
    
    def check_database_schema_match(self) -> bool:
        """Check if database schema matches current config."""
        try:
            if not self.db_path.exists():
                logging_service.log("INFO", "Database does not exist - schema check not applicable")
                return True
            
            # Use cached field mappings for efficiency
            expected_fields = set(self.field_mappings.values())
            expected_fields.add('id')  # Add primary key
            
            # Get actual database columns
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({self.db_table_media})")
                actual_columns = {row[1] for row in cursor.fetchall()}
            
            # Check if schemas match
            missing_in_db = expected_fields - actual_columns
            extra_in_db = actual_columns - expected_fields
            
            if missing_in_db or extra_in_db:
                logging_service.log("WARNING", f"Database schema mismatch detected:")
                if missing_in_db:
                    logging_service.log("WARNING", f"  Missing columns in DB: {sorted(missing_in_db)}")
                if extra_in_db:
                    logging_service.log("WARNING", f"  Extra columns in DB: {sorted(extra_in_db)}")
                return False
            else:
                logging_service.log("INFO", f"Database schema matches config - OK: {self.db_path}")
                return True
                
        except Exception as e:
            logging_service.log("ERROR", f"Error checking database schema: {e}")
            return False

    def _write_results_to_database(self, results: List[Dict[str, Any]]) -> None:
        """Write file processing results to database.
        
        Args:
            results: List of file processing results to write to database
        """
        if not results:
            return
            
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Use cached field mappings, db_fields and SQL statement for efficiency
                field_mappings = self.field_mappings
                db_fields = self.db_fields
                insert_sql = self.insert_sql
                
                # Prepare all values for batch INSERT using list comprehension for efficiency
                all_values = [
                    [None if field == 'id' else result.get('metadata', {}).get(field, '') 
                     for field in db_fields]
                    for result in results 
                    if result.get('success', False)
                ]
                
                # Execute batch INSERT for all records at once
                if all_values:
                    cursor.executemany(insert_sql, all_values)
                    # logging_service.log("DEBUG", f"Batch inserted {len(all_values)} records")#DEBUG_OFF Batch inserted X records
                    
                    # Transaction batching - commit after X batches
                    self.pending_batches += 1
                    if self.pending_batches >= self.transaction_batch_size:
                        conn.commit()
                        self.pending_batches = 0
                        # logging_service.log("DEBUG", f"Transaction committed after {self.transaction_batch_size} batches")#DEBUG_OFF Transaction committed after X batches
                    else:
                        # logging_service.log("DEBUG", f"Batch queued, pending batches: {self.pending_batches}/{self.transaction_batch_size}")#DEBUG_OFF Batch queued, pending batches: X/Y
                        pass
                # logging_service.log("DEBUG", f"Successfully wrote {len(results)} results to database")#DEBUG_OFF Successfully wrote X results to database
                
        except Exception as e:
            error_msg = f"Error writing results to database: {e}"
            logging_service.log("ERROR", error_msg)
            raise

    def _write_results_to_database(self, results: List[Dict[str, Any]]) -> None:
        """Write file processing results to database."""
        if not results:
            return
            
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Use cached field mappings, db_fields and SQL statement for efficiency
                field_mappings = self.field_mappings
                db_fields = self.db_fields
                insert_sql = self.insert_sql
                
                # Prepare all values for batch INSERT using list comprehension for efficiency
                all_values = [
                    [None if field == 'id' else result.get('metadata', {}).get(field, '') 
                     for field in db_fields]
                    for result in results 
                    if result.get('success', False)
                ]
                
                # Execute batch INSERT for all records at once
                if all_values:
                    cursor.executemany(insert_sql, all_values)
                    logging_service.log("DEBUG", f"Batch inserted {len(all_values)} records")#DEBUG_ON Batch inserted X records
                    
                    # Transaction batching - commit after X batches
                    self.pending_batches += 1
                    if self.pending_batches >= self.transaction_batch_size:
                        conn.commit()
                        self.pending_batches = 0
                        logging_service.log("DEBUG", f"Transaction committed after {self.transaction_batch_size} batches")#DEBUG_ON Transaction committed after X batches
                    else:
                        logging_service.log("DEBUG", f"Batch queued, pending batches: {self.pending_batches}/{self.transaction_batch_size}")#DEBUG_ON Batch queued, pending batches: X/Y
                        # Always commit for now to ensure data is written
                        conn.commit()
                        logging_service.log("DEBUG", "Force committed transaction to ensure data persistence")#DEBUG_ON Force committed transaction to ensure data persistence
                logging_service.log("DEBUG", f"Successfully wrote {len(results)} results to database")#DEBUG_ON Successfully wrote X results to database
                
        except Exception as e:
            error_msg = f"Error writing results to database: {e}"
            logging_service.log("ERROR", error_msg)
            raise

    def _finalize_transaction(self) -> None:
        """Finalize any pending transaction batches."""
        try:
            if self.pending_batches > 0:
                with self._get_connection() as conn:
                    conn.commit()
                logging_service.log("DEBUG", f"Finalized transaction with {self.pending_batches} pending batches")#DEBUG_ON Finalized transaction with X pending batches
                self.pending_batches = 0
        except Exception as e:
            logging_service.log("ERROR", f"Error finalizing transaction: {e}")

    def clear_database(self) -> None:
        """Clear the database by removing the database file."""
        try:
            # Finalize any pending transactions before clearing
            self._finalize_transaction()
            
            if self.db_path.exists():
                self.db_path.unlink()
                logging_service.log("INFO", f"Database cleared: {self.db_path}")
            else:
                logging_service.log("INFO", "Database does not exist, nothing to clear")
        except Exception as e:
            error_msg = f"Error clearing database: {e}"
            logging_service.log("ERROR", error_msg)
            raise


# Global database manager instance
_db_manager: Optional[DatabaseManagerV3] = None


def get_database_manager() -> DatabaseManagerV3:
    """Get global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManagerV3()
    return _db_manager


def check_database_schema() -> bool:
    """Check if database schema matches config - simple interface function."""
    try:
        db_manager = get_database_manager()
        return db_manager.check_database_schema_match()
    except Exception as e:
        logging_service.log("ERROR", f"Database schema check failed: {e}")
        return False


def create_end_of_batch_result() -> Dict[str, Any]:
    """Create END_OF_BATCH result to signal end of batch processing.
    
    Returns:
        Dictionary with END_OF_BATCH marker
    """
    return {
        'file_path': 'END_OF_BATCH',
        'is_last_result': True,
        'worker_id': -1,
        'success': True,
        'processing_time': 0.0,
        'log_messages': [{
            'level': 'DEBUG',
            'message': 'END_OF_BATCH marker - batch processing complete'
        }]
    }


def db_add_result(result: List[Dict[str, Any]]) -> None:
    """Database interface function - processes file results with batch handling.
    
    Args:
        result: List of dictionaries containing file processing results
    """
    # logging_service.log("DEBUG", f"db_add_result called with {len(result) if result else 0} results")#DEBUG_OFF db_add_result called with X results
    
    if not result:
        # logging_service.log("DEBUG", "db_add_result: No results to process, returning")#DEBUG_OFF db_add_result: No results to process, returning
        return
    
    # Check if this is the last result in a batch
    # #DEBUG_OFF Start Bock Last batch add_db_result
    # is_last_batch = any(r.get('is_last_result', False) for r in result)#DEBUG_OFF
    #     # logging_service.log("DEBUG", f"db_add_result: is_last_batch = {is_last_batch}")#DEBUG_OFF db_add_result: is_last_batch = X
    
    # if is_last_batch:
    #     logging_service.log("DEBUG", f"Processing final batch with {len(result)} results")#DEBUG_OFF Processing final batch with X results
    # else:
    #     logging_service.log("DEBUG", f"Processing batch with {len(result)} results")#DEBUG_OFF Processing batch with X results
    # #DEBUG_OFF End Block Last batch add_db_result
    # Check if this is the last batch (END_OF_BATCH marker present)
    is_last_batch = any(r.get('is_last_result', False) for r in result)
    
    # Filter out END_OF_BATCH markers and process only real results
    real_results = [r for r in result if not r.get('is_last_result', False)]
    
    if not real_results:
        # logging_service.log("DEBUG", "db_add_result: No real results to process, only END_OF_BATCH markers")#DEBUG_OFF db_add_result: No real results to process, only END_OF_BATCH markers
        return
    
    # Process real results to database
    try:
        db_manager = get_database_manager()
        db_manager._write_results_to_database(real_results)
        # logging_service.log("DEBUG", f"db_add_result: Successfully wrote {len(real_results)} results to database")#DEBUG_OFF db_add_result: Successfully wrote X results to database
        
        # Finalize transaction if this is the last batch
        if is_last_batch:
            db_manager._finalize_transaction()
            # logging_service.log("DEBUG", "db_add_result: Finalized transaction for last batch")#DEBUG_OFF db_add_result: Finalized transaction for last batch
            
    except Exception as e:
        logging_service.log("ERROR", f"db_add_result: Failed to write results to database: {e}")
        # Log individual results for debugging
        for r in real_results:
            file_path = r.get('file_path', 'unknown')
            success = r.get('success', False)
            logging_service.log("DEBUG", f"Result: {file_path} - {'SUCCESS' if success else 'FAILED'}")#DEBUG_OFF Result: file_path - SUCCESS/FAILED
