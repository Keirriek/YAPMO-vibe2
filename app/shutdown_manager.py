"""Shutdown Manager voor YAPMO applicatie.

Handles application exit logic and confirmation dialogs.
"""


from nicegui import app, ui
from theme import YAPMOTheme


def create_exit_dialog() -> None:
    """Create a confirmation dialog for the EXIT button."""

    def _exit_action(dialog: ui.dialog) -> None:
        dialog.close()
        ui.notify("Application shutting down...", type="info")  # type: ignore[arg-type]
        app.shutdown()

    # Dialog styling consistent met hoofdpagina design
    dialog = ui.dialog()
    with dialog, YAPMOTheme.create_dialog_card():
        # Titel met gradient styling zoals hoofdpagina
        YAPMOTheme.create_dialog_title("Confirm Exit")

        # Vraag met consistente styling
        YAPMOTheme.create_dialog_content("Are you sure you want to quit?")

        # Knoppen met consistente styling en focus states
        with YAPMOTheme.create_dialog_buttons():
            YAPMOTheme.create_dialog_button_cancel(dialog.close).text = "NO"
            YAPMOTheme.create_dialog_button_destructive(
                "YES",
                lambda: _exit_action(dialog),
            )

    dialog.open()


def handle_exit_click() -> None:
    """Handle EXIT button click with confirmation dialog."""
    create_exit_dialog()
