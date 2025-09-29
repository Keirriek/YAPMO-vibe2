# Stageplan YAPMO Database Integration

## Overzicht
Implementatie van file processing voor media files met database integratie. Elke media file wordt verwerkt om de volgende informatie te extraheren:
- file name (basename met extensie)
- file URL (file:// absolute path)
- file size (OS disk grootte)
- media type (image/video)
- sidecar files (lijst van sidecar extensions)

## Fase 1: Worker Function Implementatie

### 1.1 Herschrijf dummy_worker_process
**Bestand:** `/workspaces/app/worker_functions.py`

**Nieuwe functie naam:** `process_media_file(file_path: str, worker_id: int) -> Dict[str, Any]`

**Functionaliteit:**
- Extraheer file informatie van media file
- Bepaal media type op basis van file extension (case-insensitive)
- Zoek sidecar files inzelfde directory
- Handle unicode/non-ASCII karakters correct
- Error handling met logging
- Performance timing

### 1.2 File Information Extraction
```python
# File basics
file_name = os.path.basename(file_path)  # Basename met extensie
file_url = f"file://{os.path.abspath(file_path)}"  # Absolute file URL
file_size = os.path.getsize(file_path)  # OS disk grootte

# Media type detection (case-insensitive)
file_ext = os.path.splitext(file_name)[1].lower()
media_type = "image" if file_ext in image_extensions else "video"

# Sidecar detection
sidecars = find_sidecars(file_path, file_name)
```

### 1.3 Sidecar Detection Logic
```python
def find_sidecars(file_path: str, file_name: str) -> List[str]:
    """Find sidecar files for given media file."""
    # Get directory and basename without extension
    directory = os.path.dirname(file_path)
    base_name = os.path.splitext(file_name)[0]
    
    # Get sidecar extensions from config
    sidecar_extensions = get_param("processing", "sidecar_extensions", [])
    
    found_sidecars = []
    for ext in sidecar_extensions:
        sidecar_path = os.path.join(directory, f"{base_name}{ext}")
        if os.path.exists(sidecar_path):
            found_sidecars.append(ext)
    
    return found_sidecars
```

### 1.4 Error Handling
```python
# File access errors -> WARNING level
try:
    file_size = os.path.getsize(file_path)
except OSError as e:
    log_message = f"WARNING: Cannot access file {file_path}: {str(e)}"

# Unicode errors -> ERROR level  
try:
    file_name = os.path.basename(file_path)
except UnicodeDecodeError as e:
    log_message = f"ERROR: Unicode error processing {file_path}: {str(e)}"

# OS errors -> ERROR level
except Exception as e:
    log_message = f"ERROR: System error processing {file_path}: {str(e)}"
```

### 1.5 Performance Timing
```python
start_time = time.time()
# ... processing ...
processing_time = time.time() - start_time
```

### 1.6 Result Dictionary Structure
```python
result = {
    'file_path': file_path,           # Original file path
    'file_name': file_name,           # Basename met extensie
    'file_url': file_url,             # file:// absolute path
    'file_size': file_size,           # OS disk grootte in bytes
    'media_type': media_type,         # "image" of "video"
    'sidecars': sidecars,             # List van sidecar extensions [".aae", ".xmp"]
    'worker_id': worker_id,           # Worker ID voor debugging
    'success': success,               # Boolean success/failure
    'processing_time': processing_time, # Processing tijd in seconden
    'log_messages': [                 # Log messages array
        {
            'level': 'DEBUG',
            'message': f"{file_path} verwerkt als {'success' if success else 'failure'} in {processing_time:.3f} sec"
        }
    ]
}
```

## Fase 2: Database Manager Implementatie

### 2.1 Nieuwe Database Manager
**Bestand:** `/workspaces/app/core/db_manager_v2.py`

**Functie:** `db_dummy(result: dict) -> None`

**Functionaliteit:**
- Accepteert result dictionary
- Doet verder niets (dummy implementatie)
- Voorbereid voor toekomstige database operaties

### 2.2 Database Manager Interface
```python
def db_dummy(result: dict) -> None:
    """Dummy database manager - accepts result and does nothing."""
    # TODO: Implement actual database operations
    # For now, just accept the result and do nothing
    pass
```

## Fase 3: Result Processing Integration

### 3.1 Result Queue Splitting
**Bestand:** `/workspaces/app/core/result_processor.py`

**Wijziging:** `_process_result()` methode

**Functionaliteit:**
- Verwerk result van worker
- Splits log messages naar logging queue
- Stuur file data naar database manager
- Behoud bestaande queue mechanisme

### 3.2 Log Message Processing
```python
# Process log messages (bestaande functionaliteit)
for log_msg in result.get('log_messages', []):
    self.logging_queue.put(log_msg)

# Send file data to database manager
if result.get('success', False):
    db_dummy(result)  # Send successful results to database
```

### 3.3 Database Manager Import
```python
from core.db_manager_v2 import db_dummy
```

## Fase 4: Configuration Updates

### 4.1 Sidecar Extensions Config
**Bestand:** `/workspaces/app/config.json`

**Status:** Sidecar extensions zijn al aanwezig in config.json
- Controleer bestaande sidecar extensions configuratie
- Verificeer dat extensions correct zijn geformatteerd

### 4.2 Media Type Extensions Config
**Controleer:** Bestaande image/video extensions in config.json
- Zorg dat extensions case-insensitive zijn
- Voeg ontbrekende extensions toe indien nodig

## Fase 5: Unicode/Non-ASCII Handling

### 5.1 File Path Handling
- **UTF-8 encoding** voor alle file paths
- **os.path.basename()** en **os.path.dirname()** gebruiken
- **os.path.exists()** voor sidecar detection
- **os.path.getsize()** voor file size

### 5.2 Error Handling
- **UnicodeDecodeError** → ERROR level logging
- **OSError** → WARNING level logging
- **Exception** → ERROR level logging

## Fase 6: Performance Optimizations

### 6.1 Worker Function Optimizations
- **Minimale file I/O** operations
- **Efficient sidecar detection** (single directory scan)
- **Fast media type detection** (dictionary lookup)
- **Minimal memory allocation**

### 6.2 Database Communication
- **Direct function call** (geen queue overhead)
- **Synchronous processing** per result
- **No batching** (zoals gevraagd)

### 6.3 Memory Management
- **Result dictionary** direct doorgeven
- **Geen intermediate storage**
- **Immediate processing**

## Fase 7: Testing & Validation

### 7.1 Unicode Test Cases
- **Non-ASCII filenames** (zoals in test directory)
- **Special characters** in paths
- **Mixed encoding** scenarios

### 7.2 Performance Testing
- **1000 files/sec** target
- **300,000 files** total capacity
- **Memory usage** monitoring
- **Processing time** per file

### 7.3 Error Handling Testing
- **Permission denied** files
- **Corrupted files**
- **Network drive** issues
- **Unicode encoding** problems

## Implementatie Volgorde

1. **Fase 1**: Worker function implementatie
2. **Fase 2**: Database manager dummy
3. **Fase 3**: Result processing integratie
4. **Fase 4**: Configuration updates
5. **Fase 5**: Unicode handling
6. **Fase 6**: Performance optimizations
7. **Fase 7**: Testing & validation

## Success Criteria

- ✅ **File processing** werkt correct
- ✅ **Unicode handling** probleemloos
- ✅ **Performance** 1000 files/sec
- ✅ **Error handling** correct
- ✅ **Database integration** ready
- ✅ **Sidecar detection** accurate
- ✅ **Media type detection** correct
- ✅ **Logging** volledig

## Risico's & Mitigatie

### **Risico: Unicode Issues**
- **Mitigatie**: Uitgebreide testing met non-ASCII karakters
- **Fallback**: Error logging en graceful degradation

### **Risico: Performance Bottlenecks**
- **Mitigatie**: Profiling en optimization
- **Monitoring**: Real-time performance metrics

### **Risico: File Access Errors**
- **Mitigatie**: Robuuste error handling
- **Logging**: Duidelijke error messages

## Documentatie Updates

### **Code Comments**
- **Unicode handling** duidelijk gedocumenteerd
- **Case-insensitive** operations gemarkeerd
- **Error handling** locaties aangegeven
- **Performance** considerations genoteerd

### **Function Documentation**
- **Docstrings** voor alle functies
- **Parameter types** gespecificeerd
- **Return values** gedocumenteerd
- **Error conditions** beschreven
