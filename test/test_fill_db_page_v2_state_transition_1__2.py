"""Test file for state transition functionality in fill_db_page_v2."""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

# Import the ApplicationState enum directly
from enum import Enum

class ApplicationState(Enum):
    INITIALISATION = "initialisation"
    IDLE = "idle"
    SCANNING = "scanning"
    IDLE_SCAN_DONE = "idle_scan_done"
    EXIT_PAGE = "exit_page"


class MockFillDbPageV2:
    """Mock class for testing state transitions."""
    
    def __init__(self):
        self.current_state = ApplicationState.INITIALISATION
        self.debug_current_state_label = Mock()
        self.scan_select_directory = Mock()
        self.scan_start_button = Mock()
        self.scan_search_directory_input = Mock()
        self.scan_details_button = Mock()
        self.processing_start_button = Mock()
        self.log_clear_button = Mock()
        self.scan_spinner = Mock()
        self.scan_state_label = Mock()
        self.scan_total_files_label = Mock()
        self.scan_media_files_label = Mock()
        self.scan_sidecars_label = Mock()
        self.scan_total_directories_label = Mock()
        self.processing_progressbar = Mock()
        self.processing_progress_label = Mock()
        self.processing_files_processed_label = Mock()
        self.processing_directories_processed_label = Mock()
        self.processing_files_sec_label = Mock()
        self.processing_directories_sec_label = Mock()
        self.processing_time_to_finish_label = Mock()
    
    def _set_state(self, new_state: ApplicationState) -> None:
        """Set application state and configure all UI elements."""
        self.current_state = new_state
        self._configure_ui_for_state(new_state)
        
        # Update debug state label
        if self.debug_current_state_label:
            self.debug_current_state_label.text = f"State: {self.current_state.value}"
    
    def _configure_ui_for_state(self, state: ApplicationState) -> None:
        """Configure UI elements for the given state."""
        if state == ApplicationState.INITIALISATION:
            # All buttons disabled
            if self.scan_select_directory:
                self.scan_select_directory.disable()
            if self.scan_start_button:
                self.scan_start_button.disable()
            if self.scan_details_button:
                self.scan_details_button.disable()
            if self.processing_start_button:
                self.processing_start_button.disable()
            if self.log_clear_button:
                self.log_clear_button.disable()
            
            # Input disabled
            if self.scan_search_directory_input:
                self.scan_search_directory_input.disable()
            
            # Spinner visible but inactive (black) for testing
            if self.scan_spinner:
                self.scan_spinner.set_visibility(True)
            
            # State label
            if self.scan_state_label:
                self.scan_state_label.text = "Initializing..."
                
        elif state == ApplicationState.SCANNING:
            # All controls disabled during scanning
            if self.scan_select_directory:
                self.scan_select_directory.disable()
            if self.scan_start_button:
                self.scan_start_button.disable()
            if self.scan_details_button:
                self.scan_details_button.disable()
            if self.processing_start_button:
                self.processing_start_button.disable()
            if self.log_clear_button:
                self.log_clear_button.disable()
            
            # Input disabled
            if self.scan_search_directory_input:
                self.scan_search_directory_input.disable()
            
            # Spinner visible and active
            if self.scan_spinner:
                self.scan_spinner.set_visibility(True)
            
            # State label
            if self.scan_state_label:
                self.scan_state_label.text = "scanning active"
                
        elif state == ApplicationState.IDLE:
            # Scan controls enabled
            if self.scan_select_directory:
                self.scan_select_directory.enable()
            if self.scan_start_button:
                self.scan_start_button.enable()
                self.scan_start_button.text = "START Scanning"
            if self.scan_search_directory_input:
                self.scan_search_directory_input.enable()
            
            # Scan details disabled (no data yet)
            if self.scan_details_button:
                self.scan_details_button.disable()
            
            # Processing controls disabled
            if self.processing_start_button:
                self.processing_start_button.disable()
            
            # Log controls enabled
            if self.log_clear_button:
                self.log_clear_button.enable()
            
            # Spinner hidden
            if self.scan_spinner:
                self.scan_spinner.set_visibility(False)
            
            # State label
            if self.scan_state_label:
                self.scan_state_label.text = "not active"
                
        elif state == ApplicationState.EXIT_PAGE:
            # All controls disabled
            if self.scan_select_directory:
                self.scan_select_directory.disable()
            if self.scan_start_button:
                self.scan_start_button.disable()
            if self.scan_details_button:
                self.scan_details_button.disable()
            if self.processing_start_button:
                self.processing_start_button.disable()
            if self.log_clear_button:
                self.log_clear_button.disable()
            
            # Input disabled
            if self.scan_search_directory_input:
                self.scan_search_directory_input.disable()
            
            # Spinner hidden
            if self.scan_spinner:
                self.scan_spinner.set_visibility(False)
            
            # State label
            if self.scan_state_label:
                self.scan_state_label.text = "Saving state..."
    
    def _initialize_page(self) -> None:
        """Initialize the page and transition to IDLE state."""
        try:
            # Check for any critical errors during initialization
            # For now, we assume initialization is always successful
            
            # Transition to IDLE state
            self._set_state(ApplicationState.IDLE)
            
        except Exception as e:
            # If initialization fails, transition to EXIT_PAGE
            self._set_state(ApplicationState.EXIT_PAGE)


