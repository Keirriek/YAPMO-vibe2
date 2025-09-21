# YAPMO Theme Usage Examples

## Overzicht

Alle styling is nu gecentraliseerd in `theme.py` met gestandaardiseerde CSS strings. Dit zorgt voor:

- ✅ **Consistentie** - Alle UI elementen zien er hetzelfde uit
- ✅ **Onderhoudbaarheid** - Styling wijzigingen op 1 plek
- ✅ **Herbruikbaarheid** - Eenvoudig te gebruiken in andere modules

## Gestandaardiseerde CSS Classes

### Card Styling

```python
from theme import YAPMOTheme

# Basis card styling
CARD_STYLE = 'bg-white/95 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20'
CARD_PADDING = 'p-8'
CARD_SMALL_PADDING = 'p-6'
```

### Button Styling

```python
# Button types
BUTTON_PRIMARY = 'font-medium transition-all duration-200 shadow-lg bg-primary text-white hover:bg-blue-600 focus:ring-2 focus:ring-blue-400 focus:ring-offset-2'
BUTTON_SECONDARY = 'font-medium transition-all duration-200 shadow-lg bg-secondary text-white hover:bg-green-600 focus:ring-2 focus:ring-green-400 focus:ring-offset-2'
BUTTON_WARNING = 'font-medium transition-all duration-200 shadow-lg bg-warning text-white hover:bg-orange-600 focus:ring-2 focus:ring-orange-400 focus:ring-offset-2'
BUTTON_ERROR = 'font-medium transition-all duration-200 shadow-lg bg-gradient-to-r from-red-500 to-red-600 text-white hover:from-red-600 hover:to-red-700 focus:ring-2 focus:ring-red-400 focus:ring-offset-2'
BUTTON_GRAY = 'font-medium transition-all duration-200 shadow-lg bg-gray-500 text-white hover:bg-gray-600 focus:ring-2 focus:ring-gray-400 focus:ring-offset-2'

# Button sizes
BUTTON_SIZE_SM = 'px-4 py-2 rounded-lg'
BUTTON_SIZE_MD = 'px-6 py-3 rounded-2xl'
BUTTON_SIZE_LG = 'px-8 py-4 rounded-2xl'
```

## Praktische Voorbeelden

### 1. Dialog Maken

```python
from theme import YAPMOTheme

def create_my_dialog():
    dialog = ui.dialog()
    with dialog, YAPMOTheme.create_dialog_card():
        YAPMOTheme.create_dialog_title('Mijn Dialog')
        YAPMOTheme.create_dialog_content('Dit is de content van mijn dialog')

        with YAPMOTheme.create_dialog_buttons():
            YAPMOTheme.create_dialog_button_cancel(dialog.close)
            YAPMOTheme.create_dialog_button_confirm('OK', my_action)

    dialog.open()
```

### 2. Button Maken

```python
from theme import YAPMOTheme

# Eenvoudige button
button = YAPMOTheme.create_button('Klik hier', on_click=my_function)

# Button met specifieke kleur en grootte
button = YAPMOTheme.create_button('Save', on_click=save_data, color='secondary', size='lg')
```

### 3. Card Maken

```python
from theme import YAPMOTheme

# Card met theme styling
with ui.card().classes(YAPMOTheme.CARD_STYLE + ' ' + YAPMOTheme.CARD_PADDING):
    ui.label('Mijn content')
```

### 4. Custom Dialog

```python
from theme import YAPMOTheme

def create_custom_dialog(title: str, content: str, confirm_text: str = 'OK'):
    dialog = ui.dialog()
    with dialog, YAPMOTheme.create_dialog_card():
        YAPMOTheme.create_dialog_title(title)
        YAPMOTheme.create_dialog_content(content)

        with YAPMOTheme.create_dialog_buttons():
            YAPMOTheme.create_dialog_button_cancel(dialog.close)
            YAPMOTheme.create_dialog_button_confirm(confirm_text, lambda: dialog.close())

    dialog.open()
```

## Voordelen van deze Aanpak

### Voor Ontwikkelaars

- **Eenvoudig te gebruiken** - Import theme en gebruik de methodes
- **Geen CSS kennis nodig** - Alles is voorgeprogrammeerd
- **Consistent resultaat** - Alle dialogs/buttons zien er hetzelfde uit

### Voor Onderhoud

- **1 plek voor wijzigingen** - Alleen theme.py aanpassen
- **Automatische updates** - Alle modules krijgen de nieuwe styling
- **Geen duplicatie** - Geen CSS strings verspreid over bestanden

### Voor Uitbreiding

- **Nieuwe componenten** - Eenvoudig toe te voegen aan theme.py
- **Nieuwe kleuren** - Bepaal nieuwe kleur en voeg toe aan CSS classes
- **Nieuwe sizes** - Voeg nieuwe button sizes toe

## Best Practices

1. **Gebruik altijd theme methodes** - Nooit hardcoded CSS strings
2. **Voeg nieuwe styling toe aan theme.py** - Niet in individuele modules
3. **Gebruik consistente naming** - `BUTTON_*`, `CARD_*`, `DIALOG_*`
4. **Documenteer nieuwe componenten** - Voeg voorbeelden toe aan deze documentatie

## Voorbeeld: Nieuwe Component Toevoegen

```python
# In theme.py
class YAPMOTheme:
    # Nieuwe CSS class
    ALERT_STYLE = 'bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded-2xl'

    @staticmethod
    def create_alert(text: str) -> Any:
        """Maak een consistente alert"""
        return ui.label(text).classes(YAPMOTheme.ALERT_STYLE)

# In andere modules
from theme import YAPMOTheme
alert = YAPMOTheme.create_alert('Dit is een waarschuwing!')
```
