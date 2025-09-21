# voor refactoring
from nicegui import ui
import globals, config
from multiprocessing import Value
import threading
import os
import time
from exif_read_write import put_exif_data2
import shutil
import concurrent.futures
from datetime import datetime, timedelta

def process_file(file_info):
    """Process a single file with metadata and file operations"""
    log_messages = []  # Store log messages locally
    try:
        file_path = file_info['file_path']
        file_name = file_info['file_name']
        new_path = file_info['new_path']
        new_name = file_info['new_name']
        metadata = file_info['metadata']
        mode = file_info['mode']
        
        full_path = os.path.join(file_path, file_name)
        
        # Valideer source bestand
        if not os.path.exists(full_path):
            log_messages.append(f"[ERROR] Source file not found: {full_path}")
            return False, log_messages
        
        # Valideer en verwerk new_path en new_name
        if mode in ['copy', 'move']:
            # Als new_path leeg is, gebruik originele pad
            if not new_path or new_path == 'nil':
                new_path = file_path
                log_messages.append(f"[WARNING] No new path specified, using original path: {file_path}")
            
            # Als new_name leeg is, gebruik originele naam
            if not new_name or new_name == 'nil':
                new_name = file_name
                log_messages.append(f"[WARNING] No new name specified, using original name: {file_name}")
            
            new_full_path = os.path.join(new_path, new_name)
            
            # Check of doelmap bestaat, zo niet probeer te maken
            if not os.path.exists(new_path):
                try:
                    os.makedirs(new_path, exist_ok=True)
                    log_messages.append(f"[INFO] Created directory: {new_path}")
                except Exception as e:
                    log_messages.append(f"[ERROR] Cannot create directory {new_path}: {str(e)}")
                    return False, log_messages
            
            # Check of doelbestand al bestaat
            if os.path.exists(new_full_path):
                if full_path == new_full_path:
                    log_messages.append(f"[WARNING] Source and destination are identical: {full_path}")
                else:
                    log_messages.append(f"[ERROR] Destination file already exists: {new_full_path}")
                    return False, log_messages
        
        # Write metadata
        if metadata:
            if not put_exif_data2(full_path, metadata):
                log_messages.append(f"[ERROR] Failed to write metadata to: {full_path}")
                return False, log_messages
        
        # Perform file operation based on mode
        if mode == 'copy':
            try:
                shutil.copy2(full_path, new_full_path)
                log_messages.append(f"[INFO] File copied to: {new_full_path}")
            except Exception as e:
                log_messages.append(f"[ERROR] Copy failed for {full_path}: {str(e)}")
                return False, log_messages
            
        elif mode == 'move':
            try:
                shutil.move(full_path, new_full_path)
                log_messages.append(f"[INFO] File moved to: {new_full_path}")
            except Exception as e:
                log_messages.append(f"[ERROR] Move failed for {full_path}: {str(e)}")
                return False, log_messages
        
        log_messages.append(f"[INFO] Successfully processed {file_name}")
        return True, log_messages
        
    except Exception as e:
        log_messages.append(f"[ERROR] Processing failed for {file_path}/{file_name}: {str(e)}")
        return False, log_messages