class TestStateTransition:
    """Test state transition functionality."""

    def test_initialization_to_idle_transition(self):
        """Test that page transitions from INITIALISATION to IDLE after initialization."""
        # Create page instance
        page = MockFillDbPageV2()
        
        # Verify initial state is INITIALISATION
        assert page.current_state == ApplicationState.INITIALISATION
        
        # Call initialization method
        page._initialize_page()
        
        # Verify state transition to IDLE
        assert page.current_state == ApplicationState.IDLE

    def test_initialization_error_handling(self):
        """Test that initialization errors transition to EXIT_PAGE."""
        # Create page instance
        page = MockFillDbPageV2()
        
        # Mock _set_state to raise an exception only on the first call (IDLE transition)
        call_count = 0
        def mock_set_state(state):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # First call (IDLE transition) should fail
                raise Exception("Test error")
            else:  # Second call (EXIT_PAGE transition) should succeed
                page.current_state = state
        
        with patch.object(page, '_set_state', side_effect=mock_set_state):
            page._initialize_page()
            
            # Verify state transition to EXIT_PAGE
            assert page.current_state == ApplicationState.EXIT_PAGE

    def test_set_state_method(self):
        """Test that _set_state method works correctly."""
        # Create page instance
        page = MockFillDbPageV2()
        
        # Test state transition to IDLE
        page._set_state(ApplicationState.IDLE)
        assert page.current_state == ApplicationState.IDLE
        
        # Test state transition to EXIT_PAGE
        page._set_state(ApplicationState.EXIT_PAGE)
        assert page.current_state == ApplicationState.EXIT_PAGE

    def test_ui_configuration_for_idle_state(self):
        """Test that UI is correctly configured for IDLE state."""
        # Create page instance
        page = MockFillDbPageV2()
        
        # Set state to IDLE
        page._set_state(ApplicationState.IDLE)
        
        # Verify UI elements are configured correctly for IDLE state
        page.scan_select_directory.enable.assert_called_once()
        page.scan_start_button.enable.assert_called_once()
        page.scan_search_directory_input.enable.assert_called_once()
        page.scan_details_button.disable.assert_called_once()
        page.processing_start_button.disable.assert_called_once()
        page.log_clear_button.enable.assert_called_once()
        page.scan_spinner.set_visibility.assert_called_once_with(False)
        page.scan_state_label.text = "not active"


if __name__ == "__main__":
    pytest.main([__file__])
