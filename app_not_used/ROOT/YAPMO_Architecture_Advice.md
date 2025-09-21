# **🎯 YAPMO Media Management - Architectuur Advies**

## **📋 Samenvatting van je Workflow**

1. **Directory selectie** → Doorloop alle subdirectories
2. **File scanning** → Zoek media files met specifieke extensies
3. **UI updates** → Toon voortgang, gebruiker kan afbreken
4. **Progress tracking** → Maak progress kaartje met scroll bar en kentallen
5. **Parallel metadata extraction** → ExifTool met max_workers parallel processing
6. **Database storage** → Opslaan in SQLite database
7. **Logging** → UI en file logging tijdens alle processen
8. **Abort functionality** → Gebruiker kan altijd afbreken

---

## **🏗️ 1. ARCHITECTUUR ADVIES**

### **A. Hoofdcomponenten Structuur**

```
app/
├── main.py                    # Entry point
├── config.py                  # Configuratie management
├── theme.py                   # UI theming
├── shutdown_manager.py        # Graceful shutdown
├── local_directory_picker.py  # Directory selectie
├── config.json               # Configuratie bestand
├── managers/                 # Core managers
│   ├── __init__.py
│   ├── file_scanner.py       # File scanning logic
│   ├── metadata_extractor.py # ExifTool processing
│   ├── database_manager.py   # SQLite operations
│   ├── logging_manager.py    # Queue-based logging
│   └── process_manager.py    # Parallel process coordination
├── queues/                   # Queue management
│   ├── __init__.py
│   ├── result_queue.py       # Database results
│   ├── logging_queue.py      # Log messages
│   └── abort_queue.py        # Abort signals
└── pages/                    # UI pages
    ├── main_page.py
    ├── config_page.py
    ├── scan_page.py          # File scanning interface
    ├── progress_page.py      # Progress tracking
    └── element_test_page.py
```

### **B. Process Architecture**

**Hoofdprocessen:**
1. **UI Process** → NiceGUI interface
2. **File Scanner** → Directory traversal
3. **Metadata Workers** → Parallel ExifTool processing (max_workers)
4. **Database Manager** → Queue consumer voor database writes
5. **Logging Manager** → Queue consumer voor logging

**Queue System:**
- **Result Queue** → Metadata results → Database Manager
- **Logging Queue** → Log messages → Logging Manager → UI + Files
- **Abort Queue** → Abort signals → All processes

---

## **🗄️ 2. RESULTATEN VAN PARALLEL OPVOEREN AAN DATABASE**

### **A. Queue-Based Architecture**

```python
# queues/result_queue.py
import queue
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class MetadataResult:
    file_path: str
    metadata: Dict[str, Any]
    hash_value: str
    file_size: int
    timestamp: float

class ResultQueue:
    def __init__(self):
        self.queue = queue.Queue()
        self.abort_flag = False
    
    def put_result(self, result: MetadataResult):
        if not self.abort_flag:
            self.queue.put(result)
    
    def get_result(self, timeout=1.0):
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def set_abort(self):
        self.abort_flag = True
```

### **B. Database Manager (Queue Consumer)**

```python
# managers/database_manager.py
import sqlite3
from queues.result_queue import ResultQueue, MetadataResult

class DatabaseManager:
    def __init__(self, result_queue: ResultQueue):
        self.result_queue = result_queue
        self.db_path = get_param("database", "database_name")
        self.batch_size = get_param("database", "database_write_batch_size")
        self.batch = []
    
    async def start_consumer(self):
        """Consume results from queue and write to database"""
        while True:
            result = self.result_queue.get_result()
            if result:
                self.batch.append(result)
                if len(self.batch) >= self.batch_size:
                    await self._write_batch()
            elif self.result_queue.abort_flag:
                break
    
    async def _write_batch(self):
        """Write batch to database"""
        if self.batch:
            # SQLite write operations
            # Use run.io_bound for database I/O
            await run.io_bound(self._write_to_db, self.batch.copy())
            self.batch.clear()
```

