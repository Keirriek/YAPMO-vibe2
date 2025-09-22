"""Debug functionality for Fill Database V2 Page."""

from typing import Any
from nicegui import ui
from core.logging_service_v2 import logging_service


class FillDbPageV2Debug:
    """Debug helper class for FillDbPageV2."""
    
    def __init__(self, parent_page: Any) -> None:
        """Initialize debug helper with reference to parent page."""
        self.parent_page = parent_page
        self.debug_counter = 0
        
    def create_debug_section(self) -> None:
        """Create the debug section (temporary)."""
        with ui.card().classes("w-full bg-white rounded-lg mb-6"), ui.card_section():
            ui.label("DEBUG").classes("text-xl font-bold mb-4")
            
            # Current State Display
            ui.label("Current State").classes("text-lg font-bold mb-2")
            self.parent_page.debug_current_state_label = ui.label(
                f"State: {self.parent_page.current_state.value}"
            ).classes("text-xl font-bold text-blue-600")
            
            # UI Update Control
            ui.label("UI Update Control").classes("text-lg font-bold mb-2")
            
            with ui.row().classes("gap-2"):
                self.parent_page.debug_start_ui_btn = ui.button(
                    "Start UI Update", 
                    on_click=self.debug_start_ui_update
                )
                self.parent_page.debug_stop_ui_btn = ui.button(
                    "Stop UI Update", 
                    on_click=self.debug_stop_ui_update
                )
                self.parent_page.debug_status_ui_label = ui.label("Status: Stopped")
            
            # Log Message Testing
            ui.label("Log Message Testing").classes("text-lg font-bold mb-2")
            
            with ui.row().classes("gap-2"):
                self.parent_page.debug_log_input = ui.input("Log message").classes("flex-1")
                self.parent_page.debug_add_log_btn = ui.button(
                    "Add Log", 
                    on_click=self.debug_add_log_message
                )
            
            # Queue Status
            with ui.row().classes("gap-2"):
                self.parent_page.debug_show_queue_btn = ui.button(
                    "Show Queue", 
                    on_click=self.debug_show_log_queue
                )
                self.parent_page.debug_queue_count_label = ui.label("Queue: 0")
            
            # Flag Status Display
            ui.label("Flag Status").classes("text-lg font-bold mb-2")
            
            with ui.row().classes("gap-4"):
                self.parent_page.debug_ui_update_timer_label = ui.label("UI Update Timer: OFF")
                self.parent_page.debug_ui_update_finished_label = ui.label("ui_update_finished: false")
                self.parent_page.debug_action_finished_label = ui.label("action_finished: false")
                self.parent_page.debug_ui_finished_label = ui.label("ui_finished: false")
            
            # Direct UI Test
            ui.label("Direct UI Test").classes("text-lg font-bold mb-2")
            
            with ui.row().classes("gap-2"):
                self.parent_page.debug_direct_update_btn = ui.button(
                    "Direct Update", 
                    on_click=self.debug_direct_update
                )
                self.parent_page.debug_counter_label = ui.label("Counter: 0")
    
    def update_debug_state_label(self) -> None:
        """Update debug state label."""
        if hasattr(self.parent_page, 'debug_current_state_label') and self.parent_page.debug_current_state_label:
            self.parent_page.debug_current_state_label.text = f"State: {self.parent_page.current_state.value}"
    
    def update_debug_flags(self) -> None:
        """Update debug flag status labels."""
        import yapmo_globals
        
        # Update UI update timer status
        if hasattr(self.parent_page, 'debug_ui_update_timer_label') and self.parent_page.debug_ui_update_timer_label:
            timer_status = "ON" if self.parent_page.ui_update_manager.timer_active else "OFF"
            self.parent_page.debug_ui_update_timer_label.text = f"UI Update Timer: {timer_status}"
        
        # Update flag status
        if hasattr(self.parent_page, 'debug_ui_update_finished_label') and self.parent_page.debug_ui_update_finished_label:
            self.parent_page.debug_ui_update_finished_label.text = f"ui_update_finished: {yapmo_globals.ui_update_finished}"
        
        if hasattr(self.parent_page, 'debug_action_finished_label') and self.parent_page.debug_action_finished_label:
            self.parent_page.debug_action_finished_label.text = f"action_finished: {yapmo_globals.action_finished_flag}"
        
        if hasattr(self.parent_page, 'debug_ui_finished_label') and self.parent_page.debug_ui_finished_label:
            self.parent_page.debug_ui_finished_label.text = f"ui_finished: N/A (removed)"
    
    def debug_start_ui_update(self) -> None:
        """Debug: Start UI update cycle."""
        ui.notify("UI Update functionality not implemented yet", type="info")
    
    def debug_stop_ui_update(self) -> None:
        """Debug: Stop UI update cycle."""
        ui.notify("UI Update functionality not implemented yet", type="info")
    
    def debug_add_log_message(self) -> None:
        """Debug: Add a log message to the queue."""
        if not hasattr(self.parent_page, 'debug_log_input') or not self.parent_page.debug_log_input:
            ui.notify("Debug log input not available", type="error")
            return
            
        message = self.parent_page.debug_log_input.value
        if not message:
            ui.notify("Please enter a message", type="warning")
            return
            
        try:
            # Add message to logging service
            logging_service.log_info(f"DEBUG: {message}")
            
            # Update counter
            if hasattr(self.parent_page, 'debug_counter_label') and self.parent_page.debug_counter_label:
                self.debug_counter += 1
                new_count = self.debug_counter
                self.parent_page.debug_counter_label.text = f"Counter: {new_count}"
            
            ui.notify(f"Added to queue: {message} (Total: {self.debug_counter})", type="info")
            self.parent_page.debug_log_input.value = ""
            
        except Exception as e:
            ui.notify(f"Error adding log message: {str(e)}", type="error")
    
    def debug_show_log_queue(self) -> None:
        """Debug: Show log queue status."""
        try:
            # Get messages from logging service
            messages = logging_service.get_ui_messages()
            message_count = len(messages)
            
            # Update queue count label
            if hasattr(self.parent_page, 'debug_queue_count_label') and self.parent_page.debug_queue_count_label:
                self.parent_page.debug_queue_count_label.text = f"Queue: {message_count}"
            
            # Show all messages in notification
            if messages:
                message_text = "\n".join([f"{i+1}. {msg}" for i, msg in enumerate(messages)])
                ui.notify(f"Queue has {message_count} messages:\n{message_text}", type="info", timeout=10000)
            else:
                ui.notify("Queue is empty", type="info")
                
        except Exception as e:
            ui.notify(f"Error checking queue: {str(e)}", type="error")
    
    def debug_ui_update_cycle(self) -> None:
        """Debug: UI update cycle - called by timer."""
        ui.notify("UI Update functionality not implemented yet", type="info")
    
    def debug_update_ui_elements(self) -> None:
        """Debug: Update UI elements based on current state."""
        ui.notify("UI Update functionality not implemented yet", type="info")
    
    def debug_direct_update(self) -> None:
        """Debug: Direct UI update test."""
        try:
            # Update counter
            if hasattr(self.parent_page, 'debug_counter_label') and self.parent_page.debug_counter_label:
                self.debug_counter += 1
                self.parent_page.debug_counter_label.text = f"Counter: {self.debug_counter}"
                ui.notify(f"Direct update: Counter = {self.debug_counter}", type="info")
            else:
                ui.notify("Debug counter label not available", type="error")
                
        except Exception as e:
            ui.notify(f"Error in direct update: {str(e)}", type="error")
