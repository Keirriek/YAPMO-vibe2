# https://daelon.dev/posts/nicegui_dialogs/
from nicegui import ui
from typing import List, Dict, Union

class ConfirmationPopup(ui.dialog):
    def __init__(self, message: str, dialog_style: str, button_base_style: str, buttons: List[Dict[str, str]]):
        """
        Initialize dialog with custom buttons
        
        Args:
            message: The message to display in the dialog
            dialog_style: Tailwind CSS classes for the dialog card
            button_base_style: Base Tailwind CSS classes for all buttons
            buttons: List of button configurations, each containing:
                    - 'text': Text to show on button
                    - 'return_value': Value to return when clicked
                    - 'style': Additional CSS classes for this specific button
        Good values for dialog_style and button_base_style:
            dialog_style = 'w-auto p-4'
            button_base_style = 'rounded-md shadow-lg text-center w-auto'

            Colors:
            bg-green text-white
            bg-red text-white
            bg-blue text-white
            bg-white text-black  text-red
            bg-black text-white
        """
        super().__init__()
        
        with self, ui.card().classes(dialog_style):
            ui.label(message)
            with ui.row():
                for button in buttons:
                    # Combine the base button style with the specific button style
                    combined_style = f"{button_base_style} {button['style']}"
                    ui.button(
                        button['text'],
                        on_click=lambda rv=button['return_value']: self.submit(rv)
                    ).classes(replace=combined_style)

if __name__ in ['__main__', '__mp_main__']:

    async def click():
        # Example usage
        dialog_style = 'w-auto p-4'
        button_base_style = 'rounded-md shadow-lg text-center w-auto'
        
        buttons = [
            {
                'text': 'Yes',
                'return_value': 'yes',
                'style': 'text-white bg-green'
            },
            {
                'text': 'No',
                'return_value': 'no',
                'style': 'text-white bg-red'
            },
            {
                'text': 'Maybe',
                'return_value': 'maybe',
                'style': 'text-white bg-blue'
            },
            {
                'text': 'Skip',
                'return_value': 'skip',
                'style': 'text-black bg-white'
            }
        ]
        
        result = await ConfirmationPopup(
            'Do you want to continue?',
            dialog_style,
            button_base_style,
            buttons
        )
        ui.notify(f'User chose: {result}')

    ui.button("Click", on_click=click)
    ui.run()