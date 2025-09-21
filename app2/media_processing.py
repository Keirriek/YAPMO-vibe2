"""MediaProcessing - Parallel media file processing voor YAPMO applicatie.

Stap 1A: Basis MediaProcessing structuur.
Stap 1D: Hash functionaliteit toegevoegd.
"""

import hashlib
import json
import logging
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from multiprocessing import Value
from pathlib import Path
from typing import Any

from config import get_param
from globals import logging_service


# Shared variable voor progress tracking
class MediaProcessing:
    """Basis MediaProcessing class voor parallel file processing."""

    # Shared variable voor progress tracking (multiprocessing-safe)
    _shared_counter = None

    def __init__(self, log_files_count_update: int | None = None) -> None:
        """Initialize MediaProcessing met configuratie."""
        # DEV LOG: MediaProcessing initialization started
        logging_service.log("DEV", "=== MediaProcessing.__init__ STARTED ===")

        # Initialize shared counter for multiprocessing
        if MediaProcessing._shared_counter is None:
            MediaProcessing._shared_counter = Value("i", 0)

        # Load configuratie - direct individuele parameters ophalen
        # Processing instellingen
        self.max_workers = get_param("processing", "max_workers")
        # Gebruik doorgegeven parameter of haal uit config
        if log_files_count_update is not None:
            self.log_files_count_update = log_files_count_update
        else:
            self.log_files_count_update = get_param("logging", "log_files_count_update")
        self.log_extensive = get_param("logging", "log_extensive")
        self.ui_update = get_param("processing", "ui_update")
        self.use_exiftool = get_param("processing", "use_exiftool")
        self.exiftool_timeout = get_param("processing", "exiftool_timeout")

        # Hash configuratie
        self.hash_algorithm = get_param("processing", "hash_algorithm")
        self.hash_chunk_size = get_param("processing", "hash_chunk_size")
        self.video_header_size = get_param("processing", "video_header_size")

        # File type extensies
        self.image_extensions = get_param("extensions", "image_extensions")
        self.video_extensions = get_param("extensions", "video_extensions")
        self.sidecar_extensions = get_param("extensions", "sidecar_extensions")

        # Processing state
        self.is_running = False
        self.is_aborted = False
        self.processed_count = 0
        self.error_count = 0
        self.start_time = None

        # ExifTool state
        self.exiftool_available = False
        self.exiftool_first_error = True
        self.exiftool_disabled_logged = False

        # Reset shared counter
        if MediaProcessing._shared_counter:
            MediaProcessing._shared_counter.value = 0

        # Logging setup
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize logged milestones set
        self._logged_milestones: set[int] = set()



        # Check ExifTool availability
        self._check_exiftool_availability()

        # DEV LOG: MediaProcessing initialization completed
        logging_service.log("DEV", "=== MediaProcessing.__init__ COMPLETED ===")
        logging_service.log(
            "DEV",
            f"Initialized with max_workers={self.max_workers}, "
            f"use_exiftool={self.use_exiftool}, "
            f"log_files_count_update={self.log_files_count_update}, "
            f"hash_algorithm={self.hash_algorithm}, "
            f"video_header_size={self.video_header_size} bytes",
        )

    @property
    def files_processed(self) -> int:
        """Get the current number of processed files (multiprocessing-safe)."""
        if MediaProcessing._shared_counter:
            return MediaProcessing._shared_counter.value
        return 0

    @files_processed.setter
    def files_processed(self, value: int) -> None:
        """Set the number of processed files (multiprocessing-safe)."""
        if MediaProcessing._shared_counter:
            MediaProcessing._shared_counter.value = value

    def _check_exiftool_availability(self) -> None:
        """Check if ExifTool is available and handle configuration."""
        try:
            # Test ExifTool availability
            result = subprocess.run(
                ["exiftool", "-ver"],
                capture_output=True,
                text=True,
                timeout=5, check=False,
            )
            if result.returncode == 0:
                self.exiftool_available = True
                logging_service.log(
                    "INFO",
                    f"ExifTool available (version: {result.stdout.strip()})",
                )
            else:
                self.exiftool_available = False

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            self.exiftool_available = False

        # Handle ExifTool configuration
        if self.use_exiftool and not self.exiftool_available:
            # ExifTool enabled but not available - ERROR and stop
            error_msg = (
                "ExifTool is enabled in config but not available. "
                "Please install ExifTool or disable use_exiftool in config.json"
            )
            logging_service.log("ERROR", error_msg)
            msg = "ExifTool not available but enabled in config"
            raise RuntimeError(msg)

        elif not self.use_exiftool and not self.exiftool_disabled_logged:
            # ExifTool disabled in config - WARNING once
            logging_service.log(
                "WARNING",
                "ExifTool is disabled in config - metadata extraction skipped",
            )
            self.exiftool_disabled_logged = True

    def _extract_exiftool_metadata(self, file_path: Path) -> dict[str, Any]:
        """Extract metadata using ExifTool.
        
        Args:
        ----
            file_path: Path to the file to process
            
        Returns:
        -------
            Dictionary with metadata and ExiftoolExitCode
            
        """
        if not self.use_exiftool:
            # ExifTool disabled - return default values
            result = {"YAPMO_ExiftoolExitCode": 99}
            self._add_null_metadata_fields(result)
            return result

        if not self.exiftool_available:
            # ExifTool not available - return fault
            result = {"YAPMO_ExiftoolExitCode": 1}
            self._add_null_metadata_fields(result)
            return result

        try:
            # Execute ExifTool command
            cmd = ["exiftool", "-j", "-G", "-q", str(file_path)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.exiftool_timeout / 1000.0, check=False,  # Convert msec to seconds
            )

            if result.returncode == 0:
                # Success - parse JSON output
                return self._process_exiftool_output(result.stdout, file_path)
            else:
                # ExifTool error
                self._log_exiftool_error(result.stderr, file_path)
                output = {"YAPMO_ExiftoolExitCode": result.returncode}
                self._add_null_metadata_fields(output)
                return output

        except subprocess.TimeoutExpired:
            # Timeout error
            self._log_exiftool_error("Timeout expired", file_path)
            output = {"YAPMO_ExiftoolExitCode": 1}
            self._add_null_metadata_fields(output)
            return output

        except Exception as e:
            # Other errors
            self._log_exiftool_error(str(e), file_path)
            output = {"YAPMO_ExiftoolExitCode": 1}
            self._add_null_metadata_fields(output)
            return output

    def _process_exiftool_output(
        self, stdout: str, file_path: Path,
    ) -> dict[str, Any]:
        """Process ExifTool JSON output and map to database fields.
        
        Args:
        ----
            stdout: ExifTool JSON output
            file_path: Path to the processed file
            
        Returns:
        -------
            Dictionary with mapped metadata fields
            
        """
        try:
            # Parse JSON output
            json_data = json.loads(stdout)
            if not json_data or not isinstance(json_data, list):
                # Empty or invalid JSON
                result = {"YAPMO_ExiftoolExitCode": 0}
                self._add_null_metadata_fields(result)
                return result

            # Get first (and only) file data
            file_data = json_data[0] if json_data else {}

            # Start with success exit code
            result = {"YAPMO_ExiftoolExitCode": 0}

            # Map metadata fields based on file type and config
            file_type = self._determine_file_type(file_path)

            # Metadata fields
            file_fields = get_param("metadata_fields_file")
            image_fields = get_param("metadata_fields_image")
            video_fields = get_param("metadata_fields_video")

            # Map all possible fields (always same JSON structure)
            all_fields = {**file_fields, **image_fields, **video_fields}

            for exif_field, db_field in all_fields.items():
                if exif_field in file_data:
                    result[db_field] = file_data[exif_field]
                else:
                    result[db_field] = None

            return result

        except json.JSONDecodeError:
            # JSON parsing error
            self._log_exiftool_error("JSON parsing failed", file_path)
            result = {"YAPMO_ExiftoolExitCode": 1}
            self._add_null_metadata_fields(result)
            return result

    def _add_null_metadata_fields(self, result: dict[str, Any]) -> None:
        """Add all metadata fields with NULL values.
        
        Args:
        ----
            result: Dictionary to add NULL fields to
            
        """
        # Get all metadata field mappings
        file_fields = get_param("metadata_fields_file")
        image_fields = get_param("metadata_fields_image")
        video_fields = get_param("metadata_fields_video")

        # Add all fields with NULL values
        all_fields = {**file_fields, **image_fields, **video_fields}
        for db_field in all_fields.values():
            if db_field not in result:
                result[db_field] = None

    def _determine_file_type(self, file_path: Path) -> str:
        """Determine if file is image or video based on extension.
        
        Args:
        ----
            file_path: Path to the file
            
        Returns:
        -------
            "image" or "video"
            
        """
        file_ext = file_path.suffix.lower()
        if file_ext in self.image_extensions:
            return "image"
        return "video"

    def _log_exiftool_error(self, error_msg: str, file_path: Path) -> None:
        """Log ExifTool errors with proper WARNING/INFO levels.
        
        Args:
        ----
            error_msg: Error message from ExifTool
            file_path: Path to the file that caused the error
            
        """
        if self.exiftool_first_error:
            # First error - WARNING
            logging_service.log(
                "WARNING",
                "ExifTool has returned errors during processing",
            )
            self.exiftool_first_error = False

        # Individual error - INFO
        logging_service.log(
            "INFO",
            f"ExifTool error for {file_path}: {error_msg}",
        )

    def _calculate_file_hash(self, file_path: Path, file_type: str, existing_metadata: dict[str, Any] | None = None) -> str:
        """Calculate hash based on file type.
        
        Args:
        ----
            file_path: Path to the file
            file_type: Type of file ("image" or "video")
            existing_metadata: Optional existing metadata for video hash calculation
            
        Returns:
        -------
            Hash string for the file
            
        """
        try:
            if file_type == "image":
                return self._calculate_image_hash(file_path)
            elif file_type == "video":
                return self._calculate_video_hash(file_path, existing_metadata)
            else:
                # Fallback for unknown types
                return self._calculate_image_hash(file_path)
        except Exception as e:
            #DEBUG_start
            logging_service.log(
                "DEV",
                f"Hash calculation error for {file_path}: {e}",
            )
            #DEBUG_einde
            return f"hash_error_{int(time.time())}"

    def _calculate_image_hash(self, file_path: Path) -> str:
        """Calculate full SHA-256 hash for images.
        
        Args:
        ----
            file_path: Path to the image file
            
        Returns:
        -------
            SHA-256 hash string
            
        """
        #DEBUG_image_hash_start
        logging_service.log(
            "DEV",
            f"Starting full hash calculation for image: {file_path}",
        )
        #DEBUG_image_hash_end

        hash_result = hashlib.sha256()

        try:
            with file_path.open("rb") as f:
                for chunk in iter(lambda: f.read(self.hash_chunk_size), b""):
                    hash_result.update(chunk)

            hash_value = hash_result.hexdigest()

            #DEBUG_image_hash_complete
            logging_service.log(
                "DEV",
                f"Image hash calculation completed: {hash_value[:16]}...",
            )
            #DEBUG_image_hash_complete_end

            return hash_value

        except Exception as e:
            #DEBUG_image_hash_failed
            logging_service.log(
                "DEV",
                f"Image hash calculation failed: {e}",
            )
            #DEBUG_image_hash_failed_end
            raise

    def _calculate_video_hash(self, file_path: Path, existing_metadata: dict[str, Any] | None = None) -> str:
        """Calculate hybrid hash for videos using metadata and header.
        
        Args:
        ----
            file_path: Path to the video file
            existing_metadata: Optional existing metadata for video hash calculation
            
        Returns:
        -------
            Hybrid hash string for video
            
        """
        #DEBUG_video_hash_start
        logging_service.log(
            "DEV",
            f"Starting hybrid hash calculation for video: {file_path}",
        )
        #DEBUG_video_hash_end

        try:
            # Get file info
            file_stat = file_path.stat()
            file_size = file_stat.st_size
            file_ext = file_path.suffix.lower().lstrip(".")

            # Read header bytes
            header_bytes = self._read_file_header(file_path, self.video_header_size)
            header_hash = hashlib.sha256(header_bytes).hexdigest()[:16]

            # Try to get creation date from existing metadata or ExifTool
            date_str = "unknown_date"

            if existing_metadata and "EXIF_DateTimeOriginal" in existing_metadata:
                exif_date = existing_metadata["EXIF_DateTimeOriginal"]
                if exif_date and exif_date != "None":
                    # Parse ExifTool date format and convert to YYYY-MM-DD
                    try:
                        # ExifTool format: "2024:01:15 14:30:25"
                        if ":" in str(exif_date):
                            date_parts = str(exif_date).split(" ")[0].split(":")
                            if len(date_parts) >= 3:
                                date_str = f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}"
                    except (ValueError, IndexError):
                        pass

            # Fallback to file creation date if ExifTool date not available
            if date_str == "unknown_date":
                creation_time = datetime.fromtimestamp(file_stat.st_ctime, UTC)
                date_str = creation_time.strftime("%Y-%m-%d")

            # Create hybrid hash
            video_hash = f"{file_ext}_{file_size}_{date_str}_{header_hash}"

            #DEBUG_video_hash_complete
            logging_service.log(
                "DEV",
                f"Video hash calculation completed: {video_hash}",
            )
            #DEBUG_video_hash_complete_end

            return video_hash

        except Exception as e:
            #DEBUG_start
            logging_service.log(
                "DEV",
                f"Video hash calculation failed: {e}",
            )
            #DEBUG_einde
            raise

    def _read_file_header(self, file_path: Path, header_size: int) -> bytes:
        """Read first N bytes of file for video hashing.
        
        Args:
        ----
            file_path: Path to the file
            header_size: Number of bytes to read
            
        Returns:
        -------
            Bytes from file header
            
        """
        try:
            with file_path.open("rb") as f:
                return f.read(header_size)
        except Exception as e:
            #DEBUG_start
            logging_service.log(
                "DEV",
                f"File header reading failed: {e}",
            )
            #DEBUG_einde
            raise

    def process_directory(
        self, directory_path: str,
    ) -> dict[str, object | list[dict[str, object | list[str]] | None]]:
        """Verwerk een directory met media bestanden.

        Args:
        ----
            directory_path: Pad naar de directory om te verwerken

        Returns:
        -------
            Dictionary met processing resultaten

        """
        # Reset shared progress variable
        if MediaProcessing._shared_counter:
            MediaProcessing._shared_counter.value = 0

        directory = Path(directory_path)
        if not directory.exists():
            error_msg = f"Directory not found: {directory_path}"
            raise FileNotFoundError(error_msg)

        # Reset processing state
        self.is_running = True
        self.is_aborted = False
        self.processed_count = 0
        self.error_count = 0
        self.start_time = time.time()

        # Reset shared progress variable
        if MediaProcessing._shared_counter:
            MediaProcessing._shared_counter.value = 0

        # Reset logged milestones voor nieuwe processing sessie
        self._logged_milestones.clear()

        logging_service.log(
            "PROCESS",
            f"Starting media processing for directory: {directory_path}", #DEBUG_media_processing_start
        )

        try:
            # Stap 1: Verzamel alle media bestanden
            debug_path = Path("/workspaces/app/debug.txt")
            with debug_path.open("a") as f:
                f.write(f"DEBUG: [{datetime.now(UTC)}] Starting file collection\n")
            file_list = self._collect_media_files(directory_path)
            with debug_path.open("a") as f:
                f.write(
                    f"DEBUG: [{datetime.now(UTC)}] "
                    f"File collection completed: {len(file_list)} files\n",
                )

            if not file_list:
                return {
                    "processed_count": 0,
                    "error_count": 0,
                    "processing_time": 0.0,
                    "results": [],
                }

            logging_service.log(
                "INFO",
                f"Found {len(file_list)} media files to process", #DEBUG_files_found
            )

            # Stap 2: Verwerk bestanden parallel
            with debug_path.open("a") as f:
                f.write(
                    f"DEBUG: [{datetime.now(UTC)}] "
                    f"Starting parallel file processing\n",
                )
            #DEBUG
            with debug_path.open("a") as f:
                f.write(
                    f"DEBUG: [{datetime.now(UTC)}] "
                    f"About to call _process_files_parallel with "
                    f"{len(file_list)} files\n",
                )
            results = self._process_files_parallel(file_list)
            with debug_path.open("a") as f:
                f.write(
                    f"DEBUG: [{datetime.now(UTC)}] "
                    f"Parallel file processing completed\n",
                )

            # Stap 3: Bereken processing tijd
            processing_time = time.time() - self.start_time

            # Log completion
            logging_service.log(
                "PROCESS",
                f"Media processing completed. Processed: {self.processed_count}, "
                f"Errors: {self.error_count}, Time: {processing_time:.2f}s",
            )

        except (OSError, ValueError) as e:
            logging_service.log("ERROR", f"Processing error: {e}")
            return {
                "processed_count": 0,
                "error_count": 1,
                "processing_time": 0,
                "results": [],
            }
        else:
            return {
                "processed_count": self.processed_count,
                "error_count": self.error_count,
                "processing_time": processing_time,
                "results": results,
            }
        finally:
            self.is_running = False

    def process_files_from_list(
        self, file_list: list[str],
    ) -> dict[str, object | list[dict[str, object | list[str]] | None]]:
        """Verwerk een lijst van media bestanden (zonder directory scan).

        Args:
        ----
            file_list: List van file paths om te verwerken

        Returns:
        -------
            Dictionary met processing resultaten

        """
        # Reset shared progress variable
        if MediaProcessing._shared_counter:
            MediaProcessing._shared_counter.value = 0

        # Reset processing state
        self.is_running = True
        self.is_aborted = False
        self.processed_count = 0
        self.error_count = 0
        self.start_time = time.time()

        # Reset logged milestones voor nieuwe processing sessie
        self._logged_milestones.clear()

        try:
            if not file_list:
                return {
                    "processed_count": 0,
                    "error_count": 0,
                    "processing_time": 0.0,
                    "results": [],
                }

            # Verwerk bestanden parallel
            debug_path = Path("/workspaces/app/debug.txt")
            with debug_path.open("a") as f:
                f.write(
                    f"DEBUG: [{datetime.now(UTC)}] "
                    f"Starting parallel file processing for {len(file_list)} files\n",
                )
            results = self._process_files_parallel(file_list)
            with debug_path.open("a") as f:
                f.write(
                    f"DEBUG: [{datetime.now(UTC)}] "
                    f"Parallel file processing completed\n",
                )

            # Bereken processing tijd
            processing_time = time.time() - self.start_time

            # Log completion
            logging_service.log(
                "PROCESS",
                f"Media processing completed. Processed: {self.processed_count}, "
                f"Errors: {self.error_count}, Time: {processing_time:.2f}s",
            )

        except (OSError, ValueError) as e:
            logging_service.log("ERROR", f"Processing error: {e}")
            return {
                "processed_count": 0,
                "error_count": 1,
                "processing_time": 0.0,
                "results": [],
            }

        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "processing_time": processing_time,
            "results": results,
        }

    def _collect_media_files(self, directory_path: str) -> list[str]:
        """Verzamel alle media bestanden uit een directory.

        Args:
        ----
            directory_path: Pad naar de directory

        Returns:
        -------
            List van file paths

        """
        file_list = []
        directory = Path(directory_path)

        # Alle ondersteunde extensies
        supported_extensions = self.image_extensions + self.video_extensions

        # Verzamel alle bestanden met ondersteunde extensies
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                file_ext = file_path.suffix.lower()
                if file_ext in supported_extensions:
                    file_list.append(str(file_path))

        return file_list

    def _process_files_parallel(
        self, file_list: list[str],
    ) -> list[dict[str, object | list[str]] | None]:
        """Verwerk bestanden parallel met ProcessPoolExecutor.

        Args:
        ----
            file_list: List van file paths om te verwerken

        Returns:
        -------
            List van processing resultaten

        """
        # Update shared progress variable
        results: list[dict[str, object | list[str]] | None] = []

        # Gebruik max_workers uit config
        max_workers = min(self.max_workers, len(file_list))

        logging_service.log(
            "DEV",
            f"Starting parallel processing with {max_workers} workers",
        )

        # DEV LOG: Starting ProcessPoolExecutor
        logging_service.log("DEV", "=== PARALLEL PROCESSING STARTED ===")
        logging_service.log("DEV", f"Starting ProcessPoolExecutor with {max_workers} workers")

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # DEV LOG: Submitting tasks to executor
            logging_service.log("DEV", f"Submitting {len(file_list)} tasks to executor")

            # Submit alle taken
            future_to_file = {
                executor.submit(self._process_single_file, file_path): file_path
                for file_path in file_list
            }

            # DEV LOG: All tasks submitted
            logging_service.log("DEV", f"All {len(file_list)} tasks submitted to executor")

            # DEV LOG: Starting to process completed futures
            logging_service.log("DEV", "Starting to process completed futures")

            for completed_count, future in enumerate(as_completed(future_to_file), 1):
                file_path = future_to_file[future]

                # DEV LOG: Progress milestone every 100 tasks
                if completed_count % 100 == 0:
                    logging_service.log("DEV", f"Progress milestone: {completed_count}/{len(file_list)} tasks completed")

                if self.is_aborted:
                    logging_service.log("DEV", "=== PROCESSING ABORTED BY USER ===")
                    logging_service.log("DEV", f"Aborting at {completed_count}/{len(file_list)} tasks")
                    break

                try:
                    result = future.result()
                    if result:
                        # DEV LOG: Result received from worker
                        logging_service.log("DEV", f"Result received from worker for file: {file_path}")

                        # Add to results and process in batch
                        results.append(result)
                        self.processed_count += 1

                        # DEV LOG: Processing result in batch collector
                        logging_service.log("DEV", f"Processing result in batch collector: {len(results)} results collected")

                        # Check if we have enough results for a batch
                        batch_size = get_param("database", "database_write_batch_size")
                        if len(results) >= batch_size:
                            # DEV LOG: Batch size reached, processing batch
                            logging_service.log("DEV", f"Batch size reached ({len(results)} >= {batch_size}), processing batch")

                            # Process current batch (placeholder for now)
                            self._process_batch(results[:batch_size])

                            # Keep remaining results for next batch
                            results = results[batch_size:]

                            # DEV LOG: Batch processed, remaining results
                            logging_service.log("DEV", f"Batch processed, {len(results)} results remaining for next batch")

                        # Update shared progress variable (multiprocessing-safe)
                        old_value = self.files_processed
                        self.files_processed += 1
                        new_value = self.files_processed

                        # DEV LOG: Progress updated
                        logging_service.log("DEV", f"Progress updated: {old_value} → {new_value}")
                    else:
                        self.error_count += 1
                        logging_service.log("WARNING", f"No result from worker for file: {file_path}")

                except (OSError, ValueError) as e:
                    self.error_count += 1
                    logging_service.log(
                        "DEV",
                        f"Error processing future result for {file_path}: {e}",
                    )

                # DEV LOG: Progress milestones (elke N bestanden of bij laatste file)
                if not hasattr(self, "_logged_milestones"):
                    self._logged_milestones = set()

                # Bereken welke milestones we moeten loggen
                current_milestone = self.processed_count
                milestones_to_log = []

                # Check voor reguliere milestones (elke N files)
                milestones_to_log = [
                    i for i in range(1, current_milestone + 1)
                    if (i % self.log_files_count_update == 0 and
                        i not in self._logged_milestones)
                ]

                # Check voor laatste file milestone
                if (current_milestone == len(file_list) and
                    current_milestone not in self._logged_milestones):
                    milestones_to_log.append(current_milestone)

                # Log alle nieuwe milestones
                for milestone in milestones_to_log:
                    logging_service.log(
                        "DEV",
                        f"Progress milestone: {milestone}/{len(file_list)} files processed",
                    )
                    self._logged_milestones.add(milestone)

        # DEV LOG: Parallel processing completed, processing final batch
        if results:
            logging_service.log("DEV", "=== FINAL BATCH PROCESSING ===")
            logging_service.log("DEV", f"Final batch size: {len(results)} results")

            # Process final batch (may be incomplete)
            self._process_batch(results)

            logging_service.log("DEV", "Final batch processed successfully")
        else:
            logging_service.log("DEV", "No results to process in final batch")

        # DEV LOG: All processing completed
        logging_service.log("DEV", "=== ALL PROCESSING COMPLETED ===")
        logging_service.log("DEV", f"Total results processed: {self.processed_count}")
        logging_service.log("DEV", f"Total errors: {self.error_count}")

        return results

    def _process_single_file(
        self, file_path: str,
    ) -> dict[str, object | list[str]] | None:
        """Verwerk een enkel bestand (wordt uitgevoerd in worker process).

        Args:
        ----
            file_path: Pad naar het bestand

        Returns:
        -------
            Dictionary met file metadata of None bij error

        """
        #DEBUG_worker_process_start
        # Note: This method runs in worker process, so self.database_manager should NOT be accessible
        try:
            # Basis file informatie
            file_path_obj = Path(file_path)
            file_stat = file_path_obj.stat()
            file_size = file_stat.st_size
            file_ext = file_path_obj.suffix.lower()

            # Bepaal file type
            if file_ext in self.image_extensions:
                file_type = "image"
            elif file_ext in self.video_extensions:
                file_type = "video"
            else:
                return None

            # Check voor sidecars
            sidecars = []
            media_name = file_path_obj.stem
            for sidecar_ext in self.sidecar_extensions:
                sidecar_path = file_path_obj.parent / (media_name + sidecar_ext)
                if sidecar_path.exists():
                    sidecars.append(sidecar_ext)

            # Basis metadata
            result: dict[str, object | list[str]] = {
                "SourceFile": file_path,
                "File:FileSize": str(file_size),
                "File:FileType": file_ext.upper().lstrip("."),
                "YAPMO:Directory": str(file_path_obj.parent),
                "YAPMO:FileName": file_path_obj.name,
                "YAPMO:FileSize": str(file_size),
                "YAPMO:FileType": file_type,
                "YAPMO:FQPN": file_path,
                "sidecars": sidecars,  # Array van sidecar extensies
                "type": file_type,  # Voor processing log samenvatting
            }

            # ExifTool metadata extraction
            exiftool_metadata = self._extract_exiftool_metadata(file_path_obj)
            result.update(exiftool_metadata)

            # Calculate hash using existing metadata
            result["YAPMO:Hash"] = self._calculate_file_hash(file_path_obj, file_type, exiftool_metadata)

            # DEV LOG: File processing completed successfully
            # Note: logging_service not available in worker processes
            debug_path = Path("/workspaces/app/debug_processing.txt")
            with debug_path.open("a", encoding="utf-8") as f:
                f.write(f"[{datetime.now(UTC)}] DEV: File processing completed: {file_path}\n")
                f.write(f"[{datetime.now(UTC)}] DEV: JSON result ready for batch collection\n")
                f.write(f"[{datetime.now(UTC)}] DEV: Hash: {result.get('YAPMO:Hash', 'NO_HASH')[:20]}...\n")

            # DEV LOG: File processing completed - ready for batch collection
            # Note: logging_service not available in worker processes
            debug_path = Path("/workspaces/app/debug_processing.txt")
            with debug_path.open("a", encoding="utf-8") as f:
                f.write(f"[{datetime.now(UTC)}] DEV: File processing completed - ready for batch collection\n")
                f.write(f"[{datetime.now(UTC)}] DEV: File: {file_path}\n")
                f.write(f"[{datetime.now(UTC)}] DEV: Hash: {result.get('YAPMO:Hash', 'NO_HASH')[:20]}...\n")
                f.write(f"[{datetime.now(UTC)}] DEV: JSON result size: {len(result)} fields\n")

        except (OSError, ValueError) as e:
            # DEV LOG: File processing error - creating FAIL JSON
            debug_path = Path("/workspaces/app/debug_processing.txt")
            with debug_path.open("a", encoding="utf-8") as f:
                f.write(f"[{datetime.now(UTC)}] DEV: File processing ERROR: {file_path}\n")
                f.write(f"[{datetime.now(UTC)}] DEV: Error type: {type(e).__name__}\n")
                f.write(f"[{datetime.now(UTC)}] DEV: Error message: {e}\n")
                f.write(f"[{datetime.now(UTC)}] DEV: Creating FAIL JSON for batch collection\n")

            # Create FAIL JSON for batch collection
            fail_result = {
                "YAPMO:FQPN": file_path,
                "YAPMO:ProcessingStatus": "FAIL",
                "YAPMO:ErrorType": type(e).__name__,
                "YAPMO:ErrorMessage": str(e),
                "YAPMO:ProcessingTimestamp": str(datetime.now(UTC)),
            }

            # DEV LOG: FAIL JSON created
            with debug_path.open("a", encoding="utf-8") as f:
                f.write(f"[{datetime.now(UTC)}] DEV: FAIL JSON created with {len(fail_result)} fields\n")
                f.write(f"[{datetime.now(UTC)}] DEV: FAIL JSON ready for batch collection\n")

            return fail_result

    def abort_processing(self) -> None:
        """Abort de processing."""
        self.is_aborted = True
        logging_service.log("DEV", "=== PROCESSING ABORTED ===")
        logging_service.log("DEV", "Media processing aborted by user")



    def get_progress_info(self) -> dict[str, object]:
        """Haal progress informatie op voor UI updates."""
        if not self.start_time:
            return {
                "processed_count": 0,
                "error_count": 0,
                "is_running": False,
                "eta": "Not started",
            }

        elapsed_time = time.time() - (self.start_time or 0)

        if self.processed_count > 0:
            avg_time_per_file = elapsed_time / self.processed_count
            # ETA berekening (placeholder voor nu)
            eta = f"{avg_time_per_file:.2f}s per file"
        else:
            eta = "Calculating..."

        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "is_running": self.is_running,
            "elapsed_time": elapsed_time,
            "eta": eta,
        }

    def _process_batch(self, batch_results: list[dict[str, object | list[str]]]) -> None:
        """Process a batch of JSON results.
        
        Args:
        ----
            batch_results: List of JSON results to process

        """
        # DEV LOG: Starting batch processing
        logging_service.log("DEV", "=== BATCH PROCESSING STARTED ===")
        logging_service.log("DEV", f"Batch size: {len(batch_results)} results")

        # Log first JSON for debugging
        if batch_results:
            first_result = batch_results[0]
            first_fqpn = first_result.get("YAPMO:FQPN", "UNKNOWN")
            logging_service.log("DEV", f"First JSON in batch: {first_fqpn}")

            # Check if this is the last batch (incomplete)
            batch_size = get_param("database", "database_write_batch_size")
            if len(batch_results) < batch_size:
                logging_service.log("DEV", f"LAST BATCH detected: {len(batch_results)} < {batch_size}")

        # DEV LOG: Batch processing completed
        logging_service.log("DEV", "=== BATCH PROCESSING COMPLETED ===")
        logging_service.log("DEV", f"Processed {len(batch_results)} results")

        # TODO: In Fase 3, this will send the batch to DatabaseManager
        # For now, just log that the batch is ready
        logging_service.log("DEV", "Batch ready for database processing (placeholder)")
