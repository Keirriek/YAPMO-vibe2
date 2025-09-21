from nicegui import ui
from typing import Optional, Dict, List, Any
import re
import json  # Voeg json import toe bovenaan het bestand
from exif_read_write import get_exif_data_json, get_exif_data_no_json, put_exif_data2

class ExifUI:
    def __init__(self):
        self.path: str = ''
        self.result: Optional[Dict] = None
        # self.groups: List[str] = ['EXIF', 'XMP', 'IPTC', 'File', 'Composite', 'Photoshop', '<New>']
        self.groups: List[str] = None
        self.current_metadata: Dict = {}
        self.show_metadata = None  # Toevoegen
        
        # UI elements
        self.group_dropdown: Any = None
        self.field_dropdown: Any = None
        self.value_input: Any = None
        self.dialog: Any = None
        
    def get_fields_for_group(self, group: str) -> List[str]:
        """Verzamel alle velden voor een specifieke groep uit de huidige metadata"""
        fields = []
        
        # Verzamel alle velden voor deze groep
        for key in self.current_metadata.keys():
            if ':' in key:
                current_group, field = key.split(':', 1)
                if current_group == group:
                    fields.append(field)
        
        return sorted(fields)  # Verwijder '<New>' en sorteer

    def update_field_dropdown(self):
        """Update de velden dropdown op basis van geselecteerde groep"""
        if self.group_dropdown and self.field_dropdown:
            selected_group = self.group_dropdown.value
            fields = self.get_fields_for_group(selected_group)
            
            # Force UI update
            self.field_dropdown.clear()
            self.field_dropdown.options = fields
            self.field_dropdown.update()
            
            # Set initial value
            if fields:
                self.field_dropdown.value = fields[0]
                self.field_dropdown.update()
                self.update_value_input()

    def update_value_input(self):
        """Update het waarde invoerveld op basis van geselecteerde groep en veld"""
        if not (self.group_dropdown and self.field_dropdown and self.value_input):
            return
            
        if self.group_dropdown.value == '<New>' or self.field_dropdown.value == '<New>':
            self.value_input.value = ''
            return
            
        key = f"{self.group_dropdown.value}:{self.field_dropdown.value}"
        current_value = self.current_metadata.get(key, '')
        
        # Format arrays en andere speciale waarden
        if isinstance(current_value, list):
            # Converteer lijst naar komma-gescheiden string zonder quotes en brackets
            self.value_input.value = ', '.join(str(x) for x in current_value)
        else:
            # Gewone waarde direct tonen
            self.value_input.value = str(current_value)

    async def show_warning_dialog(self) -> bool:
        """Toon waarschuwing dialog en return True als gebruiker doorgaat"""
        with ui.dialog() as dialog, ui.card():
            ui.label('Are you sure you want to update the metadata?')
            with ui.row():
                ui.button('No', on_click=lambda: dialog.submit(False))
                ui.button('Yes', on_click=lambda: dialog.submit(True))
        return await dialog

    async def get_new_value(self, prompt: str) -> str:
        """Helper functie voor nieuwe waardes"""
        with ui.dialog() as dialog, ui.card():
            ui.label(prompt)
            input_field = ui.input('').classes('w-80')  # Leeg label voor het input veld
            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('Cancel', on_click=lambda: dialog.submit(None)).classes('mr-2')
                ui.button('OK', on_click=lambda: dialog.submit(input_field.value)).classes('bg-blue-500')
        
        result = await dialog
        if result:
            result = result.strip()
            if not result:  # Als de input leeg is
                ui.notify('Value cannot be empty', type='warning')
                return None
        return result

    async def build_metadata_key(self) -> Optional[str]:
        """Bouw de metadata key op basis van geselecteerde groep en veld"""
        if not (self.group_dropdown and self.field_dropdown):
            return None
            
        group = self.group_dropdown.value
        field = self.field_dropdown.value
        
        if group == '<New>':
            while True:
                group = await self.get_new_value('Enter new group name:')
                if not group:  # Als gebruiker cancel klikt of leeg laat
                    ui.notify('Group name is required', type='warning')
                    return None
                if ':' in group:
                    ui.notify('Group name cannot contain ":"', type='warning')
                    continue
                break
                
        if field == '<New>':
            while True:
                field = await self.get_new_value('Enter new field name:')
                if not field:  # Als gebruiker cancel klikt of leeg laat
                    ui.notify('Field name is required', type='warning')
                    return None
                if ':' in field:
                    ui.notify('Field name cannot contain ":"', type='warning')
                    continue
                break
                
        if not group or not field:
            return None
            
        # Zorg dat groep en veld geen ':' bevatten (extra veiligheid)
        group = group.replace(':', '_')
        field = field.replace(':', '_')
        
        return f"{group}:{field}"

    async def handle_update(self):
        """Handel de Update knop actie af"""
        if await self.show_warning_dialog():
            metadata_key = await self.build_metadata_key()
            if not metadata_key or not self.value_input:
                self.result = None
                return
            
            try:
                parsed_value = self.value_input.value.strip()
                
                # Controleer of de groep schrijfbaar is
                group = metadata_key.split(':')[0]
                if group not in ['EXIF', 'XMP', 'IPTC']:
                    ui.notify(f'Group "{group}" is not writable. Use EXIF, XMP, or IPTC instead.', type='warning')
                    return
                
                metadata = {metadata_key: parsed_value}
                
                if put_exif_data2(self.path, metadata):
                    self.result = metadata
                    # Vernieuw de metadata weergave
                    if hasattr(self, 'show_metadata'):
                        self.show_metadata(self.path)
                    # Reset de editor UI
                    self.init_put_exif_ui(self.path, self.card)
                    ui.notify('Metadata successfully updated', type='positive')
                else:
                    ui.notify('Error writing metadata: Kon metadata niet schrijven', type='negative')
                    self.result = None
            except Exception as e:
                ui.notify(f'Onverwachte fout: {str(e)}', type='negative')
                self.result = None

    def clear_put_exif_ui(self):
        """Reset alle UI elementen en ga terug naar home"""
        if self.group_dropdown:
            self.group_dropdown.value = None
        if self.field_dropdown:
            self.field_dropdown.value = None
        if self.value_input:
            self.value_input.value = ''
        if self.card:
            self.card.visible = False
            self.card.clear()
        self.result = None
        ui.navigate.to('/')  # Terug naar home page

    def init_put_exif_ui(self, path: str, card) -> None:
        """Initialiseer de UI voor metadata bewerking"""
        self.path = path
        self.result = None
        
        self.current_metadata = get_exif_data_json(path) or {}
        
        # Controleer of we metadata hebben
        if not self.current_metadata:
            ui.notify('Geen metadata gevonden in bestand', type='warning')
            return
            
        # Dan alle groepen verzamelen uit de metadata
        available_groups = set()
        group_fields = {}  # Dict om bij te houden welke velden elke groep heeft
        
        for key in self.current_metadata.keys():
            if ':' in key:
                group, field = key.split(':', 1)
                available_groups.add(group)
                if group not in group_fields:
                    group_fields[group] = []
                group_fields[group].append(field)
        
        # Voeg alleen standaard groepen toe die daadwerkelijk velden hebben
        standard_groups = ['EXIF', 'XMP', 'IPTC', 'File', 'Composite', 'Photoshop']
        for group in standard_groups:
            if group in group_fields:
                available_groups.add(group)
        
        # Sorteer de groepen (zonder '<New>')
        available_groups = sorted(list(available_groups))
        
        # Clear bestaande UI als die er is
        if hasattr(self, 'card'):
            self.card.clear()
            
        # Nu pas de UI opbouwen
        self.card = card
        self.card.visible = True
        
        with self.card:
            ui.label(f'Edit metadata for: {path}')
            ui.label('Use a comma to separate items. Use no quotes.').classes('text-sm text-gray-600')
            
            with ui.row().classes('w-full items-start'):
                with ui.column().classes('w-1/3'):
                    self.group_dropdown = ui.select(
                        label='Group',
                        options=available_groups,
                        on_change=self.update_field_dropdown,
                        value=available_groups[0] if available_groups else None
                    ).classes('w-full')
                    ui.button('New Group', on_click=self.add_new_group).classes('mt-2')
                
                with ui.column().classes('w-1/3'):
                    self.field_dropdown = ui.select(
                        label='Field',
                        options=[],
                        on_change=self.update_value_input
                    ).classes('w-full')
                    ui.button('New Field', on_click=self.add_new_field).classes('mt-2')
                
                # with ui.column().classes('w-1/3'):
                self.value_input = ui.textarea(
                    label='Value'
                ).classes('w-full h-16 border-2 border-blue-500 rounded-md')
            
            with ui.row().classes('justify-end mt-4'):
                ui.button('Back', on_click=self.clear_put_exif_ui).classes('mr-2')
                ui.button('Cancel', on_click=lambda: self.reset_page()).classes('mr-2')
                ui.button('Update', on_click=self.handle_update).classes('bg-blue-500')
        
        # Update field dropdown met de initiële groep selectie
        if self.group_dropdown:
            self.update_field_dropdown()

    def reset_page(self):
        """Reset de pagina zonder metadata wijzigingen"""
        if self.card:
            # Vernieuw alleen de editor UI
            self.init_put_exif_ui(self.path, self.card)

    async def add_new_group(self):
        """Voeg een nieuwe groep toe"""
        while True:
            group = await self.get_new_value('Enter new group name:')
            if not group:  # Als gebruiker cancel klikt of leeg laat
                return
            if ':' in group:
                ui.notify('Group name cannot contain ":"', type='warning')
                continue
            
            # Voeg de nieuwe groep toe aan de opties
            new_options = list(self.group_dropdown.options)
            new_options.insert(-1, group)  # Voeg toe voor '<New>'
            self.group_dropdown.options = new_options
            self.group_dropdown.value = group
            self.update_field_dropdown()
            break

    async def add_new_field(self):
        """Voeg een nieuw veld toe aan de huidige groep"""
        if not self.group_dropdown.value or self.group_dropdown.value == '<New>':
            ui.notify('Please select a group first', type='warning')
            return
            
        while True:
            field = await self.get_new_value('Enter new field name:')
            if not field:  # Als gebruiker cancel klikt of leeg laat
                return
            if ':' in field:
                ui.notify('Field name cannot contain ":"', type='warning')
                continue
            
            # Voeg het nieuwe veld toe aan de opties
            new_options = list(self.field_dropdown.options)
            new_options.insert(-1, field)  # Voeg toe voor '<New>'
            self.field_dropdown.options = new_options
            self.field_dropdown.value = field
            self.update_value_input()
            break

def create_main_page():
    """Maak de hoofdpagina met de Update Metadata knop"""
    @ui.page('/')
    def main():
        with ui.card().classes('w-full max-w-lg mx-auto mt-8'):
            with ui.row():
                ui.label('Label Metadata Editor').classes('text-2xl mb-4 border-2 border-blue-500') ####
                ui.button('Update Metadata', 
                         on_click=lambda: ui.navigate.to('/edit-metadata')
                ).classes('bg-blue-500')

def create_edit_page(exif_ui: ExifUI):
    """Maak de metadata editor pagina"""
    @ui.page('/edit-metadata')
    def edit():
        exif_ui.init_put_exif_ui('/workspace/Pictures-test/Small-test/DSC00018.JPG')

# Voorbeeld gebruik:
if __name__ in {"__main__", "__mp_main__"}: # dit is voor multi processing
    exif_ui = ExifUI()
    
    # Maak beide pagina's
    create_main_page()
    create_edit_page(exif_ui)
    
    ui.run() 