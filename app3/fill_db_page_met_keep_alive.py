'''
# 1.01 Werkend voor optimalisatie
Interval var in config.json
Met Abort knop
Deze blijft nog wel staan



UI voor dupDetect met voortgangsbalken
'''
from nicegui import ui,run,app
import time
from multiprocessing import Process, Value, Manager
from multiprocessing.queues import Queue as MPQueue
import threading
from typing import Dict, Union, Optional, Any, cast
import os
import atexit
import signal
import globals, config
from process_dir_tree import main as dup_detect_main
from local_file_picker import local_file_picker
from dialog import ConfirmationPopup
import pathlib
from threading import Thread
from nicegui.elements.input import Input

# Declare dir_input at module level
global dir_input, total_steps
dir_input: Optional[Input] = None  # Will be initialized in create_ui

# Define type for shared resources
ThreadDict = Dict[str, Optional[Thread]]
ValueType = Value

# Global variables for cleanup
shared_resources: Dict[str, Union[ValueType, ThreadDict]] = {
    'progress': None,
    'running': None,
    'threads': {'ui': None, 'process': None}
}
config.init_config()

# Add this near the top of the file after imports
globals.aborted = False

##########
def count_image_files2(directory,extentions):
    total_dirs = 0
    total_files = 0
    # alert_dirs_count = int(globals.config_data['alert_dirs_count'])#TP
    # dirs_step = alert_dirs_count
    # alert_files_count = int(globals.config_data['alert_files_count'])
    # files_step = alert_files_count
    # extentions = globals.config_data['image_extensions'] + globals.config_data['video_extensions']#TP run.cpu_bound#No Sidecars, there could be no associated mediafile
    path = pathlib.Path(directory)
    for root, dirs, files in path.walk():
        total_dirs += len(dirs)
        # globals.log_content.append(f'[INFO] Preparation Directory count: {total_dirs} files found: {len(files)}')
        count = 0
        for file in files:
            if file.endswith(tuple(extentions)):
                count += 1
            elif file.lower().endswith(tuple(extentions)):
                count += 1
        total_files += count
    #     if total_dirs >= alert_dirs_count:#TP
    #         alert_dirs_count += dirs_step
    #         globals.log_content.append(f'[INFO] Preparation Directory count: {total_dirs}')
    #     if total_files >= alert_files_count:
    #         alert_files_count += files_step
    #         globals.log_content.append(f'[INFO] Preparation estimated File count: {total_files}')
    # return total_files
######
def cleanup_resources():
    """Cleanup function to handle shared resources"""
    try:
        # First stop the running flag to signal threads to stop
        running = cast(ValueType, shared_resources['running'])
        if running:
            running.value = False
        
        # Wait for threads to finish
        threads = cast(ThreadDict, shared_resources['threads'])
        if isinstance(threads, dict):
            for thread_name, thread in threads.items():
                try:
                    if thread and thread.is_alive():
                        thread.join(timeout=0.5)
                except:
                    pass
                finally:
                    threads[thread_name] = None
        
        # Clean up shared progress
        progress = cast(ValueType, shared_resources['progress'])
        if progress:
            progress.value = 0
            shared_resources['progress'] = None
            
        # Reset shared resources
        shared_resources['threads'] = {'ui': None, 'process': None}
        shared_resources['progress'] = None
        shared_resources['running'] = None
        
        time.sleep(0.1)
    except Exception as e:
        ui.notify(f"Error during cleanup: {e}", type='negative')

