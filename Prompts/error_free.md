cd app# 🎯 **Perfecte Prompt voor Lint-Free Python Code**

Ik wil dat je nieuwe Python code schrijft die direct volledig lint-free is volgens de volgende strikte regels:

## 🚨 **Linting Regels (Ruff + Mypy):**

### **Code Style:**

- **E501**: Max 88 karakters per regel
- **EXE001**: Geen shebang in Python bestanden
- **D401**: Docstrings in imperative mood ("Create" niet "Creates")
- **D107**: Alle `__init__` methoden hebben docstrings
- **D205**: Blank line tussen docstring summary en description

### **Type Safety:**

- **ANN401**: Geen `Any` types tenzij expliciet nodig (dan `# type: ignore[return-value]`)
- **ANN002/ANN003**: Type annotations voor `*args: Any` en `**kwargs: Any`
- **FBT001/FBT002**: Boolean arguments zijn keyword-only (`*, active: bool = False`)

### **Modern Python:**

- **PTH123**: Gebruik `Path.open()` in plaats van `open()`
- **PTH118**: Gebruik `Path` met `/` operator in plaats van `os.path.join()`
- **PTH103**: Gebruik `Path.mkdir(parents=True)` in plaats van `os.makedirs()`
- **DTZ005**: Gebruik `datetime.now(timezone.utc)` in plaats van `datetime.now()`
- **SIM105**: Gebruik `contextlib.suppress(Exception)` in plaats van `try-except-pass`

### **Exception Handling:**

- **BLE001**: Geen blind `Exception` catches (gebruik specifieke exceptions of `# noqa: BLE001`)
- **S110**: Log exceptions in plaats van `try-except-pass`

### **Code Complexity:**

- **PLR0915**: Max 50 statements per functie
- **C901**: Max 10 cyclomatic complexity
- **PLR0912**: Max 12 branches per functie
- **SIM117**: Combineer nested `with` statements

### **NiceGUI Specifiek:**

- **UI Element Access**: Gebruik `hasattr()` checks voor dynamische UI elementen
- **Type Ignores**: Gebruik `# type: ignore[assignment]` voor UI element assignments
- **Return Types**: Gebruik `Any` met `# type: ignore[return-value]` voor UI element returns

## 📋 **Code Structuur:**

- **Imports**: Georganiseerd (standard library, third party, local)
- **Class Methods**: Kleine, gefocuste functies
- **Error Handling**: Specifieke exceptions waar mogelijk
- **Type Hints**: Volledig getypeerd waar mogelijk

## 🎨 **Voorbeelden van Correcte Code:**

```python
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

class MyClass:
    def __init__(self) -> None:
        """Initialize the class."""
        self.ui_element: Any = None  # type: ignore[assignment]

    def create_ui(self) -> Any:  # type: ignore[return-value]
        """Create the UI elements."""
        with ui.card().classes("w-full"), ui.column():
            self.ui_element = ui.button("Click me")

        return self.ui_element

    def handle_file(self, file_path: str) -> None:
        """Handle file operations."""
        path = Path(file_path)
        with suppress(OSError):
            with path.open(encoding="utf-8") as f:
                content = f.read()
```

## 🚫 **Wat NOOIT te doen:**

- ❌ `#!/usr/bin/env python3` in Python bestanden
- ❌ `except Exception:` zonder `# noqa: BLE001`
- ❌ `open()` in plaats van `Path.open()`
- ❌ `datetime.now()` zonder timezone
- ❌ Boolean arguments zonder keyword-only syntax
- ❌ Lange regels (>88 karakters)
- ❌ Grote functies (>50 statements)

## ✅ **Wat ALTIJD te doen:**

- ✅ Volledige type hints
- ✅ Imperative docstrings
- ✅ `hasattr()` checks voor UI elementen
- ✅ `Path` objecten voor file operations
- ✅ `contextlib.suppress` voor exception handling
- ✅ Kleine, gefocuste functies

Schrijf nu de code die ik vraag, zorg ervoor dat deze direct volledig lint-free is!
