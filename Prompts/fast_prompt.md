# 🚀 **Snelle Prompt voor Lint-Free Code**

Schrijf Python code die direct lint-free is volgens Ruff/Mypy. Gebruik:

- **Max 88 karakters** per regel
- **Geen shebang** (`#!/usr/bin/env python3`)
- **Imperative docstrings** ("Create" niet "Creates")
- **Path objecten** voor file operations (`Path.open()`)
- **datetime.now(timezone.utc)** voor timestamps
- **hasattr()** voor UI elementen
- **Type hints** overal waar mogelijk
- **Kleine functies** (<50 statements)
- **contextlib.suppress** voor exceptions
- **Boolean args** als keyword-only (`*, active: bool = False`)
- **Any types** met `# type: ignore[return-value]` voor UI returns

Schrijf direct lint-free code!
