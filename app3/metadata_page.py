import globals
import config
from local_file_picker import local_file_picker
from message import message
from exif_write_ui import ExifUI
from exif_read_write import get_exif_data_json, get_exif_data_no_json
from nicegui import ui

# Geen page decorator hier, zodat de functie herbruikbaar is
def content() -> None:
    exif_ui = ExifUI()
    
    def show_metadata_in_label(choses_picture):
        metadata = get_exif_data_no_json(choses_picture)
        
        if metadata:
            metadata_from_image.clear()
            metadata_from_image.visible=True
            with metadata_from_image:
                ui.label('Dit is de metadata:')
                for key, value in metadata.items():
                    ui.label(f"{key}: {value}")
        else:
            metadata_from_image.clear()
            ui.notify('No metadata available')

    # Maak show_metadata_in_label beschikbaar voor ExifUI
    exif_ui.show_metadata = show_metadata_in_label

    async def pick_file_show() -> None:
        path = globals.config_data['browse_path']
        pr = await local_file_picker(path, multiple=False)
        if pr:
            # Reset UI elementen
            metadata_from_image.clear()
            card.clear()
            
            # Update UI met nieuwe data
            image_frame.set_source(pr[0])
            show_metadata_in_label(pr[0])
            
            # ExifUI setup
            exif_ui.metadata_from_image = metadata_from_image
            exif_ui.image_frame = image_frame
            exif_ui.init_put_exif_ui(pr[0], card)
        return

    message('This is the metadata page.').classes('font-bold')
    ui.label('Use the menu on the top right to navigate.')
    ui.button('Choose file', on_click=pick_file_show, icon='folder')

    image_frame = ui.image().classes('w-1/2 h-full')
    # path_image=image_frame.source
    with ui.row().classes('w-full justify-start mt-4'):
        metadata_from_image = ui.scroll_area().classes('w-1/3 h-80 leading-3 border-2 border-blue-500 rounded-lg')
        metadata_from_image.visible=False
        card=ui.card().classes('h-80 border-2 border-blue-500 rounded-lg')
        card.visible=False
        # exif_ui.__init__()

if __name__ in ['__main__', '__mp_main__']:
    config.init_config()
    # Page decorator alleen als het script direct wordt uitgevoerd
    content = ui.page('/')(content)
    content()
    ui.run()