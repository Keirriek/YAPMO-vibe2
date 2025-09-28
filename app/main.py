"""YAPMO Main Entry Point - Yet Another Photo Manager and Organizer."""

import os
from nicegui import ui

# Import all pages to register them
from pages.main_page import create_main_page
from pages.config_page import create_config_page
from pages.element_test_page import create_element_test_page
# from pages.fill_db_new import create_fill_db_new_page
from pages.fill_db_page_v2 import create_fill_db_page_v2
# from pages.test_traverse_page import create_test_traverse_page  # Removed
from config import get_param, show_default_config_dialog, was_config_created, has_json_error, has_validation_error, show_json_error_dialog, show_validation_error_dialog

RELOAD = False

def main() -> None:
    """Main entry point for the YAPMO application."""
    # Import config to ensure it's initialized (will create config.json if missing)
    if RELOAD and __name__ == '__main__':
        ui.run(host='127.0.0.1', port=8080, reload=RELOAD)
        return
    from config import config_manager
    
    # Create all pages
    create_main_page()
    create_config_page()
    create_element_test_page()
    # create_fill_db_new_page()
    create_fill_db_page_v2()
    # create_test_traverse_page()  # Removed

    # Check for config errors will be done in main page

    # Run the application
    app_title = f"{get_param('general', 'app_name')} - {get_param('general', 'app_description')}"
    ui.run(
        title=app_title,
        port=8080,
        show=True,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