def content():
    ui.add_css('button.my-red-button:hover { background-color: red !important; }')
    keep_alive_chars = ['-', '\\', '|', '/']
    manager = Manager()
    keep_alive_queue = manager.Queue()
    update_keep_alive = 0.1

    
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
            keep_alive_label = ui.label('').classes('w-4 text-center')

        progress_bar = ui.linear_progress(value=0,show_value=False, size="20px").props('instant-feedback')
        with ui.row().classes('w-1/2 h-150'):
            ui.label('Progress info:')
            progress_label = ui.label()
        with ui.column().classes('w-full h-300'):
            ui.label('Log info:')
            log_scroll_area = ui.scroll_area().classes('w-full h-155 border-1 rounded-lg p-2').style('border: 1px solid black')
        return select_dir_button, dir_input, progress_bar, progress_label, log_scroll_area, keep_alive_label

    def update_ui(select_dir_button, dir_input, progress_bar, progress_label, log_scroll_area, shared_progress, total_steps, interval, process_running, start_button, abort_button):
        """Update the UI elements with current progress"""
        try:
            last_value = 0
            last_log_length = 0 #AI+
            
            async def update_progress(): #AI+
                """Update progress bar and label""" #AI+
                nonlocal last_value, last_log_length #AI+
                try:
                    current_count = shared_progress.value if shared_progress else 0
                    current_log_length = len(globals.log_content) #AI+
                    
                    if current_count != last_value or current_log_length != last_log_length: #AI+
                        if total_steps > 0:
                            percentage = int((current_count / total_steps) * 100)
                            progress_bar.set_value(percentage/100)
                            progress_label.text = f'Progress: {percentage}% ({current_count}/{total_steps})'
                            
                            if current_log_length > last_log_length: #AI+
                                with log_scroll_area:
                                    log_scroll_area.clear()
                                    for line in globals.log_content:
                                        ui.label(line).classes('text-sm')
                                log_scroll_area.scroll_to(percent=100)
                                last_log_length = current_log_length #AI+
                            
                            last_value = current_count
                except Exception as e:
                    print(f"Error updating progress: {e}")

            # Create timer for periodic updates
            timer = ui.timer(interval, update_progress) #AI+
            timer.active = True #AI+

            # Wait for process to complete
            while process_running and process_running.value:
                time.sleep(interval)

            # Show final status
            timer.active = False #AI+
            final_count = shared_progress.value if shared_progress else 0
            if total_steps > 0:
                percentage = int((final_count / total_steps) * 100)
                progress_bar.set_value(percentage/100)
                if globals.aborted:
                    progress_label.text = f'Aborted: {final_count} files found/{total_steps} files processed'
                else:
                    progress_label.text = f'Completed: {percentage}% ({final_count}/{total_steps} files)'

            # Final log update
            with log_scroll_area:
                log_scroll_area.clear()
                for line in globals.log_content:
                    ui.label(line).classes('text-sm')
                log_scroll_area.scroll_to(percent=100)

        except Exception as e:
            print(f"Error in update_ui thread: {e}")
        finally:
            # Reset UI
            try:
                abort_button.visible = False
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
        """Create the fill_db page"""
        config.init_config()
        
        # Add JavaScript event handlers
        ui.add_body_html("""
            <script>
            window.addEventListener('update_progress', (e) => {
                const progress_bar = document.querySelector('.q-linear-progress');
                const progress_label = document.querySelector('.progress-label');
                if (progress_bar) progress_bar.value = e.detail.percentage / 100;
                if (progress_label) progress_label.textContent = `Progress: ${e.detail.percentage}% (${e.detail.current}/${e.detail.total})`;
            });
            
            window.addEventListener('update_final', (e) => {
                const progress_bar = document.querySelector('.q-linear-progress');
                const progress_label = document.querySelector('.progress-label');
                if (progress_bar) progress_bar.value = e.detail.percentage / 100;
                if (progress_label) {
                    const text = e.detail.aborted ? 
                        `Aborted: ${e.detail.count} files found/${e.detail.total} files processed` :
                        `Completed: ${e.detail.percentage}% (${e.detail.count}/${e.detail.total} files)`;
                    progress_label.textContent = text;
                }
            });
            
            window.addEventListener('reset_ui', () => {
                const abort_btn = document.querySelector('.abort-btn');
                const start_btn = document.querySelector('.start-btn');
                if (abort_btn) abort_btn.style.display = 'none';
                if (start_btn) start_btn.style.display = '';
            });
            </script>
        """)
        search_path = globals.config_data['search_path']
        interval = float(globals.config_data['interval'])
        
        select_dir_button, dir_input, progress_bar, progress_label, log_scroll_area, keep_alive_label = create_ui()
        
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

        async def on_start():
            """Start processing en update UI"""
            globals.aborted = False
            try:
                # First clean up any existing resources
                cleanup_resources()
                
                # Clear the log area
                with log_scroll_area:
                    log_scroll_area.clear()
                globals.log_content.clear()
                
                # Get number of files using run.cpu_bound
                search_path = globals.config_data['search_path']
                extentions = globals.config_data['image_extensions'] + globals.config_data['video_extensions']
                total_steps = await run.cpu_bound(count_image_files2, search_path, extentions)
                
                if total_steps == 0:
                    ui.notify('No files found in directory', type='warning')
                    return
                
                # Initialize fresh resources
                shared_resources['progress'] = Value('i', 0)
                shared_resources['running'] = Value('b', True)
                shared_resources['threads'] = {'ui': None, 'process': None}
                
                # Update button visibility
                start_button.visible = False
                abort_button.visible = True
                abort_button.classes('bg-red-500')
                abort_button.text = 'Abort Processing'
                
                # Start UI update thread
                shared_resources['threads']['ui'] = threading.Thread(
                    target=update_ui,
                    args=(select_dir_button, dir_input, progress_bar, progress_label, log_scroll_area, 
                        shared_resources['progress'], total_steps, interval, 
                        shared_resources['running'], start_button, abort_button),
                    daemon=True
                )
                shared_resources['threads']['ui'].start()
                
                # Start the main processing using run.cpu_bound directly
                await run.cpu_bound(run_dup_detect, shared_resources['progress'], total_steps, shared_resources['running']) #AI+
                
            except Exception as e:
                ui.notify(f"Error during start: {e}", type='negative')
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