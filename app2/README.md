# YAPMO v2.0 - Yet Another Photo Management Organizer

Een moderne, modulaire applicatie voor het beheren en organiseren van media bestanden.

## 🎯 Doel

1. Alle media bestanden op een systeem vinden
2. Resultaten in een database opslaan
3. Ontdubbelen op basis van hash en metadata
4. Automatisch directory structuur genereren (Jaar/Maand/Dag/Type/GPS)
5. Media bestanden automatisch organiseren zonder dataverlies

## 🚀 Quick Start

```bash
# Start de applicatie
poetry run python main.py

# Of met debugging
poetry run python -m debugpy --listen 5678 main.py
```

## 🛠️ Development

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Format code
poetry run black .

# Lint code
poetry run flake8 .
```

## 📁 Project Structuur

```
app/
├── main.py              # Entry point
├── config.py            # Configuratie management
├── database_manager.py  # Database operaties
├── media_scanner.py     # Media bestand scanning
├── pages/               # Modulaire pagina's
│   ├── home.py         # Hoofdpagina
│   ├── config.py       # Configuratie pagina
│   └── media.py        # Media beheer pagina
├── utils/               # Utility functies
└── data/                # Database en configuratie bestanden
```

## 🔧 Features

- **Modulaire architectuur** met NiceGUI
- **Automatische metadata extractie** met ExifTool
- **Hash-based deduplicatie**
- **Intelligente directory organisatie**
- **Configuratie management** met Pydantic
- **Logging en error handling**

## 📋 TODO

- [ ] Modulaire pages opzetten
- [ ] UI structuur implementeren
- [ ] Database manager structuur
- [ ] File processing flow
- [ ] Media finder functionaliteit
- [ ] Directory tree processing
- [ ] Metadata page
- [ ] SQL query interface