### **C. Metadata Worker (Queue Producer)**

```python
# managers/metadata_extractor.py
import subprocess
import hashlib
from queues.result_queue import ResultQueue, MetadataResult

class MetadataExtractor:
    def __init__(self, result_queue: ResultQueue, logging_queue: LoggingQueue):
        self.result_queue = result_queue
        self.logging_queue = logging_queue
    
    async def process_file(self, file_path: str):
        """Process single file and put result in queue"""
        try:
            # Extract metadata with ExifTool
            metadata = await run.io_bound(self._extract_metadata, file_path)
            hash_value = await run.io_bound(self._calculate_hash, file_path)
            
            result = MetadataResult(
                file_path=file_path,
                metadata=metadata,
                hash_value=hash_value,
                file_size=os.path.getsize(file_path),
                timestamp=time.time()
            )
            
            self.result_queue.put_result(result)
            
        except Exception as e:
            self.logging_queue.put_log("ERROR", f"Failed to process {file_path}: {e}")
```

---

## **📝 3. LOGGING PROBLEMATIEK**

### **A. Queue-Based Logging System**

```python
# queues/logging_queue.py
import queue
from dataclasses import dataclass
from enum import Enum

class LogLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class LogMessage:
    level: LogLevel
    message: str
    timestamp: float
    source: str

class LoggingQueue:
    def __init__(self):
        self.queue = queue.Queue()
        self.abort_flag = False
    
    def put_log(self, level: LogLevel, message: str, source: str = "SYSTEM"):
        if not self.abort_flag:
            log_msg = LogMessage(
                level=level,
                message=message,
                timestamp=time.time(),
                source=source
            )
            self.queue.put(log_msg)
    
    def get_log(self, timeout=1.0):
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None
```

### **B. Logging Manager (Queue Consumer)**

```python
# managers/logging_manager.py
from queues.logging_queue import LoggingQueue, LogMessage, LogLevel

class LoggingManager:
    def __init__(self, logging_queue: LoggingQueue):
        self.logging_queue = logging_queue
        self.log_enabled = get_param("logging", "log_enabled")
        self.log_terminal = get_param("logging", "log_terminal")
        self.log_file = get_param("logging", "log_file")
        self.log_path = get_param("logging", "log_path")
    
    async def start_consumer(self):
        """Consume logs from queue and display/write them"""
        while True:
            log_msg = self.logging_queue.get_log()
            if log_msg:
                await self._process_log(log_msg)
            elif self.logging_queue.abort_flag:
                break
    
    async def _process_log(self, log_msg: LogMessage):
        """Process single log message"""
        # Write to file (always)
        if self.log_enabled:
            await run.io_bound(self._write_to_file, log_msg)
        
        # Show in terminal
        if self.log_terminal:
            print(f"[{log_msg.level.value}] {log_msg.message}")
        
        # Show in UI
        if log_msg.level in [LogLevel.ERROR, LogLevel.WARNING]:
            ui.notify(log_msg.message, type=log_msg.level.value.lower())
```

---

## **⚡ 4. ZORGEN DAT NICEGUI RESPONSIVE BLIJFT**

### **A. Async Processing Pattern**

```python
# managers/process_manager.py
from nicegui import run, ui
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ProcessManager:
    def __init__(self):
        self.max_workers = get_param("processing", "max_workers")
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.abort_flag = False
    
    async def start_file_processing(self, file_list: List[str]):
        """Start parallel file processing"""
        tasks = []
        
        for file_path in file_list:
            if self.abort_flag:
                break
            
            # Create task for each file
            task = asyncio.create_task(
                self._process_single_file(file_path)
            )
            tasks.append(task)
            
            # Limit concurrent tasks
            if len(tasks) >= self.max_workers:
                await asyncio.gather(*tasks, return_exceptions=True)
                tasks = []
        
        # Process remaining tasks
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_single_file(self, file_path: str):
        """Process single file using run.io_bound"""
        try:
            # Use run.io_bound for I/O operations
            result = await run.io_bound(
                self.metadata_extractor.process_file, 
                file_path
            )
            return result
        except Exception as e:
            self.logging_queue.put_log(
                LogLevel.ERROR, 
                f"Failed to process {file_path}: {e}"
            )
```

