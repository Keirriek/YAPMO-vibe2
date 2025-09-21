"""SQL Page voor YAPMO applicatie."""

from nicegui import ui
from shutdown_manager import handle_exit_click
from theme import YAPMOTheme


class SQLPage:
    """SQL query pagina van de YAPMO applicatie."""

    def __init__(self) -> None:
        """Initialize the SQL page."""
        self._create_page()

    def _create_page(self) -> None:
        """Maak de SQL pagina."""

        @ui.page("/sql")
        def sql_page() -> None:
            with YAPMOTheme.page_frame("SQL Query", exit_handler=handle_exit_click):
                self._create_content()

    def _create_content(self) -> None:
        """Maak de content van de SQL pagina."""
        ui.label("SQL Query Page").classes("text-2xl font-bold text-center")
