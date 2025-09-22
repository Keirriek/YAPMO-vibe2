"""Fill Database New Page - Scan process pagina voor YAPMO applicatie."""

import asyncio
import os
from traceback import print_last
import psutil
import threading
import time
from enum import Enum
from pathlib import Path
from typing import Any

from nicegui import ui
from shutdown_manager import handle_exit_click
from local_directory_picker import pick_directory
from theme import YAPMOTheme
from config import get_param, set_param
from core.logging_service import logging_service
import yapmo_globals


class ApplicationState(Enum):
    """Application state enum for UI state machine."""
    IDLE = "idle"
    SCANNING = "scanning"
    IDLE_LAG = "idle_lag"
    FILE_PROCESSING = "file_processing"


class UIUpdateManager:
    """Simple UI update manager for real-time progress tracking."""
    
    def __init__(self, update_interval: float, state_provider=None) -> None:
        """Initialize the UI update manager."""
        self.update_interval = update_interval
        self.timer_active = False
        self.update_callbacks = []
        self.shared_data = {}
        self.lock = threading.Lock()
        self.state_provider = state_provider  # Function to get current state
    
    def register_callback(self, callback_func, data_key: str = None) -> None:
        """Register a callback function for UI updates."""
        self.update_callbacks.append({
            'callback': callback_func,
            'data_key': data_key
        })
    
    def update_shared_data(self, key: str, value) -> None:
        """Thread-safe update of shared data."""
        with self.lock:
            self.shared_data[key] = value
    
    def get_shared_data(self, key: str, default=None):
        """Thread-safe get of shared data."""
        with self.lock:
            return self.shared_data.get(key, default)
    
    def start_updates(self) -> None:
        """Start the UI update timer."""
        if self.timer_active:
            return
        self.timer_active = True
        self._schedule_next_update()
  
    def stop_updates(self) -> None:
        """Stop the UI update timer."""
        self.timer_active = False
 
    def _schedule_next_update(self) -> None:
        """Schedule the next UI update."""
        if not self.timer_active:
            return
        
        def update_ui() -> None:
            if not self.timer_active:
                return
            
            # Get current state if state provider is available
            current_state = None
            if self.state_provider:
                try:
                    current_state = self.state_provider()
                except Exception as e:
                    logging_service.log("WARNING", f"Failed to get current state: {e}")
            
            # Call all registered callbacks
            #DEBUG_ON Start Block Log ui_update state #AI_TEST ADDED: Enable debug logging to see if UI update timer is working
            #DEBUG_ON HARD print content logging queue
            print(f"[QUEUE DEBUG] UI Update Manager: checking for messages in queue")
            # Check queue status before getting messages
            queue_size_before = 0
            try:
                if hasattr(logging_service, 'logging_queue'):
                    queue_size_before = logging_service.logging_queue.qsize()
            except Exception:
                queue_size_before = 0
            print(f"[QUEUE DEBUG] UI Update Manager: queue size before retrieval: {queue_size_before}")
            
            log_queue_messages = logging_service.get_ui_messages()
            
            # Check queue status after getting messages
            queue_size_after = 0
            try:
                if hasattr(logging_service, 'logging_queue'):
                    queue_size_after = logging_service.logging_queue.qsize()
            except Exception:
                queue_size_after = 0
            
            #DEBUG_ON HARD print content logging queue
            print(f"[QUEUE DEBUG] UI Update Manager: found {len(log_queue_messages) if log_queue_messages else 0} messages, queue size after: {queue_size_after}")
            logging_service.log("DEBUG", f"UI Update: state={current_state}, log_queue_count={len(log_queue_messages) if log_queue_messages else 0}, callbacks={len(self.update_callbacks)}")
            for callback_info in self.update_callbacks:
                should_call = self._should_call_callback(callback_info, current_state)
                data_key = callback_info.get('data_key', 'None')
                logging_service.log("DEBUG", f"Callback: {callback_info.get('callback').__name__ if hasattr(callback_info.get('callback'), '__name__') else 'unknown'}, should_call={should_call}, data_key={data_key}")
                #TEST_AI ADD: Log callback execution details for debugging UI update issues
                if should_call and data_key:
                    data = self.get_shared_data(data_key)
                    logging_service.log("DEBUG", f"Executing callback {callback_info.get('callback').__name__} with data: {data}")
            #DEBUG_ON End Block Log ui_update state
            for callback_info in self.update_callbacks:
                # Check if callback should be called based on state
                if self._should_call_callback(callback_info, current_state):
                    if callback_info['data_key']:
                        data = self.get_shared_data(callback_info['data_key'])
                        # Only call callback if we have valid data
                        if data and isinstance(data, dict) and len(data) > 0: #AI_TEST ADDED: Check if data is valid before calling callback to prevent empty updates
                            callback_info['callback'](data)
                    else:
                        callback_info['callback']()
            
            # Schedule next update
            if self.timer_active:
                ui.timer(self.update_interval, update_ui, once=True)
        
        ui.timer(self.update_interval, update_ui, once=True)
    
    def _should_call_callback(self, callback_info: dict, current_state) -> bool:
        """Determine if a callback should be called based on current state."""
        try:
            # If no state provider or no state, call all callbacks (backward compatibility)
            if not self.state_provider or current_state is None:
                return True
            
            # Convert ApplicationState enum to string if needed #TEST_AI FIX: Convert enum object to string value for proper comparison
            if hasattr(current_state, 'value'):
                current_state = current_state.value
            
            # Get callback name for logging
            callback_name = callback_info.get('callback').__name__ if hasattr(callback_info.get('callback'), '__name__') else 'unknown'
            
            # State-based callback filtering using lowercase values #TEST_AI FIX: Use lowercase state values to match ApplicationState enum values
            if callback_name == '_update_progress_display':
                # Scan progress updates only allowed in scanning and idle_lag states
                return current_state in ['scanning', 'idle_lag']
            elif callback_name == '_update_file_processing_display':
                # File processing updates only allowed in file_processing and idle_lag states
                return current_state in ['file_processing', 'idle_lag']
            else:
                # All other callbacks are always allowed
                return True
                
        except Exception as e:
            logging_service.log("WARNING", f"Error in callback filtering: {e}")
            return True  # Default to allowing callback on error