class WriteDBUI:
    def __init__(self):
        self.shared_progress = None
        self.running = None
        self.threads = {'ui': None, 'process': None}
        self.operation_mode = 'update'  # Default mode
        self.max_workers = int(globals.config_data['maxworkers'])
        self.completion_event = threading.Event()
        self.total_files = 0  # Track total files to process
        self.processed_files = 0  # Track successfully processed files

    def cleanup_resources(self):
        """Cleanup function to handle shared resources"""
        try:
            # First stop the running flag to signal threads to stop
            if self.running:
                self.running.value = False
            
            # Wait for threads with timeout
            for thread_name, thread in self.threads.items():
                try:
                    if thread and thread.is_alive():
                        thread.join(timeout=1.0)  # Increased timeout for better cleanup
                except:
                    pass
                finally:
                    self.threads[thread_name] = None
            
            # Reset shared resources
            if self.shared_progress:
                self.shared_progress.value = 0
                self.shared_progress = None
            
            self.running = None
            self.threads = {'ui': None, 'process': None}
            
            # Force process pool shutdown
            import concurrent.futures
            concurrent.futures.process._global_shutdown()
            
            time.sleep(0.2)  # Give more time for cleanup
        except Exception as e:
            globals.log_content.append(f"[ERROR] Error during cleanup: {str(e)}")

    def count_records(self):
        """Count total records in Media_New table"""
        try:
            import sqlite3
            conn = sqlite3.connect(globals.config_data['db'])
            cursor = conn.cursor()
            
            # First check if table exists
            cursor.execute(f"""
                SELECT count(name) FROM sqlite_master 
                WHERE type='table' AND name='{globals.config_data['dbtable_media_new']}'
            """)
            
            if cursor.fetchone()[0] == 0:
                globals.log_content.append(f"[ERROR] Table {globals.config_data['dbtable_media_new']} does not exist")
                return 0
            
            #TODO FILE_modify is not yet used
            cursor.execute(f"SELECT COUNT(*) FROM {globals.config_data['dbtable_media_new']}")
            count = cursor.fetchone()[0]
            globals.log_content.append(f"[INFO] Found {count} records in {globals.config_data['dbtable_media_new']}")
            conn.close()
            return count
        except Exception as e:
            globals.log_content.append(f"[ERROR] Error counting records: {str(e)}")
            ui.notify(f"Error counting records: {e}",type='negative')
            return 0

    def signal_completion(self, success=True):
        """Signal completion in a thread-safe way"""
        self.completion_event.set()
        if success:
            # Ensure final count matches total
            if self.shared_progress and self.shared_progress.value != self.total_files:
                with self.shared_progress.get_lock():
                    self.shared_progress.value = self.processed_files

    def process_records(self, progress, running):
        """Process all records from Media_New table"""
        try:
            import sqlite3
            conn = sqlite3.connect(globals.config_data['db'])
            cursor = conn.cursor()
            # Get field mappings
            image_extensions = globals.config_data['image_extensions']
            video_extensions = globals.config_data['video_extensions']
            image_fields = globals.config_data['dbtable_fields_file']
            image_fields.update(globals.config_data['dbtable_fields_image'])
            video_fields = globals.config_data['dbtable_fields_file'].copy()  # Gebruik copy() om een nieuwe dictionary te maken
            video_fields.update(globals.config_data['dbtable_fields_video'])
            image_write_flags = globals.config_data['dbtable_fields_image_write']
            video_write_flags = globals.config_data['dbtable_fields_video_write']
            #TODO Media_New=Media, so no need for explicitly building filedlist
            # Build field list explicitly for Media_New
            field_list = []
            for field in image_fields.values():
                if field not in field_list:
                    field_list.append(field)
            for field in video_fields.values():
                if field not in field_list:
                    field_list.append(field)
            
            # Create the query with explicit field list
            query = f"""
                SELECT {', '.join(field_list)}
                FROM {globals.config_data['dbtable_media_new']}
                WHERE 1=1
            """
            cursor.execute(query)
            records = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            
            start_time = time.perf_counter()
            
            # Get total count of records to process
            self.total_files = len(records)
            self.processed_files = 0
            
            with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                # Submit all tasks first
                for record in records:
                    if not running.value:
                        break
                    # if record[column_names.index("FILE_modify")] == 'nil':#TODO FILE_modify is not yet used
                    #     continue #Guard against unwanted updates
                    try:
                        # Get file info
                        file_name = record["YAPMO_FILE_Name"]
                        file_path = record["YAPMO_FILE_Path"]
                        new_name = record["YAPMO_FILE_Name_New"] if record["YAPMO_FILE_Name_New"] else file_name
                        new_path = record["YAPMO_FILE_Path_New"] if record["YAPMO_FILE_Path_New"] else file_path
                        file_type=record["YAPMO_FILE_Type"]
                        
                        # Determine if video
                        is_video = file_type in ['mov', 'm4v', 'mp4', 'avi', '3gp']
                        
                        # Select appropriate mappings and flags
                        fields = video_fields if is_video else image_fields
                        write_flags = video_write_flags if is_video else image_write_flags
                        
                        # Build metadata dictionary
                        #TODO conf.json image_write en Video_write bevatten alleen key: true so no need for explicitly building metadata dictionary
                        
                        metadata = {}
                        for exif_field, should_write in write_flags.items():
                            if should_write:  # Only process fields marked as True
                                db_field = fields.get(exif_field)#TODO only "EXIFTOOL" fields are used
                                if db_field and db_field in column_names:
                                    field_index = column_names.index(db_field)
                                    value = record[field_index]
                                    if value and value != 'nil':
                                        metadata[exif_field] = value
                        
                        # Prepare file info for processing
                        file_info = {
                            'file_path': file_path,
                            'file_name': file_name,
                            'new_path': new_path,
                            'new_name': new_name,
                            'metadata': metadata,
                            'mode': self.operation_mode
                        }
                        
                        # Submit task to process pool
                        future = executor.submit(process_file, file_info)
                        futures.append(future)
                        
                    except ValueError as e:
                        globals.log_content.append(f"[ERROR] Required column missing: {str(e)}")
                        continue
                
                # Process completed tasks
                for future in concurrent.futures.as_completed(futures):
                    if not running.value:
                        for f in futures:
                            f.cancel()
                        break
                    
                    try:
                        success, log_messages = future.result()
                        for msg in log_messages:
                            globals.log_content.append(msg)
                        if success:
                            with progress.get_lock():
                                progress.value += 1
                                self.processed_files += 1
                    except Exception as e:
                        globals.log_content.append(f"[ERROR] Task failed: {str(e)}")
                
                # Add completion messages
                if self.processed_files == self.total_files and running.value:
                    end_time = time.perf_counter()
                    total_seconds = end_time - start_time
                    formatted_delta = str(timedelta(seconds=round(total_seconds * 100) / 100))
                    dat_str = datetime.now().strftime("%m/%d/%Y, %H:%M:%S:%f")
                    # Ready with processing
                    globals.log_content.append(f'[INFO] Processing completed successfully')
                    globals.log_content.append(f'[INFO] Script ended at: {dat_str}')
                    globals.log_content.append(f"[INFO] Elapsed time: {total_seconds:.4f} seconds")
                    globals.log_content.append(f'[INFO] Script elapsed time: {formatted_delta}')
                    globals.log_content.append(f'[INFO] Successfully processed {self.processed_files} out of {self.total_files} files')
                    
                    
                    # Signal completion - let update_ui handle the UI changes
                    self.signal_completion(True)
                
                elif not running.value:
                    globals.log_content.append(f'[WARNING] Process Aborted by User')
                    globals.log_content.append(f'[INFO] Processed {self.processed_files} out of {self.total_files} files before abort')
                    self.signal_completion(False)

            conn.close()
            
        except Exception as e:
            error_msg = f"[ERROR] 320: Database error: {str(e)}"
            globals.log_content.append(error_msg)
            self.signal_completion(False)

    def update_ui(self, progress_bar, progress_label, log_area, total_steps, abort_button, start_button, operation_radio):
        """Update UI elements with current progress"""
        last_value = 0
        last_log_length = 0
        success_message = f'[INFO] Successfully processed {self.total_files} out of {self.total_files} files'
        
        while self.running and self.running.value:
            try:
                current_count = min(self.shared_progress.value if self.shared_progress else 0, total_steps)
                current_log_length = len(globals.log_content)
                
                # Check for success message in new log entries<<<<<<<<<<<<<<<<<<<<<<<<<<<<<WAT eeen rare aanpak #TODO dit is een rare aanpak
                if current_log_length > last_log_length:
                    new_logs = globals.log_content[last_log_length:]
                    if success_message in new_logs:
                        # Success detected - reset UI
                        abort_button.visible = False
                        start_button.visible = True
                        operation_radio.enabled = True
                        progress_bar.set_value(1.0)  # Set to 100%
                        progress_label.text = f'Uitvoer rare clausule Completed: 100% ({self.total_files}/{self.total_files} files processed)'
                        ui.notify('Processing completed')
                        self.cleanup_resources()
                        break
                
                # Update if progress changed or new log entries
                if current_count != last_value or current_log_length != last_log_length:
                    try:
                        if not progress_bar._deleted and not log_area._deleted:
                            percentage = min(100, int((current_count / total_steps) * 100))
                            progress_bar.set_value(percentage/100)
                            progress_label.text = f'Progress: {percentage}% ({current_count}/{total_steps} files processed)'
                            if current_log_length > last_log_length:
                                with log_area:
                                    for line in globals.log_content[last_log_length:]:
                                        ui.label(line).classes('text-sm')
                                log_area.scroll_to(percent=100)
                                last_log_length = current_log_length
                            
                            last_value = current_count
                        else:
                            pass
                    except Exception as e:
                        globals.log_content.append(f"[ERROR] Failed to update UI: {str(e)}")
                        break
                
                time.sleep(float(globals.config_data['interval']))
            except Exception as e:
                globals.log_content.append(f"[ERROR] Error in UI update loop: {str(e)}")
                break

    async def show_confirmation_dialog(self):
        """Show confirmation dialog before starting operation"""
        # Get write flags
        image_write_flags = globals.config_data['dbtable_fields_image_write']
        video_write_flags = globals.config_data['dbtable_fields_video_write']
        
        # Create lists of fields that will be written
        image_fields_to_write = [field for field, flag in image_write_flags.items() if flag]
        video_fields_to_write = [field for field, flag in video_write_flags.items() if flag]
        
        with ui.dialog() as dialog, ui.card():
            ui.label('Are you sure you want to update the media files?').classes('text-lg font-bold mb-2')
            
            # Mode-specific warning message
            if self.operation_mode == 'update':
                ui.label('These Fields will be updated!').classes('text-red-500 font-bold mb-2')
            elif self.operation_mode == 'copy':
                ui.label('These Fields will be updated and the file will be COPIED to the new location and will be RENAMED!').classes('text-red-500 font-bold mb-2')
            elif self.operation_mode == 'move':
                ui.label('These Fields will be updated and the file will be MOVED to the new location and will be RENAMED!').classes('text-red-500 font-bold mb-2')
            
            # Show fields that will be written
            if image_fields_to_write:
                ui.label('Image fields to write:').classes('font-bold mt-2')
                for field in image_fields_to_write:
                    ui.label(f'• {field}').classes('ml-4')
            
            if video_fields_to_write:
                ui.label('Video fields to write:').classes('font-bold mt-2')
                for field in video_fields_to_write:
                    ui.label(f'• {field}').classes('ml-4')
            
            if not image_fields_to_write and not video_fields_to_write:
                ui.label('Warning: No fields are selected for writing!').classes('text-red-500 font-bold mt-2')
            
            ui.label('If not correct: Change config.json and restart!').classes('text-red-500 font-bold mt-2')

            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('No', on_click=lambda: dialog.submit(False)).classes('mr-2')
                ui.button('Yes', on_click=lambda: dialog.submit(True))
            
        return await dialog

    def test_db_connection(self):
        """Test database connection and table existence"""
        try:
            import sqlite3
            conn = sqlite3.connect(globals.config_data['db'])
            cursor = conn.cursor()
            
            # First check if database file exists
            if not os.path.exists(globals.config_data['db']):
                return False, f"Database file {globals.config_data['db']} does not exist"
            
            # Test Media table existence
            cursor.execute(f"""
                SELECT count(name) FROM sqlite_master 
                WHERE type='table' AND name='{globals.config_data['dbtable_media']}'
            """)
            if cursor.fetchone()[0] == 0:
                return False, f"Source table '{globals.config_data['dbtable_media']}' does not exist"
            
            # Test Media_New table existence
            cursor.execute(f"""
                SELECT count(name) FROM sqlite_master 
                WHERE type='table' AND name='{globals.config_data['dbtable_media_new']}'
            """)
            if cursor.fetchone()[0] == 0:
                return False, f"Target table '{globals.config_data['dbtable_media_new']}' does not exist"
            
            # Test record count
            cursor.execute(f"SELECT COUNT(*) FROM {globals.config_data['dbtable_media_new']}")
            count = cursor.fetchone()[0]
            
            conn.close()
            return True, f"Database connected, found {count} records"
            
        except sqlite3.OperationalError as e:
            return False, f"457: Database error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

