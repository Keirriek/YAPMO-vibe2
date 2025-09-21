"""Main Page - Hoofdpagina van de YAPMO applicatie."""

from nicegui import ui
from shutdown_manager import handle_exit_click
from theme import YAPMOTheme
from config import get_param, show_default_config_dialog, has_json_error, has_validation_error, show_json_error_dialog, show_validation_error_dialog


class MainPage:
    """Main page van de YAPMO applicatie."""

    def __init__(self) -> None:
        """Initialize the main page."""
        self._create_page()

    def _create_page(self) -> None:
        """Maak de main page."""

        @ui.page("/")
        def main_page() -> None:
            with YAPMOTheme.page_frame("Main Page", exit_handler=handle_exit_click):
                self._create_content()
                # Check for config errors and show dialogs if needed
                if has_json_error():
                    show_json_error_dialog()
                elif has_validation_error():
                    show_validation_error_dialog()
                elif get_param("general", "default_config"):
                    show_default_config_dialog()

    def _create_content(self) -> None:
        """Create the content of the main page."""
        self._create_welcome_section()
        self._create_navigation_section()
        self._create_info_section()

    def _create_welcome_section(self) -> None:
        """Create the welcome section."""
        with ui.card().classes("w-full mb-6"), ui.card_section():
            app_name = get_param("general", "app_name")
            app_description = get_param("general", "app_description")
            ui.label(f"Welcome to {app_name}").classes(
                "text-3xl font-bold text-center mb-4")
            ui.label(
                f"{app_description} - Your media management solution",
            ).classes("text-lg text-center text-gray-600")

    def _create_navigation_section(self) -> None:
        """Create the navigation section."""
        with ui.card().classes("w-full mb-6"), ui.card_section():
            ui.label("Navigation").classes("text-xl font-bold mb-4")
            with ui.row().classes("gap-4 flex-wrap justify-center"):
                YAPMOTheme.create_button(
                    "Configuration",
                    lambda: ui.navigate.to("/config"),
                    "primary",
                    "lg",
                )
                YAPMOTheme.create_button(
                    "Element Test",
                    lambda: ui.navigate.to("/element-test"),
                    "secondary",
                    "lg",
                )
                YAPMOTheme.create_button(
                    "Fill Database New",
                    lambda: ui.navigate.to("/fill-db-new"),
                    "primary",
                    "lg",
                )
                YAPMOTheme.create_button(
                    "Fill Database Page V2",
                    lambda: ui.navigate.to("/fill-db-page-v2"),
                    "secondary",
                    "lg",
                )
                # YAPMOTheme.create_button(
                #     "Test Traverse",
                #     lambda: ui.navigate.to("/test-traverse"),
                #     "secondary",
                #     "lg",
                # )  # Removed

    def _create_info_section(self) -> None:
        """Create the info section."""
        with ui.card().classes("w-full mb-6"), ui.card_section():
            ui.label("Application Information").classes("text-xl font-bold mb-4")
            with ui.column().classes("gap-2"):
                app_version = get_param("general", "app_version")
                ui.label(f"Version: {app_version}").classes("text-base")
                ui.label("Status: Ready").classes("text-base text-green-600")
                ui.label("Features:").classes("text-base font-medium mt-2")
                with ui.column().classes("ml-4 gap-1"):
                    ui.label("• Modular page structure").classes("text-sm")
                    ui.label("• Consistent UI theme").classes("text-sm")
                    ui.label("• Element testing capabilities").classes("text-sm")
                    ui.label("• Configuration management").classes("text-sm")


def create_main_page() -> MainPage:
    """Maak de main page."""
    return MainPage()


if __name__ == "__main__":
    create_main_page()
    ui.run(title="YAPMO Main Page", port=8080)
