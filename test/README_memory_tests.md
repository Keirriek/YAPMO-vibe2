# Memory Leak Testing voor Fill Database V2

## Test Bestanden

### 1. `memory_monitor.py` - Real-time Monitor ⭐ **AANBEVOLEN**
**Doel:** Real-time memory monitoring tijdens app gebruik
**Features:**
- Live memory monitoring (elke seconde)
- Memory leak detection
- Thread leak detection
- Process leak detection
- Real-time dashboard
- Detailed reports

**Uitvoeren:**
```bash
cd /workspaces && poetry run python test/memory_monitor.py
# of
./test/run_memory_test.sh
```

### 2. `test_scenarios.py` - Test Scenario's
**Doel:** Gedefinieerde test scenario's voor memory testing
**Scenario's:**
- Large Directory Scan
- Large File Processing
- Multiple Scan Cycles
- Multiple Processing Cycles
- Abort Testing
- Mixed Operations

**Uitvoeren:**
```bash
cd /workspaces && poetry run python test/test_scenarios.py
```

### 3. `test_memory_leaks.py` - Volledige Test
**Doel:** Uitgebreide memory leak testing (simulatie)
**Cycles:** 10 cycles (configureerbaar)
**Tests:**
- Herhaalde scan/process cycles
- ProcessPoolExecutor cleanup
- Queue memory management
- Worker process cleanup
- Memory trend analysis

**Uitvoeren:**
```bash
cd /workspaces && poetry run python test/test_memory_leaks.py
```

### 4. `test_memory_quick.py` - Snelle Test
**Doel:** Snelle development testing (simulatie)
**Cycles:** 3 cycles
**Tests:**
- Basis memory monitoring
- Quick leak detection

**Uitvoeren:**
```bash
cd /workspaces && poetry run python test/test_memory_quick.py
```

## Memory Leak Thresholds

### Memory Leaks
- **⚠️ POTENTIAL LEAK:** > 10MB per cycle
- **❌ CRITICAL LEAK:** > 20MB per cycle
- **✅ OK:** < 5MB per cycle

### Process Leaks
- **⚠️ PROCESS LEAK:** > 0 processes na cleanup
- **❌ CRITICAL LEAK:** > 2 processes na cleanup
- **✅ OK:** 0 processes na cleanup

## Test Output Interpretatie

### Normale Output
```
📊 Cycle 1/10
   Before: 45.2 MB RSS, 156 processes
   After:  47.1 MB RSS, 156 processes
   Diff:   +1.9 MB RSS, +0 processes
   ✅ OK: +1.9 MB change
```

### Memory Leak Output
```
📊 Cycle 3/10
   Before: 47.1 MB RSS, 156 processes
   After:  62.3 MB RSS, 158 processes
   Diff:   +15.2 MB RSS, +2 processes
   ⚠️  POTENTIAL MEMORY LEAK: 15.2 MB increase
   ⚠️  PROCESS LEAK: 2 processes not cleaned up
```

## Troubleshooting

### Import Errors
```bash
# Zorg dat je in de juiste directory bent
cd /workspaces

# Check of app module beschikbaar is
python -c "from app.pages.fill_db_page_v2 import FillDatabasePageV2"
```

### Permission Errors
```bash
# Test directory permissions
mkdir -p /workspaces/test/test_data
touch /workspaces/test/test_data/test.jpg
```

### Process Cleanup Issues
- Check of `worker_manager.cleanup()` wordt aangeroepen
- Check of `ProcessPoolExecutor.shutdown()` wordt aangeroepen
- Check of alle worker futures worden gecancelled

## Real-time Monitoring Workflow ⭐ **AANBEVOLEN**

### **Poetry Workflow (Aanbevolen)**

#### **Stap 1: Start Memory Monitor**
```bash
cd /workspaces && poetry run python test/memory_monitor.py
# of
./test/run_poetry_memory_test.sh
```

#### **Stap 2: Start App**
```bash
# In nieuwe terminal
cd /workspaces/app && poetry run python main.py
```

#### **Stap 3: Voer Test Scenario's Uit**
```bash
# In nieuwe terminal
cd /workspaces && poetry run python test/test_scenarios.py
# Kies een scenario en volg de stappen
```

#### **Stap 4: Stop Monitoring**
```bash
# In memory monitor terminal
Ctrl+C
```

#### **Stap 5: Check Reports**
- **Real-time log:** `/workspaces/test/memory_log.txt`
- **Detailed report:** `/workspaces/test/memory_report.txt`

### **Alternatieve Workflow (Zonder Poetry)**
```bash
# Alleen als Poetry niet beschikbaar is
cd /workspaces && python test/memory_monitor.py
# In nieuwe terminal:
cd /workspaces/app && python main.py
```

## Development Workflow

1. **Real-time Monitor** voor echte app testing ⭐
2. **Quick Test** tijdens development
3. **Volledige Test** voor belangrijke changes
4. **Trend Analysis** voor memory leak patterns
5. **Fix & Retest** tot alle leaks opgelost zijn

## Memory Monitoring Tools

### System Tools
```bash
# Monitor memory usage
htop
# of
top -p $(pgrep -f "python.*fill_db")

# Monitor processes
ps aux | grep python
```

### Python Tools
```python
import psutil
process = psutil.Process()
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
print(f"Threads: {process.num_threads()}")
```
