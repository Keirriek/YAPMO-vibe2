"""Debug functionality for Fill Database V2 Page."""

from typing import Any
from nicegui import ui


class FillDbPageV2Debug:
    """Debug helper class for FillDbPageV2."""
    
    def __init__(self, parent_page: Any) -> None:
        """Initialize debug helper with reference to parent page."""
        self.parent_page = parent_page
        
    def create_debug_section(self) -> None:
        """Create the debug section (minimal)."""
        with ui.card().classes("w-full bg-white rounded-lg mb-6"), ui.card_section():
            ui.label("DEBUG").classes("text-xl font-bold mb-4")
            
            # Current State Display
            ui.label("Current State").classes("text-lg font-bold mb-2")
            self.parent_page.debug_current_state_label = ui.label(
                f"State: {self.parent_page.current_state.value}"
            ).classes("text-xl font-bold text-blue-600")
    
    def update_debug_state_label(self) -> None:
        """Update debug state label."""
        if hasattr(self.parent_page, 'debug_current_state_label') and self.parent_page.debug_current_state_label:
            self.parent_page.debug_current_state_label.text = f"State: {self.parent_page.current_state.value}"
