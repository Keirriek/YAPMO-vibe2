from contextlib import contextmanager
from menu import menu
from nicegui import ui, app


@contextmanager
def frame(navigation_title: str):
    """Custom page frame to share the same styling and behavior across all pages"""
    
    def handle_exit():
        """Handle exit button click"""
        ui.notify('Shutting down...')
        app.shutdown()
    
    ui.colors(primary='#6E93D6', secondary='#53B689', accent='#111B1E', positive='#53B689')
    
    with ui.header().classes('justify-between'):
        with ui.row():
            ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
            ui.label('YAPMO  ').style('font-size: 1.5em; font-weight: bold;')
            ui.label('   (yet another photo & metadata organiser)').style('font-weight: normal; align-self: center;')
        
        # Exit button aan de rechterkant
        ui.button('EXIT', on_click=handle_exit).classes('bg-red text-white')
    
    with ui.column().classes('absolute-start w-full items-start bg-white-100'):
        yield
    
    with ui.left_drawer().classes('bg-blue-100').props('width=100 bordered') as left_drawer:
        ui.label('Side menu')
        menu()

