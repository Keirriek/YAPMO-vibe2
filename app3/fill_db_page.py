'''
# 1.01 Werkend voor optimalisatie
Interval var in config.json
Met Abort knop
Deze blijft nog wel staan



UI voor dupDetect met voortgangsbalken
'''
from nicegui import ui,app
import time
from multiprocessing import Process, Value, Manager
from multiprocessing.queues import Queue as MPQueue
import threading
from typing import Dict, Union, Optional, Any
import os
import atexit
import signal
import globals, config
from process_dir_tree import main as dup_detect_main
from local_file_picker import local_file_picker
from dialog import ConfirmationPopup
import pathlib

# Declare dir_input at module level
global dir_input
dir_input = None  # Will be initialized in create_ui

# Define type for shared resources
ThreadDict = Dict[str, Optional[threading.Thread]]
SharedResources = Dict[str, Union[Optional[Value], Optional[ThreadDict]]]

# Global variables for cleanup
shared_resources: SharedResources = {
    'progress': None,
    'running': None,
    'threads': {'ui': None, 'process': None}
}
config.init_config()

# Add this near the top of the file after imports
globals.aborted = False

def cleanup_resources():
    """Cleanup function to handle shared resources"""
    try:
        # First stop the running flag to signal threads to stop
        if shared_resources['running']:
            try:
                shared_resources['running'].value = False
            except:
                pass
        
        # Wait for threads to finish
        for thread_name, thread in shared_resources['threads'].items():
            try:
                if thread and thread.is_alive():
                    thread.join(timeout=0.5)
            except:
                pass
            finally:
                shared_resources['threads'][thread_name] = None
        
        # Clean up shared progress
        if shared_resources['progress']:
            try:
                shared_resources['progress'].value = 0
                shared_resources['progress'] = None
            except:
                pass
            
        # Ensure running flag is cleaned up
        shared_resources['running'] = None
        
        # Clear the shared resources
        shared_resources['threads'] = {'ui': None, 'process': None}
        shared_resources['progress'] = None
        shared_resources['running'] = None
        
        # Give a small delay to ensure cleanup is complete
        time.sleep(0.1)
    except Exception as e:
        ui.notify(f"Error during cleanup: {e}",type='negative')

