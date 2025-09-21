"""Main Page voor YAPMO applicatie."""

from config import get_version
from nicegui import ui
from shutdown_manager import handle_exit_click
from theme import YAPMOTheme


class MainPage:
    """Hoofdpagina van YAPMO applicatie."""

    def __init__(self) -> None:
        """Initialize the main page."""
        self.setup_page()

    def setup_page(self) -> None:
        """Set up the main page."""
        # Custom styling voor moderne, professionele look
        custom_styles = """
        <style>
        /* Global styles */
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }

        /* Navigation cards */
        .nav-card {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.3);
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .nav-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
        }

        /* Icon styling */
        .nav-icon {
            color: #667eea;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }

        /* Text styling */
        .main-title {
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
            text-align: center;
            margin-bottom: 0.5rem;
        }

        .subtitle {
            color: rgba(0, 0, 0, 0.7);
            text-align: center;
            font-weight: 300;
            margin-bottom: 2rem;
        }

        /* Container styling */
        .main-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }
        </style>
        """

        ui.add_head_html(custom_styles)

        # Gebruik theme voor consistente header
        with YAPMOTheme.page_frame(
            "Main Page",
            exit_handler=handle_exit_click,
        ):

            # Header section
            with ui.card().classes(
                "bg-white/95 backdrop-blur-sm rounded-2xl shadow-xl "
                "border border-white/20 p-8 w-full mb-8",
            ):
                ui.html(f'<h1 class="main-title text-5xl">{get_version()}</h1>')
                ui.html(
                    '<p class="subtitle text-xl">Yet Another Photo Management '
                    'Organizer</p>',
                )
                ui.html(
                    '<p class="text-center text-gray-600">Professional Media '
                    'Management Solution</p>',
                )

            # Navigation section - 2x2 grid van kaarten
            with ui.row().classes("gap-6 w-full justify-center mb-6"):
                # Configuratie kaart
                with ui.card().classes("nav-card p-6 w-64 text-center").on(
                    "click", lambda: ui.navigate.to("/config"),
                ):
                    ui.icon("settings").classes("nav-icon")
                    ui.label("Configuration").classes(
                        "text-xl font-semibold mb-2")
                    ui.label("Manage your application settings").classes(
                        "text-sm text-gray-600")

                # Database Vullen kaart
                with ui.card().classes("nav-card p-6 w-64 text-center").on(
                    "click", lambda: ui.navigate.to("/fill-db"),
                ):
                    ui.icon("storage").classes("nav-icon")
                    ui.label("Fill Database").classes(
                        "text-xl font-semibold mb-2")
                    ui.label("Scan and add media files").classes(
                        "text-sm text-gray-600")

            with ui.row().classes("gap-6 w-full justify-center mb-8"):
                # Metadata Beheer kaart
                with ui.card().classes("nav-card p-6 w-64 text-center").on(
                    "click", lambda: ui.navigate.to("/metadata"),
                ):
                    ui.icon("image").classes("nav-icon")
                    ui.label("Metadata Management").classes(
                        "text-xl font-semibold mb-2")
                    ui.label("View and edit metadata").classes(
                        "text-sm text-gray-600")

                # SQL Query kaart
                with ui.card().classes("nav-card p-6 w-64 text-center").on(
                    "click", lambda: ui.navigate.to("/sql"),
                ):
                    ui.icon("code").classes("nav-icon")
                    ui.label("SQL Query").classes("text-xl font-semibold mb-2")
                    ui.label("Execute SQL queries").classes(
                        "text-sm text-gray-600")