def content():
    write_ui = WriteDBUI()

    with ui.column().classes('w-full gap-4'):
        ui.label('Write DB to Metadata').classes('text-h4 mb-4')
        
        # Operation selection with radio buttons
        with ui.row().classes('w-full mb-4 gap-2'):
            ui.label('Operation mode:').classes('self-center')
            operation_radio = ui.radio(['update', 'copy', 'move'], 
                value='update',  # Default value
                on_change=lambda e: setattr(write_ui, 'operation_mode', e.value)
            ).props('inline').classes('self-center')
        
        # Progress elements
        progress_bar = ui.linear_progress(value=0, show_value=False, size='20px').props('instant-feedback')
        with ui.row().classes('w-1/2'):
            ui.label('Progress info:')
            progress_label = ui.label()
        
        with ui.column().classes('w-full flex-grow'):
            ui.label('Log info:')
            log_area = ui.scroll_area().classes('w-full h-80 border-1 rounded-lg p-2').style('border: 1px solid blue')
            
            with log_area:
                ui.label('Ready to process...').classes('text-sm')
                status, message = write_ui.test_db_connection()
                if status:
                    ui.label(f"Database status: {message}").classes('text-sm font-bold text-green-600')
                else:
                    ui.label(f"ERROR: {message}").classes('text-sm font-bold text-red-600')
        
        async def execute_operation():
            """Execute the selected operation after confirmation"""
            if await write_ui.show_confirmation_dialog():
                total_steps = write_ui.count_records()
                if total_steps == 0:
                    ui.notify('No records to process', type='warning')
                    return
                
                write_ui.shared_progress = Value('i', 0)
                write_ui.running = Value('b', True)
                
                # Update button visibility
                start_button.visible = False
                abort_button.classes('bg-red text-white')
                abort_button.text = 'Abort Processing'
                abort_button.visible = True
                
                # Start processing thread
                write_ui.threads['process'] = threading.Thread(
                    target=write_ui.process_records,
                    args=(write_ui.shared_progress, write_ui.running),
                    daemon=True
                )
                
                # Start UI update thread with UI elements
                write_ui.threads['ui'] = threading.Thread(
                    target=write_ui.update_ui,
                    args=(progress_bar, progress_label, log_area, total_steps, 
                          abort_button, start_button, operation_radio),
                    daemon=True
                )
                
                write_ui.threads['process'].start()
                write_ui.threads['ui'].start()

        def abort_processing():
            """Stop alle processen en threads"""
            try:
                abort_button.text = 'Aborting...'
                abort_button.classes('bg-red-500 text-white')
                
                # Set the running flag to False to signal threads to stop
                if write_ui.running:
                    write_ui.running.value = False
                
                # Clean up resources
                write_ui.cleanup_resources()
                
                # Reset UI
                abort_button.visible = False
                start_button.visible = True
                operation_radio.enabled = True  # Re-enable radio buttons after abort
                
                ui.notify('Process aborted by user', type='warning')
            except Exception as e:
                ui.notify(f"Error during abort: {e}", type='negative')
        
        with ui.row().classes('w-full justify-between mt-4'):
            back_btn = ui.button('Back', on_click=lambda: ui.navigate.to('/'))
            start_button = ui.button('Start Processing', on_click=execute_operation).classes('bg-blue-500')
            abort_button = ui.button('Abort Processing', on_click=abort_processing).classes('bg-red')
            abort_button.visible = False  # Begin met verborgen abort knop

        def handle_completion():
            """Handle completion of the process"""
            try:
                # Reset UI elements directly
                abort_button.visible = False
                start_button.visible = True
                operation_radio.enabled = True
                progress_bar.set_value(0)
                
                # Clean up resources
                write_ui.cleanup_resources()
                
            except Exception as e:
                globals.log_content.append(f"[ERROR] Error during completion handling: {str(e)}")

        # Register completion handler
        ui.on('completion', handle_completion)#TODO ui.om() for handle completion????

if __name__ in {"__main__", "__mp_main__"}:
    config.init_config()
    ui.run(title='Write DB to Metadata')
