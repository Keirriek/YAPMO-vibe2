import sqlite3
import globals
import config
from message import message
from nicegui import ui
css_border='border-2 border-blue-500 rounded-lg items-center'
def content():
    message('This is the SQL page.').classes('font-bold')
    ui.label('Use the menu on the top right to navigate.')
    query_name='Query Name  '
    query_code='Query Code'
    with ui.row().classes('w-full items-center'):
        with ui.dropdown_button('SQL query', auto_close=True):
            ui.item('Item 1', on_click=lambda: ui.notify('You clicked item 1'))
            ui.item('Item 2', on_click=lambda: ui.notify('You clicked item 2'))
        ui.label('Query name').classes('w-1/4 pl-2 pt-4 pb-4 '+css_border).props('readonly')
        ui.number(prefix='Start row1:',value=1, format='%i').classes('pl-2 '+css_border)
        ui.number(prefix='End row:', value=1, format='%i').classes('pl-2 '+css_border)
        ui.button('Execute', on_click=lambda: ui.notify('Execute query'))
    with ui.scroll_area().classes('w-full h-20 '+css_border):
        ui.label('Query code')
    with ui.scroll_area().classes('w-full h-80 '+css_border):
        ui.label('Results')
    with ui.row().classes('w-full items-center'):
        ui.button('Clear', on_click=lambda: ui.notify('Clear form'))
        ui.button('Menu', on_click=lambda: ui.notify('Back to menu'))












if __name__ in ['__main__', '__mp_main__']:
    config.init_config()
    # Page decorator alleen als het script direct wordt uitgevoerd
    content = ui.page('/')(content)
    content()
    ui.run()