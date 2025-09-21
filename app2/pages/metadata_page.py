"""Metadata Page voor YAPMO applicatie."""

from nicegui import ui
from shutdown_manager import handle_exit_click
from theme import YAPMOTheme


class MetadataPage:
    """Metadata beheer pagina van de YAPMO applicatie."""

    def __init__(self) -> None:
        """Initialize the metadata page."""
        self._create_page()

    def _create_page(self) -> None:
        """Maak de metadata pagina."""

        @ui.page("/metadata")
        def metadata_page() -> None:
            with YAPMOTheme.page_frame(
                "Metadata Management", exit_handler=handle_exit_click,
            ):
                self._create_content()

    def _create_content(self) -> None:
        """Maak de content van de metadata pagina."""
        ui.label("Metadata Management Page").classes(
            "text-2xl font-bold text-center")
