"""Local Directory Picker for YAPMO.

A NiceGUI dialog for selecting directories from the local filesystem.
Based on the original local_file_picker.py but specialized for directories.
"""

from pathlib import Path

from nicegui import events, ui


class LocalDirectoryPicker(ui.dialog):
    """Local Directory Picker for selecting directories."""

    def __init__(self, directory: str = "/workspaces", *,
                 upper_limit: str | None = None,
                 show_hidden_files: bool = False) -> None:
        """Local Directory Picker.

        :param directory: The directory to start in
        :param upper_limit: The directory to stop at (None: no limit)
        :param show_hidden_files: Whether to show hidden directories
        """
        super().__init__()
        self.selected_directory: str | None = None

        self.path = Path(directory).expanduser()
        if upper_limit is None:
            self.upper_limit = None
        else:
            self.upper_limit = Path(upper_limit).expanduser()
        self.show_hidden_files = show_hidden_files

        with self, ui.card().classes("w-[600px] h-[500px]"):
            ui.label("Select Directory").classes("text-lg font-semibold mb-2")

            # Current path display
            self.path_label = ui.label(f"Current: {self.path}").classes(
                "text-sm text-gray-600 mb-2")

            # Directory grid
            self.grid = ui.aggrid({
                "columnDefs": [
                    {"field": "name", "headerName": "Directory", "flex": 1},
                    {"field": "type", "headerName": "Type", "width": 100},
                ],
                "rowSelection": "single",
                "domLayout": "normal",
                "suppressRowClickSelection": False,
            }, html_columns=[0]).classes("w-full h-64 mb-4").on(
                "cellDoubleClicked", self.handle_double_click,
            )

            # Current selection display
            self.selection_label = ui.label(
                "No directory selected").classes("text-sm mb-2")

            # Buttons (herstel: met Select Current Directory knop)
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=self.close).props(
                    "outline color=grey")
                self.ok_button = ui.button(
                    "Select", on_click=self.handle_ok).props("color=primary")

        self.update_grid()

    def update_grid(self) -> None:
        """Update the directory grid with current path contents."""
        try:
            paths = [p for p in self.path.iterdir() if p.is_dir()]
            if not self.show_hidden_files:
                paths = [p for p in paths if not p.name.startswith(".")]
            paths.sort(key=lambda p: p.name.lower())

            self.grid.options["rowData"] = [
                {
                    "name": f"📁 <strong>{p.name}</strong>",
                    "type": "Directory",
                    "path": str(p),
                }
                for p in paths
            ]

            # Add parent directory option
            if ((self.upper_limit is None and self.path != self.path.parent) or
                    (self.upper_limit is not None and self.path != self.upper_limit)):
                self.grid.options["rowData"].insert(0, {
                    "name": "📁 <strong>..</strong>",
                    "type": "Parent",
                    "path": str(self.path.parent),
                })

            self.grid.update()
            self.path_label.text = f"Current: {self.path}"
            self.selection_label.text = f"Selected: {self.path}"

        except PermissionError:
            ui.notify("Permission denied accessing this directory",
                      type="negative")
        except (OSError, ValueError, RuntimeError) as e:
            ui.notify(f"Error reading directory: {e}", type="negative")

    def handle_double_click(self, e: events.GenericEventArguments) -> None:
        """Handle double-click on a directory."""
        new_path = Path(e.args["data"]["path"])
        if new_path.is_dir():
            self.path = new_path
            self.update_grid()
            # Clear selection after navigating
            self.grid.run_method("deselectAll")
            # Update selection label to new path
            self.selection_label.text = f"Selected: {self.path}"

    async def handle_ok(self) -> None:
        """Handle Select button - select highlighted directory or current directory."""
        try:
            rows = await self.grid.get_selected_rows()
            if rows:
                selected_path = rows[0]["path"]
                self.selected_directory = selected_path
                self.submit(selected_path)
            else:
                # No selection, use current directory
                self.selected_directory = str(self.path)
                self.submit(self.selected_directory)
        except (OSError, ValueError, RuntimeError) as e:
            ui.notify(f"Error selecting directory: {e}", type="negative")


async def pick_directory(
    directory: str = "/workspaces",
    upper_limit: str | None = None,
    *,
    show_hidden_files: bool = False,
) -> str | None:
    """Pick a directory using a convenience function.

    :param directory: Starting directory
    :param upper_limit: Upper limit directory
    :param show_hidden_files: Show hidden directories
    :return: Selected directory path or None if cancelled
    """
    picker = LocalDirectoryPicker(
        directory, upper_limit=upper_limit, show_hidden_files=show_hidden_files)
    result = await picker
    return result if result else None