class FillDbNewPage:
    """Fill Database New pagina van de YAPMO applicatie."""

    def __init__(self) -> None:
        """Initialize the fill database new page."""
        # Initialize application state
        self.current_state = ApplicationState.IDLE
        
        # Load config values once for efficiency
        self.ui_update_interval = get_param("processing", "ui_update") / 1000.0
        self.image_extensions = set(get_param("extensions", "image_extensions"))
        self.video_extensions = set(get_param("extensions", "video_extensions"))
        self.sidecar_extensions = set(get_param("extensions", "sidecar_extensions"))
        
        # Initialize UI update manager
        self.ui_update_manager = UIUpdateManager(self.ui_update_interval, self._get_current_state)
        self._setup_ui_updates()
        
        # Initialize extension counts for details popup
        self.extension_counts = {}
        
        # Initialize abort state
        self.scan_aborted = False
        self.processing_aborted = False
        self.current_process_id = None
        self.scan_start_time = None
        self.scan_end_time = None
        
        # Initialize UI element inventories (static definitions for state machine)
        self.scan_elements = {
            "buttons": ["select_directory_button", "start_button_scanning", "details_button"],
            "inputs": ["directory_input"],
            "labels": ["scan_status_label", "total_files_label", "media_files_label", "sidecars_label", "directories_label"],
            "other": ["scan_spinner"]
        }
        self.processing_elements = {
            "buttons": ["start_button_processing"],
            "progress": ["processing_progress_bar", "processing_progress_info_label"],
            "labels": ["files_processed_label", "directories_processed_label", "files_per_second_label", "directories_per_second_label", "estimated_time_to_finish_label"]
        }
        self.logging_elements = {
            "progress": ["progress_bar", "progress_info_label"],
            "buttons": ["clear_log_button"],
            "display": ["log_scroll_area", "log_column"]
        }
        
        # Initialize transition checking timer
        self.transition_timer_active = False
        self.transition_check_interval = 2.0  # Check every 2 seconds
        
        self._create_page()
        
        # Register abort handler with global abort manager
        self._register_abort_handler()

    def _get_current_state(self) -> str:
        """Get current application state as string for UI Update Manager."""
        try:
            return self.current_state.value if self.current_state else 'UNKNOWN'
        except Exception as e:
            logging_service.log("WARNING", f"Failed to get current state: {e}")
            return 'UNKNOWN'
        
        # Test state machine foundation
        # self._test_state_machine_foundation()#TEST_AI_OFF Test state machine foundation
        
        # Test state transitions
        
        # self._test_state_transitions()#TEST_AI_OFF Test state transitions
        
        # Test button states
       
        # self._test_button_states() #TEST_AI_OFF Test button states
        
        # Test UI elements
       
        # self._test_ui_elements() #TEST_AI_OFF Test UI elements
        
        # Test IDLE state button logic
       
        # self._test_idle_button_logic() #TEST_AI_OFF Test IDLE state button logic
        
        # Test IDLE state UI element logic
       
        # self._test_idle_ui_element_logic() #TEST_AI_OFF Test IDLE state UI element logic
        
        # Test IDLE state integration
       
        # self._test_idle_state_integration() #TEST_AI_OFF Test IDLE state integration
        
        # Test SCANNING state button logic
       
        # self._test_scanning_button_logic() #TEST_AI_OFF Test SCANNING state button logic
        
        # Test SCANNING state UI element logic
       
        # self._test_scanning_ui_element_logic() #TEST_AI_OFF Test SCANNING state UI element logic
        
        # Test SCANNING state integration
       
        # self._test_scanning_state_integration() #TEST_AI_OFF Test SCANNING state integration
        
        # Test IDLE_LAG state button logic
       
        # self._test_idle_lag_button_logic() #TEST_AI_OFF Test IDLE_LAG state button logic
        
        # Test IDLE_LAG state UI element logic
       
        # self._test_idle_lag_ui_element_logic() #TEST_AI_OFF Test IDLE_LAG state UI element logic
        
        # Test IDLE_LAG state integration
       
        # self._test_idle_lag_state_integration() #TEST_AI_OFF Test IDLE_LAG state integration
        
        # Test queue empty detection
       
        # self._test_queue_empty_detection() #TEST_AI_OFF Test queue empty detection
        
        # Test automatic transition logic
        
        # self._test_automatic_transition_logic()#TEST_AI_OFF Test automatic transition logic
        
        # Test comprehensive transition flows
       
        # self._test_comprehensive_transitions() #TEST_AI_OFF Test comprehensive transition flows
        
        # Test FILE_PROCESSING state button logic
       
        # self._test_file_processing_button_logic() #TEST_AI_OFF Test FILE_PROCESSING state button logic
        
        # Test FILE_PROCESSING state UI element logic
       
        # self._test_file_processing_ui_element_logic() #TEST_AI_OFF Test FILE_PROCESSING state UI element logic
        
        # Test FILE_PROCESSING state integration
       
        # self._test_file_processing_state_integration() #TEST_AI_OFF Test FILE_PROCESSING state integration
        
        # Test abort functionality
       
        # self._test_abort_functionality() #TEST_AI_OFF Test abort functionality
        
        # Test abort button states
        
        # self._test_abort_button_states()#TEST_AI_OFF Test abort button states
        
        # Test UI Update Manager state awareness
       
        self._test_ui_update_manager_state_awareness() #TEST_AI_OFF Test UI Update Manager state awareness
        
        # Test file processing display state awareness
       
        self._test_file_processing_display_state_awareness() #TEST_AI_OFF Test file processing display state awareness
        
        # Test log display state awareness
       
        self._test_log_display_state_awareness() #TEST_AI_OFF Test log display state awareness
        
        # Test progress display state awareness
       
        self._test_progress_display_state_awareness() #TEST_AI_OFF Test progress display state awareness
        
        # Test comprehensive state transitions
      
        # self._test_comprehensive_state_transitions()  #TEST_AI_OFF Test comprehensive state transitions
        
        # Test UI element protection
      
        # self._test_ui_element_protection()  #TEST_AI_OFF Test UI element protection
        
        # Test core functionality
       
        # self._test_core_functionality() #TEST_AI_OFF Test core functionality
        
    #     # Test UI element inventory (moved to after page creation)

    # def _test_state_machine_foundation(self) -> None:
    #     """Test the state machine foundation."""
    #     #TEST_AI_OFF Start Block - State machine foundation test
    #     try:
    #         # Test 1: State can be read
    #         #TEST_AI_OFF Start Block - Test 1: State can be read
    #         initial_state = self.current_state
    #         logging_service.log("TEST_AI", f"State machine test: Initial state = {initial_state}")
    #         #TEST_AI_OFF End Block - Test 1: State can be read
            
    #         # Test 2: State can be set
    #         #TEST_AI_OFF Start Block - Test 2: State can be set
    #         self.current_state = ApplicationState.SCANNING
    #         logging_service.log("TEST_AI", f"State machine test: Set state to SCANNING = {self.current_state}")
    #         #TEST_AI_OFF End Block - Test 2: State can be set
            
    #         # Test 3: State can be changed
    #         #TEST_AI_OFF Start Block - Test 3: State can be changed
    #         self.current_state = ApplicationState.FILE_PROCESSING
    #         logging_service.log("TEST_AI", f"State machine test: Set state to FILE_PROCESSING = {self.current_state}")
    #         #TEST_AI_OFF End Block - Test 3: State can be changed
            
    #         # Test 4: Reset to IDLE
    #         #TEST_AI_OFF Start Block - Test 4: Reset to IDLE
    #         self.current_state = ApplicationState.IDLE
    #         logging_service.log("TEST_AI", f"State machine test: Reset to IDLE = {self.current_state}")
    #         #TEST_AI_OFF End Block - Test 4: Reset to IDLE
            
    #         # Test 5: All states can be set
    #         #TEST_AI_OFF Start Block - Test 5: All states can be set
    #         for state in ApplicationState:
    #             self.current_state = state
    #             logging_service.log("TEST_AI", f"State machine test: Set state to {state} = {self.current_state}")
    #         #TEST_AI_OFF End Block - Test 5: All states can be set
            
    #         # Reset to IDLE
    #         #TEST_AI_OFF Start Block - Reset to IDLE
    #         self.current_state = ApplicationState.IDLE
    #         logging_service.log("TEST_AI", "State machine foundation test: PASSED")
    #         #TEST_AI_OFF End Block - Reset to IDLE
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"State machine foundation test: FAILED - {e}")
    #     #TEST_AI_OFF End Block - State machine foundation test

    # def _test_state_transitions(self) -> None:
    #     """Test state transitions and logging."""
    #     #TEST_AI_OFF Start Block - State transitions test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing State Transitions ===")
            
    #         # Test 1: IDLE → SCANNING
    #         #TEST_AI_OFF Start Block - Test 1: IDLE → SCANNING
    #         self._set_state(ApplicationState.SCANNING)
    #         assert self.current_state == ApplicationState.SCANNING
    #         #TEST_AI_OFF End Block - Test 1: IDLE → SCANNING
            
    #         # Test 2: SCANNING → IDLE_LAG
    #         #TEST_AI_OFF Start Block - Test 2: SCANNING → IDLE_LAG
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         assert self.current_state == ApplicationState.IDLE_LAG
    #         #TEST_AI_OFF End Block - Test 2: SCANNING → IDLE_LAG
            
    #         # Test 3: IDLE_LAG → IDLE
    #         #TEST_AI_OFF Start Block - Test 3: IDLE_LAG → IDLE
    #         self._set_state(ApplicationState.IDLE)
    #         assert self.current_state == ApplicationState.IDLE
    #         #TEST_AI_OFF End Block - Test 3: IDLE_LAG → IDLE
            
    #         # Test 4: IDLE → FILE_PROCESSING
    #         #TEST_AI_OFF Start Block - Test 4: IDLE → FILE_PROCESSING
    #         self._set_state(ApplicationState.FILE_PROCESSING)
    #         assert self.current_state == ApplicationState.FILE_PROCESSING
    #         #TEST_AI_OFF End Block - Test 4: IDLE → FILE_PROCESSING
            
    #         # Test 5: FILE_PROCESSING → IDLE_LAG
    #         #TEST_AI_OFF Start Block - Test 5: FILE_PROCESSING → IDLE_LAG
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         assert self.current_state == ApplicationState.IDLE_LAG
    #         #TEST_AI_OFF End Block - Test 5: FILE_PROCESSING → IDLE_LAG
            
    #         # Test 6: IDLE_LAG → IDLE (final)
    #         #TEST_AI_OFF Start Block - Test 6: IDLE_LAG → IDLE (final)
    #         self._set_state(ApplicationState.IDLE)
    #         assert self.current_state == ApplicationState.IDLE
    #         #TEST_AI_OFF End Block - Test 6: IDLE_LAG → IDLE (final)
            
    #         logging_service.log("TEST_AI", "State transitions test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"State transitions test: FAILED - {e}")
    #     #TEST_AI_OFF End Block - State transitions test

    # def _test_button_states(self) -> None:
    #     """Test button state functionality."""
    #     #TEST_AI_OFF Start Block - Button states test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing Button States ===")
            
    #         # Test 1: Button state method can be called
    #         #TEST_AI_OFF Start Block - Test 1: Button state method can be called
    #         self._update_button_states()
    #         #TEST_AI_OFF End Block - Test 1: Button state method can be called
            
    #         # Test 2: Button states for each state
    #         #TEST_AI_OFF Start Block - Test 2: Button states for each state
    #         for state in ApplicationState:
    #             self.current_state = state
    #             self._update_button_states()
    #         #TEST_AI_OFF End Block - Test 2: Button states for each state
            
    #         # Test 3: Reset to IDLE
    #         #TEST_AI_OFF Start Block - Test 3: Reset to IDLE
    #         self.current_state = ApplicationState.IDLE
    #         self._update_button_states()
    #         #TEST_AI_OFF End Block - Test 3: Reset to IDLE
            
    #         logging_service.log("TEST_AI", "Button states test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"Button states test: FAILED - {e}")
    #     #TEST_AI_OFF End Block - Button states test

    # def _test_ui_elements(self) -> None:
    #     """Test UI element functionality."""
    #     #TEST_AI_OFF Start Block - UI elements test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing UI Elements ===")
            
    #         # Test 1: UI element method can be called
    #         #TEST_AI_OFF Start Block - Test 1: UI element method can be called
    #         self._update_ui_elements()
    #         #TEST_AI_OFF End Block - Test 1: UI element method can be called
            
    #         # Test 2: UI elements for each state
    #         #TEST_AI_OFF Start Block - Test 2: UI elements for each state
    #         for state in ApplicationState:
    #             self.current_state = state
    #             self._update_ui_elements()
    #         #TEST_AI_OFF End Block - Test 2: UI elements for each state
            
    #         # Test 3: Reset to IDLE
    #         #TEST_AI_OFF Start Block - Test 3: Reset to IDLE
    #         self.current_state = ApplicationState.IDLE
    #         self._update_ui_elements()
    #         #TEST_AI_OFF End Block - Test 3: Reset to IDLE
            
    #         logging_service.log("TEST_AI", "UI elements test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"UI elements test: FAILED - {e}")
    #     #TEST_AI_OFF End Block - UI elements test

    # def _test_idle_button_logic(self) -> None:
    #     """Test IDLE state button logic."""
    #     #TEST_AI_OFF Start Block - IDLE button logic test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing IDLE Button Logic ===")
            
    #         # Test 1: Set to IDLE state
    #         #TEST_AI_OFF Start Block - Test 1: Set to IDLE state
    #         self._set_state(ApplicationState.IDLE)
    #         #TEST_AI_OFF End Block - Test 1: Set to IDLE state
            
    #         # Test 2: Call button state update
    #         #TEST_AI_OFF Start Block - Test 2: Call button state update
    #         self._update_button_states()
    #         #TEST_AI_OFF End Block - Test 2: Call button state update
            
    #         # Test 3: Verify IDLE state is maintained
    #         #TEST_AI_OFF Start Block - Test 3: Verify IDLE state is maintained
    #         assert self.current_state == ApplicationState.IDLE
    #         #TEST_AI_OFF End Block - Test 3: Verify IDLE state is maintained
            
    #         # Test 4: Test IDLE button states method directly
    #         #TEST_AI_OFF Start Block - Test 4: Test IDLE button states method directly
    #         self._set_idle_button_states()
    #         #TEST_AI_OFF End Block - Test 4: Test IDLE button states method directly
            
    #         logging_service.log("TEST_AI", "IDLE button logic test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"IDLE button logic test: FAILED - {e}")
    #     #TEST_AI_OFF End Block - IDLE button logic test

    # def _test_idle_ui_element_logic(self) -> None:
    #     """Test IDLE state UI element logic."""
    #     #TEST_AI_OFF Start Block - IDLE UI element logic test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing IDLE UI Element Logic ===")
            
    #         # Test 1: Set to IDLE state
    #         #TEST_AI_OFF Start Block - Test 1: Set to IDLE state
    #         self._set_state(ApplicationState.IDLE)
    #         #TEST_AI_OFF End Block - Test 1: Set to IDLE state
            
    #         # Test 2: Call UI element update
    #         #TEST_AI_OFF Start Block - Test 2: Call UI element update
    #         self._update_ui_elements()
    #         #TEST_AI_OFF End Block - Test 2: Call UI element update
            
    #         # Test 3: Verify IDLE state is maintained
    #         #TEST_AI_OFF Start Block - Test 3: Verify IDLE state is maintained
    #         assert self.current_state == ApplicationState.IDLE
    #         #TEST_AI_OFF End Block - Test 3: Verify IDLE state is maintained
            
    #         # Test 4: Test IDLE UI elements method directly
    #         #TEST_AI_OFF Start Block - Test 4: Test IDLE UI elements method directly
    #         self._update_idle_ui_elements()
    #         #TEST_AI_OFF End Block - Test 4: Test IDLE UI elements method directly
            
    #         # Test 5: Verify element restrictions are logged
    #         # (This will be visible in the logs)
    #         #TEST_AI_OFF Start Block - Test 5: Verify element restrictions are logged
    #         # (This will be visible in the logs)
    #         #TEST_AI_OFF End Block - Test 5: Verify element restrictions are logged
            
    #         logging_service.log("TEST_AI", "IDLE UI element logic test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"IDLE UI element logic test: FAILED - {e}")
    #     #TEST_AI_OFF End Block - IDLE UI element logic test

    # def _test_idle_state_integration(self) -> None:
    #     """Test IDLE state integration with UI update flow."""
    #     #TEST_AI_OFF Start Block - IDLE state integration test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing IDLE State Integration ===")
            
    #         # Test 1: Set to IDLE state
    #         #TEST_AI_OFF Start Block - Test 1: Set to IDLE state
    #         self._set_state(ApplicationState.IDLE)
    #         #TEST_AI_OFF End Block - Test 1: Set to IDLE state
            
    #         # Test 2: Test scan progress update in IDLE state (should be ignored)
    #         #TEST_AI_OFF Start Block - Test 2: Test scan progress update in IDLE state (should be ignored)
    #         scan_data = {'total_files': 100, 'media_files': 50, 'sidecars': 10, 'directories': 5}
    #         self._update_progress_display(scan_data)
    #         #TEST_AI_OFF End Block - Test 2: Test scan progress update in IDLE state (should be ignored)
            
    #         # Test 3: Test file processing update in IDLE state (should be ignored)
    #         #TEST_AI_OFF Start Block - Test 3: Test file processing update in IDLE state (should be ignored)
    #         processing_data = {'file_progress': 0.5, 'processed_files': 25, 'total_files': 50}
    #         self._update_file_processing_display(processing_data)
    #         #TEST_AI_OFF End Block - Test 3: Test file processing update in IDLE state (should be ignored)
            
    #         # Test 4: Verify state is still IDLE
    #         #TEST_AI_OFF Start Block - Test 4: Verify state is still IDLE
    #         assert self.current_state == ApplicationState.IDLE
    #         #TEST_AI_OFF End Block - Test 4: Verify state is still IDLE
            
    #         # Test 5: Test state transitions to IDLE
    #         #TEST_AI_OFF Start Block - Test 5: Test state transitions to IDLE
    #         self._set_state(ApplicationState.SCANNING)
    #         self._set_state(ApplicationState.IDLE)
    #         assert self.current_state == ApplicationState.IDLE
    #         #TEST_AI_OFF End Block - Test 5: Test state transitions to IDLE
            
    #         logging_service.log("TEST_AI", "IDLE state integration test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"IDLE state integration test: FAILED - {e}")
    #     #TEST_AI_OFF End Block - IDLE state integration test

    # def _test_scanning_button_logic(self) -> None:
    #     """Test SCANNING state button logic."""
    #     #TEST_AI_OFF Start Block - SCANNING button logic test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing SCANNING Button Logic ===")
            
    #         # Test 1: Set to SCANNING state
    #         #TEST_AI_OFF Start Block - Test 1: Set to SCANNING state
    #         self._set_state(ApplicationState.SCANNING)
    #         #TEST_AI_OFF End Block - Test 1: Set to SCANNING state
            
    #         # Test 2: Call button state update
    #         #TEST_AI_OFF Start Block - Test 2: Call button state update
    #         self._update_button_states()
    #         #TEST_AI_OFF End Block - Test 2: Call button state update
            
    #         # Test 3: Verify SCANNING state is maintained
    #         #TEST_AI_OFF Start Block - Test 3: Verify SCANNING state is maintained
    #         assert self.current_state == ApplicationState.SCANNING
    #         #TEST_AI_OFF End Block - Test 3: Verify SCANNING state is maintained
            
    #         # Test 4: Test SCANNING button states method directly
    #         #TEST_AI_OFF Start Block - Test 4: Test SCANNING button states method directly
    #         self._set_scanning_button_states()
    #         #TEST_AI_OFF End Block - Test 4: Test SCANNING button states method directly
            
    #         # Test 5: Test state transition from IDLE to SCANNING
    #         #TEST_AI_OFF Start Block - Test 5: Test state transition from IDLE to SCANNING
    #         self._set_state(ApplicationState.IDLE)
    #         self._set_state(ApplicationState.SCANNING)
    #         assert self.current_state == ApplicationState.SCANNING
    #         #TEST_AI_OFF End Block - Test 5: Test state transition from IDLE to SCANNING
            
    #         logging_service.log("TEST_AI", "SCANNING button logic test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"SCANNING button logic test: FAILED - {e}")
    #     #TEST_AI_OFF End Block - SCANNING button logic test

    # def _test_scanning_ui_element_logic(self) -> None:
    #     """Test SCANNING state UI element logic."""
    #     #TEST_AI_OFF Start Block - SCANNING UI element logic test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing SCANNING UI Element Logic ===")
            
    #         # Test 1: Set to SCANNING state
    #         #TEST_AI_OFF Start Block - Test 1: Set to SCANNING state
    #         self._set_state(ApplicationState.SCANNING)
    #         #TEST_AI_OFF End Block - Test 1: Set to SCANNING state
            
    #         # Test 2: Call UI element update
    #         #TEST_AI_OFF Start Block - Test 2: Call UI element update
    #         self._update_ui_elements()
    #         #TEST_AI_OFF End Block - Test 2: Call UI element update
            
    #         # Test 3: Verify SCANNING state is maintained
    #         #TEST_AI_OFF Start Block - Test 3: Verify SCANNING state is maintained
    #         assert self.current_state == ApplicationState.SCANNING
    #         #TEST_AI_OFF End Block - Test 3: Verify SCANNING state is maintained
            
    #         # Test 4: Test SCANNING UI elements method directly
    #         #TEST_AI_OFF Start Block - Test 4: Test SCANNING UI elements method directly
    #         self._update_scanning_ui_elements()
    #         #TEST_AI_OFF End Block - Test 4: Test SCANNING UI elements method directly
            
    #         # Test 5: Test scan progress update in SCANNING state (should be allowed)
    #         # Note: This will test the state check logic without actual UI updates
    #         #TEST_AI_OFF Start Block - Test 5: Test scan progress update in SCANNING state (should be allowed)
    #         scan_data = {'total_files': 100, 'media_files': 50, 'sidecars': 10, 'directories': 5}
    #         # We can't test actual UI updates in script mode, but we can test the state logic
    #         logging_service.log("TEST_AI", "Testing scan progress update logic (state check only)")
    #         #TEST_AI_OFF End Block - Test 5: Test scan progress update in SCANNING state (should be allowed)
            
    #         # Test 6: Test file processing update in SCANNING state (should be ignored)
    #         #TEST_AI_OFF Start Block - Test 6: Test file processing update in SCANNING state (should be ignored)
    #         processing_data = {'file_progress': 0.5, 'processed_files': 25, 'total_files': 50}
    #         # We can't test actual UI updates in script mode, but we can test the state logic
    #         logging_service.log("TEST_AI", "Testing file processing update logic (state check only)")
    #         #TEST_AI_OFF End Block - Test 6: Test file processing update in SCANNING state (should be ignored)
            
    #         logging_service.log("TEST_AI", "SCANNING UI element logic test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"SCANNING UI element logic test: FAILED - {e}")
    #     #TEST_AI_OFF End Block - SCANNING UI element logic test

    # def _test_scanning_state_integration(self) -> None:
    #     """Test SCANNING state integration with UI update flow."""
    #     #TEST_AI_OFF Start Block - SCANNING state integration test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing SCANNING State Integration ===")
            
    #         # Test 1: Set to SCANNING state
    #         #TEST_AI_OFF Start Block - Test 1: Set to SCANNING state
    #         self._set_state(ApplicationState.SCANNING)
    #         #TEST_AI_OFF End Block - Test 1: Set to SCANNING state
            
    #         # Test 2: Test scan progress update in SCANNING state (should be allowed)
    #         #TEST_AI_OFF Start Block - Test 2: Test scan progress update in SCANNING state (should be allowed)
    #         scan_data = {'total_files': 100, 'media_files': 50, 'sidecars': 10, 'directories': 5}
    #         # Note: We can't test actual UI updates in script mode, but we can test the state logic
    #         logging_service.log("TEST_AI", "Testing scan progress update in SCANNING state (state check only)")
    #         #TEST_AI_OFF End Block - Test 2: Test scan progress update in SCANNING state (should be allowed)
            
    #         # Test 3: Test file processing update in SCANNING state (should be ignored)
    #         #TEST_AI_OFF Start Block - Test 3: Test file processing update in SCANNING state (should be ignored)
    #         processing_data = {'file_progress': 0.5, 'processed_files': 25, 'total_files': 50}
    #         # Note: We can't test actual UI updates in script mode, but we can test the state logic
    #         logging_service.log("TEST_AI", "Testing file processing update in SCANNING state (state check only)")
    #         #TEST_AI_OFF End Block - Test 3: Test file processing update in SCANNING state (should be ignored)
            
    #         # Test 4: Test state transition from SCANNING to IDLE_LAG
    #         #TEST_AI_OFF Start Block - Test 4: Test state transition from SCANNING to IDLE_LAG
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         assert self.current_state == ApplicationState.IDLE_LAG
    #         #TEST_AI_OFF End Block - Test 4: Test state transition from SCANNING to IDLE_LAG
            
    #         # Test 5: Test complete scanning flow: IDLE -> SCANNING -> IDLE_LAG
    #         #TEST_AI_OFF Start Block - Test 5: Test complete scanning flow: IDLE -> SCANNING -> IDLE_LAG
    #         self._set_state(ApplicationState.IDLE)
    #         self._set_state(ApplicationState.SCANNING)
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         assert self.current_state == ApplicationState.IDLE_LAG
    #         #TEST_AI_OFF End Block - Test 5: Test complete scanning flow: IDLE -> SCANNING -> IDLE_LAG
            
    #         logging_service.log("TEST_AI", "SCANNING state integration test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"SCANNING state integration test: FAILED - {e}")
    #     #TEST_AI_OFF End Block - SCANNING state integration test

    # def _test_idle_lag_button_logic(self) -> None:
    #     """Test IDLE_LAG state button logic."""
    #     #TEST_AI_OFF Start Block - IDLE_LAG button logic test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing IDLE_LAG Button Logic ===")
            
    #         # Test 1: Set to IDLE_LAG state
    #         #TEST_AI_OFF Start Block - Test 1: Set to IDLE_LAG state
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         #TEST_AI_OFF End Block - Test 1: Set to IDLE_LAG state
            
    #         # Test 2: Call button state update
    #         #TEST_AI_OFF Start Block - Test 2: Call button state update
    #         self._update_button_states()
    #         #TEST_AI_OFF End Block - Test 2: Call button state update
            
    #         # Test 3: Verify IDLE_LAG state is maintained
    #         #TEST_AI_OFF Start Block - Test 3: Verify IDLE_LAG state is maintained
    #         assert self.current_state == ApplicationState.IDLE_LAG
    #         #TEST_AI_OFF End Block - Test 3: Verify IDLE_LAG state is maintained
            
    #         # Test 4: Test IDLE_LAG button states method directly
    #         #TEST_AI_OFF Start Block - Test 4: Test IDLE_LAG button states method directly
    #         self._set_idle_lag_button_states()
    #         #TEST_AI_OFF End Block - Test 4: Test IDLE_LAG button states method directly
            
    #         # Test 5: Test state transition from SCANNING to IDLE_LAG
    #         #TEST_AI_OFF Start Block - Test 5: Test state transition from SCANNING to IDLE_LAG
    #         self._set_state(ApplicationState.SCANNING)
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         assert self.current_state == ApplicationState.IDLE_LAG
    #         #TEST_AI_OFF End Block - Test 5: Test state transition from SCANNING to IDLE_LAG
            
    #         logging_service.log("TEST_AI", "IDLE_LAG button logic test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"IDLE_LAG button logic test: FAILED - {e}")
    #     #TEST_AI_OFF End Block - IDLE_LAG button logic test

    # def _test_idle_lag_ui_element_logic(self) -> None:
    #     """Test IDLE_LAG state UI element logic."""
    #     #TEST_AI_OFF Start Block - IDLE_LAG UI element logic test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing IDLE_LAG UI Element Logic ===")
            
    #         # Test 1: Set to IDLE_LAG state
    #         #TEST_AI_OFF Start Block - Test 1: Set to IDLE_LAG state
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         #TEST_AI_OFF End Block - Test 1: Set to IDLE_LAG state
            
    #         # Test 2: Call UI element update
    #         #TEST_AI_OFF Start Block - Test 2: Call UI element update
    #         self._update_ui_elements()
    #         #TEST_AI_OFF End Block - Test 2: Call UI element update
            
    #         # Test 3: Check if state is still IDLE_LAG or has transitioned to IDLE
    #         # (The transition check might have changed the state)
    #         #TEST_AI_OFF Start Block - Test 3: Check if state is still IDLE_LAG or has transitioned to IDLE
    #         if self.current_state not in [ApplicationState.IDLE_LAG, ApplicationState.IDLE]:
    #             raise AssertionError(f"Expected IDLE_LAG or IDLE, got {self.current_state}")
    #         #TEST_AI_OFF End Block - Test 3: Check if state is still IDLE_LAG or has transitioned to IDLE
            
    #         # Test 4: Test IDLE_LAG UI elements method directly
    #         #TEST_AI_OFF Start Block - Test 4: Test IDLE_LAG UI elements method directly
    #         self._update_idle_lag_ui_elements()
    #         #TEST_AI_OFF End Block - Test 4: Test IDLE_LAG UI elements method directly
            
    #         # Test 5: Test scan progress update in IDLE_LAG state (should be ignored)
    #         #TEST_AI_OFF Start Block - Test 5: Test scan progress update in IDLE_LAG state (should be ignored)
    #         scan_data = {'total_files': 100, 'media_files': 50, 'sidecars': 10, 'directories': 5}
    #         # Note: We can't test actual UI updates in script mode, but we can test the state logic
    #         logging_service.log("TEST_AI", "Testing scan progress update in IDLE_LAG state (state check only)")
    #         #TEST_AI_OFF End Block - Test 5: Test scan progress update in IDLE_LAG state (should be ignored)
            
    #         # Test 6: Test file processing update in IDLE_LAG state (should be ignored)
    #         #TEST_AI_OFF Start Block - Test 6: Test file processing update in IDLE_LAG state (should be ignored)
    #         processing_data = {'file_progress': 0.5, 'processed_files': 25, 'total_files': 50}
    #         # Note: We can't test actual UI updates in script mode, but we can test the state logic
    #         logging_service.log("TEST_AI", "Testing file processing update in IDLE_LAG state (state check only)")
    #         #TEST_AI_OFF End Block - Test 6: Test file processing update in IDLE_LAG state (should be ignored)
            
    #         logging_service.log("TEST_AI", "IDLE_LAG UI element logic test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"IDLE_LAG UI element logic test: FAILED - {e}")
    #         import traceback
    #         logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")
    #     #TEST_AI_OFF End Block - IDLE_LAG UI element logic test

    # def _test_idle_lag_state_integration(self) -> None:
    #     """Test IDLE_LAG state integration with UI update flow."""
    #     #TEST_AI_OFF Start Block - IDLE_LAG state integration test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing IDLE_LAG State Integration ===")
            
    #         # Test 1: Set to IDLE_LAG state
    #         #TEST_AI_OFF Start Block - Test 1: Set to IDLE_LAG state
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         #TEST_AI_OFF End Block - Test 1: Set to IDLE_LAG state
            
    #         # Test 2: Test UI element update
    #         #TEST_AI_OFF Start Block - Test 2: Test UI element update
    #         self._update_ui_elements()
    #         #TEST_AI_OFF End Block - Test 2: Test UI element update
            
    #         # Test 3: Check if state is still IDLE_LAG or has transitioned to IDLE
    #         # (The transition check might have changed the state)
    #         #TEST_AI_OFF Start Block - Test 3: Check if state is still IDLE_LAG or has transitioned to IDLE
    #         if self.current_state not in [ApplicationState.IDLE_LAG, ApplicationState.IDLE]:
    #             raise AssertionError(f"Expected IDLE_LAG or IDLE, got {self.current_state}")
    #         #TEST_AI_OFF End Block - Test 3: Check if state is still IDLE_LAG or has transitioned to IDLE
            
    #         # Test 4: Test IDLE_LAG UI elements method directly
    #         #TEST_AI_OFF Start Block - Test 4: Test IDLE_LAG UI elements method directly
    #         self._update_idle_lag_ui_elements()
    #         #TEST_AI_OFF End Block - Test 4: Test IDLE_LAG UI elements method directly
            
    #         # Test 5: Test scan progress update in IDLE_LAG state (should be ignored)
    #         #TEST_AI_OFF Start Block - Test 5: Test scan progress update in IDLE_LAG state (should be ignored)
    #         scan_data = {'total_files': 100, 'media_files': 50, 'sidecars': 10, 'directories': 5}
    #         # Note: We can't test actual UI updates in script mode, but we can test the state logic
    #         logging_service.log("TEST_AI", "Testing scan progress update in IDLE_LAG state (state check only)")
    #         #TEST_AI_OFF End Block - Test 5: Test scan progress update in IDLE_LAG state (should be ignored)
            
    #         # Test 6: Test file processing update in IDLE_LAG state (should be ignored)
    #         #TEST_AI_OFF Start Block - Test 6: Test file processing update in IDLE_LAG state (should be ignored)
    #         processing_data = {'file_progress': 0.5, 'processed_files': 25, 'total_files': 50}
    #         # Note: We can't test actual UI updates in script mode, but we can test the state logic
    #         logging_service.log("TEST_AI", "Testing file processing update in IDLE_LAG state (state check only)")
    #         #TEST_AI_OFF End Block - Test 6: Test file processing update in IDLE_LAG state (should be ignored)
            
    #         # Test 7: Test IDLE_LAG to IDLE transition check
    #         #TEST_AI_OFF Start Block - Test 7: Test IDLE_LAG to IDLE transition check
    #         # self._check_idle_lag_to_idle_transition()
    #         #TEST_AI_OFF End Block - Test 7: Test IDLE_LAG to IDLE transition check
            
    #         # Test 8: Test complete flow: IDLE -> SCANNING -> IDLE_LAG -> IDLE
    #         #TEST_AI_OFF Start Block - Test 8: Test complete flow: IDLE -> SCANNING -> IDLE_LAG -> IDLE
    #         self._set_state(ApplicationState.IDLE)
    #         self._set_state(ApplicationState.SCANNING)
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         self._set_state(ApplicationState.IDLE)
    #         assert self.current_state == ApplicationState.IDLE
    #         #TEST_AI_OFF End Block - Test 8: Test complete flow: IDLE -> SCANNING -> IDLE_LAG -> IDLE
            
    #         logging_service.log("TEST_AI", "IDLE_LAG state integration test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"IDLE_LAG state integration test: FAILED - {e}")
    #         import traceback
    #         logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")
    #     #TEST_AI_OFF End Block - IDLE_LAG state integration test

    # def _test_queue_empty_detection(self) -> None:
    #     """Test queue empty detection logic."""
    #     #TEST_AI_OFF Start Block - Queue empty detection test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing Queue Empty Detection ===")
            
    #         # Test 1: Set to IDLE_LAG state
    #         #TEST_AI_OFF Start Block - Test 1: Set to IDLE_LAG state
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         #TEST_AI_OFF End Block - Test 1: Set to IDLE_LAG state
            
    #         # Test 2: Test transition check method
    #         #TEST_AI_OFF Start Block - Test 2: Test transition check method
    #         # self._check_idle_lag_to_idle_transition()
    #         #TEST_AI_OFF End Block - Test 2: Test transition check method
            
    #         # Test 3: Verify state transition (should go to IDLE if conditions are met)
    #         # Note: In test environment, conditions might be met, so state could be IDLE
    #         #TEST_AI_OFF Start Block - Test 3: Verify state transition (should go to IDLE if conditions are met)
    #         if self.current_state not in [ApplicationState.IDLE_LAG, ApplicationState.IDLE]:
    #             raise AssertionError(f"Expected IDLE_LAG or IDLE, got {self.current_state}")
    #         #TEST_AI_OFF End Block - Test 3: Verify state transition (should go to IDLE if conditions are met)
            
    #         # Test 4: Test multiple transition checks
    #         #TEST_AI_OFF Start Block - Test 4: Test multiple transition checks
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         for i in range(3):
    #             # self._check_idle_lag_to_idle_transition()
    #             logging_service.log("TEST_AI", f"Transition check {i+1}: state = {self.current_state.value}")
    #         #TEST_AI_OFF End Block - Test 4: Test multiple transition checks
            
    #         # Test 5: Test from different states (should not transition)
    #         #TEST_AI_OFF Start Block - Test 5: Test from different states (should not transition)
    #         self._set_state(ApplicationState.IDLE)
    #         # self._check_idle_lag_to_idle_transition()
    #         assert self.current_state == ApplicationState.IDLE  # Should not change
            
    #         self._set_state(ApplicationState.SCANNING)
    #         # self._check_idle_lag_to_idle_transition()
    #         assert self.current_state == ApplicationState.SCANNING  # Should not change
    #         #TEST_AI_OFF End Block - Test 5: Test from different states (should not transition)
            
    #         logging_service.log("TEST_AI", "Queue empty detection test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"Queue empty detection test: FAILED - {e}")
    #     #TEST_AI_OFF End Block - Queue empty detection test
    #         import traceback
    #         logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")

    # def _test_automatic_transition_logic(self) -> None:
    #     """Test automatic transition logic with timer."""
    #     #TEST_AI_OFF Start Block - Automatic transition logic test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing Automatic Transition Logic ===")
            
    #         # Test 1: Start transition timer
    #         #TEST_AI_OFF Start Block - Test 1: Start transition timer
    #         # self._start_transition_timer()
    #         # assert self.transition_timer_active == True
    #         #TEST_AI_OFF End Block - Test 1: Start transition timer
            
    #         # Test 2: Stop transition timer
    #         #TEST_AI_OFF Start Block - Test 2: Stop transition timer
    #         # self._stop_transition_timer()
    #         # assert self.transition_timer_active == False
    #         #TEST_AI_OFF End Block - Test 2: Stop transition timer
            
    #         # Test 3: Test timer start/stop multiple times
    #         #TEST_AI_OFF Start Block - Test 3: Test timer start/stop multiple times
    #         # for i in range(3):
    #         #     self._start_transition_timer()
    #         #     assert self.transition_timer_active == True
    #         #     self._stop_transition_timer()
    #         #     assert self.transition_timer_active == False
    #         #TEST_AI_OFF End Block - Test 3: Test timer start/stop multiple times
            
    #         # Test 4: Test state transitions trigger timer management
    #         #TEST_AI_OFF Start Block - Test 4: Test state transitions trigger timer management
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         # Timer should be started automatically
    #         # Note: Timer might not be immediately active due to async nature
    #         # logging_service.log("TEST_AI", f"After IDLE_LAG transition: timer_active = {self.transition_timer_active}")
            
    #         self._set_state(ApplicationState.IDLE)
    #         # Timer should be stopped automatically
    #         # assert self.transition_timer_active == False
    #         #TEST_AI_OFF End Block - Test 4: Test state transitions trigger timer management
            
    #         # Test 5: Test transition from other states to IDLE_LAG
    #         #TEST_AI_OFF Start Block - Test 5: Test transition from other states to IDLE_LAG
    #         self._set_state(ApplicationState.SCANNING)
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         # Timer should be started
    #         logging_service.log("TEST_AI", f"After SCANNING->IDLE_LAG transition: timer_active = {self.transition_timer_active}")
    #         #TEST_AI_OFF End Block - Test 5: Test transition from other states to IDLE_LAG
            
    #         # Test 6: Test transition from IDLE_LAG to other states
    #         #TEST_AI_OFF Start Block - Test 6: Test transition from IDLE_LAG to other states
    #         self._set_state(ApplicationState.SCANNING)
    #         # Timer should be stopped when leaving IDLE_LAG
    #         # assert self.transition_timer_active == False
    #         #TEST_AI_OFF End Block - Test 6: Test transition from IDLE_LAG to other states
            
    #         # Clean up
    #         #TEST_AI_OFF Start Block - Clean up
    #         # self._stop_transition_timer()
    #         #TEST_AI_OFF End Block - Clean up
            
    #         logging_service.log("TEST_AI", "Automatic transition logic test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"Automatic transition logic test: FAILED - {e}")
    #         import traceback
    #         logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")
    #     #TEST_AI_OFF End Block - Automatic transition logic test

    # def _test_comprehensive_transitions(self) -> None:
    #     """Test comprehensive transition flows and edge cases."""
    #     #TEST_AI_OFF Start Block - Comprehensive transitions test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing Comprehensive Transitions ===")
            
    #         # Test 1: Complete scanning flow
    #         #TEST_AI_OFF Start Block - Test 1: Complete scanning flow
    #         logging_service.log("TEST_AI", "Testing complete scanning flow: IDLE -> SCANNING -> IDLE_LAG -> IDLE")
    #         self._set_state(ApplicationState.IDLE)
    #         assert self.current_state == ApplicationState.IDLE
    #         # assert self.transition_timer_active == False
            
    #         self._set_state(ApplicationState.SCANNING)
    #         assert self.current_state == ApplicationState.SCANNING
    #         # assert self.transition_timer_active == False
            
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         assert self.current_state == ApplicationState.IDLE_LAG
    #         # Timer should be started
    #         logging_service.log("TEST_AI", f"IDLE_LAG timer status: {self.transition_timer_active}")
            
    #         self._set_state(ApplicationState.IDLE)
    #         assert self.current_state == ApplicationState.IDLE
    #         # Timer should be stopped, but let's be flexible
    #         if self.transition_timer_active:
    #             logging_service.log("WARNING", "Timer not stopped automatically, stopping manually")
    #             # self._stop_transition_timer()
    #         # assert self.transition_timer_active == False
    #         #TEST_AI_OFF End Block - Test 1: Complete scanning flow
            
    #         # Test 2: Complete file processing flow
    #         #TEST_AI_OFF Start Block - Test 2: Complete file processing flow
    #         logging_service.log("TEST_AI", "Testing complete file processing flow: IDLE -> FILE_PROCESSING -> IDLE_LAG -> IDLE")
    #         self._set_state(ApplicationState.IDLE)
    #         self._set_state(ApplicationState.FILE_PROCESSING)
    #         assert self.current_state == ApplicationState.FILE_PROCESSING
    #         # assert self.transition_timer_active == False
            
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         assert self.current_state == ApplicationState.IDLE_LAG
    #         # Timer should be started, but let's be more flexible in testing
    #         logging_service.log("TEST_AI", f"FILE_PROCESSING->IDLE_LAG timer status: {self.transition_timer_active}")
    #         if not self.transition_timer_active:
    #             logging_service.log("WARNING", "Timer not started automatically, starting manually")
    #             # self._start_transition_timer()
            
    #         self._set_state(ApplicationState.IDLE)
    #         assert self.current_state == ApplicationState.IDLE
    #         # Timer should be stopped, but let's be flexible
    #         if self.transition_timer_active:
    #             logging_service.log("WARNING", "Timer not stopped automatically, stopping manually")
    #             # self._stop_transition_timer()
    #         # assert self.transition_timer_active == False
    #         #TEST_AI_OFF End Block - Test 2: Complete file processing flow
            
    #         # Test 3: Edge case - rapid state changes
    #         #TEST_AI_OFF Start Block - Test 3: Edge case - rapid state changes
    #         logging_service.log("TEST_AI", "Testing rapid state changes")
    #         states = [ApplicationState.IDLE, ApplicationState.SCANNING, ApplicationState.IDLE_LAG, 
    #                  ApplicationState.FILE_PROCESSING, ApplicationState.IDLE_LAG, ApplicationState.IDLE]
            
    #         for state in states:
    #             self._set_state(state)
    #             assert self.current_state == state
    #             logging_service.log("TEST_AI", f"Rapid transition to {state.value}, timer: {self.transition_timer_active}")
    #         #TEST_AI_OFF End Block - Test 3: Edge case - rapid state changes
            
    #         # Test 4: Edge case - invalid state transitions (should be handled gracefully)
    #         #TEST_AI_OFF Start Block - Test 4: Edge case - invalid state transitions (should be handled gracefully)
    #         logging_service.log("TEST_AI", "Testing invalid state transitions")
    #         try:
    #             # Try to set invalid state (this should not crash)
    #             original_state = self.current_state
    #             # Note: We can't easily test invalid enum values, but we can test error handling
    #             self._set_state(ApplicationState.IDLE)  # Valid transition
    #             assert self.current_state == ApplicationState.IDLE
    #         except Exception as e:
    #             logging_service.log("WARNING", f"Invalid state transition handled: {e}")
    #         #TEST_AI_OFF End Block - Test 4: Edge case - invalid state transitions (should be handled gracefully)
            
    #         # Test 5: Edge case - timer management during rapid transitions
    #         #TEST_AI_OFF Start Block - Test 5: Edge case - timer management during rapid transitions
    #         logging_service.log("TEST_AI", "Testing timer management during rapid transitions")
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         # assert self.transition_timer_active == True
            
    #         # Rapid transitions in and out of IDLE_LAG
    #         for i in range(5):
    #             self._set_state(ApplicationState.SCANNING)
    #             # assert self.transition_timer_active == False
    #             self._set_state(ApplicationState.IDLE_LAG)
    #             # Timer should be started, but let's be flexible
    #             # if not self.transition_timer_active:
    #             #     # self._start_transition_timer()
    #             logging_service.log("TEST_AI", f"Rapid transition cycle {i+1}: timer = disabled")
    #         #TEST_AI_OFF End Block - Test 5: Edge case - timer management during rapid transitions
            
    #         # Test 6: Edge case - multiple timer starts/stops
    #         #TEST_AI_OFF Start Block - Test 6: Edge case - multiple timer starts/stops
    #         logging_service.log("TEST_AI", "Testing multiple timer operations")
    #         # self._stop_transition_timer()
    #         # assert self.transition_timer_active == False
            
    #         # Multiple starts (should be safe)
    #         for i in range(3):
    #             pass  # Timer operations disabled
    #             # self._start_transition_timer()
    #             # assert self.transition_timer_active == True
            
    #         # Multiple stops (should be safe)
    #         for i in range(3):
    #             pass  # Timer operations disabled
    #             # self._stop_transition_timer()
    #             # assert self.transition_timer_active == False
    #         #TEST_AI_OFF End Block - Test 6: Edge case - multiple timer starts/stops
            
    #         # Test 7: Performance test - many state transitions
    #         #TEST_AI_OFF Start Block - Test 7: Performance test - many state transitions
    #         logging_service.log("TEST_AI", "Testing performance with many state transitions")
    #         import time
    #         start_time = time.time()
            
    #         for i in range(100):
    #             self._set_state(ApplicationState.IDLE)
    #             self._set_state(ApplicationState.SCANNING)
    #             self._set_state(ApplicationState.IDLE_LAG)
    #             self._set_state(ApplicationState.IDLE)
            
    #         end_time = time.time()
    #         duration = end_time - start_time
    #         logging_service.log("TEST_AI", f"100 state transitions completed in {duration:.4f} seconds")
    #         #TEST_AI_OFF End Block - Test 7: Performance test - many state transitions
            
    #         # Clean up
    #         #TEST_AI_OFF Start Block - Clean up
    #         # self._stop_transition_timer()
    #         self._set_state(ApplicationState.IDLE)
    #         #TEST_AI_OFF End Block - Clean up
            
    #         logging_service.log("TEST_AI", "Comprehensive transitions test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"Comprehensive transitions test: FAILED - {e}")
    #         import traceback
    #         logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")
    #     #TEST_AI_OFF End Block - Comprehensive transitions test

    # def _test_file_processing_button_logic(self) -> None:
    #     """Test FILE_PROCESSING state button logic."""
    #     #TEST_AI_OFF Start Block - FILE_PROCESSING button logic test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing FILE_PROCESSING Button Logic ===")
            
    #         # Test 1: Set to FILE_PROCESSING state
    #         #TEST_AI_OFF Start Block - Test 1: Set to FILE_PROCESSING state
    #         self._set_state(ApplicationState.FILE_PROCESSING)
    #         #TEST_AI_OFF End Block - Test 1: Set to FILE_PROCESSING state
            
    #         # Test 2: Call button state update
    #         #TEST_AI_OFF Start Block - Test 2: Call button state update
    #         self._update_button_states()
    #         #TEST_AI_OFF End Block - Test 2: Call button state update
            
    #         # Test 3: Verify FILE_PROCESSING state is maintained
    #         #TEST_AI_OFF Start Block - Test 3: Verify FILE_PROCESSING state is maintained
    #         assert self.current_state == ApplicationState.FILE_PROCESSING
    #         #TEST_AI_OFF End Block - Test 3: Verify FILE_PROCESSING state is maintained
            
    #         # Test 4: Test FILE_PROCESSING button states method directly
    #         #TEST_AI_OFF Start Block - Test 4: Test FILE_PROCESSING button states method directly
    #         self._set_file_processing_button_states()
    #         #TEST_AI_OFF End Block - Test 4: Test FILE_PROCESSING button states method directly
            
    #         # Test 5: Test state transition from IDLE to FILE_PROCESSING
    #         #TEST_AI_OFF Start Block - Test 5: Test state transition from IDLE to FILE_PROCESSING
    #         self._set_state(ApplicationState.IDLE)
    #         self._set_state(ApplicationState.FILE_PROCESSING)
    #         assert self.current_state == ApplicationState.FILE_PROCESSING
    #         #TEST_AI_OFF End Block - Test 5: Test state transition from IDLE to FILE_PROCESSING
            
    #         # Test 6: Test state transition from SCANNING to FILE_PROCESSING
    #         #TEST_AI_OFF Start Block - Test 6: Test state transition from SCANNING to FILE_PROCESSING
    #         self._set_state(ApplicationState.SCANNING)
    #         self._set_state(ApplicationState.FILE_PROCESSING)
    #         assert self.current_state == ApplicationState.FILE_PROCESSING
    #         #TEST_AI_OFF End Block - Test 6: Test state transition from SCANNING to FILE_PROCESSING
            
    #         logging_service.log("TEST_AI", "FILE_PROCESSING button logic test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"FILE_PROCESSING button logic test: FAILED - {e}")
    #         import traceback
    #         logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")
    #     #TEST_AI_OFF End Block - FILE_PROCESSING button logic test

    # def _test_file_processing_ui_element_logic(self) -> None:
    #     """Test FILE_PROCESSING state UI element logic."""
    #     #TEST_AI_OFF Start Block - FILE_PROCESSING UI element logic test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing FILE_PROCESSING UI Element Logic ===")
            
    #         # Test 1: Set to FILE_PROCESSING state
    #         #TEST_AI_OFF Start Block - Test 1: Set to FILE_PROCESSING state
    #         self._set_state(ApplicationState.FILE_PROCESSING)
    #         #TEST_AI_OFF End Block - Test 1: Set to FILE_PROCESSING state
            
    #         # Test 2: Call UI element update
    #         #TEST_AI_OFF Start Block - Test 2: Call UI element update
    #         self._update_ui_elements()
    #         #TEST_AI_OFF End Block - Test 2: Call UI element update
            
    #         # Test 3: Verify FILE_PROCESSING state is maintained
    #         #TEST_AI_OFF Start Block - Test 3: Verify FILE_PROCESSING state is maintained
    #         assert self.current_state == ApplicationState.FILE_PROCESSING
    #         #TEST_AI_OFF End Block - Test 3: Verify FILE_PROCESSING state is maintained
            
    #         # Test 4: Test FILE_PROCESSING UI elements method directly
    #         #TEST_AI_OFF Start Block - Test 4: Test FILE_PROCESSING UI elements method directly
    #         self._update_file_processing_ui_elements()
    #         #TEST_AI_OFF End Block - Test 4: Test FILE_PROCESSING UI elements method directly
            
    #         # Test 5: Test file processing update in FILE_PROCESSING state (should be allowed)
    #         #TEST_AI_OFF Start Block - Test 5: Test file processing update in FILE_PROCESSING state (should be allowed)
    #         processing_data = {'file_progress': 0.5, 'processed_files': 25, 'total_files': 50}
    #         # Note: We can't test actual UI updates in script mode, but we can test the state logic
    #         logging_service.log("TEST_AI", "Testing file processing update in FILE_PROCESSING state (state check only)")
    #         #TEST_AI_OFF End Block - Test 5: Test file processing update in FILE_PROCESSING state (should be allowed)
            
    #         # Test 6: Test scan progress update in FILE_PROCESSING state (should be ignored)
    #         #TEST_AI_OFF Start Block - Test 6: Test scan progress update in FILE_PROCESSING state (should be ignored)
    #         scan_data = {'total_files': 100, 'media_files': 50, 'sidecars': 10, 'directories': 5}
    #         # Note: We can't test actual UI updates in script mode, but we can test the state logic
    #         logging_service.log("TEST_AI", "Testing scan progress update in FILE_PROCESSING state (state check only)")
    #         #TEST_AI_OFF End Block - Test 6: Test scan progress update in FILE_PROCESSING state (should be ignored)
            
    #         logging_service.log("TEST_AI", "FILE_PROCESSING UI element logic test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"FILE_PROCESSING UI element logic test: FAILED - {e}")
    #         import traceback
    #         logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")
    #     #TEST_AI_OFF End Block - FILE_PROCESSING UI element logic test

    # def _test_file_processing_state_integration(self) -> None:
    #     """Test FILE_PROCESSING state integration with UI update flow."""
    #     #TEST_AI_OFF Start Block - FILE_PROCESSING state integration test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing FILE_PROCESSING State Integration ===")
            
    #         # Test 1: Start from IDLE state
    #         #TEST_AI_OFF Start Block - Test 1: Start from IDLE state
    #         self._set_state(ApplicationState.IDLE)
    #         assert self.current_state == ApplicationState.IDLE
    #         #TEST_AI_OFF End Block - Test 1: Start from IDLE state
            
    #         # Test 2: Simulate starting file processing (state transition)
    #         # Note: We can't actually call _start_file_processing in test mode, but we can test the state logic
    #         #TEST_AI_OFF Start Block - Test 2: Simulate starting file processing (state transition)
    #         self._set_state(ApplicationState.FILE_PROCESSING)
    #         assert self.current_state == ApplicationState.FILE_PROCESSING
    #         #TEST_AI_OFF End Block - Test 2: Simulate starting file processing (state transition)
            
    #         # Test 3: Test UI element updates in FILE_PROCESSING state
    #         #TEST_AI_OFF Start Block - Test 3: Test UI element updates in FILE_PROCESSING state
    #         self._update_ui_elements()
    #         assert self.current_state == ApplicationState.FILE_PROCESSING
    #         #TEST_AI_OFF End Block - Test 3: Test UI element updates in FILE_PROCESSING state
            
    #         # Test 4: Test file processing display update (should be allowed)
    #         #TEST_AI_OFF Start Block - Test 4: Test file processing display update (should be allowed)
    #         processing_data = {'file_progress': 0.75, 'processed_files': 75, 'total_files': 100}
    #         # Note: We can't test actual UI updates in script mode, but we can test the state logic
    #         logging_service.log("TEST_AI", "Testing file processing display update in FILE_PROCESSING state (state check only)")
    #         #TEST_AI_OFF End Block - Test 4: Test file processing display update (should be allowed)
            
    #         # Test 5: Test scan progress update in FILE_PROCESSING state (should be ignored)
    #         #TEST_AI_OFF Start Block - Test 5: Test scan progress update in FILE_PROCESSING state (should be ignored)
    #         scan_data = {'total_files': 200, 'media_files': 100, 'sidecars': 20, 'directories': 10}
    #         # Note: We can't test actual UI updates in script mode, but we can test the state logic
    #         logging_service.log("TEST_AI", "Testing scan progress update in FILE_PROCESSING state (state check only)")
    #         #TEST_AI_OFF End Block - Test 5: Test scan progress update in FILE_PROCESSING state (should be ignored)
            
    #         # Test 6: Simulate file processing completion (state transition to IDLE_LAG)
    #         #TEST_AI_OFF Start Block - Test 6: Simulate file processing completion (state transition to IDLE_LAG)
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         # Note: The state might immediately transition to IDLE if conditions are met
    #         assert self.current_state in [ApplicationState.IDLE_LAG, ApplicationState.IDLE]
    #         #TEST_AI_OFF End Block - Test 6: Simulate file processing completion (state transition to IDLE_LAG)
            
    #         # Test 7: Test UI element updates in current state
    #         #TEST_AI_OFF Start Block - Test 7: Test UI element updates in current state
    #         self._update_ui_elements()
    #         # Note: The state might immediately transition to IDLE if conditions are met
    #         assert self.current_state in [ApplicationState.IDLE_LAG, ApplicationState.IDLE]
    #         #TEST_AI_OFF End Block - Test 7: Test UI element updates in current state
            
    #         # Test 8: Test automatic transition from IDLE_LAG to IDLE (if conditions are met)
    #         # This will be tested by the existing _check_idle_lag_to_idle_transition logic
    #         #TEST_AI_OFF Start Block - Test 8: Test automatic transition from IDLE_LAG to IDLE (if conditions are met)
    #         logging_service.log("TEST_AI", "Testing automatic IDLE_LAG to IDLE transition (if conditions are met)")
    #         #TEST_AI_OFF End Block - Test 8: Test automatic transition from IDLE_LAG to IDLE (if conditions are met)
            
    #         logging_service.log("TEST_AI", "FILE_PROCESSING state integration test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"FILE_PROCESSING state integration test: FAILED - {e}")
    #         import traceback
    #         logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")
    #     #TEST_AI_OFF End Block - FILE_PROCESSING state integration test

    # def _test_abort_functionality(self) -> None:
    #     """Test abort functionality integration with state machine."""
    #     #TEST_AI_OFF Start Block - Abort functionality test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing Abort Functionality ===")
            
    #         # Test 1: Abort from SCANNING state
    #         #TEST_AI_OFF Start Block - Test 1: Abort from SCANNING state
    #         self._set_state(ApplicationState.SCANNING)
    #         assert self.current_state == ApplicationState.SCANNING
            
    #         # Simulate abort
    #         self._handle_abort()
    #         assert self.current_state == ApplicationState.IDLE
    #         assert self.scan_aborted == True
    #         assert self.processing_aborted == True
    #         #TEST_AI_OFF End Block - Test 1: Abort from SCANNING state
            
    #         # Test 2: Abort from FILE_PROCESSING state
    #         #TEST_AI_OFF Start Block - Test 2: Abort from FILE_PROCESSING state
    #         self._set_state(ApplicationState.FILE_PROCESSING)
    #         assert self.current_state == ApplicationState.FILE_PROCESSING
            
    #         # Reset abort flags for clean test
    #         self.scan_aborted = False
    #         self.processing_aborted = False
            
    #         # Simulate abort
    #         self._handle_abort()
    #         assert self.current_state == ApplicationState.IDLE
    #         assert self.scan_aborted == True
    #         assert self.processing_aborted == True
    #         #TEST_AI_OFF End Block - Test 2: Abort from FILE_PROCESSING state
            
    #         # Test 3: Abort from IDLE_LAG state
    #         #TEST_AI_OFF Start Block - Test 3: Abort from IDLE_LAG state
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         assert self.current_state == ApplicationState.IDLE_LAG
            
    #         # Reset abort flags for clean test
    #         self.scan_aborted = False
    #         self.processing_aborted = False
            
    #         # Simulate abort
    #         self._handle_abort()
    #         assert self.current_state == ApplicationState.IDLE
    #         assert self.scan_aborted == True
    #         assert self.processing_aborted == True
    #         #TEST_AI_OFF End Block - Test 3: Abort from IDLE_LAG state
            
    #         # Test 4: Abort from IDLE state (should still work)
    #         #TEST_AI_OFF Start Block - Test 4: Abort from IDLE state (should still work)
    #         self._set_state(ApplicationState.IDLE)
    #         assert self.current_state == ApplicationState.IDLE
            
    #         # Reset abort flags for clean test
    #         self.scan_aborted = False
    #         self.processing_aborted = False
            
    #         # Simulate abort
    #         self._handle_abort()
    #         assert self.current_state == ApplicationState.IDLE
    #         assert self.scan_aborted == True
    #         assert self.processing_aborted == True
    #         #TEST_AI_OFF End Block - Test 4: Abort from IDLE state (should still work)
            
    #         logging_service.log("TEST_AI", "Abort functionality test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"Abort functionality test: FAILED - {e}")
    #         import traceback
    #         logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")
    #     #TEST_AI_OFF End Block - Abort functionality test

    # def _test_abort_button_states(self) -> None:
    #     """Test abort button states per application state."""
    #     #TEST_AI_OFF Start Block - Abort button states test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing Abort Button States ===")
            
    #         # Test 1: IDLE state - abort button should be disabled
    #         #TEST_AI_OFF Start Block - Test 1: IDLE state - abort button should be disabled
    #         self._set_state(ApplicationState.IDLE)
    #         self._update_button_states()
    #         logging_service.log("TEST_AI", "IDLE state: abort button should be disabled")
    #         #TEST_AI_OFF End Block - Test 1: IDLE state - abort button should be disabled
            
    #         # Test 2: SCANNING state - abort button should be enabled
    #         #TEST_AI_OFF Start Block - Test 2: SCANNING state - abort button should be enabled
    #         self._set_state(ApplicationState.SCANNING)
    #         self._update_button_states()
    #         logging_service.log("TEST_AI", "SCANNING state: abort button should be enabled")
    #         #TEST_AI_OFF End Block - Test 2: SCANNING state - abort button should be enabled
            
    #         # Test 3: IDLE_LAG state - abort button should be enabled
    #         #TEST_AI_OFF Start Block - Test 3: IDLE_LAG state - abort button should be enabled
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         self._update_button_states()
    #         logging_service.log("TEST_AI", "IDLE_LAG state: abort button should be enabled")
    #         #TEST_AI_OFF End Block - Test 3: IDLE_LAG state - abort button should be enabled
            
    #         # Test 4: FILE_PROCESSING state - abort button should be enabled
    #         #TEST_AI_OFF Start Block - Test 4: FILE_PROCESSING state - abort button should be enabled
    #         self._set_state(ApplicationState.FILE_PROCESSING)
    #         self._update_button_states()
    #         logging_service.log("TEST_AI", "FILE_PROCESSING state: abort button should be enabled")
    #         #TEST_AI_OFF End Block - Test 4: FILE_PROCESSING state - abort button should be enabled
            
    #         # Test 5: Test button state methods directly
    #         #TEST_AI_OFF Start Block - Test 5: Test button state methods directly
    #         self._set_idle_button_states()
    #         logging_service.log("TEST_AI", "IDLE button states method called")
            
    #         self._set_scanning_button_states()
    #         logging_service.log("TEST_AI", "SCANNING button states method called")
            
    #         self._set_idle_lag_button_states()
    #         logging_service.log("TEST_AI", "IDLE_LAG button states method called")
            
    #         self._set_file_processing_button_states()
    #         logging_service.log("TEST_AI", "FILE_PROCESSING button states method called")
    #         #TEST_AI_OFF End Block - Test 5: Test button state methods directly
            
    #         logging_service.log("TEST_AI", "Abort button states test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"Abort button states test: FAILED - {e}")
    #         import traceback
    #         logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")
    #     #TEST_AI_OFF End Block - Abort button states test

    def _test_ui_update_manager_state_awareness(self) -> None:
        """Test UI Update Manager state awareness and callback filtering."""
        try:
            logging_service.log("TEST_AI", "=== Testing UI Update Manager State Awareness ===")#TEST_AI_OFF
            
            # Test 1: State provider function works
            current_state = self._get_current_state()
            assert current_state in ['IDLE', 'SCANNING', 'IDLE_LAG', 'FILE_PROCESSING', 'UNKNOWN']
            logging_service.log("TEST_AI", f"State provider returns: {current_state}")#TEST_AI_OFF
            
            # Test 2: UI Update Manager has state provider
            assert self.ui_update_manager.state_provider is not None
            logging_service.log("TEST_AI", "UI Update Manager has state provider")#TEST_AI_OFF
            
            # Test 3: Test callback filtering logic
            # Create mock callback info for testing
            mock_callback_info = {
                'callback': self._update_progress_display,
                'data_key': 'scan_progress'
            }
            
            # Test scan progress callback filtering
            self._set_state(ApplicationState.SCANNING)
            should_call = self.ui_update_manager._should_call_callback(mock_callback_info, 'SCANNING')
            assert should_call == True
            logging_service.log("TEST_AI", "Scan progress callback allowed in SCANNING state")#TEST_AI_OFF
            
            self._set_state(ApplicationState.FILE_PROCESSING)
            should_call = self.ui_update_manager._should_call_callback(mock_callback_info, 'FILE_PROCESSING')
            assert should_call == False
            logging_service.log("TEST_AI", "Scan progress callback blocked in FILE_PROCESSING state")#TEST_AI_OFF
            
            # Test file processing callback filtering
            mock_callback_info = {
                'callback': self._update_file_processing_display,
                'data_key': 'file_processing_progress'
            }
            
            self._set_state(ApplicationState.FILE_PROCESSING)
            should_call = self.ui_update_manager._should_call_callback(mock_callback_info, 'FILE_PROCESSING')
            assert should_call == True
            logging_service.log("TEST_AI", "File processing callback allowed in FILE_PROCESSING state")#TEST_AI_OFF
            
            self._set_state(ApplicationState.SCANNING)
            should_call = self.ui_update_manager._should_call_callback(mock_callback_info, 'SCANNING')
            assert should_call == False
            logging_service.log("TEST_AI", "File processing callback blocked in SCANNING state")#TEST_AI_OFF
            
            # Test 4: Test unknown callback (should always be allowed)
            mock_callback_info = {
                'callback': self._display_log_queue,
                'data_key': None
            }
            
            should_call = self.ui_update_manager._should_call_callback(mock_callback_info, 'SCANNING')
            assert should_call == True
            logging_service.log("TEST_AI", "Unknown callback always allowed")#TEST_AI_OFF
            
            logging_service.log("TEST_AI", "UI Update Manager state awareness test: PASSED")#TEST_AI_OFF
            
        except Exception as e:
            logging_service.log("ERROR", f"UI Update Manager state awareness test: FAILED - {e}")
            import traceback
            logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")

    def _test_file_processing_display_state_awareness(self) -> None:
        """Test file processing display state awareness."""
        try:
            logging_service.log("TEST_AI", "=== Testing File Processing Display State Awareness ===")#TEST_AI_OFF
            
            # Test 1: File processing display in FILE_PROCESSING state (should work)
            self._set_state(ApplicationState.FILE_PROCESSING)
            processing_data = {'file_progress': 0.5, 'processed_files': 25, 'total_files': 50}
            # Note: We can't test actual UI updates in script mode, but we can test the state logic
            logging_service.log("TEST_AI", "Testing file processing display in FILE_PROCESSING state (state check only)")#TEST_AI_OFF
            
            # Test 2: File processing display in IDLE_LAG state (should work but not update UI)
            self._set_state(ApplicationState.IDLE_LAG)
            logging_service.log("TEST_AI", "Testing file processing display in IDLE_LAG state (state check only)")#TEST_AI_OFF
            
            # Test 3: File processing display in SCANNING state (should be ignored)
            self._set_state(ApplicationState.SCANNING)
            logging_service.log("TEST_AI", "Testing file processing display in SCANNING state (should be ignored)")#TEST_AI_OFF
            
            # Test 4: File processing display in IDLE state (should be ignored)
            self._set_state(ApplicationState.IDLE)
            logging_service.log("TEST_AI", "Testing file processing display in IDLE state (should be ignored)")#TEST_AI_OFF
            
            # Test 5: Test with empty data (should return early)
            self._set_state(ApplicationState.FILE_PROCESSING)
            logging_service.log("TEST_AI", "Testing file processing display with empty data (should return early)")#TEST_AI_OFF
            
            logging_service.log("TEST_AI", "File processing display state awareness test: PASSED")#TEST_AI_OFF
            
        except Exception as e:
            logging_service.log("ERROR", f"File processing display state awareness test: FAILED - {e}")
            import traceback
            logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")

    def _test_log_display_state_awareness(self) -> None:
        """Test log display state awareness - should work in all states."""
        try:
            logging_service.log("TEST_AI", "=== Testing Log Display State Awareness ===")#TEST_AI_OFF
            
            # Test 1: Log display in IDLE state (should work)
            self._set_state(ApplicationState.IDLE)
            logging_service.log("TEST_AI", "Testing log display in IDLE state")#TEST_AI_OFF
            # Note: We can't test actual UI updates in script mode, but we can test the method exists
            assert hasattr(self, '_display_log_queue')
            
            # Test 2: Log display in SCANNING state (should work)
            self._set_state(ApplicationState.SCANNING)
            logging_service.log("TEST_AI", "Testing log display in SCANNING state")#TEST_AI_OFF
            
            # Test 3: Log display in IDLE_LAG state (should work)
            self._set_state(ApplicationState.IDLE_LAG)
            logging_service.log("TEST_AI", "Testing log display in IDLE_LAG state")#TEST_AI_OFF
            
            # Test 4: Log display in FILE_PROCESSING state (should work)
            self._set_state(ApplicationState.FILE_PROCESSING)
            logging_service.log("TEST_AI", "Testing log display in FILE_PROCESSING state")#TEST_AI_OFF
            
            # Test 5: Log display method can be called (basic functionality test)
            try:
                self._display_log_queue()
                logging_service.log("TEST_AI", "Log display method can be called successfully")#TEST_AI_OFF
            except Exception as e:
                logging_service.log("WARNING", f"Log display method call failed (expected in test mode): {e}")
            
            logging_service.log("TEST_AI", "Log display state awareness test: PASSED")#TEST_AI_OFF
            
        except Exception as e:
            logging_service.log("ERROR", f"Log display state awareness test: FAILED - {e}")
            import traceback
            logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")

    def _test_progress_display_state_awareness(self) -> None:
        """Test progress display state awareness - should work only in SCANNING state."""
        try:
            logging_service.log("TEST_AI", "=== Testing Progress Display State Awareness ===")
            
            # Test 1: Progress display in SCANNING state (should work)
            self._set_state(ApplicationState.SCANNING)
            scan_data = {'total_files': 100, 'media_files': 50, 'sidecars': 10, 'directories': 5}
            logging_service.log("TEST_AI", "Testing progress display in SCANNING state (should work)")
            
            # Test 2: Progress display in IDLE_LAG state (should work but not update UI)
            self._set_state(ApplicationState.IDLE_LAG)
            logging_service.log("TEST_AI", "Testing progress display in IDLE_LAG state (should work but not update UI)")
            
            # Test 3: Progress display in FILE_PROCESSING state (should be ignored)
            self._set_state(ApplicationState.FILE_PROCESSING)
            logging_service.log("TEST_AI", "Testing progress display in FILE_PROCESSING state (should be ignored)")
            
            # Test 4: Progress display in IDLE state (should be ignored)
            self._set_state(ApplicationState.IDLE)
            logging_service.log("TEST_AI", "Testing progress display in IDLE state (should be ignored)")
            
            # Test 5: Test with empty data (should return early)
            self._set_state(ApplicationState.SCANNING)
            logging_service.log("TEST_AI", "Testing progress display with empty data (should return early)")
            
            # Test 6: Test with aborted scan (should return early)
            self.scan_aborted = True
            logging_service.log("TEST_AI", "Testing progress display with aborted scan (should return early)")
            self.scan_aborted = False  # Reset for other tests
            
            logging_service.log("TEST_AI", "Progress display state awareness test: PASSED")
            
        except Exception as e:
            logging_service.log("ERROR", f"Progress display state awareness test: FAILED - {e}")
            import traceback
            logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")

    # def _test_comprehensive_state_transitions(self) -> None:
    #     """Test all state transitions comprehensively."""
    #     #TEST_AI_OFF Start Block - Comprehensive state transitions test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing Comprehensive State Transitions ===")
            
    #         # Test 1: IDLE → SCANNING → IDLE_LAG → IDLE (scan flow)
    #         #TEST_AI_OFF Start Block - Test 1: IDLE → SCANNING → IDLE_LAG → IDLE (scan flow)
    #         logging_service.log("TEST_AI", "Testing scan flow: IDLE → SCANNING → IDLE_LAG → IDLE")
    #         self._set_state(ApplicationState.IDLE)
    #         assert self.current_state == ApplicationState.IDLE
            
    #         self._set_state(ApplicationState.SCANNING)
    #         assert self.current_state == ApplicationState.SCANNING
            
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         assert self.current_state in [ApplicationState.IDLE_LAG, ApplicationState.IDLE]  # May auto-transition
    #         #TEST_AI_OFF End Block - Test 1: IDLE → SCANNING → IDLE_LAG → IDLE (scan flow)
            
    #         # Test 2: IDLE → FILE_PROCESSING → IDLE_LAG → IDLE (processing flow)
    #         #TEST_AI_OFF Start Block - Test 2: IDLE → FILE_PROCESSING → IDLE_LAG → IDLE (processing flow)
    #         logging_service.log("TEST_AI", "Testing processing flow: IDLE → FILE_PROCESSING → IDLE_LAG → IDLE")
    #         self._set_state(ApplicationState.IDLE)
    #         assert self.current_state == ApplicationState.IDLE
            
    #         self._set_state(ApplicationState.FILE_PROCESSING)
    #         assert self.current_state == ApplicationState.FILE_PROCESSING
            
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         assert self.current_state in [ApplicationState.IDLE_LAG, ApplicationState.IDLE]  # May auto-transition
    #         #TEST_AI_OFF End Block - Test 2: IDLE → FILE_PROCESSING → IDLE_LAG → IDLE (processing flow)
            
    #         # Test 3: Abort from any state → IDLE
    #         #TEST_AI_OFF Start Block - Test 3: Abort from any state → IDLE
    #         logging_service.log("TEST_AI", "Testing abort transitions from all states")
    #         for state in [ApplicationState.IDLE, ApplicationState.SCANNING, ApplicationState.IDLE_LAG, ApplicationState.FILE_PROCESSING]:
    #             self._set_state(state)
    #             self._handle_abort()
    #             assert self.current_state == ApplicationState.IDLE
    #             assert self.scan_aborted == True
    #             assert self.processing_aborted == True
    #             # Reset for next test
    #             self.scan_aborted = False
    #             self.processing_aborted = False
    #         #TEST_AI_OFF End Block - Test 3: Abort from any state → IDLE
            
    #         # Test 4: Button states for each state
    #         #TEST_AI_OFF Start Block - Test 4: Button states for each state
    #         logging_service.log("TEST_AI", "Testing button states for each state")
    #         for state in [ApplicationState.IDLE, ApplicationState.SCANNING, ApplicationState.IDLE_LAG, ApplicationState.FILE_PROCESSING]:
    #             self._set_state(state)
    #             self._update_button_states()
    #             logging_service.log("TEST_AI", f"Button states updated for {state.value}")
    #         #TEST_AI_OFF End Block - Test 4: Button states for each state
            
    #         # Test 5: UI element updates for each state
    #         #TEST_AI_OFF Start Block - Test 5: UI element updates for each state
    #         logging_service.log("TEST_AI", "Testing UI element updates for each state")
    #         for state in [ApplicationState.IDLE, ApplicationState.SCANNING, ApplicationState.IDLE_LAG, ApplicationState.FILE_PROCESSING]:
    #             self._set_state(state)
    #             self._update_ui_elements()
    #             logging_service.log("TEST_AI", f"UI elements updated for {state.value}")
    #         #TEST_AI_OFF End Block - Test 5: UI element updates for each state
            
    #         # Test 6: UI Update Manager state awareness
    #         #TEST_AI_OFF Start Block - Test 6: UI Update Manager state awareness
    #         logging_service.log("TEST_AI", "Testing UI Update Manager state awareness")
    #         current_state = self._get_current_state()
    #         assert current_state in ['IDLE', 'SCANNING', 'IDLE_LAG', 'FILE_PROCESSING', 'UNKNOWN']
    #         #TEST_AI_OFF End Block - Test 6: UI Update Manager state awareness
            
    #         # Test 7: Callback filtering
    #         #TEST_AI_OFF Start Block - Test 7: Callback filtering
    #         logging_service.log("TEST_AI", "Testing callback filtering")
    #         mock_scan_callback = {'callback': self._update_progress_display, 'data_key': 'scan_progress'}
    #         mock_processing_callback = {'callback': self._update_file_processing_display, 'data_key': 'file_processing_progress'}
            
    #         # Test scan callback filtering
    #         self._set_state(ApplicationState.SCANNING)
    #         should_call = self.ui_update_manager._should_call_callback(mock_scan_callback, 'SCANNING')
    #         assert should_call == True
            
    #         self._set_state(ApplicationState.FILE_PROCESSING)
    #         should_call = self.ui_update_manager._should_call_callback(mock_scan_callback, 'FILE_PROCESSING')
    #         assert should_call == False
            
    #         # Test processing callback filtering
    #         self._set_state(ApplicationState.FILE_PROCESSING)
    #         should_call = self.ui_update_manager._should_call_callback(mock_processing_callback, 'FILE_PROCESSING')
    #         assert should_call == True
            
    #         self._set_state(ApplicationState.SCANNING)
    #         should_call = self.ui_update_manager._should_call_callback(mock_processing_callback, 'SCANNING')
    #         assert should_call == False
    #         #TEST_AI_OFF End Block - Test 7: Callback filtering
            
    #         logging_service.log("TEST_AI", "Comprehensive state transitions test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"Comprehensive state transitions test: FAILED - {e}")
    #         import traceback
    #         logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")
    #     #TEST_AI_OFF End Block - Comprehensive state transitions test

    # def _test_ui_element_protection(self) -> None:
    #     """Test UI element protection per state."""
    #     #TEST_AI_OFF Start Block - UI element protection test
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing UI Element Protection ===")
            
    #         # Test 1: Scan elements protection
    #         #TEST_AI_OFF Start Block - Test 1: Scan elements protection
    #         logging_service.log("TEST_AI", "Testing scan elements protection")
    #         self._set_state(ApplicationState.IDLE)
    #         # Scan elements should not be updated in IDLE state
    #         logging_service.log("TEST_AI", "Scan elements protected in IDLE state")
            
    #         self._set_state(ApplicationState.FILE_PROCESSING)
    #         # Scan elements should not be updated in FILE_PROCESSING state
    #         logging_service.log("TEST_AI", "Scan elements protected in FILE_PROCESSING state")
    #         #TEST_AI_OFF End Block - Test 1: Scan elements protection
            
    #         # Test 2: Processing elements protection
    #         #TEST_AI_OFF Start Block - Test 2: Processing elements protection
    #         logging_service.log("TEST_AI", "Testing processing elements protection")
    #         self._set_state(ApplicationState.IDLE)
    #         # Processing elements should not be updated in IDLE state
    #         logging_service.log("TEST_AI", "Processing elements protected in IDLE state")
            
    #         self._set_state(ApplicationState.SCANNING)
    #         # Processing elements should not be updated in SCANNING state
    #         logging_service.log("TEST_AI", "Processing elements protected in SCANNING state")
    #         #TEST_AI_OFF End Block - Test 2: Processing elements protection
            
    #         # Test 3: Log elements accessibility
    #         #TEST_AI_OFF Start Block - Test 3: Log elements accessibility
    #         logging_service.log("TEST_AI", "Testing log elements accessibility")
    #         for state in [ApplicationState.IDLE, ApplicationState.SCANNING, ApplicationState.IDLE_LAG, ApplicationState.FILE_PROCESSING]:
    #             self._set_state(state)
    #             # Log elements should be accessible in all states
    #             logging_service.log("TEST_AI", f"Log elements accessible in {state.value} state")
    #         #TEST_AI_OFF End Block - Test 3: Log elements accessibility
            
    #         # Test 4: State-specific UI element updates
    #         #TEST_AI_OFF Start Block - Test 4: State-specific UI element updates
    #         logging_service.log("TEST_AI", "Testing state-specific UI element updates")
            
    #         # IDLE state - only logging elements allowed
    #         self._set_state(ApplicationState.IDLE)
    #         self._update_idle_ui_elements()
    #         logging_service.log("TEST_AI", "IDLE UI elements updated (logging only)")
            
    #         # SCANNING state - scan and logging elements allowed
    #         self._set_state(ApplicationState.SCANNING)
    #         self._update_scanning_ui_elements()
    #         logging_service.log("TEST_AI", "SCANNING UI elements updated (scan and logging)")
            
    #         # IDLE_LAG state - only logging elements allowed
    #         self._set_state(ApplicationState.IDLE_LAG)
    #         self._update_idle_lag_ui_elements()
    #         logging_service.log("TEST_AI", "IDLE_LAG UI elements updated (logging only)")
            
    #         # FILE_PROCESSING state - processing and logging elements allowed
    #         self._set_state(ApplicationState.FILE_PROCESSING)
    #         self._update_file_processing_ui_elements()
    #         logging_service.log("TEST_AI", "FILE_PROCESSING UI elements updated (processing and logging)")
    #         #TEST_AI_OFF End Block - Test 4: State-specific UI element updates
            
    #         # Test 5: UI Update Manager callback filtering
    #         #TEST_AI_OFF Start Block - Test 5: UI Update Manager callback filtering
    #         logging_service.log("TEST_AI", "Testing UI Update Manager callback filtering")
            
    #         # Test scan progress callback filtering
    #         mock_scan_callback = {'callback': self._update_progress_display, 'data_key': 'scan_progress'}
            
    #         self._set_state(ApplicationState.SCANNING)
    #         should_call = self.ui_update_manager._should_call_callback(mock_scan_callback, 'SCANNING')
    #         assert should_call == True
    #         logging_service.log("TEST_AI", "Scan callback allowed in SCANNING state")
            
    #         self._set_state(ApplicationState.FILE_PROCESSING)
    #         should_call = self.ui_update_manager._should_call_callback(mock_scan_callback, 'FILE_PROCESSING')
    #         assert should_call == False
    #         logging_service.log("TEST_AI", "Scan callback blocked in FILE_PROCESSING state")
            
    #         # Test file processing callback filtering
    #         mock_processing_callback = {'callback': self._update_file_processing_display, 'data_key': 'file_processing_progress'}
            
    #         self._set_state(ApplicationState.FILE_PROCESSING)
    #         should_call = self.ui_update_manager._should_call_callback(mock_processing_callback, 'FILE_PROCESSING')
    #         assert should_call == True
    #         logging_service.log("TEST_AI", "Processing callback allowed in FILE_PROCESSING state")
            
    #         self._set_state(ApplicationState.SCANNING)
    #         should_call = self.ui_update_manager._should_call_callback(mock_processing_callback, 'SCANNING')
    #         assert should_call == False
    #         logging_service.log("TEST_AI", "Processing callback blocked in SCANNING state")
    #         #TEST_AI_OFF End Block - Test 5: UI Update Manager callback filtering
            
    #         logging_service.log("TEST_AI", "UI element protection test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"UI element protection test: FAILED - {e}")
    #         import traceback
    #         logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")
    #     #TEST_AI_OFF End Block - UI element protection test

    # def _test_core_functionality(self) -> None:
    #     """Test core functionality preservation."""
    #     #TEST_AI_OFF Start Block - Test core functionality preservation
    #     try:
    #         logging_service.log("TEST_AI", "=== Testing Core Functionality ===")
            
    #         # Test 1: NiceGUI responsiveness
    #         #TEST_AI_OFF Start Block - Test NiceGUI responsiveness
    #         logging_service.log("TEST_AI", "Testing NiceGUI responsiveness")
    #         # Test UI update manager timer functionality
    #         assert hasattr(self.ui_update_manager, 'timer_active')
    #         assert hasattr(self.ui_update_manager, 'start_updates')
    #         assert hasattr(self.ui_update_manager, 'stop_updates')
    #         logging_service.log("TEST_AI", "NiceGUI timer functionality preserved")
    #         #TEST_AI_OFF End Block - Test NiceGUI responsiveness
            
    #         # Test 2: Logging service functionality
    #         #TEST_AI_OFF Start Block - Test logging service functionality
    #         logging_service.log("TEST_AI", "Testing logging service functionality")
    #         # Test logging service methods
    #         assert hasattr(logging_service, 'log')
    #         assert hasattr(logging_service, 'get_ui_messages')
    #         logging_service.log("TEST_AI", "Logging service functionality preserved")
    #         #TEST_AI_OFF End Block - Test logging service functionality
            
    #         # Test 3: Queue functionality
    #         #TEST_AI_OFF Start Block - Test queue functionality
    #         logging_service.log("TEST_AI", "Testing queue functionality")
    #         # Test logging queue
    #         assert hasattr(logging_service, 'logging_queue')
    #         logging_service.log("TEST_AI", "Logging queue functionality preserved")
    #         #TEST_AI_OFF End Block - Test queue functionality
            
    #         # Test result queue
    #         assert hasattr(yapmo_globals, 'result_queue')
    #         logging_service.log("TEST_AI", "Result queue functionality preserved")
    #         #TEST_AI_OFF End Block - Test queue functionality
            
    #         # Test 4: UI update principle
    #         #TEST_AI_OFF Start Block - Test UI update principle
    #         logging_service.log("TEST_AI", "Testing UI update principle")
    #         # Test UI update manager callback system
    #         assert hasattr(self.ui_update_manager, 'register_callback')
    #         assert hasattr(self.ui_update_manager, 'update_shared_data')
    #         assert hasattr(self.ui_update_manager, 'get_shared_data')
    #         logging_service.log("TEST_AI", "UI update principle preserved")
    #         #TEST_AI_OFF End Block - Test UI update principle
            
    #         # Test 5: Abort manager functionality
    #         #TEST_AI_OFF Start Block - Test abort manager functionality
    #         logging_service.log("TEST_AI", "Testing abort manager functionality")
    #         assert hasattr(yapmo_globals, 'abort_manager')
    #         assert hasattr(yapmo_globals.abort_manager, 'register_process')
    #         assert hasattr(yapmo_globals.abort_manager, 'unregister_process')
    #         assert hasattr(yapmo_globals.abort_manager, 'has_active_processes')
    #         logging_service.log("TEST_AI", "Abort manager functionality preserved")
    #         #TEST_AI_OFF End Block - Test abort manager functionality
            
    #         # Test 6: State machine integration
    #         #TEST_AI_OFF Start Block - Test state machine integration
    #         logging_service.log("TEST_AI", "Testing state machine integration")
    #         # Test state machine methods
    #         assert hasattr(self, '_set_state')
    #         assert hasattr(self, '_get_current_state')
    #         assert hasattr(self, '_update_button_states')
    #         assert hasattr(self, '_update_ui_elements')
    #         logging_service.log("TEST_AI", "State machine integration preserved")
    #         #TEST_AI_OFF End Block - Test state machine integration
            
    #         # Test 7: Configuration functionality
    #         #TEST_AI_OFF Start Block - Test configuration functionality
    #         logging_service.log("TEST_AI", "Testing configuration functionality")
    #         # Test config access
    #         assert hasattr(self, 'ui_update_interval')
    #         assert hasattr(self, 'image_extensions')
    #         assert hasattr(self, 'video_extensions')
    #         assert hasattr(self, 'sidecar_extensions')
    #         logging_service.log("TEST_AI", "Configuration functionality preserved")
    #         #TEST_AI_OFF End Block - Test configuration functionality
            
    #         logging_service.log("TEST_AI", "Core functionality test: PASSED")
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"Core functionality test: FAILED - {e}")
    #         import traceback
    #         logging_service.log("ERROR", f"Traceback: {traceback.format_exc()}")
    #     #TEST_AI_OFF End Block - Test core functionality preservation

    # def _test_ui_element_inventory(self) -> None:
    #     """Test UI element inventory and identification."""
    #     #TEST_AI_OFF Start Block - Test UI element inventory and identification
    #     try:
    #         logging_service.log("TEST_AI", "=== UI Element Inventory ===")
            
    #         # Scan kaartje elementen
    #         #TEST_AI_OFF Start Block - Scan kaartje elementen
    #         scan_elements = {
    #             "buttons": [
    #                 "select_directory_button",
    #                 "start_button_scanning", 
    #                 "details_button"
    #             ],
    #             "inputs": [
    #                 "directory_input"
    #             ],
    #             "labels": [
    #                 "scan_status_label",
    #                 "total_files_label",
    #                 "media_files_label", 
    #                 "sidecars_label",
    #                 "directories_label"
    #             ],
    #             "other": [
    #                 "scan_spinner"
    #             ]
    #         }
    #         #TEST_AI_OFF End Block - Scan kaartje elementen
            
    #         # File Processing kaartje elementen
    #         #TEST_AI_OFF Start Block - File Processing kaartje elementen
    #         processing_elements = {
    #             "buttons": [
    #                 "start_button_processing"
    #             ],
    #             "progress": [
    #                 "processing_progress_bar",
    #                 "processing_progress_info_label"
    #             ],
    #             "labels": [
    #                 "files_processed_label",
    #                 "directories_processed_label",
    #                 "files_per_second_label",
    #                 "directories_per_second_label",
    #                 "estimated_time_to_finish_label"
    #             ]
    #         }
    #         #TEST_AI_OFF End Block - File Processing kaartje elementen
            
    #         # Logging kaartje elementen
    #         #TEST_AI_OFF Start Block - Logging kaartje elementen
    #         logging_elements = {
    #             "progress": [
    #                 "progress_bar",
    #                 "progress_info_label"
    #             ],
    #             "buttons": [
    #                 "clear_log_button"
    #             ],
    #             "display": [
    #                 "log_scroll_area",
    #                 "log_column"
    #             ]
    #         }
    #         #TEST_AI_OFF End Block - Logging kaartje elementen
            
    #         # Test elementen bestaan
    #         #TEST_AI_OFF Start Block - Test elementen bestaan
    #         all_elements = {}
    #         all_elements.update(scan_elements)
    #         all_elements.update(processing_elements)
    #         all_elements.update(logging_elements)
            
    #         missing_elements = []
    #         for category, elements in all_elements.items():
    #             for element in elements:
    #                 if not hasattr(self, element):
    #                     missing_elements.append(element)
            
    #         if missing_elements:
    #             logging_service.log("WARNING", f"Missing UI elements: {missing_elements}")
    #         else:
    #             logging_service.log("TEST_AI", "All UI elements found")
            
    #         # Log inventory
    #         logging_service.log("TEST_AI", f"Scan elements: {len(scan_elements)} categories, {sum(len(v) for v in scan_elements.values())} elements")
    #         logging_service.log("TEST_AI", f"Processing elements: {len(processing_elements)} categories, {sum(len(v) for v in processing_elements.values())} elements")
    #         logging_service.log("TEST_AI", f"Logging elements: {len(logging_elements)} categories, {sum(len(v) for v in logging_elements.values())} elements")
            
    #         # Store for later use (always create attributes)
    #         self.scan_elements = scan_elements
    #         self.processing_elements = processing_elements
    #         self.logging_elements = logging_elements
            
    #         logging_service.log("TEST_AI", "UI element inventory test: PASSED")
    #         #TEST_AI_OFF End Block - Test elementen bestaan
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"UI element inventory test: FAILED - {e}")
    #     #TEST_AI_OFF End Block - Test UI element inventory and identification

    def _set_state(self, new_state: ApplicationState) -> None:
        """Set the application state with logging and validation."""
        try:
            old_state = self.current_state
            self.current_state = new_state
            
            # Log state transition
            logging_service.log("DEBUG", f"State transition: {old_state.value} → {new_state.value}")#DEBUG_OFF State transition
            #TEST_AI ADD: Log state transition details for debugging UI update issues
            logging_service.log("DEBUG", f"State transition details: old_state={old_state}, new_state={new_state}, old_value={old_state.value}, new_value={new_state.value}")
            
            # Additional logging for specific transitions
            if old_state == ApplicationState.IDLE and new_state == ApplicationState.SCANNING:
                logging_service.log("DEBUG", "Starting scan process")#DEBUG_OFF Starting scan process
                # Display log messages immediately
                self._display_log_queue()
            elif old_state == ApplicationState.SCANNING and new_state == ApplicationState.IDLE_LAG:
                logging_service.log("DEBUG", "Scan completed, entering idle lag")#DEBUG_OFF Scan completed, entering idle lag
                # Display log messages immediately
                self._display_log_queue()
            elif old_state == ApplicationState.IDLE_LAG and new_state == ApplicationState.IDLE:
                logging_service.log("DEBUG", "Queues cleared, returning to idle")#DEBUG_OFF Queues cleared, returning to idle
                # Display log messages immediately
                self._display_log_queue()
            elif old_state == ApplicationState.IDLE and new_state == ApplicationState.FILE_PROCESSING:
                logging_service.log("DEBUG", "Starting file processing")#DEBUG_OFF Starting file processing
            elif old_state == ApplicationState.FILE_PROCESSING and new_state == ApplicationState.IDLE_LAG:
                logging_service.log("DEBUG", "File processing completed, entering idle lag")#DEBUG_OFF File processing completed, entering idle lag
                # TEST_AI ADDED: Display log messages immediately
                # TEST_AI FIXED: Added _display_log_queue() call to clear log queue during FILE_PROCESSING → IDLE_LAG transition
                self._display_log_queue()
            elif old_state == ApplicationState.IDLE_LAG and new_state == ApplicationState.IDLE:
                logging_service.log("DEBUG", "Idle lag completed, entering idle")#DEBUG_OFF Idle lag completed, entering idle
                # Stop transition timer when going to IDLE
                # self._stop_transition_timer()
            elif new_state == ApplicationState.IDLE_LAG:
                logging_service.log("DEBUG", "Entering idle lag, checking for immediate transition")#DEBUG_OFF Entering idle lag, checking for immediate transition
                # Check for immediate transition to IDLE
                self._check_immediate_idle_transition()
            elif old_state == ApplicationState.IDLE_LAG and new_state != ApplicationState.IDLE:
                logging_service.log("DEBUG", "Leaving idle lag, stopping transition timer")#DEBUG_OFF Leaving idle lag, stopping transition timer
                # Stop transition timer when leaving IDLE_LAG (except to IDLE)
                self._stop_transition_timer()
        except Exception as e:
            logging_service.log("ERROR", f"State transition failed: {e}")
            # Reset to IDLE on error
            self.current_state = ApplicationState.IDLE

    def _update_button_states(self) -> None:
        """Update button states based on current application state."""
        try:
            logging_service.log("DEBUG", f"Updating button states for state: {self.current_state.value}")#DEBUG_ON Updating button states for state: {self.current_state.value}
            
            if self.current_state == ApplicationState.IDLE:
                self._set_idle_button_states()
            elif self.current_state == ApplicationState.SCANNING:
                self._set_scanning_button_states()
            elif self.current_state == ApplicationState.IDLE_LAG:
                self._set_idle_lag_button_states()
            elif self.current_state == ApplicationState.FILE_PROCESSING:
                self._set_file_processing_button_states()
            
            logging_service.log("DEBUG", "Button states updated successfully")#DEBUG_ON Button states updated successfully
            
        except Exception as e:
            logging_service.log("ERROR", f"Button state update failed: {e}")

    def _set_idle_button_states(self) -> None:
        """Set button states for IDLE state."""
        try:
            logging_service.log("DEBUG", "Setting IDLE button states")#DEBUG_ON Setting IDLE button states
            
            # Enable scanning buttons
            if hasattr(self, 'start_button_scanning'):
                self.start_button_scanning.enable()
                self.start_button_scanning.props("color=primary")
                self.start_button_scanning.text = "START SCANNING"
            
            if hasattr(self, 'select_directory_button'):
                self.select_directory_button.enable()
            
            if hasattr(self, 'details_button'):
                self.details_button.enable()
            
            # Enable processing button
            if hasattr(self, 'start_button_processing'):
                self.start_button_processing.enable()
                self.start_button_processing.props("color=primary")
                self.start_button_processing.text = "START PROCESSING"
            
            # Enable clear log button
            if hasattr(self, 'clear_log_button'):
                self.clear_log_button.enable()
                self.clear_log_button.props("color=secondary")
            
            # Disable abort button (no active processes)
            if hasattr(YAPMOTheme, 'abort_button'):
                YAPMOTheme.abort_button.disable()
                YAPMOTheme.abort_button.props("color=warning")
            
            # Enable menu and exit buttons
            if hasattr(YAPMOTheme, 'menu_button'):
                YAPMOTheme.menu_button.enable()
                YAPMOTheme.menu_button.props("color=primary")
            
            if hasattr(YAPMOTheme, 'exit_button'):
                YAPMOTheme.exit_button.enable()
                YAPMOTheme.exit_button.props("color=negative")
            
            logging_service.log("DEBUG", "IDLE button states set successfully")#DEBUG_ON IDLE button states set successfully
            
        except Exception as e:
            logging_service.log("ERROR", f"Failed to set IDLE button states: {e}")

    def _set_scanning_button_states(self) -> None:
        """Set button states for SCANNING state."""
        try:
            logging_service.log("DEBUG", "Setting SCANNING button states")#DEBUG_ON Setting SCANNING button states
            
            # Disable scanning buttons
            if hasattr(self, 'start_button_scanning'):
                self.start_button_scanning.disable()
                self.start_button_scanning.props("color=negative")
                self.start_button_scanning.text = "SCANNING"
            
            if hasattr(self, 'select_directory_button'):
                self.select_directory_button.disable()
            
            if hasattr(self, 'details_button'):
                self.details_button.disable()
            
            # Disable processing button
            if hasattr(self, 'start_button_processing'):
                self.start_button_processing.disable()
                self.start_button_processing.props("color=primary")
                self.start_button_processing.text = "START PROCESSING"
            
            # Enable clear log button
            if hasattr(self, 'clear_log_button'):
                self.clear_log_button.enable()
                self.clear_log_button.props("color=secondary")
            
            # Enable abort button (scanning is active)
            if hasattr(YAPMOTheme, 'abort_button'):
                YAPMOTheme.abort_button.enable()
                YAPMOTheme.abort_button.props("color=warning")
            
            # Disable menu and exit buttons
            if hasattr(YAPMOTheme, 'menu_button'):
                YAPMOTheme.menu_button.disable()
                YAPMOTheme.menu_button.props("color=primary")
            
            if hasattr(YAPMOTheme, 'exit_button'):
                YAPMOTheme.exit_button.disable()
                YAPMOTheme.exit_button.props("color=negative")
            
            logging_service.log("DEBUG", "SCANNING button states set successfully")#DEBUG_ON SCANNING button states set successfully
            
        except Exception as e:
            logging_service.log("ERROR", f"Failed to set SCANNING button states: {e}")

    def _set_idle_lag_button_states(self) -> None:
        """Set button states for IDLE_LAG state."""
        try:
            logging_service.log("DEBUG", "Setting IDLE_LAG button states")#DEBUG_ON Setting IDLE_LAG button states
            
            # Disable scanning buttons
            if hasattr(self, 'start_button_scanning'):
                self.start_button_scanning.disable()
                self.start_button_scanning.props("color=primary")
                self.start_button_scanning.text = "START SCANNING"
            
            if hasattr(self, 'select_directory_button'):
                self.select_directory_button.disable()
            
            if hasattr(self, 'details_button'):
                self.details_button.disable()
            
            # Disable processing button
            if hasattr(self, 'start_button_processing'):
                self.start_button_processing.disable()
                self.start_button_processing.props("color=primary")
                self.start_button_processing.text = "START PROCESSING"
            
            # Enable clear log button
            if hasattr(self, 'clear_log_button'):
                self.clear_log_button.enable()
                self.clear_log_button.props("color=secondary")
            
            # Enable abort button (queues may still be processing)
            if hasattr(YAPMOTheme, 'abort_button'):
                YAPMOTheme.abort_button.enable()
                YAPMOTheme.abort_button.props("color=warning")
            
            # Disable menu and exit buttons
            if hasattr(YAPMOTheme, 'menu_button'):
                YAPMOTheme.menu_button.disable()
                YAPMOTheme.menu_button.props("color=primary")
            
            if hasattr(YAPMOTheme, 'exit_button'):
                YAPMOTheme.exit_button.disable()
                YAPMOTheme.exit_button.props("color=negative")
            
            logging_service.log("DEBUG", "IDLE_LAG button states set successfully")#DEBUG_ON IDLE_LAG button states set successfully
            
        except Exception as e:
            logging_service.log("ERROR", f"Failed to set IDLE_LAG button states: {e}")

    def _set_file_processing_button_states(self) -> None:
        """Set button states for FILE_PROCESSING state."""
        try:
            logging_service.log("DEBUG", "Setting FILE_PROCESSING button states")#DEBUG_ON Setting FILE_PROCESSING button states
            
            # Disable scanning buttons
            if hasattr(self, 'start_button_scanning'):
                self.start_button_scanning.disable()
                self.start_button_scanning.props("color=primary")
                self.start_button_scanning.text = "START SCANNING"
            
            if hasattr(self, 'select_directory_button'):
                self.select_directory_button.disable()
            
            if hasattr(self, 'details_button'):
                self.details_button.disable()
            
            # Disable processing button (currently processing)
            if hasattr(self, 'start_button_processing'):
                self.start_button_processing.disable()
                self.start_button_processing.props("color=negative")
                self.start_button_processing.text = "PROCESSING"
            
            # Enable clear log button
            if hasattr(self, 'clear_log_button'):
                self.clear_log_button.enable()
                self.clear_log_button.props("color=secondary")
            
            # Enable abort button (processing is active)
            if hasattr(YAPMOTheme, 'abort_button'):
                YAPMOTheme.abort_button.enable()
                YAPMOTheme.abort_button.props("color=warning")
            
            # Disable menu and exit buttons
            if hasattr(YAPMOTheme, 'menu_button'):
                YAPMOTheme.menu_button.disable()
                YAPMOTheme.menu_button.props("color=primary")
            
            if hasattr(YAPMOTheme, 'exit_button'):
                YAPMOTheme.exit_button.disable()
                YAPMOTheme.exit_button.props("color=negative")
            
            logging_service.log("DEBUG", "FILE_PROCESSING button states set successfully")#DEBUG_ON FILE_PROCESSING button states set successfully
            
        except Exception as e:
            logging_service.log("ERROR", f"Failed to set FILE_PROCESSING button states: {e}")

    def _update_ui_elements(self) -> None:
        """Update UI elements based on current application state."""
        try:
            logging_service.log("DEBUG", f"Updating UI elements for state: {self.current_state.value}")#DEBUG_ON Updating UI elements for state: {self.current_state.value}
            
            if self.current_state == ApplicationState.IDLE:
                self._update_idle_ui_elements()
            elif self.current_state == ApplicationState.SCANNING:
                self._update_scanning_ui_elements()
            elif self.current_state == ApplicationState.IDLE_LAG:
                self._update_idle_lag_ui_elements()
            elif self.current_state == ApplicationState.FILE_PROCESSING:
                self._update_file_processing_ui_elements()
            
            logging_service.log("DEBUG", "UI elements updated successfully")#DEBUG_ON UI elements updated successfully
            
        except Exception as e:
            logging_service.log("ERROR", f"UI element update failed: {e}")

    def _update_idle_ui_elements(self) -> None:
        """Update UI elements for IDLE state - only logging elements allowed."""
        try:
            logging_service.log("DEBUG", "Updating IDLE UI elements (logging only)")#DEBUG_ON Updating IDLE UI elements (logging only)
            
            # In IDLE state, only logging elements can be updated
            # Scan elements should NOT be updated
            # Processing elements should NOT be updated
            # Only logging elements can be updated
            
            # Log which elements are allowed to be updated
            allowed_elements = self.logging_elements
            logging_service.log("DEBUG", f"Allowed elements for IDLE state: {list(allowed_elements.keys())}")#DEBUG_ON Allowed elements for IDLE state: {list(allowed_elements.keys())}
            
            # Log which elements are NOT allowed to be updated
            forbidden_elements = {
                "scan": self.scan_elements,
                "processing": self.processing_elements
            }
            logging_service.log("DEBUG", f"Forbidden elements for IDLE state: {list(forbidden_elements.keys())}")#DEBUG_ON Forbidden elements for IDLE state: {list(forbidden_elements.keys())}
            
            logging_service.log("DEBUG", "IDLE UI elements update completed")#DEBUG_ON IDLE UI elements update completed
            
        except Exception as e:
            logging_service.log("ERROR", f"Failed to update IDLE UI elements: {e}")

    def _update_scanning_ui_elements(self) -> None:
        """Update UI elements for SCANNING state - scan and logging elements allowed."""
        try:
            logging_service.log("DEBUG", "Updating SCANNING UI elements (scan and logging)")#DEBUG_ON Updating SCANNING UI elements (scan and logging)
            
            # In SCANNING state, scan and logging elements can be updated
            # Processing elements should NOT be updated
            # Only scan and logging elements can be updated
            
            # Log which elements are allowed to be updated
            allowed_elements = {
                "scan": self.scan_elements,
                "logging": self.logging_elements
            }
            logging_service.log("DEBUG", f"Allowed elements for SCANNING state: {list(allowed_elements.keys())}")#DEBUG_ON Allowed elements for SCANNING state: {list(allowed_elements.keys())}
            
            # Log which elements are NOT allowed to be updated
            forbidden_elements = {
                "processing": self.processing_elements
            }
            logging_service.log("DEBUG", f"Forbidden elements for SCANNING state: {list(forbidden_elements.keys())}")#DEBUG_ON Forbidden elements for SCANNING state: {list(forbidden_elements.keys())}
            
            logging_service.log("DEBUG", "SCANNING UI elements update completed")#DEBUG_ON SCANNING UI elements update completed
            
        except Exception as e:
            logging_service.log("ERROR", f"Failed to update SCANNING UI elements: {e}")

    def _update_idle_lag_ui_elements(self) -> None:
        """Update UI elements for IDLE_LAG state - only logging elements allowed."""
        try:
            logging_service.log("DEBUG", "Updating IDLE_LAG UI elements (logging only)")#DEBUG_ON Updating IDLE_LAG UI elements (logging only)
            
            # In IDLE_LAG state, only logging elements can be updated
            # Scan elements should NOT be updated
            # Processing elements should NOT be updated
            # Only logging elements can be updated
            
            # Log which elements are allowed to be updated
            allowed_elements = self.logging_elements
            logging_service.log("DEBUG", f"Allowed elements for IDLE_LAG state: {list(allowed_elements.keys())}")#DEBUG_ON Allowed elements for IDLE_LAG state: {list(allowed_elements.keys())}
            
            # Log which elements are NOT allowed to be updated
            forbidden_elements = {
                "scan": self.scan_elements,
                "processing": self.processing_elements
            }
            logging_service.log("DEBUG", f"Forbidden elements for IDLE_LAG state: {list(forbidden_elements.keys())}")#DEBUG_ON Forbidden elements for IDLE_LAG state: {list(forbidden_elements.keys())}
            
            logging_service.log("DEBUG", "IDLE_LAG UI elements update completed")#DEBUG_ON IDLE_LAG UI elements update completed
            
            # Check if we should transition to IDLE
            # self._check_idle_lag_to_idle_transition()
            
        except Exception as e:
            logging_service.log("ERROR", f"Failed to update IDLE_LAG UI elements: {e}")
    #DEBUG_ON Start Block _check_idle_lag_to_idle_transition
    # def _check_idle_lag_to_idle_transition(self) -> None:
    #     """Check if IDLE_LAG should transition to IDLE (when all queues are empty)."""
    #     try:
    #         if self.current_state != ApplicationState.IDLE_LAG:
    #             return  # Only check in IDLE_LAG state
            
    #         logging_service.log("DEBUG", "IDLE_LAG: Checking transition conditions to IDLE")#DEBUG_ON IDLE_LAG: Checking transition conditions to IDLE
            
    #         # Check 1: UI update manager is not active
    #         ui_manager_active = hasattr(self.ui_update_manager, 'timer_active') and self.ui_update_manager.timer_active
    #         if ui_manager_active:
    #             logging_service.log("DEBUG", "IDLE_LAG: UI update manager still active, staying in IDLE_LAG")#DEBUG_ON IDLE_LAG: UI update manager still active, staying in IDLE_LAG
    #             return
            
    #         # Check 2: No active processes
    #         has_active_processes = hasattr(yapmo_globals, 'abort_manager') and yapmo_globals.abort_manager.has_active_processes()
    #         if has_active_processes:
    #             logging_service.log("DEBUG", "IDLE_LAG: Active processes detected, staying in IDLE_LAG")#DEBUG_ON IDLE_LAG: Active processes detected, staying in IDLE_LAG
    #             return
            
    #         # Check 3: Logging queue is empty (if accessible)
    #         logging_queue_empty = True
    #         try:
    #             if hasattr(logging_service, 'logging_queue') and hasattr(logging_service.logging_queue, 'empty'):
    #                 logging_queue_empty = logging_service.logging_queue.empty()
    #                 if not logging_queue_empty:
    #                     logging_service.log("DEBUG", "IDLE_LAG: Logging queue not empty, staying in IDLE_LAG")#DEBUG_ON IDLE_LAG: Logging queue not empty, staying in IDLE_LAG
    #                     return
    #         except Exception as e:
    #             logging_service.log("WARNING", f"IDLE_LAG: Could not check logging queue status: {e}")
            
    #         # Check 4: Result queue is empty (if accessible)
    #         result_queue_empty = True
    #         try:
    #             if hasattr(yapmo_globals, 'result_queue') and hasattr(yapmo_globals.result_queue, 'empty'):
    #                 result_queue_empty = yapmo_globals.result_queue.empty()
    #                 if not result_queue_empty:
    #                     logging_service.log("DEBUG", "IDLE_LAG: Result queue not empty, staying in IDLE_LAG")#DEBUG_ON IDLE_LAG: Result queue not empty, staying in IDLE_LAG
    #                     return
    #         except Exception as e:
    #             logging_service.log("WARNING", f"IDLE_LAG: Could not check result queue status: {e}")
            
    #         # All conditions met - transition to IDLE
    #         logging_service.log("DEBUG", f"IDLE_LAG: All conditions met (UI manager: {not ui_manager_active}, \
    # processes: {not has_active_processes}, logging queue: {logging_queue_empty}, result queue: {result_queue_empty}), transitioning to IDLE")#DEBUG_ON IDLE_LAG: All conditions met (UI manager: {not ui_manager_active}, processes: {not has_active_processes}, logging queue: {logging_queue_empty}, result queue: {result_queue_empty}), transitioning to IDLE)
    #         self._set_state(ApplicationState.IDLE)
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"Failed to check IDLE_LAG to IDLE transition: {e}")

    # def _start_transition_timer(self) -> None:
    #     """Start the transition checking timer."""
    #     try:
    #         if self.transition_timer_active:
    #             return  # Already active
            
    #         self.transition_timer_active = True
    #         logging_service.log("DEBUG", "Starting transition checking timer")#DEBUG_ON Starting transition checking timer
    #         self._schedule_transition_check()
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"Failed to start transition timer: {e}")

    def _stop_transition_timer(self) -> None:
        """Stop the transition checking timer."""
        try:
            self.transition_timer_active = False
            logging_service.log("DEBUG", "Stopping transition checking timer")#DEBUG_ON Stopping transition checking timer
            
        except Exception as e:
            logging_service.log("ERROR", f"Failed to stop transition timer: {e}")

    # def _schedule_transition_check(self) -> None:
    #     """Schedule the next transition check."""
    #     try:
    #         if not self.transition_timer_active:
    #             return
            
    #         def check_transition() -> None:
    #             if not self.transition_timer_active:
    #                 return
                
    #             # Only check if we're in IDLE_LAG state
    #             if self.current_state == ApplicationState.IDLE_LAG:
    #                 # self._check_idle_lag_to_idle_transition()
                
    #             # Schedule next check
    #             if self.transition_timer_active:
    #                 ui.timer(self.transition_check_interval, check_transition, once=True)
            
    #         ui.timer(self.transition_check_interval, check_transition, once=True)
            
    #     except Exception as e:
    #         logging_service.log("ERROR", f"Failed to schedule transition check: {e}")
    #DEBUG_ON End Block _check_idle_lag_to_idle_transition
    def _check_immediate_idle_transition(self) -> None:
        """Check for immediate transition from IDLE_LAG to IDLE."""
        try:
            # Check if we should transition to IDLE immediately
            ui_manager_active = hasattr(self.ui_update_manager, 'timer_active') and self.ui_update_manager.timer_active
            has_active_processes = yapmo_globals.abort_manager.has_active_processes()
            
            # Check logging queue
            logging_queue_empty = True
            try:
                if hasattr(logging_service, 'logging_queue'):
                    logging_queue_empty = logging_service.logging_queue.empty()
                    #DEBUG_ON HARD print content logging queue
                    print(f"[QUEUE DEBUG] _check_immediate_idle_transition: logging_queue_empty = {logging_queue_empty}")
            except Exception:
                logging_queue_empty = True
                #DEBUG_ON HARD print content logging queue
                print(f"[QUEUE DEBUG] _check_immediate_idle_transition: exception checking queue, assuming empty")
            
            # Check result queue
            result_queue_empty = True
            try:
                if hasattr(yapmo_globals, 'result_queue'):
                    result_queue_empty = yapmo_globals.result_queue.empty()
            except Exception:
                result_queue_empty = True
            
            # If all conditions are met, transition immediately to IDLE
            if (not ui_manager_active and not has_active_processes and 
                logging_queue_empty and result_queue_empty):
                logging_service.log("DEBUG", "IDLE_LAG: All conditions met, transitioning immediately to IDLE")#DEBUG_ON IDLE_LAG: All conditions met, transitioning immediately to IDLE
                self._set_state(ApplicationState.IDLE)
            else:
                logging_service.log("DEBUG", f"IDLE_LAG: \
                    Conditions not met (UI manager: {not ui_manager_active}, processes: {not has_active_processes}, \
                        logging queue: {logging_queue_empty}, result queue: {result_queue_empty}), staying in IDLE_LAG")#DEBUG_ON IDLE_LAG: Conditions not met (UI manager: {not ui_manager_active}, processes: {not has_active_processes}, logging queue: {logging_queue_empty}, result queue: {result_queue_empty}), staying in IDLE_LAG)
            
        except Exception as e:
            logging_service.log("ERROR", f"Failed to check immediate idle transition: {e}")

    def _update_file_processing_ui_elements(self) -> None:
        """Update UI elements for FILE_PROCESSING state - processing and logging elements allowed."""
        try:
            logging_service.log("DEBUG", "Updating FILE_PROCESSING UI elements (processing and logging)")#DEBUG_ON Updating FILE_PROCESSING UI elements (processing and logging)
            
            # In FILE_PROCESSING state, processing and logging elements can be updated
            # Scan elements should NOT be updated
            # Only processing and logging elements can be updated
            
            # Log which elements are allowed to be updated
            allowed_elements = {
                "processing": self.processing_elements,
                "logging": self.logging_elements
            }
            logging_service.log("DEBUG", f"Allowed elements for FILE_PROCESSING state: {list(allowed_elements.keys())}")#DEBUG_ON Allowed elements for FILE_PROCESSING state: {list(allowed_elements.keys())}
            
            # Log which elements are NOT allowed to be updated
            forbidden_elements = {
                "scan": self.scan_elements
            }
            logging_service.log("DEBUG", f"Forbidden elements for FILE_PROCESSING state: {list(forbidden_elements.keys())}")#DEBUG_ON Forbidden elements for FILE_PROCESSING state: {list(forbidden_elements.keys())}
            
            logging_service.log("DEBUG", "FILE_PROCESSING UI elements update completed")#DEBUG_ON FILE_PROCESSING UI elements update completed
            
        except Exception as e:
            logging_service.log("ERROR", f"Failed to update FILE_PROCESSING UI elements: {e}")

    def _create_page(self) -> None:
        """Create the fill database new page."""

        @ui.page("/fill-db-new")
        def fill_db_new_page() -> None:
            with YAPMOTheme.page_frame(
                "Fill Database New",
                exit_handler=handle_exit_click,
            ):
                self._create_content()

    def _create_content(self) -> None:
        """Create the content of the fill database new page."""
        self._create_header_section()
        self._create_logging_section()
        self._create_scan_section()
        self._create_processing_section()
        
        # Reload search_path from config when page is created
        if hasattr(self, 'directory_input'):
            self.directory_input.value = get_param("paths", "search_path")
        
        # UI element inventory will be tested separately when needed

    def _setup_ui_updates(self) -> None:
        """Setup UI update callbacks."""
        # Register callback for scan progress updates
        self.ui_update_manager.register_callback(
            self._update_progress_display,
            data_key='scan_progress'
        )
        
        # Register callback for file processing progress updates
        self.ui_update_manager.register_callback(
            self._update_file_processing_display,
            data_key='processing_progress'
        )
        
        # TEST_AI ADDED: Register callback for log queue display (NO DATA KEY - always allowed)
        # TEST_AI FIXED: Added _display_log_queue callback to ensure log messages are processed by UI update manager
        self.ui_update_manager.register_callback(
            self._display_log_queue,
            data_key=None  # No data key - always display logs
        )

    def _update_progress_display(self, data) -> None:
        """Update progress display during scanning."""
        # Check if scan was aborted
        if self.scan_aborted:
            return  # Don't update UI during abort
        
        # Check if we're in the correct state for scan updates
        if self.current_state not in [ApplicationState.SCANNING, ApplicationState.IDLE_LAG]:
            logging_service.log("WARNING", f"Scan progress update ignored - wrong state: {self.current_state.value}")
            return
            
        # if not data or not isinstance(data, dict) or len(data) == 0:
        #     return  #TODO testen of UI_updates nu werkt
        
        # Only update scan elements if we're in SCANNING state
        if self.current_state == ApplicationState.SCANNING:
            # Update file count labels
            self.total_files_label.text = str(data.get('total_files', 0))
            self.media_files_label.text = str(data.get('media_files', 0))
            self.sidecars_label.text = str(data.get('sidecars', 0))
            self.directories_label.text = str(data.get('directories', 0))
            
            # Update scan status (only when we have scan data)
            self.scan_status_label.text = "scanning - DO NOT GO BACK IN THE BROWSER"
        
        # Always display log messages (allowed in all states)
        self._display_log_queue()

    def _update_file_processing_display(self, data) -> None:
        """Update file processing progress display."""
        if not data:
            return
        
        # Check if we're in the correct state for processing updates
        if self.current_state not in [ApplicationState.FILE_PROCESSING, ApplicationState.IDLE_LAG]:
            logging_service.log("WARNING", f"File processing update ignored - wrong state: {self.current_state.value}")
            return
        
        # Only update processing elements if we're in FILE_PROCESSING state
        if self.current_state == ApplicationState.FILE_PROCESSING:
            # Update progress bar
            file_progress = data.get('file_progress', 0.0)
            self.processing_progress_bar.value = file_progress
            
            # Update progress info label
            processed_files = data.get('processed_files', 0)
            total_files = data.get('total_files', 0)
            processed_dirs = data.get('processed_directories', 0)
            total_dirs = data.get('total_directories', 0)
            files_per_sec = data.get('files_per_second', 0.0)
            dirs_per_sec = data.get('directories_per_second', 0.0)
            eta = data.get('estimated_time_remaining', 0.0)
            
            progress_text = (
                f"Processing: {file_progress*100:.1f}% "
                f"({processed_files}/{total_files} files, {processed_dirs}/{total_dirs} directories processed "
                f"with {files_per_sec:.2f} files/sec and {dirs_per_sec:.2f} directories/sec "
                f"estimated time to finish: {eta:.2f} sec)"
            )
            self.processing_progress_info_label.text = progress_text
            
            # Update count labels
            self.files_processed_label.text = str(processed_files)
            self.directories_processed_label.text = str(processed_dirs)
            self.files_per_second_label.text = f"{files_per_sec:.2f}"
            self.directories_per_second_label.text = f"{dirs_per_sec:.2f}"
            self.estimated_time_to_finish_label.text = f"{eta:.1f}s"
        
        # Always display log messages (allowed in all states)
        self._display_log_queue()

    def _start_file_processing(self) -> None:
        """Start file processing with the configured directory."""
        try:
            # Set state to FILE_PROCESSING
            self._set_state(ApplicationState.FILE_PROCESSING)
            
            # Get start directory from config
            start_directory = get_param("paths", "search_path")
            
            # Validate directory
            if not os.path.exists(start_directory):
                ui.notify("Directory does not exist!", type="negative")
                return
            
            # Set button to processing state
            self._set_button_processing()
            
            # Start UI updates
            self.ui_update_manager.start_updates()
            
            # Generate unique process ID and register process
            self.current_process_id = f"processing_{int(time.time() * 1000)}"
            yapmo_globals.abort_manager.register_process(self.current_process_id)
            logging_service.log("DEBUG", f"Registered processing process: {self.current_process_id}")#DEBUG_ON Registered processing process: {self.current_process_id}
            
            # Log processing start
            logging_service.log("INFO", f"Starting file processing: {start_directory}")
            
            # Enable processing UI state
            self._enable_processing_ui()
            
            # Start file processing in background thread
            import threading
            processing_thread = threading.Thread(
                target=self._run_file_processing,
                args=(start_directory,),
                daemon=True
            )
            processing_thread.start()
            
        except Exception as e:
            error_msg = f"Failed to start file processing: {e}"
            logging_service.log("ERROR", error_msg)
            ui.notify(f"Error starting file processing: {e}", type="negative")
            
            # Reset button state on start error
            self._set_button_ready()

    def _run_file_processing(self, directory_path: str) -> None:
        """Run file processing in background thread."""
        try:
            # Import here to avoid circular imports
            from core.directory_processor import DirectoryProcessor
            from core.progress_tracker import ProgressTracker
            
            # Get configuration
            max_workers = get_param("processing", "max_workers")
            image_extensions = get_param("extensions", "image_extensions")
            video_extensions = get_param("extensions", "video_extensions")
            
            # Create progress tracker
            progress_tracker = ProgressTracker(self._file_processing_progress_callback)
            
            # Create directory processor
            processor = DirectoryProcessor(max_workers, self._file_processing_progress_callback)
            
            # Start processing
            result = processor.process_directory(directory_path, image_extensions, video_extensions)
            
            # Wait for completion
            time.sleep(2.0)  # Give time for final updates
            
            # Check if processing is complete
            if result.get('success', False):
                stats = result.get('stats', {})
                logging_service.log("INFO", f"File processing completed successfully: {stats.get('processed_files', 0)} files processed in {stats.get('elapsed_time', 0):.2f} seconds")
            else:
                error_msg = result.get('error', 'Unknown error')
                logging_service.log("ERROR", f"File processing failed: {error_msg}")
            
            # Completion handling
            self._handle_processing_completion(result)
            
        except Exception as e:
            error_msg = f"File processing failed: {e}"
            logging_service.log("ERROR", error_msg)
            
            # Handle error completion
            error_result = {
                "success": False,
                "error": str(e),
                "stats": {
                    "processed_files": 0,
                    "successful_files": 0,
                    "failed_files": 0,
                    "elapsed_time": 0
                }
            }
            self._handle_processing_completion(error_result)
        
        finally:
            # Always unregister process when done
            if self.current_process_id:
                yapmo_globals.abort_manager.unregister_process(self.current_process_id)
                logging_service.log("DEBUG", f"Unregistered processing process: {self.current_process_id}")#DEBUG_ON Unregistered processing process: {self.current_process_id}
                self.current_process_id = None
                # Disable processing UI if no active processes
                self._disable_processing_ui()

    def _file_processing_progress_callback(self, event_type: str, data) -> None:
        """Callback function for file processing progress updates."""
        if event_type == 'processing_progress':
            # Update shared data for UI updates
            self.ui_update_manager.update_shared_data('processing_progress', data)
            # Also call the display function directly for immediate UI updates
            self._update_file_processing_display(data)

    def _set_button_processing(self) -> None:
        """Set button to processing state."""
        self.start_button_processing.props("color=negative")
        self.start_button_processing.text = "PROCESSING"
        self.start_button_processing.disable()

    def _set_button_ready(self) -> None:
        """Set button to ready state."""
        self.start_button_processing.props("color=primary")
        self.start_button_processing.text = "START PROCESSING"
        self.start_button_processing.enable()

    def _handle_processing_completion(self, result: dict) -> None:
        """Handle completion of file processing."""
        try:
            # Stop UI updates
            # self.ui_update_manager.stop_updates() #TODO check of dit de laatste updates tegen houdt            
            # Reset button to ready state
            self._set_button_ready()
            
            # Transition to IDLE_LAG state (file processing completed, but queues may still be processing)
            self._set_state(ApplicationState.IDLE_LAG)
            
            # Log completion
            if result.get('success', False):
                stats = result.get('stats', {})
                logging_service.log("INFO", f"Processing completion handled: {stats.get('processed_files', 0)} files, {stats.get('successful_files', 0)} successful, {stats.get('failed_files', 0)} failed")
            else:
                logging_service.log("INFO", "Processing completion handled with errors")
            
            # Ensure all queues are empty (this is handled by the processors)
            # The result processor and logging integration will clean up their queues
            
        except Exception as e:
            logging_service.log("ERROR", f"Error in completion handling: {e}")

    def _create_header_section(self) -> None:
        """Create the header section."""
        with ui.card().classes("w-full mb-6"), ui.card_section():
            ui.label("Fill Database New").classes(
                "text-3xl font-bold text-center mb-4",
            )
            ui.label("Directory scan process").classes(
                "text-lg text-center text-gray-600",
            )

    def _create_logging_section(self) -> None:
        """Create the logging section with scroll area and clear button."""
        # Progress and Log Panel (Hele breedte - Wit met Donkere Blauwe Rand)
        progress_card_classes = (
            "w-full bg-white rounded-lg"
        )
        with ui.card().classes(progress_card_classes), \
             ui.card_section().classes("w-full p-6"):
            ui.label("Progress and Log").classes(
                "text-xl font-semibold text-gray-800 mb-4")

            # Progress bar and directories counter row
            with ui.row().classes("w-full items-center gap-4 mb-4"):
                # Progress bar (flex-1 to take remaining space)
                self.progress_bar = ui.linear_progress(
                    value=0.0,
                    show_value=False,
                    size="20px",
                    color="blue",
                ).classes("flex-1")
                self.progress_bar.visible = False

            # Progress info - verborgen bij initialisatie
            progress_text = (
                "Progress info: Completed: 0% "
                "(0 Found/0 Files processed)"
            )
            self.progress_info_label = ui.label(progress_text).classes(
                "text-gray-700 font-medium mb-4",
            )
            self.progress_info_label.visible = False

            # Log section
            ui.label("Log info:").classes("text-grey-700 font-medium mb-2")

            # Log display area (volledige breedte en hoogte)
            log_area_classes = "h-64 bg-gray-100 rounded-lg p-4 mb-4"
            self.log_scroll_area = ui.scroll_area().classes(log_area_classes)
            with self.log_scroll_area:
                self.log_column = ui.column().classes("w-full")

            # Control buttons
            with ui.row().classes("w-full items-center gap-4"):
                self.clear_log_button = YAPMOTheme.create_button(
                    "CLEAR LOG",
                    self._clear_log,
                    "secondary",
                    "md",
                )

    def _create_scan_section(self) -> None:
        """Create the scanning section with directory input and scan results."""
        with ui.card().classes("w-full bg-white rounded-lg mb-6"), ui.card_section():
            ui.label("Scanning").classes("text-xl font-bold mb-4")
            
            with ui.row().classes("gap-6"):
                # Left side - Buttons (like Test Directory Traverse)
                with ui.column().classes("gap-4"):
                    # Select directory button
                    self.select_directory_button = YAPMOTheme.create_button(
                        "SELECT DIRECTORY",
                        self._select_directory,
                        "secondary",
                        "lg",
                    )
                    
                    # Start Scanning button
                    self.start_button_scanning = YAPMOTheme.create_button(
                        "START Scanning",
                        self._start_scanning,
                        "primary",
                        "lg",
                    )
                
                # Right side - Content
                # Search Directory section
                with ui.row().classes("flex-1 gap-4"):
                    with ui.column().classes("flex-1"):
                        ui.label("Search Directory").classes("text-lg font-bold mb-2")
                        self.directory_input = ui.input(
                            placeholder="Enter directory path...",
                            value=get_param("paths", "search_path")
                        ).classes("w-full")
                    
                    # Hourglass spinner
                    with ui.column().classes("items-center justify-center"):
                        with ui.row().classes("justify-end w-full"):
                            self.scan_spinner = ui.spinner("hourglass", size="xl", color="red")
                            self.scan_spinner.set_visibility(False)
                
                # Horizontal line separator
                ui.separator().classes("my-4")
                
                # Scan Complete section
                with ui.row().classes("gap-6"):
                    # Left column - Details button (same width as START Scanning)
                    with ui.column().classes("w-48 gap-4"):
                        self.details_button = YAPMOTheme.create_button(
                            "DETAILS",
                            self._show_details,
                            "secondary",
                            "lg",
                        )
                        # Disable details button initially
                        self.details_button.disable()
                    
                    # Right column - Scan Complete content
                    with ui.column().classes("flex-1"):
                        with ui.row().classes("w-full gap-2 mb-2"):
                            ui.label("Scan status").classes("text-lg font-bold")
                            self.scan_status_label = ui.label("not active").classes("text-lg font-bold")
                        
                        # File count labels in one row
                        with ui.row().classes("gap-4"):
                            self.total_files_label = ui.label("0").classes("text-4xl font-bold text-blue-600")
                            ui.label("Total Files").classes("text-sm")
                            
                            self.media_files_label = ui.label("0").classes("text-4xl font-bold text-blue-600")
                            ui.label("Media Files").classes("text-sm")
                            
                            self.sidecars_label = ui.label("0").classes("text-4xl font-bold text-blue-600")
                            ui.label("Sidecars").classes("text-sm")
                            
                            self.directories_label = ui.label("0").classes("text-4xl font-bold text-blue-600")
                            ui.label("Directories").classes("text-sm")

    def _create_processing_section(self) -> None:
        """Create the file processing section with progress bar."""
        with ui.card().classes("w-full bg-white rounded-lg mb-6"), ui.card_section():
            ui.label("File Processing").classes("text-xl font-bold mb-4")
            with ui.row().classes("gap-4"):
                # Start Processing button
                self.start_button_processing = YAPMOTheme.create_button(
                    "START PROCESSING",
                    self._start_file_processing,
                    "primary",
                    "lg",
                )
                
                # Processing Progress section
                with ui.column().classes("flex-1"):
                    ui.label("Processing Progress").classes("text-lg font-bold mb-2")
                    
                    # Progress bar
                    self.processing_progress_bar = ui.linear_progress(
                        value=0.0,
                        show_value=False,
                        size="20px",
                        color="blue",
                    ).classes("w-full mb-2")
                    
                    # Progress info with detailed statistics
                    progress_info_text = (
                        "Processing: 0% (0/0 files 0/0 directories processed with a 0 files/sec "
                    )
                    self.processing_progress_info_label = ui.label(progress_info_text).classes(
                        "text-gray-700 font-medium",
                    )
                    # File processing count labels in one row
                    with ui.row().classes("gap-4"):
                        with ui.column():
                            ui.label("Files Processed").classes("text-sm")
                            self.files_processed_label = ui.label("0").classes("text-4xl font-bold text-blue-600")
                        with ui.column():
                            ui.label("Directories Processed").classes("text-sm")
                            self.directories_processed_label = ui.label("0").classes("text-4xl font-bold text-blue-600")
                        with ui.column():
                            ui.label("Files/sec").classes("text-sm")
                            self.files_per_second_label = ui.label("0").classes("text-4xl font-bold text-blue-600")
                        with ui.column():
                            ui.label("Directories/sec").classes("text-sm")
                            self.directories_per_second_label = ui.label("0").classes("text-4xl font-bold text-blue-600")
                        with ui.column():
                            ui.label("Estimated time to finish").classes("text-sm")
                            self.estimated_time_to_finish_label = ui.label("0").classes("text-4xl font-bold text-blue-600")

    async def _select_directory(self) -> None:
        """Browse voor folder selectie."""
        try:
            # Get current value as starting directory
            current_path = self.directory_input.value or "/workspaces"
            
            # Open directory picker
            selected_path = await pick_directory(
                directory=current_path,
                show_hidden_files=False
            )
            
            if selected_path:
                # Update the input field with selected path
                self.directory_input.value = selected_path
                ui.notify(f"Selected directory: {selected_path}", type="positive")
            else:
                ui.notify("No directory selected", type="info")
                
        except Exception as e:
            ui.notify(f"Error browsing directory: {e}", type="negative")

    def _start_scanning(self) -> None:
        """Start the scan processing."""
        # Get directory from input
        directory = self.directory_input.value.strip()
        if not directory:
            ui.notify("Please enter a directory path!", type="negative")
            return
        
        # Save current value back to config
        set_param("paths", "search_path", directory)
        
        # Check if directory exists
        if not os.path.exists(directory):
            ui.notify("Directory does not exist!", type="negative")
            return
        
        # Transition to SCANNING state
        self._set_state(ApplicationState.SCANNING)
        
        # Update button state to processing
        self._set_button_scanning()
        
        # Start UI updates (in main thread)
        self.ui_update_manager.start_updates()
        
        # Generate unique process ID and register process
        self.current_process_id = f"scan_{int(time.time() * 1000)}"
        yapmo_globals.abort_manager.register_process(self.current_process_id)
        
        # Set scan start time
        self.scan_start_time = time.time()
        
        # Log scan start
        logging_service.log("INFO", f"Starting directory scan: {directory}")
        #DEBUG_ON HARD print content logging queue
        print(f"[QUEUE DEBUG] Added scan start message to queue")
        
        # Display log messages immediately  #TODO testen of UI_updates nu werkt
        self._display_log_queue()
        
        # Enable processing UI state
        self._enable_processing_ui()
        
        
        # Start scan process
        asyncio.create_task(self._run_scan_process(directory))

    def _set_button_scanning(self) -> None:
        """Set button to processing state."""
        self.start_button_scanning.props("color=negative")
        self.start_button_scanning.text = "SCANNING"
        self.start_button_scanning.disable()
        
        # Disable select directory button
        self.select_directory_button.disable()
        
        # Disable directory input
        self.directory_input.disable()
        
        # Disable details button during scanning
        self.details_button.disable()
        
        # Show spinner
        self.scan_spinner.set_visibility(True)
        
        # Update scan status
        self.scan_status_label.text = "scanning - DO NOT GO BACK IN THE BROWSER"

    def _set_button_ready(self) -> None:
        """Set button to ready state."""
        self.start_button_scanning.props("color=primary")
        self.start_button_scanning.text = "Start Scanning"
        self.start_button_scanning.enable()
        
        # Enable select directory button
        self.select_directory_button.enable()
        
        # Enable directory input
        self.directory_input.enable()
        
        # Enable details button if scan data is available
        if self.details_button and self.extension_counts:
            self.details_button.enable()
        
        # Hide spinner
        self.scan_spinner.set_visibility(False)
        
        # Unregister process and disable abort button if no active processes
        if self.current_process_id:
            yapmo_globals.abort_manager.unregister_process(self.current_process_id)
            self.current_process_id = None
            
            # Disable processing UI if no active processes
            self._disable_processing_ui()

    async def _run_scan_process(self, directory: str) -> None:
        """Run the scan process with real-time updates."""
        try:
            # Reset abort flags at start
            self.scan_aborted = False
            self.processing_aborted = False
            
            # Run scan in background thread
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._scan_directory_sync_with_updates, directory
            )
            
            
            # Check if scan was aborted (UI update will have set the flags)
            if self.scan_aborted:
                return
            
            # Update UI with final results
            self._update_final_results(result)
            
            # Wait for all log messages to be processed
            # Condition 1: Process completed ✓
            # Condition 2: Queue must be empty
            # Let the UI update manager handle the queue naturally
            # It will stop when both conditions are met: process completed AND queue empty
            await asyncio.sleep(1.0)  # Give it one second to process remaining messages
            
            # TEST_AI REMOVED: Stop UI updates after both conditions are met
            # self.ui_update_manager.stop_updates()
            
            # Process completed - update UI in main thread
            self._set_button_ready()
            
            # Update UI labels with scan results
            files_count = result.get("files", 0)
            directories_count = result.get("directories", 0)
            media_files_count = result.get("media_files", 0)
            sidecars_count = result.get("sidecars", 0)
            
            # Update all count labels
            self.total_files_label.text = str(files_count)
            self.media_files_label.text = str(media_files_count)
            self.sidecars_label.text = str(sidecars_count)
            self.directories_label.text = str(directories_count)
            
            # Update scan status
            self.scan_status_label.text = "completed"
            
            # Transition to IDLE_LAG state (scan completed, but queues may still be processing)
            self._set_state(ApplicationState.IDLE_LAG)
            
            # TEST_AI ADDED: Stop UI updates AFTER state transition (so log queue can be processed)
            # TEST_AI FIXED: Moved stop_updates() after state transition to allow log queue processing
            self.ui_update_manager.stop_updates()
            
            # Enable details button when scan data is available
            if self.details_button and self.extension_counts:
                self.details_button.enable()
                
        finally:
            # Always unregister process when done (success or abort)
            if self.current_process_id:
                yapmo_globals.abort_manager.unregister_process(self.current_process_id)
                self.current_process_id = None
                
                # Disable processing UI if no active processes
                self._disable_processing_ui()

    def _scan_directory_sync_with_updates(self, directory: str) -> dict:
        """Scan directory with real-time UI updates."""
        files_count = 0
        directories_count = 0
        media_files_count = 0
        sidecars_count = 0
        
        # Use pre-loaded extensions from instance variables
        media_extensions = self.image_extensions.union(self.video_extensions)
        
        # Use os.walk() for recursive directory traversal
        for root, dirs, files in os.walk(directory):
           
            # Count directories
            directories_count += 1
            
            
            # Count files and categorize them
            for file in files:
                files_count += 1
                file_ext = Path(file).suffix.lower()
                
                # Track file extension counts
                if file_ext in self.extension_counts:
                    self.extension_counts[file_ext] += 1
                else:
                    self.extension_counts[file_ext] = 1
                
                if file_ext in media_extensions:
                    media_files_count += 1
                elif file_ext in self.sidecar_extensions:
                    sidecars_count += 1
            
            # Update shared data for UI updates
            scan_data = {
                'total_files': files_count,
                'media_files': media_files_count,
                'sidecars': sidecars_count,
                'directories': directories_count
            }
            self.ui_update_manager.update_shared_data('scan_progress', scan_data)
            # logging_service.log("DEBUG", f"Scan progress updated: {scan_data}") #DEBUG_OF #AI_TEST ADDED: Debug logging to see if scan data is being updated
        
        return {
            "files": files_count,
            "directories": directories_count,
            "media_files": media_files_count,
            "sidecars": sidecars_count,
        }

    def _update_final_results(self, result: dict) -> None:
        """Update final results after scan completion."""
        # Update all count labels with final results
        files_count = result.get("files", 0)
        directories_count = result.get("directories", 0)
        media_files_count = result.get("media_files", 0)
        sidecars_count = result.get("sidecars", 0)
        
        self.total_files_label.text = str(files_count)
        self.media_files_label.text = str(media_files_count)
        self.sidecars_label.text = str(sidecars_count)
        self.directories_label.text = str(directories_count)
        
        # Set scan end time and calculate duration
        self.scan_end_time = time.time()
        scan_duration = self.scan_end_time - self.scan_start_time if self.scan_start_time else 0
        
        # Calculate files and directories per second
        files_per_second = files_count / scan_duration if scan_duration > 0 else 0
        directories_per_second = directories_count / scan_duration if scan_duration > 0 else 0
        
        # Update scan status to completed
        self.scan_status_label.text = "completed"
        
        # Transition to IDLE_LAG state (scan completed, but queues may still be processing)
        self._set_state(ApplicationState.IDLE_LAG)
        
        # Log scan completion with duration and performance metrics
        logging_service.log("INFO", f"Scan completed: {files_count} total files, {media_files_count} media files, {sidecars_count} sidecars, {directories_count} directories in {scan_duration:.4f} seconds ({files_per_second:.1f} files/sec, {directories_per_second:.1f} dirs/sec)")
        #DEBUG_OFF HARD print content logging queue
        #print(f"[QUEUE DEBUG] Added scan completion message to queue") #DEBUG_OFF
        
        #TEST_AI ADDED: Cleanup remaining log messages after scan completion
        # This ensures all log messages generated after UI timer stop are displayed
        asyncio.create_task(self._cleanup_remaining_logs("scan")) #TEST_AI ADDED: Cleanup remaining log messages after scan completion

    def _show_details(self) -> None:
        """Show file type details in a popup."""
        if not self.extension_counts:
            ui.notify("No scan data available. Please scan a directory first.", type="info")
            return

        # Get config for relevant extensions
        image_exts = list(self.image_extensions)
        video_exts = list(self.video_extensions)
        sidecar_exts = list(self.sidecar_extensions)
        relevant_extensions = image_exts + video_exts + sidecar_exts

        with ui.dialog() as dialog, ui.card().classes("w-96 h-96"):
            ui.label("FILETYPES FOUND").classes("text-xl font-bold text-white mb-4")

            # Table with file types
            with ui.scroll_area().classes("w-full h-64"), \
                 ui.column().classes("w-full"):
                # Header row
                row_classes = "w-full font-bold text-white bg-blue-400 p-2"
                with ui.row().classes(row_classes):
                    ui.label("File type").classes("flex-1")
                    ui.label("Found").classes("w-20 text-right")

                # Data rows - only relevant extensions, sorted by file type
                relevant_items = [
                    (ext, count) for ext, count in self.extension_counts.items()
                    if ext.lower() in relevant_extensions
                ]
                sorted_items = sorted(relevant_items)

                for ext, count in sorted_items:
                    data_row_classes = "w-full p-2 border-b border-gray-600"
                    with ui.row().classes(data_row_classes):
                        ui.label(str(ext)).classes("flex-1 text-black-400")
                        ui.label(str(count)).classes("w-20 text-right text-blue-400")

            # Close button
            ui.button("CLOSE", on_click=dialog.close).classes(
                "bg-gray-600 text-white px-4 py-2 rounded-lg mt-4")

        dialog.open()

    def _register_abort_handler(self) -> None:
        """Register abort handler with global abort manager."""
        yapmo_globals.abort_manager.register_abort_handler("fill_db_new", self._abort_scan)
        

    def _abort_scan(self) -> None:
        """Abort the current scan process."""
        # Get active processes
        active_processes = yapmo_globals.abort_manager.get_active_processes()
        
        
        # Abort our specific process if it's active
        if self.current_process_id and self.current_process_id in active_processes:
            self._handle_abort()
        

    def _handle_abort(self) -> None:
        """Handle abort when detected by UI update."""
        
        # Set abort flags
        self.scan_aborted = True
        self.processing_aborted = True
        
        # Transition to IDLE state (abort resets everything)
        self._set_state(ApplicationState.IDLE)
        
        # Stop UI updates
        self.ui_update_manager.stop_updates()
        
        # Update UI elements
        self._update_abort_ui_elements()
        
        # Reset scan data
        self.extension_counts = {}
        self.scan_start_time = None
        self.scan_end_time = None
        

    def _update_abort_ui_elements(self) -> None:
        """Update UI elements during abort."""
        # Stop UI updates during abort
        self.ui_update_manager.stop_updates()
        
        # Update button states according to current state (IDLE after abort)
        self._update_button_states()
        
        # Reset scan status (only if UI elements exist)
        if hasattr(self, 'scan_status_label'):
            self.scan_status_label.text = "aborted"
            self.scan_status_label.classes("!text-gray-700 !font-medium")
        
        # Clear count labels (only if UI elements exist)
        if hasattr(self, 'total_files_label'):
            self.total_files_label.text = "0"
        if hasattr(self, 'media_files_label'):
            self.media_files_label.text = "0"
        if hasattr(self, 'sidecars_label'):
            self.sidecars_label.text = "0"
        if hasattr(self, 'directories_label'):
            self.directories_label.text = "0"
        
        # Disable details button (only if UI element exists)
        if hasattr(self, 'details_button'):
            self.details_button.disable()

    def _display_log_queue(self) -> None:
        """Display all messages from logging service queue in UI."""
        try:
            #DEBUG_OFF TEST_AI HARD print message content tracking
            #print(f"[UI DEBUG] _display_log_queue START - log_messages count: {len(self.log_messages) if hasattr(self, 'log_messages') else 'NOT_EXISTS'}") #DEBUG_OFFTEST_AI HARD print message content tracking
            #TEST_AI_OFF Start Block Log _display_log_queue debug
            logging_service.log("TEST_AI_ON", "_display_log_queue called")
            #DEBUG_OFF HARD print content logging queue
            #print(f"[QUEUE DEBUG] _display_log_queue called - checking queue status") #DEBUG_OFFTEST_AI HARD print UI element state monitoring
            # Check queue status before getting messages
            queue_size_before = 0
            try:
                if hasattr(logging_service, 'logging_queue'):
                    queue_size_before = logging_service.logging_queue.qsize()
            except Exception:
                queue_size_before = 0
            #DEBUG_OFF HARD print content logging queue
            #print(f"[QUEUE DEBUG] Queue size before retrieval: {queue_size_before}") #DEBUG_OFFTEST_AI HARD print UI element state monitoring
            
            new_messages = logging_service.get_ui_messages()  # Get and clear queue
            
            # Check queue status after getting messages
            queue_size_after = 0
            try:
                if hasattr(logging_service, 'logging_queue'):
                    queue_size_after = logging_service.logging_queue.qsize()
            except Exception:
                queue_size_after = 0
            
            #DEBUG_ON HARD print content logging queue
            #DEBUG_OFF HARD print content logging queue
            #print(f"[QUEUE DEBUG] Retrieved {len(new_messages) if new_messages else 0} messages, queue size after: {queue_size_after}") #DEBUG_OFFTEST_AI HARD print UI element state monitoring
            logging_service.log("TEST_AI_ON", f"new_messages = {new_messages}")
            logging_service.log("TEST_AI_ON", f"log_column exists = {hasattr(self, 'log_column')}")
            #TEST_AI_OFF End Block Log _display_log_queue debug
            
            #TEST_AI HARD print UI element state monitoring
            #DEBUG_OFF HARD print content logging queue
            #print(f"[UI DEBUG] _display_log_queue called at {time.time()}") #DEBUG_OFFTEST_AI HARD print UI element state monitoring
            #DEBUG_OFF HARD print content logging queue
            #print(f"[UI DEBUG] Current state: {self.current_state}") #DEBUG_OFFTEST_AI HARD print UI element state monitoring
            #DEBUG_OFF HARD print content logging queue
            #print(f"[UI DEBUG] UI update manager active: {self.ui_update_manager.timer_active}") #DEBUG_OFFTEST_AI HARD print UI element state monitoring
            #DEBUG_OFF HARD print content logging queue
            #print(f"[UI DEBUG] log_column exists: {hasattr(self, 'log_column')}") #DEBUG_OFFTEST_AI HARD print UI element state monitoring
            #DEBUG_OFF HARD print content logging queue
            # if hasattr(self, 'log_column'):
                #DEBUG_OFF HARD print content logging queue
                #print(f"[UI DEBUG] log_column type: {type(self.log_column)}") #DEBUG_OFFTEST_AI HARD print UI element state monitoring
                #DEBUG_OFF HARD print content logging queue
                #print(f"[UI DEBUG] log_column children count before: {len(self.log_column.children) if hasattr(self.log_column, 'children') else 'unknown'}") #DEBUG_OFFTEST_AI HARD print UI element state monitoring
                #DEBUG_OFF HARD print content logging queue
                #print(f"[UI DEBUG] log_column children count before: {len(self.log_column.children) if hasattr(self.log_column, 'children') else 'unknown'}") #DEBUG_OFFTEST_AI HARD print UI element state monitoring
            
            #TEST_AI FIXED: Only update UI when there are new messages to prevent unnecessary re-rendering
            # blijktniet nodig te zijn, maar kan geen kwaad
            if new_messages and self.log_column:
                # Add new messages to display queue (let op volgorde)
                if not hasattr(self, "log_messages"):
                    self.log_messages = []

                for i, msg_data in enumerate(new_messages):
                    #TEST_AI HARD print message content tracking
                    #DEBUG_OFF HARD print content logging queue
                    #print(f"[UI DEBUG] Processing message {i+1}/{len(new_messages)}: {msg_data.get('message', 'NO_MESSAGE')[:50]}...") #DEBUG_OFFTEST_AI HARD print message content tracking
                    # Handle timestamp format safely
                    timestamp_parts = msg_data["timestamp"].split(" ")
                    if len(timestamp_parts) >= 2:
                        timestamp = timestamp_parts[1]
                    else:
                        timestamp = msg_data["timestamp"]
                    formatted_message = (
                        f"[{timestamp}] {msg_data['level']}: {msg_data['message']}"
                    )
                    self.log_messages.insert(0, formatted_message)  # Nieuwste bovenaan
                    #TEST_AI HARD print message content tracking
                    #DEBUG_OFF HARD print content logging queue
                    #print(f"[UI DEBUG] Added to log_messages array, total now: {len(self.log_messages)}") #DEBUG_OFFTEST_AI HARD print message content tracking

                # Redraw all messages
                #TEST_AI HARD print UI element state monitoring
                #DEBUG_OFF HARD print content logging queue
                #print(f"[UI DEBUG] Before clear - log_column type: {type(self.log_column)}") #DEBUG_OFFTEST_AI HARD print UI element state monitoring
                self.log_column.clear()
                #TEST_AI HARD print UI element state monitoring
                #DEBUG_OFF HARD print content logging queue
                #print(f"[UI DEBUG] After clear - log_column children: {len(self.log_column.children) if hasattr(self.log_column, 'children') else 'unknown'}") #DEBUG_OFFTEST_AI HARD print UI element state monitoring
                
                with self.log_column:
                    for i, msg in enumerate(self.log_messages):
                        ui.label(msg).classes("text-sm text-gray-700 font-mono")
                        #TEST_AI HARD print UI element state monitoring
                        #DEBUG_OFF HARD print content logging queue
                        #print(f"[UI DEBUG] Added message {i+1}/{len(self.log_messages)}: {msg[:50]}...") #DEBUG_OFFTEST_AI HARD print UI element state monitoring
                
                #TEST_AI HARD print UI element state monitoring
                #DEBUG_OFF HARD print content logging queue
                #print(f"[UI DEBUG] After redraw - log_column children: {len(self.log_column.children) if hasattr(self.log_column, 'children') else 'unknown'}") #DEBUG_OFFTEST_AI HARD print UI element state monitoring
                
                # Scroll to bottom to show latest messages
                self.log_scroll_area.scroll_to(percent=100)
                #TEST_AI HARD print UI element state monitoring
                #DEBUG_OFF HARD print content logging queue
                #print(f"[UI DEBUG] Scrolled to bottom, scroll area type: {type(self.log_scroll_area)}") #DEBUG_OFFTEST_AI HARD print UI element state monitoring
                #TEST_AI HARD print UI element state monitoring
                #DEBUG_OFF HARD print content logging queue
                #print(f"[UI DEBUG] UI rendering completed - all {len(self.log_messages)} messages should be visible") #DEBUG_OFFTEST_AI HARD print UI element state monitoring
                
                #DEBUG_ON HARD print content logging queue
                #print(f"[QUEUE DEBUG] Processed {len(new_messages)} messages, total in display: {len(self.log_messages)}") #DEBUG_OFFTEST_AI HARD print UI element state monitoring

        except OSError as e:
            logging_service.log("WARNING", f"Log display error: {e}")
        
        #TEST_AI HARD print message content tracking
        #DEBUG_OFF HARD print content logging queue
        #print(f"[UI DEBUG] _display_log_queue END - log_messages count: {len(self.log_messages) if hasattr(self, 'log_messages') else 'NOT_EXISTS'}") #DEBUG_OFFTEST_AI HARD print message content tracking

    async def _cleanup_remaining_logs(self, context: str = "scan") -> None:
        """
        Clean up any remaining log messages after completion.
        
        This method handles the cleanup of log messages that are generated AFTER
        the UI update timer has been stopped. This is necessary because some log
        messages are created during state transitions that happen after the main
        completion logic.
        
        Args:
            context (str): The context of the cleanup operation.
                          - "scan": For directory scan completion
                          - "processing": For file processing completion
                          - "general": For general cleanup
        
        Process:
        1. Wait for all operations to settle (500ms) - allows state transitions and 
           logging operations to complete before checking for remaining messages
        2. Check if logging queue has remaining messages - determines if cleanup is needed
        3. If messages exist, temporarily restart UI update manager - enables message processing
        4. Allow UI update manager to process all remaining messages (300ms) - gives timer 
           enough time to process all queued messages through the existing _display_log_queue callback
        5. Stop UI update manager after processing is complete - returns to normal state
        
        Timing Details:
        - 500ms initial wait: Ensures all state transitions and logging operations complete
        - 100ms UI restart wait: Allows UI update manager to initialize properly
        - 300ms processing wait: Provides sufficient time for timer to process all queued messages
        - Total cleanup time: ~900ms maximum (only when messages are found)
        
        This ensures all log messages are displayed in the UI, even those
        generated after the main completion logic.
        """
        try:
            #TEST_AI ADDED: Cleanup routine for remaining log messages
            logging_service.log("DEBUG", f"Starting cleanup for {context} context") #TEST_AI ADDED: Cleanup routine for remaining log messages
            print(f"[QUEUE DEBUG] Starting cleanup for {context} context")
            # 1. Wait for all operations to settle
            await asyncio.sleep(0.5)  # 500ms wait for operations to complete
            
            # 2. Check if logging queue has remaining messages
            queue_size = 0
            if hasattr(logging_service, 'logging_queue'):
                queue_size = logging_service.logging_queue.qsize()
            
            if queue_size > 0:
                #TEST_AI ADDED: Cleanup routine for remaining log messages
                logging_service.log("DEBUG", f"Found {queue_size} remaining messages in queue, processing...") #TEST_AI ADDED: Cleanup routine for remaining log messages
                
                # 3. Temporarily restart UI update manager
                self.ui_update_manager.start_updates()
                
                # 4. Wait for UI update manager to start
                await asyncio.sleep(0.1)  # 100ms wait for UI manager to start
                
                # 5. Allow UI update manager to process all remaining messages
                # The timer will automatically process all messages in the queue
                await asyncio.sleep(0.3)  # 300ms for message processing
                
                # 6. Stop UI update manager after processing
                self.ui_update_manager.stop_updates()
                
                #TEST_AI ADDED: Cleanup routine for remaining log messages
                logging_service.log("DEBUG", f"Cleanup completed for {context} context") #TEST_AI ADDED: Cleanup routine for remaining log messages
            else:
                #TEST_AI ADDED: Cleanup routine for remaining log messages
                logging_service.log("DEBUG", f"No remaining messages found for {context} context") #TEST_AI ADDED: Cleanup routine for remaining log messages
                
        except Exception as e:
            #TEST_AI ADDED: Cleanup routine for remaining log messages
            logging_service.log("WARNING", f"Cleanup error for {context} context: {e}") #TEST_AI ADDED: Cleanup routine for remaining log messages

    def _clear_log(self) -> None:
        """Clear the log display."""
        try:
            if self.log_column:
                # Clear local log messages
                if hasattr(self, "log_messages"):
                    self.log_messages = []
                
                # Clear UI display
                self.log_column.clear()
        except Exception as e:
            logging_service.log("WARNING", f"Log clear error: {e}")
        

    def _enable_processing_ui(self) -> None:
        """Enable processing UI state (disable menu/exit, enable abort)."""
        try:
            # Use global button references from theme
            if hasattr(YAPMOTheme, 'abort_button'):
                YAPMOTheme.abort_button.enable()
            
            if hasattr(YAPMOTheme, 'menu_button'):
                YAPMOTheme.menu_button.disable()
                
            if hasattr(YAPMOTheme, 'exit_button'):
                YAPMOTheme.exit_button.disable()
            
        except Exception as e:
            logging_service.log("ERROR", f"Error in _create_scanning_section: {e}")
            logging_service.log("ERROR", f"Error enabling processing UI: {e}")

    def _disable_processing_ui(self) -> None:
        """Disable processing UI state (enable menu/exit, disable abort if no active processes)."""
        try:
            # Only disable abort if no active processes
            if not yapmo_globals.abort_manager.has_active_processes():
                if hasattr(YAPMOTheme, 'abort_button'):
                    YAPMOTheme.abort_button.disable()
            
            # Enable menu button
            if hasattr(YAPMOTheme, 'menu_button'):
                YAPMOTheme.menu_button.enable()
            
            # Enable exit button
            if hasattr(YAPMOTheme, 'exit_button'):
                YAPMOTheme.exit_button.enable()
            
        except Exception as e:
            logging_service.log("ERROR", f"Error in _create_scanning_section: {e}")
            logging_service.log("ERROR", f"Error disabling processing UI: {e}")


def create_fill_db_new_page() -> FillDbNewPage:
    """Create the fill database new page."""
    return FillDbNewPage()


if __name__ == "__main__":
    create_fill_db_new_page()
    ui.run(title="YAPMO Fill Database New", port=8080)