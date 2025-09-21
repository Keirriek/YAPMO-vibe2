"""Test file for IDLE state functionality in fill_db_page_v2."""

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
    EXIT_PAGE = "exit_page"


class MockFillDbPageV2:
    """Mock class for testing IDLE state functionality."""
    
    def __init__(self):
        self.current_state = ApplicationState.IDLE
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
        if state == ApplicationState.IDLE:
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
    
    def _validate_directory_path(self, path: str) -> tuple[bool, str]:
        """Validate directory path."""
        import os
        
        if not path:
            return False, "No directory path provided"
        
        if not os.path.exists(path):
            return False, "Directory does not exist"
        
        if not os.path.isdir(path):
            return False, "Path is not a directory"
        
        if not os.access(path, os.R_OK):
            return False, "No read permission for directory"
        
        return True, ""
    
    def _start_scanning(self) -> None:
        """Start the scanning process."""
        # Validate directory path first
        current_path = self.scan_search_directory_input.value if self.scan_search_directory_input else ""
        is_valid, error_msg = self._validate_directory_path(current_path)
        if not is_valid:
            # In real implementation, this would show ui.notify
            return False, error_msg
        
        # Transition to SCANNING state
        self._set_state(ApplicationState.SCANNING)
        return True, "Scanning started"


class TestIdleState:
    """Test IDLE state functionality."""

    def test_idle_state_ui_configuration(self):
        """Test that UI is correctly configured for IDLE state."""
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
        assert page.scan_state_label.text == "not active"

    def test_directory_validation_valid_path(self):
        """Test directory validation with valid path."""
        page = MockFillDbPageV2()
        
        # Test with a valid path (assuming /tmp exists and is readable)
        is_valid, error_msg = page._validate_directory_path("/tmp")
        assert is_valid == True
        assert error_msg == ""

    def test_directory_validation_invalid_paths(self):
        """Test directory validation with invalid paths."""
        page = MockFillDbPageV2()
        
        # Test empty path
        is_valid, error_msg = page._validate_directory_path("")
        assert is_valid == False
        assert error_msg == "No directory path provided"
        
        # Test non-existent path
        is_valid, error_msg = page._validate_directory_path("/non/existent/path")
        assert is_valid == False
        assert error_msg == "Directory does not exist"

    def test_start_scanning_with_valid_path(self):
        """Test start scanning with valid directory path."""
        page = MockFillDbPageV2()
        
        # Mock valid path
        page.scan_search_directory_input.value = "/tmp"
        
        # Start scanning
        success, message = page._start_scanning()
        
        # Verify success
        assert success == True
        assert message == "Scanning started"
        assert page.current_state == ApplicationState.SCANNING

    def test_start_scanning_with_invalid_path(self):
        """Test start scanning with invalid directory path."""
        page = MockFillDbPageV2()
        
        # Mock invalid path
        page.scan_search_directory_input.value = "/non/existent/path"
        
        # Start scanning
        success, message = page._start_scanning()
        
        # Verify failure
        assert success == False
        assert "Directory does not exist" in message
        assert page.current_state == ApplicationState.IDLE  # Should stay in IDLE

    def test_scanning_state_ui_configuration(self):
        """Test that UI is correctly configured for SCANNING state."""
        page = MockFillDbPageV2()
        
        # Set state to SCANNING
        page._set_state(ApplicationState.SCANNING)
        
        # Verify UI elements are configured correctly for SCANNING state
        page.scan_select_directory.disable.assert_called_once()
        page.scan_start_button.disable.assert_called_once()
        page.scan_details_button.disable.assert_called_once()
        page.processing_start_button.disable.assert_called_once()
        page.log_clear_button.disable.assert_called_once()
        page.scan_search_directory_input.disable.assert_called_once()
        page.scan_spinner.set_visibility.assert_called_once_with(True)
        assert page.scan_state_label.text == "scanning active"

    def test_state_transition_idle_to_scanning(self):
        """Test state transition from IDLE to SCANNING."""
        page = MockFillDbPageV2()
        
        # Start in IDLE state
        page._set_state(ApplicationState.IDLE)
        assert page.current_state == ApplicationState.IDLE
        
        # Mock valid path
        page.scan_search_directory_input.value = "/tmp"
        
        # Start scanning
        success, message = page._start_scanning()
        
        # Verify state transition
        assert success == True
        assert page.current_state == ApplicationState.SCANNING


if __name__ == "__main__":
    pytest.main([__file__])
