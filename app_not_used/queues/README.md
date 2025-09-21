# **YAPMO Queues Documentation**

## **📋 Overzicht**

Deze directory bevat alle queue implementaties voor YAPMO. Elke queue heeft een specifieke verantwoordelijkheid en is geoptimaliseerd voor verschillende soorten data.

---

## **🏗️ Queue Architectuur**

### **Queue Types**
- **ResultQueue** - Metadata results naar database
- **LoggingQueue** - Log messages naar UI/files
- **ProgressQueue** - Progress updates naar UI

### **Queue Manager**
- **QueueManager** - Unified interface voor alle queues

---

## **📊 ResultQueue**

### **Overzicht**
De ResultQueue beheert metadata results van file processing naar de database.

### **Features**
- **Thread-safe operations**
- **Configurable queue depth** (default: 32)
- **Timeout handling** (default: 500ms)
- **Abort functionality**
- **Database integration**

### **Usage**
```python
from queues.result_queue import ResultQueue, MetadataResult

result_queue = ResultQueue()

# Put result
result = MetadataResult(
    file_path="test.jpg",
    exif_data={"camera": "Canon"},
    file_info={"size": 1024},
    hash_value="abc123",
    file_size=1024,
    timestamp=time.time()
)
await result_queue.put_result(result)

# Get result
retrieved = result_queue.get_result()
```

### **Configuration**
```json
{
  "processing_queues": {
    "result_queue_depth": 32,
    "get_result_timeout": 500
  }
}
```

---

## **📝 LoggingQueue**

### **Overzicht**
De LoggingQueue beheert log messages voor UI en file output.

### **Features**
- **Multiple log levels** (INFO, WARNING, ERROR, DEBUG)
- **Configurable queue depth** (default: 200)
- **Timeout handling** (default: 100ms)
- **Abort functionality**
- **Source tracking**

### **Usage**
```python
from queues.logging_queue import LoggingQueue, LogLevel

logging_queue = LoggingQueue()

# Put log message
await logging_queue.put_log(LogLevel.INFO, "Processing started", "ProcessManager")

# Get log message
log_msg = logging_queue.get_log()
print(f"{log_msg.level}: {log_msg.message}")
```

### **Log Levels**
- **INFO** - General information
- **WARNING** - Warning messages
- **ERROR** - Error messages
- **DEBUG** - Debug information

### **Configuration**
```json
{
  "processing_queues": {
    "logging_queue_depth": 200,
    "get_log_timeout": 100
  }
}
```

---

## **📈 ProgressQueue**

### **Overzicht**
De ProgressQueue beheert progress updates van ProcessManager naar UI.

### **Features**
- **Thread-safe operations**
- **Configurable queue depth** (default: 50)
- **Timeout handling** (default: 100ms)
- **Abort functionality**
- **Optimized voor file-based processing**

### **Usage**
```python
from queues.progress_queue import ProgressQueue, ProgressUpdate

progress_queue = ProgressQueue()

# Put progress update
update = ProgressUpdate(
    task_id="main_process",
    progress=50.0,
    status="running",
    eta="2m 30s",
    message="Processing files"
)
await progress_queue.put_progress(update)

# Get progress update
retrieved = progress_queue.get_progress()
print(f"Progress: {retrieved.progress:.1f}%")
```

### **ProgressUpdate Structure**
```python
@dataclass
class ProgressUpdate:
    task_id: str          # Task identifier
    progress: float       # Progress percentage (0.0-100.0)
    status: str          # Status ("running", "completed", "error")
    eta: str             # Estimated time remaining
    message: str         # Additional message
    timestamp: float     # Timestamp when created
```

### **Configuration**
```json
{
  "processing_queues": {
    "progress_queue_depth": 50,
    "get_progress_timeout": 100
  }
}
```

---

## **🎛️ QueueManager**

### **Overzicht**
De QueueManager coördineert alle queues en biedt een uniforme interface.

### **Features**
- **Unified interface** voor alle queues
- **Abort/reset/clear** functionaliteit
- **Queue statistics** en monitoring
- **Integration** met ProcessManager

### **Usage**
```python
from managers.queue_manager import QueueManager
from queues.progress_queue import ProgressUpdate
from queues.logging_queue import LogLevel

queue_manager = QueueManager()

# Progress updates
update = ProgressUpdate(
    task_id="main_process",
    progress=75.0,
    status="running",
    eta="1m 30s"
)
await queue_manager.put_progress(update)

# Log messages
await queue_manager.put_log(LogLevel.INFO, "Processing 75% complete")

# Queue management
queue_manager.abort_all()  # Abort all queues
queue_manager.reset_all()  # Reset all queues
queue_manager.clear_all()  # Clear all queues

# Statistics
stats = queue_manager.get_queue_stats()
print(f"Queue sizes: {stats}")
```

### **Queue Statistics**
```python
stats = queue_manager.get_queue_stats()
# Returns:
{
    'result_queue': {
        'size': 5,
        'is_full': False,
        'is_empty': False,
        'is_aborted': False
    },
    'logging_queue': {
        'size': 12,
        'is_full': False,
        'is_empty': False,
        'is_aborted': False
    },
    'progress_queue': {
        'size': 1,
        'is_full': False,
        'is_empty': False,
        'is_aborted': False
    }
}
```

---

## **🧪 Testing**

### **Test Coverage**
- **ResultQueue**: 5/5 tests slagen
- **LoggingQueue**: 7/7 tests slagen
- **ProgressQueue**: Thread-safe operations
- **QueueManager**: Integration tests

### **Running Tests**
```bash
cd app
python -m pytest tests/test_result_queue.py -v
python -m pytest tests/test_logging_queue.py -v
python -m pytest tests/test_process_manager.py -v
```

---

## **📈 Performance**

### **Queue Performance**
- **ResultQueue**: 32 items, 500ms timeout
- **LoggingQueue**: 200 items, 100ms timeout
- **ProgressQueue**: 50 items, 100ms timeout

### **Memory Usage**
- **Minimal overhead** per queue
- **Configurable depth** voor memory management
- **Automatic cleanup** bij abort/reset

---

## **🔧 Configuration**

### **Complete Configuration**
```json
{
  "processing_queues": {
    "result_queue_depth": 32,
    "get_result_timeout": 500,
    "logging_queue_depth": 200,
    "get_log_timeout": 100,
    "progress_queue_depth": 50,
    "get_progress_timeout": 100
  }
}
```

### **Parameter Ranges**
- **Queue depths**: 5-500 items
- **Timeouts**: 1-6000ms
- **Optimized defaults** voor 200k+ files

---

## **🚀 Integration**

### **ProcessManager Integration**
```python
# ProcessManager gebruikt QueueManager
process_manager = ProcessManager(config_manager, queue_manager, abort_manager)

# Progress updates worden automatisch gestuurd
await process_manager.process_files(file_list, process_func)
```

### **UI Integration**
```python
# UI haalt progress updates op
progress_update = queue_manager.get_progress()
if progress_update:
    update_progress_bar(progress_update.progress)
    update_eta_label(progress_update.eta)
```

---

## **🎯 Next Steps**

Alle queues zijn volledig geïmplementeerd en getest. Klaar voor Stage 2: UI Development!

### **Ready for UI:**
- ✅ **ResultQueue** - Database results
- ✅ **LoggingQueue** - Log messages
- ✅ **ProgressQueue** - Progress updates
- ✅ **QueueManager** - Unified interface

**Klaar voor UI Development!** 🎉
