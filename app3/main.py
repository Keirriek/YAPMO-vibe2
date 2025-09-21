'''
pip install json5
pip install pyexiftool
pip install pillow
'''
import globals, config
# import home_page, config_page, metadata_page, fill_db_page
import home_page
import config_page
import metadata_page
import fill_db_page
import theme
import json
from nicegui import ui
from message import message
import write_db_page
import sql_db_page

config.init_config()

s=json.dumps(globals.config_data)
# message(s)

@ui.page('/')
def index1_page() -> None:
    with theme.frame('Homepage'):
        home_page.content()

@ui.page('/config_page')
def index2_page() -> None:
    with theme.frame('Configpage'):
        config_page.content()

@ui.page('/metadata_page')
def index3_page() -> None:
    with theme.frame('Metadata'):
        metadata_page.content()

@ui.page('/fill_db_page')
def index4_page() -> None:
    with theme.frame('Fill Database'):
        fill_db_page.content()

@ui.page('/write_db_page')
def index5_page() -> None:
    with theme.frame('Write DB'):
        write_db_page.content()

@ui.page('/sql_db_page')
def index6_page() -> None:
    with theme.frame('SQL Database'):
        sql_db_page.content()

ui.run(title='main', reload=True)