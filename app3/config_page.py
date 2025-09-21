import datetime, json
import globals, config
from message import message
from nicegui import ui

def content()-> None:
    temp_config = dict(globals.config_data)
    ui_elements = {}
    
    with ui.card().classes('w-1/2'):
        with ui.grid(columns=2).classes('w-full'):
            # Eerst de basis configuratie items
            basic_config = {k: v for k, v in globals.config_data.items() 
                          if not isinstance(v, dict)}
            
            for key, value in basic_config.items():
                if isinstance(value, bool):
                    ui_elements[key] = ui.checkbox(key, value=value).on_value_change(
                        lambda e, k=key: temp_config.update({k: e})
                    )
                elif isinstance(value, (str, int, float)):
                    ui_elements[key] = ui.input(label=key, value=str(value)).on_value_change(
                        lambda e, k=key: temp_config.update({k: e})
                    )
        
        # Field Mappings in scroll areas
        with ui.grid(columns=2).classes('w-full gap-4 mt-4'):
            # Image Fields Column
            with ui.column().classes('w-full border-1 rounded-lg p-2').style('border: 1px solid blue'):
                ui.label('Image Fields Mapping').classes('font-bold mb-2')
                with ui.scroll_area().classes('h-48 border-1 rounded-lg p-2'):
                    # Regular mappings
                    ui.label('Field Mappings:').classes('font-bold')
                    for exif_key, db_field in globals.config_data.get('dbtable_fields_image', {}).items():
                        ui.label(f'{exif_key} → {db_field}').classes('text-sm text-gray-600')
                    
                    # Write flags
                    ui.label('Write-enabled Fields:').classes('font-bold mt-4')
                    write_flags = globals.config_data.get('dbtable_fields_image_write', {})
                    for field, enabled in write_flags.items():
                        if enabled:
                            ui.label(f'• {field}').classes('text-sm text-green-600')
            
            # Video Fields Column
            with ui.column().classes('w-full border-1 rounded-lg p-2').style('border: 1px solid blue'):
                ui.label('Video Fields Mapping').classes('font-bold mb-2')
                with ui.scroll_area().classes('h-48 border-1 rounded-lg p-2'):
                    # Regular mappings
                    ui.label('Field Mappings:').classes('font-bold')
                    for exif_key, db_field in globals.config_data.get('dbtable_fields_video', {}).items():
                        ui.label(f'{exif_key} → {db_field}').classes('text-sm text-gray-600')
                    
                    # Write flags
                    ui.label('Write-enabled Fields:').classes('font-bold mt-4')
                    write_flags = globals.config_data.get('dbtable_fields_video_write', {})
                    for field, enabled in write_flags.items():
                        if enabled:
                            ui.label(f'• {field}').classes('text-sm text-green-600')
        
        def update_and_save():
            # Update config met huidige UI waarden (alleen basis configuratie)
            for key, element in ui_elements.items():
                temp_config[key] = element.value
            
            # Behoud de bestaande database veld mappings
            temp_config['dbtable_fields_image'] = globals.config_data.get('dbtable_fields_image', {})
            temp_config['dbtable_fields_video'] = globals.config_data.get('dbtable_fields_video', {})
            temp_config['dbtable_fields_image_write'] = globals.config_data.get('dbtable_fields_image_write', {})
            temp_config['dbtable_fields_video_write'] = globals.config_data.get('dbtable_fields_video_write', {})
            
            globals.config_data.update(temp_config)
            with open('conf.json', 'w', encoding='utf-8') as f:
                json.dump(globals.config_data, f, indent=4)
            
            ui.notify('Configuration saved successfully', type='positive')
            
        ui.button('Update', on_click=update_and_save).classes('w-32 mt-4')


    