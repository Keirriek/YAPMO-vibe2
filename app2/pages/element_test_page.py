"""Element Test Page - Test pagina voor alle gestandaardiseerde UI elementen."""

from nicegui import ui
from shutdown_manager import handle_exit_click
from theme import YAPMOTheme


class ElementTestPage:
    """Element test pagina van de YAPMO applicatie."""

    def __init__(self) -> None:
        """Initialize the element test page."""
        self._create_page()

    def _create_page(self) -> None:
        """Maak de element test pagina."""

        @ui.page("/element-test")
        def element_test_page() -> None:
            with YAPMOTheme.page_frame("Element Test", exit_handler=handle_exit_click):
                self._create_content()

    def _create_content(self) -> None:
        """Create the content of the element test page."""
        self._create_header_section()
        self._create_buttons_section()
        self._create_labels_section()
        self._create_cards_section()
        self._create_scroll_window_section()
        self._create_progress_bars_section()
        self._create_slider_section()
        self._create_toggle_switch_section()
        self._create_checkbox_section()
        self._create_radio_buttons_section()
        self._create_input_boxes_section()

    def _create_header_section(self) -> None:
        """Create the header section."""
        with ui.card().classes("w-full mb-6"), ui.card_section():
            ui.label("UI Element Test Page").classes(
                "text-3xl font-bold text-center mb-4")
            ui.label(
                "Testing all standardized UI elements from the project plan",
            ).classes("text-lg text-center text-gray-600")

    def _create_buttons_section(self) -> None:
        """Create the buttons section."""
        with ui.card().classes("w-full mb-6"), ui.card_section():
            ui.label("Buttons").classes("text-xl font-bold mb-4")
            self._create_button_dimensions()
            self._create_button_quasar_colors()
            self._create_button_yapmo_colors()
            self._create_button_disabled_colors()

    def _create_button_dimensions(self) -> None:
        """Create button dimension examples."""
        ui.label("Dimensions").classes("text-lg font-bold mt-6 mb-4")
        with ui.row().classes("gap-4 flex-wrap"):
            YAPMOTheme.create_button(
                "Primary Small", lambda: ui.notify("Primary Small"), "primary", "sm",
            )
            YAPMOTheme.create_button(
                "Primary Medium", lambda: ui.notify("Primary Medium"), "primary", "md",
            )
            YAPMOTheme.create_button(
                "Primary Large", lambda: ui.notify("Primary Large"), "primary", "lg",
            )

    def _create_button_quasar_colors(self) -> None:
        """Create Quasar color button examples."""
        ui.label("Quasar Colors").classes("text-lg font-bold mt-6 mb-4")
        with ui.grid(columns=4).classes("gap-4 w-full"):
            YAPMOTheme.create_button("Blue", lambda: ui.notify("Blue"), "blue")
            YAPMOTheme.create_button("Green", lambda: ui.notify("Green"), "green")
            YAPMOTheme.create_button("Red", lambda: ui.notify("Red"), "red")
            YAPMOTheme.create_button("Orange", lambda: ui.notify("Orange"), "orange")
            YAPMOTheme.create_button("Purple", lambda: ui.notify("Purple"), "purple")
            YAPMOTheme.create_button("Teal", lambda: ui.notify("Teal"), "teal")
            YAPMOTheme.create_button("Pink", lambda: ui.notify("Pink"), "pink")
            YAPMOTheme.create_button("Indigo", lambda: ui.notify("Indigo"), "indigo")

    def _create_button_yapmo_colors(self) -> None:
        """Create YAPMO color button examples."""
        ui.label("YAPMO Colors").classes("text-lg font-bold mt-6 mb-4")
        with ui.grid(columns=4).classes("gap-4 w-full"):
            YAPMOTheme.create_button(
                "Primary", lambda: ui.notify("Primary"), "primary",
            )
            YAPMOTheme.create_button(
                "Secondary", lambda: ui.notify("Secondary"), "secondary",
            )
            YAPMOTheme.create_button(
                "Positive", lambda: ui.notify("Positive"), "positive",
            )
            YAPMOTheme.create_button(
                "Negative", lambda: ui.notify("Negative"), "negative",
            )
            YAPMOTheme.create_button(
                "Warning", lambda: ui.notify("Warning"), "warning",
            )
            YAPMOTheme.create_button(
                "Info", lambda: ui.notify("Info"), "info",
            )
            YAPMOTheme.create_button(
                "Primary Light", lambda: ui.notify("Primary Light"), "primary_light",
            )
            YAPMOTheme.create_button("Accent", lambda: ui.notify("Accent"), "accent")

    def _create_button_disabled_colors(self) -> None:
        """Create disabled button examples."""
        with ui.card().classes("w-full"):
            ui.label("YAPMO Disabled Colors").classes("text-h6 q-mb-md")
            with ui.grid(columns=4).classes("gap-4"):
                YAPMOTheme.create_button(
                    "Primary", lambda: ui.notify("Primary"), "primary",
                ).disable()
                YAPMOTheme.create_button(
                    "Secondary", lambda: ui.notify("Secondary"), "secondary",
                ).disable()
                YAPMOTheme.create_button(
                    "Positive", lambda: ui.notify("Positive"), "positive",
                ).disable()
                YAPMOTheme.create_button(
                    "Negative", lambda: ui.notify("Negative"), "negative",
                ).disable()
                YAPMOTheme.create_button(
                    "Warning", lambda: ui.notify("Warning"), "warning",
                ).disable()
                YAPMOTheme.create_button(
                    "Info", lambda: ui.notify("Info"), "info",
                ).disable()
                YAPMOTheme.create_button(
                    "Primary Light",
                    lambda: ui.notify("Primary Light"),
                    "primary_light",
                ).disable()
                YAPMOTheme.create_button(
                    "Accent", lambda: ui.notify("Accent"), "accent",
                ).disable()

    def _create_labels_section(self) -> None:
        """Create the labels section."""
        with ui.card().classes("w-full mb-6"), ui.card_section():
            ui.label("Labels").classes("text-xl font-bold mb-4")
            with ui.column().classes("gap-2"):
                ui.label("Regular Label").classes("text-base")
                ui.label("Bold Label").classes("text-base font-bold")
                ui.label("Colored Label").classes("text-base text-blue-600")
                ui.label("Large Label").classes("text-2xl")

    def _create_cards_section(self) -> None:
        """Create the cards section."""
        with ui.card().classes("w-full mb-6"), ui.card_section():
            ui.label("Cards").classes("text-xl font-bold mb-4")
            with ui.row().classes("gap-4"):
                with ui.card().classes("p-4 w-48"):
                    ui.label("Card 1").classes("font-bold")
                    ui.label("Card content here")
                with ui.card().classes("p-4 w-48"):
                    ui.label("Card 2").classes("font-bold")
                    ui.label("More card content")

    def _create_scroll_window_section(self) -> None:
        """Create the scroll window section."""
        with ui.card().classes("w-full mb-6"), ui.card_section():
            ui.label("Scroll Window").classes("text-xl font-bold mb-4")
            with ui.scroll_area().classes("h-32 w-full border rounded"):
                for i in range(20):
                    ui.label(f"Scroll item {i+1}").classes("p-2")

    def _create_progress_bars_section(self) -> None:
        """Create the progress bars section."""
        with ui.card().classes("w-full mb-6"), ui.card_section():
            ui.label("Progress Bars").classes("text-xl font-bold mb-4")
            with ui.column().classes("gap-4"):
                ui.label("Linear Progress Bar").classes("font-medium")
                ui.linear_progress().classes("w-full").props("value=0.6")
                ui.label("Circular Progress Bar").classes("font-medium")
                ui.circular_progress().classes("w-16 h-16").props("value=0.75")
                with ui.row():
                    ui.spinner(size="lg")
                    ui.spinner("audio", size="lg", color="green")
                    ui.spinner("dots", size="lg", color="red")

    def _create_slider_section(self) -> None:
        """Create the slider section."""
        with ui.card().classes("w-full mb-6"), ui.card_section():
            ui.label("Slider").classes("text-xl font-bold mb-4")
            slider_value = ui.label("Value: 50").classes("font-medium")
            ui.slider(min=0, max=100, value=50, step=1).classes("w-full").on(
                "update", lambda e: slider_value.set_text(f"Value: {e.value}"),
            )

    def _create_toggle_switch_section(self) -> None:
        """Create the toggle switch section."""
        with ui.card().classes("w-full mb-6"), ui.card_section():
            ui.label("Toggle Switch").classes("text-xl font-bold mb-4")
            toggle_state = ui.label("State: OFF").classes("font-medium")
            ui.switch().classes("w-12").on(
                "change",
                lambda e: toggle_state.set_text(
                    f'State: {"ON" if e.value else "OFF"}',
                ),
            )

    def _create_checkbox_section(self) -> None:
        """Create the checkbox section."""
        with ui.card().classes("w-full mb-6"), ui.card_section():
            ui.label("Checkboxes").classes("text-xl font-bold mb-4")
            with ui.column().classes("gap-2"):
                ui.checkbox("Option 1").on(
                    "change", lambda e: ui.notify(f"Checkbox 1: {e.value}"),
                )
                ui.checkbox("Option 2").on(
                    "change", lambda e: ui.notify(f"Checkbox 2: {e.value}"),
                )
                ui.checkbox("Option 3").on(
                    "change", lambda e: ui.notify(f"Checkbox 3: {e.value}"),
                )

    def _create_radio_buttons_section(self) -> None:
        """Create the radio buttons section."""
        with ui.card().classes("w-full mb-6"), ui.card_section():
            ui.label("Radio Buttons").classes("text-xl font-bold mb-4")
            radio_state = ui.label("Selected: None").classes("font-medium mb-2")
            with ui.column().classes("gap-2"):
                ui.radio(
                    ["Option A", "Option B", "Option C"], value="Option A",
                ).classes("w-full").on(
                    "change", lambda e: radio_state.set_text(f"Selected: {e.value}"),
                )

    def _create_input_boxes_section(self) -> None:
        """Create the input boxes section."""
        with ui.card().classes("w-full mb-6"), ui.card_section():
            ui.label("Input Boxes").classes("text-xl font-bold mb-4")
            with ui.column().classes("gap-4"):
                single_input = YAPMOTheme.create_input(
                    "Single Line Input", "Enter text here...",
                )
                single_input.on(
                    "change", lambda e: ui.notify(f"Single input: {e.value}"),
                )
                multi_input = YAPMOTheme.create_textarea(
                    "Multi Line Input", "Enter multiple lines here...",
                )
                multi_input.on("change", lambda e: ui.notify(f"Multi input: {e.value}"))


def create_element_test_page() -> ElementTestPage:
    """Maak de element test pagina."""
    return ElementTestPage()


if __name__ == "__main__":
    create_element_test_page()
    ui.run(title="Element Test Page", port=8082)
