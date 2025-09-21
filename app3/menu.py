from nicegui import ui
# https://tailwindcss.com/docs/min-width

def menu() -> None:
    tailcss= 'text-white bg-blue-500 rounded-md w-16 shadow-lg text-center'
    ui.link('Home', '/').classes(replace=tailcss)
    ui.link('Metadata', '/metadata_page').classes(replace=tailcss)
    ui.link('Fill DB', '/fill_db_page').classes(replace= tailcss)
    ui.link('SQL DB', '/sql_db_page').classes(replace=tailcss)
    ui.link('Write DB', '/write_db_page').classes(replace=tailcss)
    # ui.link('    B    <', '/b').classes(replace=tailcss)
    # ui.link('    C    <', '/c').classes(replace=tailcss)
    # ui.link('    D    ', '/d').classes(replace=tailcss)
    # ui.link('    E    ', '/e').classes(replace=tailcss)
    ui.link('Config', '/config_page').classes(replace=tailcss)
    