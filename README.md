# 🎨 YAPMO - Yet Another Photo Manager and Organizer

Een moderne media management applicatie gebouwd met Python en NiceGUI.

## ✨ Features

- **Moderne UI Design** - Elegante interface met gestandaardiseerde elementen
- **Configuratie Management** - Robuust configuratie systeem met validatie
- **Modulaire Structuur** - Schone, onderhoudbare code
- **Error Handling** - Intelligente configuratie error dialogs
- **File Management** - Media file organisatie en metadata extractie

## 🚀 Installatie

1. **Installeer dependencies:**
   ```bash
   poetry install
   ```

2. **Start de applicatie:**
   ```bash
   cd app
   python main.py
   ```

3. **Open in browser:**
   ```
   http://localhost:8080
   ```

## 📱 Pagina's

### 🏠 Hoofdpagina (`/`)
- Welkomstpagina met applicatie informatie
- Navigatie naar configuratie en elementen test
- Versie informatie uit configuratie

### ⚙️ Configuratie (`/config`)
- Uitgebreide configuratie interface met tabs
- General, Database, Logging, Paths, File Types, Metadata, Advanced
- Real-time validatie van configuratie waarden
- Reset naar default waarden functionaliteit

### 🧪 Elementen Test (`/element-test`)
- Test alle gestandaardiseerde UI elementen
- Buttons, inputs, progress bars
- Sliders, checkboxes, switches
- Kleur demonstratie voor buttons

## 🎨 UI Elementen

Alle UI elementen zijn gestandaardiseerd en beschikbaar via de `YAPMOTheme` class:

- **Cards** - Elegante styling met consistente spacing
- **Buttons** - Verschillende kleuren (primary, secondary, positive, negative, warning)
- **Input Fields** - Moderne styling met validatie
- **Progress Bars** - Lineair en circulair
- **Interactive Elements** - Sliders, switches, checkboxes, radio buttons
- **Directory Picker** - Lokale directory selectie functionaliteit

## 🏗️ Architectuur

```
app/
├── main.py                    # Hoofdingang van de applicatie
├── config.py                  # Configuratie management met validatie
├── theme.py                   # UI thema en gestandaardiseerde elementen
├── shutdown_manager.py        # Graceful shutdown functionaliteit
├── local_directory_picker.py  # Directory selectie component
├── config.json               # Configuratie bestand
└── pages/                    # Pagina modules
    ├── __init__.py           # Pages package
    ├── main_page.py          # Hoofdpagina
    ├── config_page.py        # Configuratie pagina
    └── element_test_page.py  # Elementen test pagina
```

## 🔧 Configuratie

De applicatie gebruikt een robuust configuratie systeem in `config.py`:

### **Configuratie Bestand** (`config.json`)
- **General** - App naam, versie, beschrijving
- **Processing** - Max workers, update intervals, ExifTool settings
- **Database** - Database naam, tabellen, retry instellingen
- **Logging** - Log bestand, pad, debug mode
- **Paths** - Source, search, browse directories
- **Extensions** - Ondersteunde bestandstypen

### **Validatie Systeem**
- **Automatische validatie** van configuratie waarden
- **Min/max waarde controles** voor numerieke parameters
- **Error dialogs** voor corrupte of ongeldige configuratie
- **Default waarden** bij ontbrekende parameters

## 🚨 Error Handling

Intelligente error handling voor configuratie problemen:

### **Configuratie Error Dialogs**
- **JSON Error** - Corrupte of onleesbare configuratie bestanden
- **Validation Error** - Ongeldige parameter waarden
- **Default Config** - Eerste keer opstarten met default waarden

### **Error Types**
- **Missing config.json** → Default config dialog
- **Corrupted JSON** → JSON error dialog met herstel opties
- **Invalid values** → Validation error dialog met correctie opties

## 🎯 Volgende Stappen

Deze applicatie is de basis voor media management functionaliteit:

- **File Scanning** - Automatische detectie van media bestanden
- **Metadata Extraction** - ExifTool integratie voor foto/video metadata
- **Database Management** - SQLite database voor file tracking
- **Deduplication** - Hash-based duplicate detection
- **File Organization** - Automatische directory structuur

---

**Gebouwd met ❤️ en Python + NiceGUI**