### **B. UI Update Pattern**

```python
# pages/progress_page.py
class ProgressPage:
    def __init__(self):
        self.progress_bar = ui.linear_progress(0)
        self.status_label = ui.label("Ready to start...")
        self.files_processed = ui.label("Files processed: 0")
        self.current_file = ui.label("Current file: None")
    
    async def update_progress(self, processed: int, total: int, current_file: str):
        """Update UI progress indicators"""
        # Update progress bar
        self.progress_bar.value = processed / total if total > 0 else 0
        
        # Update labels
        self.files_processed.text = f"Files processed: {processed}/{total}"
        self.current_file.text = f"Current file: {os.path.basename(current_file)}"
        
        # Force UI update
        await asyncio.sleep(0.01)  # Small delay to allow UI updates
```

### **C. Keep-Alive Mechanism**

```python
# main.py
from nicegui import ui, run
import asyncio

async def keep_alive_worker():
    """Keep UI alive during long operations"""
    while True:
        # Send heartbeat to browser
        ui.run_javascript("console.log('UI alive')")
        await asyncio.sleep(1.0)

async def start_application():
    """Start all background processes"""
    # Start keep-alive worker
    asyncio.create_task(keep_alive_worker())
    
    # Start queue consumers
    asyncio.create_task(database_manager.start_consumer())
    asyncio.create_task(logging_manager.start_consumer())
    
    # Start UI
    ui.run(title="YAPMO", port=8080, show=True)

if __name__ in {"__main__", "__mp_main__"}:
    asyncio.run(start_application())
```

---

## **🎯 IMPLEMENTATIE AANBEVELINGEN**

### **A. Configuratie Parameters**
- **`max_workers`** → Beperk parallel processing (1-32)
- **`nicegui_update_interval`** → UI update frequentie (10-60000ms)
- **`ui_update`** → UI refresh interval (20-60000ms)
- **`database_write_batch_size`** → Batch size voor database writes
- **`exiftool_timeout`** → Timeout voor ExifTool operations

### **B. Error Handling**
- **Queue timeouts** → Voorkom deadlocks
- **Process monitoring** → Detecteer crashed workers
- **Graceful shutdown** → Stop alle processes netjes
- **Resource cleanup** → Sluit database connections

### **C. Performance Optimization**
- **Batch processing** → Database writes in batches
- **Memory management** → Limiteer queue sizes
- **I/O optimization** → Gebruik `run.io_bound` voor alle I/O
- **Progress updates** → Throttle UI updates

---

## **✅ CONCLUSIE**

Deze architectuur lost je problemen op:

1. **SQLite paralleliteit** → Queue-based approach met single database writer
2. **Logging problematiek** → Centralized logging via queues
3. **UI responsiveness** → Async processing met `run.io_bound`
4. **Abort functionality** → Queue-based abort signals
5. **Progress tracking** → Real-time UI updates via queues

**Deze aanpak is gebaseerd op NiceGUI best practices en lost de bekende problemen op met parallel processing en UI responsiveness.**

---

## **📚 REFERENTIES**

- [NiceGUI GitHub Repository](https://github.com/zauberzeug/nicegui/tree/3df8b2b16eb7ac471cc36bf9498a3cd652e95bb9)
- [NiceGUI Global Worker Example](https://github.com/zauberzeug/nicegui/tree/3df8b2b16eb7ac471cc36bf9498a3cd652e95bb9/examples/global_worker)
- [NiceGUI Progress Example](https://github.com/zauberzeug/nicegui/tree/3df8b2b16eb7ac471cc36bf9498a3cd652e95bb9/examples/progress)
- [NiceGUI SQLite Database Example](https://github.com/zauberzeug/nicegui/tree/3df8b2b16eb7ac471cc36bf9498a3cd652e95bb9/examples/sqlite_database)
