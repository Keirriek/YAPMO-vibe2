"""Test file for fill_db_page_v2 state machine functionality."""

import pytest
from unittest.mock import Mock, patch
from pages.fill_db_page_v2 import FillDbPageV2, ApplicationState


class TestFillDbPageV2States:
    """Test class for FillDbPageV2 state machine."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Mock UI elements to avoid NiceGUI dependency
        self.mock_ui_elements = {
            'scan_select_directory': Mock(),
            'scan_start_button': Mock(),
            'scan_details_button': Mock(),
            'processing_start_button': Mock(),
            'log_clear_button': Mock(),
            'scan_search_directory_input': Mock(),
            'scan_spinner': Mock(),
            'scan_state_label': Mock(),
            'scan_total_files_label': Mock(),
            'scan_media_files_label': Mock(),
            'scan_sidecars_label': Mock(),
            'scan_total_directories_label': Mock(),
            'processing_progressbar': Mock(),
            'processing_progress_label': Mock(),
            'processing_files_processed_label': Mock(),
            'processing_directories_processed_label': Mock(),
            'processing_files_sec_label': Mock(),
            'processing_directories_sec_label': Mock(),
            'processing_time_to_finish_label': Mock(),
            'debug_current_state_label': Mock(),
        }

    @patch('pages.fill_db_page_v2.ui')
    def test_initialization_state(self, mock_ui: Mock) -> None:
        """Test INITIALISATION state configuration."""
        # Create page instance
        page = FillDbPageV2()
        
        # Mock UI elements
        for attr_name, mock_element in self.mock_ui_elements.items():
            setattr(page, attr_name, mock_element)
        
        # Test INITIALISATION state
        page._set_state(ApplicationState.INITIALISATION)
        
        # Verify state is set
        assert page.current_state == ApplicationState.INITIALISATION
        
        # Verify UI elements are configured correctly
        assert page.scan_select_directory.disable.called
        assert page.scan_start_button.disable.called
        assert page.scan_details_button.disable.called
        assert page.processing_start_button.disable.called
        assert page.log_clear_button.disable.called
        assert page.scan_search_directory_input.disable.called
        
        # Verify spinner is visible
        assert page.scan_spinner.set_visibility.called_with(True)
        
        # Verify state label
        assert page.scan_state_label.text == "Initializing..."
        
        # Verify debug state label is updated
        assert page.debug_current_state_label.text == "State: initialisation"

    @patch('pages.fill_db_page_v2.ui')
    def test_idle_state(self, mock_ui: Mock) -> None:
        """Test IDLE state configuration."""
        # Create page instance
        page = FillDbPageV2()
        
        # Mock UI elements
        for attr_name, mock_element in self.mock_ui_elements.items():
            setattr(page, attr_name, mock_element)
        
        # Test IDLE state
        page._set_state(ApplicationState.IDLE)
        
        # Verify state is set
        assert page.current_state == ApplicationState.IDLE
        
        # Verify UI elements are configured correctly
        assert page.scan_select_directory.enable.called
        assert page.scan_start_button.enable.called
        assert page.scan_start_button.text == "START Scanning"
        assert page.scan_search_directory_input.enable.called
        
        # Verify scan details is disabled (no data yet)
        assert page.scan_details_button.disable.called
        
        # Verify processing controls are disabled
        assert page.processing_start_button.disable.called
        
        # Verify log controls are enabled
        assert page.log_clear_button.enable.called
        
        # Verify spinner is hidden
        assert page.scan_spinner.set_visibility.called_with(False)
        
        # Verify state label
        assert page.scan_state_label.text == "not active"
        
        # Verify debug state label is updated
        assert page.debug_current_state_label.text == "State: idle"

    @patch('pages.fill_db_page_v2.ui')
    def test_scanning_state(self, mock_ui: Mock) -> None:
        """Test SCANNING state configuration."""
        # Create page instance
        page = FillDbPageV2()
        
        # Mock UI elements
        for attr_name, mock_element in self.mock_ui_elements.items():
            setattr(page, attr_name, mock_element)
        
        # Test SCANNING state
        page._set_state(ApplicationState.SCANNING)
        
        # Verify state is set
        assert page.current_state == ApplicationState.SCANNING
        
        # Verify UI elements are configured correctly
        assert page.scan_select_directory.disable.called
        assert page.scan_start_button.disable.called
        assert page.scan_search_directory_input.disable.called
        
        # Verify scan details is disabled (scanning in progress)
        assert page.scan_details_button.disable.called
        
        # Verify processing controls are disabled
        assert page.processing_start_button.disable.called
        
        # Verify log controls are enabled
        assert page.log_clear_button.enable.called
        
        # Verify spinner is visible and active
        assert page.scan_spinner.set_visibility.called_with(True)
        
        # Verify state label
        assert page.scan_state_label.text == "scanning..."
        
        # Verify debug state label is updated
        assert page.debug_current_state_label.text == "State: scanning"

    @patch('pages.fill_db_page_v2.ui')
    def test_idle_scan_done_state(self, mock_ui: Mock) -> None:
        """Test IDLE_SCAN_DONE state configuration."""
        # Create page instance
        page = FillDbPageV2()
        
        # Mock UI elements
        for attr_name, mock_element in self.mock_ui_elements.items():
            setattr(page, attr_name, mock_element)
        
        # Test IDLE_SCAN_DONE state
        page._set_state(ApplicationState.IDLE_SCAN_DONE)
        
        # Verify state is set
        assert page.current_state == ApplicationState.IDLE_SCAN_DONE
        
        # Verify UI elements are configured correctly
        assert page.scan_select_directory.enable.called
        assert page.scan_start_button.enable.called
        assert page.scan_start_button.text == "RESET"
        assert page.scan_search_directory_input.enable.called
        
        # Verify scan details is enabled (scan data available)
        assert page.scan_details_button.enable.called
        
        # Verify processing controls are enabled
        assert page.processing_start_button.enable.called
        
        # Verify log controls are enabled
        assert page.log_clear_button.enable.called
        
        # Verify spinner is hidden
        assert page.scan_spinner.set_visibility.called_with(False)
        
        # Verify state label
        assert page.scan_state_label.text == "scan complete"
        
        # Verify debug state label is updated
        assert page.debug_current_state_label.text == "State: idle_scan_done"

    @patch('pages.fill_db_page_v2.ui')
    def test_state_transitions(self, mock_ui: Mock) -> None:
        """Test state transitions work correctly."""
        # Create page instance
        page = FillDbPageV2()
        
        # Mock UI elements
        for attr_name, mock_element in self.mock_ui_elements.items():
            setattr(page, attr_name, mock_element)
        
        # Test multiple state transitions
        states_to_test = [
            ApplicationState.INITIALISATION,
            ApplicationState.IDLE,
            ApplicationState.SCANNING,
            ApplicationState.IDLE_SCAN_DONE,
            ApplicationState.FILE_PROCESSING,
            ApplicationState.IDLE_PROCESSING_DONE,
            ApplicationState.ABORTED,
            ApplicationState.IDLE_AFTER_ABORT,
            ApplicationState.EXIT_PAGE,
        ]
        
        for state in states_to_test:
            page._set_state(state)
            assert page.current_state == state
            assert page.debug_current_state_label.text == f"State: {state.value}"

    @patch('pages.fill_db_page_v2.ui')
    def test_ui_element_safety(self, mock_ui: Mock) -> None:
        """Test that _set_state handles None UI elements safely."""
        # Create page instance
        page = FillDbPageV2()
        
        # Don't set any UI elements (they should be None)
        # This should not raise an exception
        page._set_state(ApplicationState.IDLE)
        
        # Verify state is still set correctly
        assert page.current_state == ApplicationState.IDLE

    def test_application_state_enum(self) -> None:
        """Test that ApplicationState enum has all required values."""
        expected_states = [
            "initialisation",
            "idle", 
            "scanning",
            "idle_scan_done",
            "file_processing",
            "idle_processing_done",
            "aborted",
            "idle_after_abort",
            "exit_page",
        ]
        
        actual_states = [state.value for state in ApplicationState]
        
        for expected_state in expected_states:
            assert expected_state in actual_states, f"Missing state: {expected_state}"
        
        assert len(actual_states) == len(expected_states), "Unexpected number of states"


if __name__ == "__main__":
    pytest.main([__file__])
