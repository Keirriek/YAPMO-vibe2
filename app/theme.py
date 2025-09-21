"""YAPMO Theme - Consistente styling en layout voor alle pagina's."""

from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, ClassVar, Literal

from nicegui import ui  # type: ignore[import-untyped]

from config import get_version


class YAPMOTheme:
    """Theme class voor YAPMO applicatie."""

    # Kleuren schema (voor ui.colors() setup)
    PRIMARY_COLOR: ClassVar[str] = "#6E93D6"  # Blauw
    PRIMARY_LIGHT_COLOR: ClassVar[str] = "#E3F2FD"  # Lichtblauw
    SECONDARY_COLOR: ClassVar[str] = "#53B689"  # Groen
    ACCENT_COLOR: ClassVar[str] = "#111B1E"  # Donkergrijs
    POSITIVE_COLOR: ClassVar[str] = "#53B689"  # Groen
    WARNING_COLOR: ClassVar[str] = "#FF9800"  # Oranje
    ERROR_COLOR: ClassVar[str] = "#F44336"  # Rood

    # Quasar kleur mapping voor buttons (voor props)

    # Quasar Basic Colors (8 brand colors)
    QUASAR_BASIC: ClassVar[dict[str, str]] = {
        "primary": "primary",           # Blauw (hoofdkleur)
        "secondary": "secondary",       # Groen (secundaire kleur)
        "accent": "accent",             # Paars (accent kleur)
        "dark": "dark",                 # Donkergrijs
        "positive": "positive",         # Groen (succes)
        "negative": "negative",         # Rood (fout/gevaar)
        "info": "info",                 # Lichtblauw (informatie)
        "warning": "warning",            # Oranje (waarschuwing)
    }

    # Extended Quasar Colors (met tinten)
    EXTENDED_QUASAR: ClassVar[dict[str, str]] = {
        # Blauwe tinten
        "blue_1": "blue-1", "blue_2": "blue-2", "blue_3": "blue-3",
        "blue_4": "blue-4", "blue_5": "blue-5", "blue_6": "blue-6",
        "blue_7": "blue-7", "blue_8": "blue-8", "blue_9": "blue-9",
        "blue_10": "blue-10", "blue_11": "blue-11", "blue_12": "blue-12",
        "blue_13": "blue-13", "blue_14": "blue-14",

        # Groene tinten
        "green_1": "green-1", "green_2": "green-2", "green_3": "green-3",
        "green_4": "green-4", "green_5": "green-5", "green_6": "green-6",
        "green_7": "green-7", "green_8": "green-8", "green_9": "green-9",
        "green_10": "green-10", "green_11": "green-11", "green_12": "green-12",
        "green_13": "green-13", "green_14": "green-14",

        # Rode tinten
        "red_1": "red-1", "red_2": "red-2", "red_3": "red-3", "red_4": "red-4",
        "red_5": "red-5", "red_6": "red-6", "red_7": "red-7", "red_8": "red-8",
        "red_9": "red-9", "red_10": "red-10", "red_11": "red-11", "red_12": "red-12",
        "red_13": "red-13", "red_14": "red-14",

        # Paarse tinten
        "purple_1": "purple-1", "purple_2": "purple-2", "purple_3": "purple-3",
        "purple_4": "purple-4", "purple_5": "purple-5", "purple_6": "purple-6",
        "purple_7": "purple-7", "purple_8": "purple-8", "purple_9": "purple-9",
        "purple_10": "purple-10", "purple_11": "purple-11", "purple_12": "purple-12",
        "purple_13": "purple-13", "purple_14": "purple-14",

        # Oranje tinten
        "orange_1": "orange-1", "orange_2": "orange-2", "orange_3": "orange-3",
        "orange_4": "orange-4", "orange_5": "orange-5", "orange_6": "orange-6",
        "orange_7": "orange-7", "orange_8": "orange-8", "orange_9": "orange-9",
        "orange_10": "orange-10", "orange_11": "orange-11", "orange_12": "orange-12",
        "orange_13": "orange-13", "orange_14": "orange-14",

        # Grijze tinten
        "grey_1": "grey-1", "grey_2": "grey-2", "grey_3": "grey-3",
        "grey_4": "grey-4", "grey_5": "grey-5", "grey_6": "grey-6",
        "grey_7": "grey-7", "grey_8": "grey-8", "grey_9": "grey-9",
        "grey_10": "grey-10", "grey_11": "grey-11", "grey_12": "grey-12",
        "grey_13": "grey-13", "grey_14": "grey-14",
    }

    # Alle kleuren (zonder tinten)
    ALL_COLORS: ClassVar[dict[str, str]] = {
        "red": "red", "pink": "pink", "purple": "purple",
        "deep-purple": "deep-purple", "indigo": "indigo", "blue": "blue",
        "light-blue": "light-blue", "cyan": "cyan", "teal": "teal",
        "green": "green", "light-green": "light-green", "lime": "lime",
        "yellow": "yellow", "amber": "amber", "orange": "orange",
        "deep-orange": "deep-orange", "brown": "brown", "grey": "grey",
        "blue-grey": "blue-grey",
    }

    # YAPMO Color Set (voorgestelde combinatie)
    YAPMO_COLORS: ClassVar[dict[str, str]] = {
        "primary": "primary",            # Zelfde kleur als bovenbalk
        "secondary": "blue-3",          # Lichtere variant van primary
        "positive": "green-6",          # Mooie groene succes kleur
        "negative": "red-6",            # Mooie rode fout kleur
        "warning": "orange-6",          # Mooie oranje waarschuwing
        "info": "blue-2",               # Lichte blauwe informatie
        "primary_light": "blue-1",      # Zeer lichte blauwe variant
        "accent": "purple-6",           # Mooie paarse accent kleur
        "light": "grey-3",               # Lichtgrijs
    }

    # Combinatie van alle beschikbare kleuren voor buttons
    BUTTON_COLORS: ClassVar[dict[str, str]] = {
        **QUASAR_BASIC,
        **EXTENDED_QUASAR,
        **ALL_COLORS,
        **YAPMO_COLORS,
    }

    # Gestandaardiseerde CSS classes
    CARD_STYLE = (
        "bg-white/95 backdrop-blur-sm rounded-lg shadow-xl border border-white/20"
    )
    CARD_PADDING = "p-8"
    CARD_SMALL_PADDING = "p-6"

    # Button styles
    BUTTON_BASE = (
        "font-medium transition-all duration-200 shadow-lg "
        "disabled:opacity-50 disabled:cursor-not-allowed"
    )
    BUTTON_PRIMARY = (
        f"{BUTTON_BASE} bg-blue-600 text-white hover:bg-blue-700 "
        "focus:ring-2 focus:ring-blue-400 focus:ring-offset-2"
    )
    BUTTON_SECONDARY = (
        f"{BUTTON_BASE} bg-blue-300 text-blue-900 hover:bg-blue-400 "
        "focus:ring-2 focus:ring-blue-400 focus:ring-offset-2"
    )
    BUTTON_PRIMARY_LIGHT = (
        f"{BUTTON_BASE} bg-blue-100 text-blue-900 hover:bg-blue-200 "
        "focus:ring-2 focus:ring-blue-400 focus:ring-offset-2"
    )
    BUTTON_WARNING = (
        f"{BUTTON_BASE} bg-warning text-white hover:bg-orange-600 "
        "focus:ring-2 focus:ring-orange-400 focus:ring-offset-2"
    )
    BUTTON_ERROR = (
        f"{BUTTON_BASE} bg-gradient-to-r from-red-500 to-red-600 text-white "
        "hover:from-red-600 hover:to-red-700 focus:ring-2 focus:ring-red-400 "
        "focus:ring-offset-2"
    )
    BUTTON_GRAY = (
        f"{BUTTON_BASE} bg-gray-500 text-white hover:bg-gray-600 "
        "focus:ring-2 focus:ring-gray-400 focus:ring-offset-2"
    )

    # Button sizes
    BUTTON_SIZE_SM = "px-4 py-2 rounded-lg"
    BUTTON_SIZE_MD = "px-6 py-3 rounded-2xl"
    BUTTON_SIZE_LG = "px-8 py-4 rounded-2xl"

    # Dialog styles
    DIALOG_CARD = f"{CARD_STYLE} {CARD_PADDING}"
    DIALOG_TITLE_GRADIENT = "text-2xl font-bold mb-4"
    DIALOG_CONTENT = "text-lg text-gray-700 mb-6"
    DIALOG_BUTTONS = "justify-end gap-3"

    # Text styles
    TITLE_GRADIENT = "text-2xl font-bold mb-4"
    SUBTITLE = "text-lg text-gray-700 mb-6"

    @classmethod
    def setup_colors(cls) -> None:
        """Set up the colors for the application."""
        ui.colors(
            primary=cls.PRIMARY_COLOR,
            secondary=cls.SECONDARY_COLOR,
            accent=cls.ACCENT_COLOR,
            positive=cls.POSITIVE_COLOR,
            warning=cls.WARNING_COLOR,
            error=cls.ERROR_COLOR,
        )

    @classmethod
    @contextmanager
    def page_frame(cls, title: str, exit_handler: Callable | None = None) -> Any:  # noqa: ANN401
        """Context manager voor consistente pagina layout."""
        cls.setup_colors()

        with ui.header().classes("bg-primary shadow-lg"), \
             ui.row().classes("w-full items-center justify-between px-4 py-2"):
            ui.label(get_version()).classes("font-bold text-2xl text-white")
            ui.label(title).classes("text-lg font-medium text-white")
            cls._create_header_buttons(exit_handler)

        with ui.column().classes("w-full max-w-7xl mx-auto p-6"):
            yield

    @staticmethod
    def _create_header_buttons(exit_handler: Callable | None = None) -> None:
        """Maak de header knoppen voor alle pagina's."""
        with ui.row().classes("gap-3"):
            # Menu dropdown knop
            YAPMOTheme.menu_button = ui.button("MENU", icon="menu").classes(
                "font-medium px-4 py-2 rounded-lg transition-colors text-white",
            ).props("flat color=primary")

            with YAPMOTheme.menu_button, ui.menu().classes("bg-white shadow-lg rounded-lg"):
                ui.menu_item("Main Page", lambda: ui.navigate.to("/")).classes(
                    "hover:bg-blue-50 px-4 py-2",
                )
                ui.menu_item(
                    "Configuration",
                    lambda: ui.navigate.to("/config"),
                ).classes("hover:bg-blue-50 px-4 py-2")
                ui.menu_item(
                    "Element Test",
                    lambda: ui.navigate.to("/element-test"),
                ).classes("hover:bg-blue-50 px-4 py-2")
                ui.menu_item(
                    "Fill Database New",
                    lambda: ui.navigate.to("/fill-db-new"),
                ).classes("hover:bg-blue-50 px-4 py-2")
                ui.menu_item(
                    "Fill Database Page V2",
                    lambda: ui.navigate.to("/fill-db-page-v2"),
                ).classes("hover:bg-blue-50 px-4 py-2")

            # ABORT knop - state controlled by global abort manager
            YAPMOTheme.abort_button = ui.button(
                "ABORT",
                on_click=YAPMOTheme._create_abort_dialog,
            ).classes(
                "font-medium px-4 py-2 rounded-lg transition-colors "
                "disabled:opacity-50 disabled:cursor-not-allowed",
            ).props("color=warning")
            # State will be controlled by global abort manager
            YAPMOTheme.abort_button.disable()

            # EXIT knop met optionele handler
            exit_on_click = (
                exit_handler
                if exit_handler
                else lambda: ui.notify(
                    "EXIT functionaliteit wordt geladen...", type="info",
                )
            )
            YAPMOTheme.exit_button = ui.button(
                "EXIT",
                icon="exit_to_app",
                on_click=exit_on_click,
            ).classes(
                "font-medium px-4 py-2 rounded-lg transition-colors",
            ).props("color=negative")

    @staticmethod
    def create_section(title: str, icon: str | None = None) -> None:
        """Maak een consistente sectie met titel."""
        with ui.card().classes("w-full mb-4"), \
             ui.card_section(), \
             ui.row().classes("items-center"):
            if icon:
                ui.icon(icon).classes("text-primary mr-2")
            ui.label(title).classes("text-xl font-bold text-primary")

    @staticmethod
    def create_button(
        text: str,
        on_click: Callable | None = None,
        color: str = "primary",
        size: str = "md",
    ) -> Any:  # noqa: ANN401
        """Maak een consistente knop."""
        # Bepaal button style op basis van color
        if color == "primary":
            button_style = YAPMOTheme.BUTTON_PRIMARY
        elif color == "secondary":
            button_style = YAPMOTheme.BUTTON_SECONDARY
        elif color == "warning":
            button_style = YAPMOTheme.BUTTON_WARNING
        elif color == "error":
            button_style = YAPMOTheme.BUTTON_ERROR
        elif color == "gray":
            button_style = YAPMOTheme.BUTTON_GRAY
        else:
            button_style = YAPMOTheme.BUTTON_PRIMARY_LIGHT

        # Bepaal button size
        if size == "sm":
            size_class = YAPMOTheme.BUTTON_SIZE_SM
        elif size == "lg":
            size_class = YAPMOTheme.BUTTON_SIZE_LG
        else:
            size_class = YAPMOTheme.BUTTON_SIZE_MD

        return ui.button(text, on_click=on_click).classes(
            f"{button_style} {size_class}",
        ).props(f"color={color}")

    @staticmethod
    def create_dialog_card() -> Any:  # noqa: ANN401
        """Maak een consistente dialog card."""
        return ui.card().classes(YAPMOTheme.DIALOG_CARD)

    @staticmethod
    def create_dialog_title(text: str) -> Any:  # noqa: ANN401
        """Maak een consistente dialog title."""
        return ui.label(text).classes(YAPMOTheme.DIALOG_TITLE_GRADIENT)

    @staticmethod
    def create_dialog_content(text: str) -> Any:  # noqa: ANN401
        """Maak consistente dialog content."""
        return ui.label(text).classes(YAPMOTheme.DIALOG_CONTENT)

    @staticmethod
    def create_dialog_buttons() -> Any:  # noqa: ANN401
        """Maak consistente dialog buttons container."""
        return ui.row().classes(YAPMOTheme.DIALOG_BUTTONS)

    @staticmethod
    def create_dialog_button_cancel(on_click: Callable) -> Any:  # noqa: ANN401
        """Maak een consistente cancel button voor dialogs."""
        return ui.button("Cancel", on_click=on_click).classes(
            "font-medium px-4 py-2 rounded-lg transition-colors",
        ).props("color=positive")

    @staticmethod
    def create_dialog_button_confirm(text: str, on_click: Callable) -> Any:  # noqa: ANN401
        """Maak een consistente confirm button voor dialogs."""
        return ui.button(text, on_click=on_click).classes(
            "font-medium px-4 py-2 rounded-lg transition-colors",
        ).props("color=primary")

    @staticmethod
    def create_dialog_button_destructive(text: str, on_click: Callable) -> Any:  # noqa: ANN401
        """Maak een consistente destructive button voor dialogs."""
        return ui.button(text, on_click=on_click).classes(
            "font-medium px-4 py-2 rounded-lg transition-colors",
        ).props("color=negative")

    @staticmethod
    def create_input(label: str, placeholder: str = "", value: str = "") -> Any:  # noqa: ANN401
        """Maak een consistente input field."""
        with ui.column().classes("w-full"):
            ui.label(label).classes("text-sm font-medium mb-1")
            return ui.input(placeholder=placeholder, value=value).classes("w-full")

    @staticmethod
    def create_textarea(label: str, placeholder: str = "", value: str = "") -> Any:  # noqa: ANN401
        """Maak een consistente textarea."""
        with ui.column().classes("w-full"):
            ui.label(label).classes("text-sm font-medium mb-1")
            return ui.textarea(placeholder=placeholder, value=value).classes("w-full")

    @staticmethod
    def create_file_picker(label: str, *, multiple: bool = False) -> Any:  # noqa: ANN401
        """Maak een consistente file picker."""
        with ui.column().classes("w-full"):
            ui.label(label).classes("text-sm font-medium mb-1")
            return ui.upload(multiple=multiple, auto_upload=True).classes("w-full")

    @staticmethod
    def show_message(message: str, message_type: str = "info") -> Any:  # noqa: ANN401
        """Toon een consistente message."""
        color_map = {
            "info": "text-blue-600",
            "success": "text-green-600",
            "warning": "text-orange-600",
            "error": "text-red-600",
        }

        # Type cast for notify function
        notify_type: Literal["positive", "negative",
                             "warning", "info", "ongoing"] = "info"
        if message_type in ["positive", "negative", "warning", "info", "ongoing"]:
            notify_type = message_type  # type: ignore[assignment]

        ui.notify(message, type=notify_type, position="top-right")

        return ui.label(message).classes(
            f'p-2 rounded {color_map.get(message_type, "text-blue-600")}',
        )

    @staticmethod
    def _create_abort_dialog() -> None:
        """Create a confirmation dialog for the ABORT button."""

        def _abort_action(dialog: Any) -> None:  # noqa: ANN401
            dialog.close()
            # Import here to avoid circular imports
            from yapmo_globals import abort_manager
            # Only abort the current page, not all processes
            if "fill_db_page_v2" in abort_manager.abort_handlers:
                abort_manager.abort_handlers["fill_db_page_v2"]()
            ui.notify("Aborting SCANNING process...", type="warning")

        dialog = ui.dialog()
        with dialog, YAPMOTheme.create_dialog_card():
            YAPMOTheme.create_dialog_title("Confirm Abort")
            YAPMOTheme.create_dialog_content(
                "Are you sure you want to abort the current scanning process?")
            with YAPMOTheme.create_dialog_buttons():
                YAPMOTheme.create_dialog_button_cancel(dialog.close)
                YAPMOTheme.create_dialog_button_destructive(
                    "Abort",
                    lambda: _abort_action(dialog),
                )

        dialog.open()
