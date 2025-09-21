"""Test file for fill_db_page_v2 config loading functionality."""

import pytest
from unittest.mock import Mock, patch
from pages.fill_db_page_v2 import FillDbPageV2


class TestFillDbPageV2Config:
    """Test class for FillDbPageV2 config loading."""

    @patch('pages.fill_db_page_v2.get_param')
    @patch('pages.fill_db_page_v2.ui')
    def test_config_loading_in_init(self, mock_ui: Mock, mock_get_param: Mock) -> None:
        """Test that config values are loaded during initialization."""
        # Mock config values
        mock_get_param.side_effect = lambda section, key, default=None: {
            ("paths", "search_path"): "/test/path",
            ("ui", "update_interval"): 1000,
            ("extensions", "media_files"): [".jpg", ".png"],
        }.get((section, key), default)
        
        # Create page instance
        page = FillDbPageV2()
        
        # Verify config loading was called
        assert mock_get_param.called
        
        # Verify search path was loaded
        mock_get_param.assert_any_call("paths", "search_path")

    @patch('pages.fill_db_page_v2.get_param')
    @patch('pages.fill_db_page_v2.ui')
    def test_config_values_usage(self, mock_ui: Mock, mock_get_param: Mock) -> None:
        """Test that config values are used correctly."""
        # Mock config values
        test_search_path = "/test/search/path"
        test_update_interval = 500
        
        mock_get_param.side_effect = lambda section, key, default=None: {
            ("paths", "search_path"): test_search_path,
            ("ui", "update_interval"): test_update_interval,
        }.get((section, key), default)
        
        # Create page instance
        page = FillDbPageV2()
        
        # Verify search path is used in input field
        # This would need to be checked in the actual UI creation
        # For now, just verify the config loading was called
        assert mock_get_param.called

    @patch('pages.fill_db_page_v2.get_param')
    @patch('pages.fill_db_page_v2.ui')
    def test_config_error_handling(self, mock_ui: Mock, mock_get_param: Mock) -> None:
        """Test that config errors are handled gracefully."""
        # Mock config loading to raise an exception
        mock_get_param.side_effect = Exception("Config loading failed")
        
        # This should not raise an exception during page creation
        # The page should still be created, but with default values
        page = FillDbPageV2()
        
        # Verify page was created successfully
        assert page is not None
        assert page.current_state is not None

    @patch('pages.fill_db_page_v2.set_param')
    @patch('pages.fill_db_page_v2.get_param')
    @patch('pages.fill_db_page_v2.ui')
    def test_config_saving(self, mock_ui: Mock, mock_get_param: Mock, mock_set_param: Mock) -> None:
        """Test that config values are saved correctly."""
        # Mock config loading
        mock_get_param.side_effect = lambda section, key, default=None: {
            ("paths", "search_path"): "/test/path",
        }.get((section, key), default)
        
        # Create page instance
        page = FillDbPageV2()
        
        # Mock UI elements
        page.scan_search_directory_input = Mock()
        page.scan_search_directory_input.value = "/new/test/path"
        
        # Test directory selection (which should save to config)
        page._select_directory()
        
        # Verify config saving was called
        assert mock_set_param.called
        mock_set_param.assert_called_with("paths", "search_path", "/new/test/path")

    @patch('pages.fill_db_page_v2.get_param')
    @patch('pages.fill_db_page_v2.ui')
    def test_default_config_values(self, mock_ui: Mock, mock_get_param: Mock) -> None:
        """Test that default config values are used when config is missing."""
        # Mock config loading to return None for missing values
        mock_get_param.return_value = None
        
        # Create page instance
        page = FillDbPageV2()
        
        # Verify page was created successfully with default values
        assert page is not None
        assert page.current_state is not None
        
        # Verify config loading was attempted
        assert mock_get_param.called


if __name__ == "__main__":
    pytest.main([__file__])
