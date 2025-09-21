"""Work1 Page - Werk pagina 1 van de YAPMO applicatie."""

from contextlib import suppress
from typing import Any

from globals import logging_service
from nicegui import ui
from shutdown_manager import handle_exit_click
from theme import LoggingUI, YAPMOTheme


class Work1Page:
    """Werk pagina van de YAPMO applicatie."""

    def __init__(self) -> None:
        """Initialize the work page."""
        self.log_input: Any | None = None
        self.logging_ui: LoggingUI | None = None
        self._create_page()

    def _create_page(self) -> None:
        """Maak de werk pagina."""

        @ui.page("/work1")
        def work1_page() -> None:
            # Reload config when page is visited
            self._reload_config()

            with YAPMOTheme.page_frame("Work1", exit_handler=handle_exit_click):
                self._create_content()

    def _reload_config(self) -> None:
        """Reload the configuration."""
        with suppress(Exception):
            # Force reload van de config in de logging service
            logging_service._load_config()  # noqa: SLF001

    def _create_content(self) -> None:
        """Maak de content van de werk pagina."""
        # Header section
        with ui.card().classes("w-full mb-6"):
            ui.label("Work Area").classes("text-h6 q-mb-md")
            ui.label("Work functionality will be implemented here").classes(
                "text-body1")

            # Input field and buttons section
            with ui.row().classes("w-full justify-between items-center mt-4"):
                # Input field
                self.log_input = ui.input(
                    placeholder="Enter log message",
                    value="INFO 2",
                ).classes("flex-grow mr-4")

                # Buttons
                with ui.row().classes("gap-2"):
                    YAPMOTheme.create_button(
                        "ADD INFO", self._add_info_log, "primary", "sm")
                    YAPMOTheme.create_button(
                        "ADD WARNING", self._add_warning_log, "warning", "sm")
                    YAPMOTheme.create_button(
                        "ADD ERROR", self._add_error_log, "negative", "sm")
                    YAPMOTheme.create_button(
                        "ADD DEV", self._add_dev_log, "info", "sm")

        # Test Logging Section
        with ui.card().classes("w-full mb-6"):
            ui.label("Test Logging Section").classes("text-h6 q-mb-md")

            # Gestandaardiseerde logging UI
            self.logging_ui = LoggingUI(
                title="Log Messages",
                show_checkboxes=True,
                show_clear_button=True,
                scroll_height=10,
            )
            self.logging_ui.create_ui()

    def _add_info_log(self) -> None:
        """Voeg INFO log toe."""
        if self.log_input and self.log_input.value:
            message = self.log_input.value
            logging_service.log("INFO", message)

    def _add_warning_log(self) -> None:
        """Voeg WARNING log toe."""
        if self.log_input and self.log_input.value:
            message = self.log_input.value
            logging_service.log("WARNING", message)

    def _add_error_log(self) -> None:
        """Voeg ERROR log toe."""
        if self.log_input and self.log_input.value:
            message = self.log_input.value
            logging_service.log("ERROR", message)

    def _add_dev_log(self) -> None:
        """Voeg DEV log toe."""
        if self.log_input and self.log_input.value:
            message = self.log_input.value
            logging_service.log("DEV", message)


def create_work1_page() -> Work1Page:
    """Maak de werk pagina."""
    return Work1Page()


if __name__ == "__main__":
    create_work1_page()
    ui.run(title="Work1 Page", port=8081)