def content():
    ui.add_css('button.my-red-button:hover { background-color: red !important; }')
    # keep_alive_chars = ['-', '\\', '|', '/']
    # manager = Manager()
    # keep_alive_queue = manager.Queue()
    # update_keep_alive = 0.1

    # def update_keep_alive_indicator():
    #     keep_alive_index = 0
    #     last_update = time.time()
    #     while not keep_alive_queue.empty():
    #         current_time = time.time()
    #         if current_time - last_update >= update_keep_alive:
    #             keep_alive_label.text = keep_alive_chars[keep_alive_index]
    #             keep_alive_index = (keep_alive_index + 1) % len(keep_alive_chars)
    #             last_update = current_time
    #         time.sleep(0.01)
    #     keep_alive_label.text = ''

    def count_image_files(directory):
        total_dirs = 0
        total_files = 0
        alert_dirs_count = int(globals.config_data['alert_dirs_count'])
        dirs_step = alert_dirs_count
        alert_files_count = int(globals.config_data['alert_files_count'])
        files_step = alert_files_count
        extentions = globals.config_data['image_extensions'] + globals.config_data['video_extensions'] + globals.config_data['sidecar_extensions']
        path = pathlib.Path(directory)
        
        # keep_alive_thread = threading.Thread(target=update_keep_alive_indicator, daemon=True)
        # keep_alive_thread.start()
        
        # try: #hoort bij keep_alive
        for root, dirs, files in path.walk():
            # keep_alive_queue.put_nowait(True)
            total_dirs += len(dirs)
            count = 0
            for file in files:
                if file.lower().endswith(tuple(extentions)):
                    count += 1
            total_files += count
            if total_dirs >= alert_dirs_count:
                alert_dirs_count += dirs_step
                globals.log_content.append(f'[INFO] Preparation Directory count: {total_dirs}')
            if total_files >= alert_files_count:
                alert_files_count += files_step
                globals.log_content.append(f'[INFO] Preparation estimated File count: {total_files}')
        # finally:
            # while not keep_alive_queue.empty():
            #     keep_alive_queue.get()
            # keep_alive_thread.join(timeout=1.0)
            
        return total_files

    async def get_dir()-> None:
        dpath=globals.config_data['browse_path']
        pr = await local_file_picker(dpath, multiple=False)
        if pr:  # Add check if pr has a value
            d_path = pr[0]
            # Update both the input field and the config
            if os.path.isdir(d_path):  # Check if dir_input exists
                dir_input.value = d_path
                globals.config_data['search_path'] = d_path
                config.set_config_par('search_path', d_path)
                config.write_config(globals.config_data)
                ui.notify(f'Directory selected (search_path changed): {d_path}', type='positive')
            else:
                ui.notify(f'Directory not found: {d_path}', type='negative')
        return


    def create_ui():
        """Create and return UI elements"""
        global dir_input
        with ui.row().classes('w-full h-150'):
            select_dir_button = ui.button('Choose Dir', on_click=get_dir).classes('bg-blue-500')
            dir_input = ui.input(value=globals.config_data['search_path']).classes('w-1/2')
            # keep_alive_label = ui.label('').classes('w-4 text-center')

        progress_bar = ui.linear_progress(value=0,show_value=False, size="20px").props('instant-feedback')
        with ui.row().classes('w-1/2 h-150'):
            ui.label('Progress info:')
            progress_label = ui.label()
        with ui.column().classes('w-full h-300'):
            ui.label('Log info:')
            log_scroll_area = ui.scroll_area().classes('w-full h-155 border-1 rounded-lg p-2').style('border: 1px solid black')
        # return select_dir_button, dir_input, progress_bar, progress_label, log_scroll_area, keep_alive_label
        return select_dir_button, dir_input, progress_bar, progress_label, log_scroll_area


    # def update_ui(progress_bar, progress_bar2, progress_label, log_scroll_area, shared_progress, total_steps, interval, process_running):
    def update_ui(select_dir_button, dir_input, progress_bar, progress_label, log_scroll_area, shared_progress, total_steps, interval, process_running, start_button, abort_button):
        """Update the UI elements with current progress"""
        try:
            last_value = 0
            while process_running and process_running.value:
                try:
                    current_count = shared_progress.value if shared_progress else 0
                    if current_count != last_value:
                        percentage = int((current_count / total_steps) * 100)
                        progress_bar.set_value(percentage/100)
                        progress_label.text = f'Progress Raw: {percentage}% ({current_count}/ {total_steps})'
                        last_value = current_count
                        log_content = globals.log_content
                        with log_scroll_area:
                            log_scroll_area.clear()  # Clear before adding new content
                            for line in log_content:    
                                ui.label(f'{line}')
                            log_scroll_area.scroll_to(percent=100)
                    time.sleep(interval)
                except AttributeError:
                    # Resources have been cleaned up, exit thread
                    break
                except Exception as e:
                    ui.notify(f"Error in update_ui: {e}",type='negative')
                    break
            
            # Show final messages after process completion
            try:
                time.sleep(0.5)  # Give time for final messages to be added
                #MP there could be division by 0 Afer finished Testing, see if it occers. otherwise delete
                final_count = shared_progress.value if shared_progress else 0
                percentage = int((total_steps/ final_count) * 100)
                progress_bar.set_value(percentage/100)
                progress_label.text = f'Completed: {percentage}% ({final_count} Found/{total_steps} Files processed, incl. SideCars)'
                
                # Update log with final messages
                log_content = globals.log_content
                with log_scroll_area:
                    for line in log_content:    
                        ui.label(f'{line}')
                    log_scroll_area.scroll_to(percent=100)
                    
                # Reset UI buttons after completion
                abort_button.visible = False
                start_button.visible = True
            except Exception as e:
                ui.notify(f"Error showing final messages: {e}",type='warning')
        except Exception as e:
            ui.notify(f"Error in update_ui thread: {e}",type='negative')
        finally:
            # Ensure UI is reset even if there was an error
            try:
                abort_button.visible = False
                abort_button.text = 'Abort Processing'
                start_button.visible = True
            except:
                pass

    def run_dup_detect(shared_progress, total_steps, process_running):
        """Start dupDetect process"""
        try:
            if process_running and process_running.value:
                dup_detect_main(shared_progress)
                # Set the running flag to False after the process is completed
                if process_running:
                    process_running.value = False
        except AttributeError:
            # Resources have been cleaned up
            ui.notify(f"Attribute Error", type='warning')
            pass
        except Exception as e:
            # Check if the abortion was intentional
            if globals.aborted:
                return  # Do not notify if aborted intentionally
            ui.notify(f"Error in run_dup_detect: {e}", type='negative')
        finally:
            try:
                # Ensure that running is always set to False
                if process_running:
                    process_running.value = False
                # Reset UI after completion
                ui.run_javascript('setTimeout(() => window.dispatchEvent(new Event("completion")), 100)')
            except:
                pass

    @ui.page('/fill_db')
    def fill_db_page():
        config.init_config()
        search_path = globals.config_data['search_path']
        interval = float(globals.config_data['interval'])
        
        # select_dir_button, dir_input, progress_bar, progress_label, log_scroll_area, keep_alive_label = create_ui()
        select_dir_button, dir_input, progress_bar, progress_label, log_scroll_area = create_ui()
        # Initialize shared resources
        shared_resources['progress'] = Value('i', 0)
        shared_resources['running'] = Value('b', True)
        shared_resources['threads'] = {'ui': None, 'process': None}
        
        def reset_ui():
            """Reset UI naar initiële staat"""
            try:
                # Reset UI elements
                dir_input.value = globals.config_data['search_path']
                progress_bar.set_value(0)
                progress_label.text = ''
                globals.log_content.clear()
                abort_button.visible = False
                # abort_button.classes('bg-red text-white')
                abort_button.text = 'Abort Processing'
                start_button.visible = True
                
                # Reinitialize shared resources for a new start
                shared_resources['progress'] = Value('i', 0)
                shared_resources['running'] = Value('b', True)
                shared_resources['threads'] = {'ui': None, 'process': None}
            except Exception as e:
                ui.notify(f"Error during UI reset: {e}",type='warning')
        def handle_completion():
            """Handle completion of the process"""
            abort_button.visible = False
            start_button.visible = True

        # Register completion handler
        ui.on('completion', handle_completion)

        def abort_processing():
            """Stop alle processen en threads"""
            # Set the global abort flag
            globals.aborted = True
            abort_button.text = 'Aborted'
            abort_button.classes('bg-red text-white')  # Change button color

            # Prevent warning notification on intentional abort
            if shared_resources['running'] and shared_resources['running'].value:
                shared_resources['running'].value = False  # Signal to stop the process

        def on_start():
            """Start processing en update UI"""
            # Reset the abort flag when starting
            globals.aborted = False
            try:
                
                # First clean up any existing resources
                cleanup_resources()
                
                # Recalculate total_steps
                config.init_config()
                
                # Clear the log area
                with log_scroll_area:
                    log_scroll_area.clear()
                globals.log_content.clear()
                
                # Get number of files
                search_path = globals.config_data['search_path']
                total_steps = count_image_files(search_path)
                if total_steps == 0:
                    ui.notify('No files found in directory', type='warning')
                    return
                
                # Reset progress bar and label
                progress_bar.set_value(0)
                progress_label.text = ''
                
                # Initialize fresh resources
                shared_resources['progress'] = Value('i', 0)
                shared_resources['running'] = Value('b', True)
                shared_resources['threads'] = {'ui': None, 'process': None}
                
                # Update button visibility
                start_button.visible = False
                abort_button.classes('my-red-button text-white')
                abort_button.text = 'Abort Processing'
                ui.add_css('button.my-red-button:hover { background-color: red !important; }')#Hoover Abort_button

                abort_button.classes('my-red-button')
                abort_button.visible = True
                # Create and start new threads
                shared_resources['threads']['ui'] = threading.Thread(
                    target=update_ui,
                    args=(select_dir_button, dir_input, progress_bar, progress_label, log_scroll_area, 
                        shared_resources['progress'], total_steps, interval, 
                        shared_resources['running'], start_button, abort_button),
                    daemon=True
                )

                shared_resources['threads']['process'] = threading.Thread(
                    target=run_dup_detect,
                    args=(shared_resources['progress'], total_steps, shared_resources['running']),
                    daemon=True
                )
                
                shared_resources['threads']['ui'].start()
                shared_resources['threads']['process'].start()
            except Exception as e:
                ui.notify(f"Error during start: {e}",type='negative')
                # Reset UI in case of error
                reset_ui()

        # Creëer beide knoppen
        # ui.colors(primary='#1111bc', secondary='#b65398', accent='#111B1E', positive='#53B689')
        start_button = ui.button('Start Filling DB', on_click=on_start)
        abort_button = ui.button('Abort Processing', on_click=abort_processing)
        abort_button.visible = False  # Begin met verborgen abort knop

        # Register cleanup on page disconnect
        app.on_shutdown(cleanup_resources)
    fill_db_page()
if __name__ in {"__main__", "__mp_main__"}:
    
    def signal_handler(sig, frame):
        """Handle interrupt signal"""
        cleanup_resources()
        signal.default_int_handler(sig, frame)
    
    # Register cleanup handlers
    atexit.register(cleanup_resources)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        ui.run()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    finally:
        cleanup_resources()