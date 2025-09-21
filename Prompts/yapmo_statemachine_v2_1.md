# YAPMO State Machine V2.2 - Unified Action State Architecture

## **Globale State Coordination Flags:**
- `yapmo_globals.action_finished_flag` - Unified flag voor alle acties (scan, process, abort) - gezet door actie proces
- `yapmo_globals.ui_update_finished` - UI update is klaar met bijwerken (gezet door UI update)
- `yapmo_globals.stop_processing_flag` - Abort flag voor processing proces
- `yapmo_globals.abort_requested` - Abort flag voor UI coordination

## **Parallel Processing Flags:**
- `yapmo_globals.parallel_workers_active` - Parallel workers zijn actief
- `yapmo_globals.worker_results_ready` - Worker resultaten beschikbaar in queue
- `yapmo_globals.worker_logs_ready` - Worker log messages beschikbaar in queue

## **State Transitions naar IDLE - BELANGRIJK!**
**ALLE transitions naar IDLE moeten `ui_update_finished` clearen!**

## **State Coordination System (V2.2 - Unified Action State):**

### **SCANNING → IDLE_ACTION_DONE:**
1. Scan proces is klaar
2. Zet `yapmo_globals.action_finished_flag = True`
3. Transition naar `IDLE_ACTION_DONE`

### **PROCESSING → IDLE_ACTION_DONE:**
1. Processing proces is klaar
2. Zet `yapmo_globals.action_finished_flag = True`
3. Transition naar `IDLE_ACTION_DONE`

### **ABORT → IDLE_ACTION_DONE:**
1. Abort proces is klaar
2. Zet `yapmo_globals.action_finished_flag = True`
3. Zet `yapmo_globals.ui_update_finished = True` (abort heeft geen queue processing nodig)
4. Transition naar `IDLE_ACTION_DONE`

### **IDLE_ACTION_DONE → IDLE/IDLE_SCAN_DONE:**
1. Wacht op `yapmo_globals.ui_update_finished = True`
2. Wanneer beide flags `True` zijn:
   - Clear `yapmo_globals.action_finished_flag = False`
   - Clear `yapmo_globals.ui_update_finished = False`
   - Stop UI update process
   - **State determination:**
     - Als `scanned_files` beschikbaar → `IDLE_SCAN_DONE`
     - Anders → `IDLE`

### **IDLE → SCANNING:**
1. Directory validation
2. Zet `yapmo_globals.action_finished_flag = False`
3. Zet `yapmo_globals.ui_update_finished = False`
4. Start UI update timer
5. Transition naar `SCANNING`

### **IDLE_SCAN_DONE → PROCESSING:**
1. Directory validation
2. Zet `yapmo_globals.action_finished_flag = False`
3. Zet `yapmo_globals.stop_processing_flag = False`
4. Start UI update timer
5. Transition naar `PROCESSING`

### **Directory Change Detection:**
- **IDLE_SCAN_DONE** → directory wijziging → **IDLE**
- Real-time detection via `on_change` event
- Clears `scanned_files` en `last_scanned_directory`
- Forces new scan before processing

### **UI Update Logic (V2.2 - Unified):**
- Wanneer `yapmo_globals.action_finished_flag = True` EN state = `IDLE_ACTION_DONE`:
  - Check of log queue leeg is
  - Als log queue leeg: Zet `yapmo_globals.ui_update_finished = True`
  - UI update is klaar met bijwerken
  - Transition naar `IDLE` state

## **Flag Management:**

### **Flag Setting (V2.2 - Unified):**
- `action_finished_flag = True`: Gezet door actie proces (scan/process/abort) wanneer klaar
- `ui_update_finished = True`: Gezet door UI update wanneer log queue leeg is
- `stop_processing_flag = True`: Gezet door abort handler voor processing
- `abort_requested = True`: Gezet door abort handler voor UI coordination
- `parallel_workers_active = True`: Gezet wanneer parallel workers starten
- `worker_results_ready = True`: Gezet wanneer result_queue items bevat
- `worker_logs_ready = True`: Gezet wanneer logging_queue items bevat

### **Flag Clearing (V2.2 - Unified):**
- `action_finished_flag = False`: Gecleared door `IDLE_ACTION_DONE` → `IDLE` transition
- `ui_update_finished = False`: Gecleared door `IDLE_ACTION_DONE` → `IDLE` transition
- `stop_processing_flag = False`: Gecleared bij processing start en IDLE state
- `abort_requested = False`: Gecleared bij IDLE state
- `parallel_workers_active = False`: Gecleared wanneer alle workers stoppen
- `worker_results_ready = False`: Gecleared wanneer result_queue leeg is
- `worker_logs_ready = False`: Gecleared wanneer logging_queue leeg is

### **Flag Reset (V2.2 - Unified):**
- Alle flags worden gecleared bij:
  - Actie start (om oude waarden te resetten)
  - Actie fout (om consistentie te behouden)
  - State transition naar `IDLE` (om clean state te garanderen)

## **Parallel Processing Architecture:**

### **Queue-Based Communicatie:**
- **result_queue**: Worker resultaten → Manager → UI updates
- **logging_queue**: Worker log messages → Manager → UI logging
- **abort_queue**: Abort signals → Alle workers

### **Worker Management:**
- **max_workers**: Configuratie voor aantal parallelle workers
- **ProcessPoolExecutor**: Python's built-in parallel processing
- **Dummy Workers**: Simuleren file processing voor testing
- **Real Workers**: Toekomstige implementatie voor echte file processing

### **UI Integration:**
- **Real-time Progress**: Updates van parallel workers
- **Worker Statistics**: Files/sec per worker, total throughput
- **Log Messages**: Worker log messages in UI
- **Abort Support**: Stop alle workers via abort_queue

## State Machine Principe
**Elke state configureert ALLE UI elementen in één keer:**
- **Enabled/Disabled status** - Welke elementen actief zijn
- **Kleuren en captions** - Hoe elementen eruitzien
- **Zichtbaarheid** - Welke elementen zichtbaar zijn
- **Updates** - Welke elementen live updates krijgen
- **Data** - Welke data wordt getoond

**Voordelen:**
- **Centralized control** - Eén plek voor alle UI configuratie
- **Eenvoudige code** - `self._set_state(ApplicationState.SCANNING)`
- **Minder bugs** - Geen vergeten elementen of inconsistenties
- **Onderhoudbaar** - Nieuwe elementen gewoon toevoegen aan state

## Code Implementatie Voorbeeld
```python
def _set_state(self, new_state: ApplicationState) -> None:
    """Set application state and configure all UI elements."""
    self.current_state = new_state
    
    if new_state == ApplicationState.SCANNING:
        # Configure ALL UI elements for SCANNING state
        self.scan_select_directory.disable()
        self.scan_start_button.disable()
        self.scan_spinner.enable()
        self.scan_spinner.set_visibility(True)
        self.scan_state_label.text = "scanning..."
        # ... configure all other elements
    elif new_state == ApplicationState.IDLE:
        # Configure ALL UI elements for IDLE state
        self.scan_select_directory.enable()
        self.scan_start_button.enable()
        self.scan_spinner.disable()
        self.scan_spinner.set_visibility(False)
        self.scan_state_label.text = "not active"
        # ... configure all other elements
```

## States (V2.2 - Unified Action State):
- [x] **INITIALISATION**: Page loading, setting up UI elements
- [x] **IDLE**: Ready to scan, processing disabled (no scan data available)
- [x] **SCANNING**: Currently scanning directory (collects files for processing)
- [x] **IDLE_SCAN_DONE**: Scan completed, ready to process (scan data available)
- [x] **PROCESSING**: Currently processing files (uses collected files from scan)
- [x] **IDLE_ACTION_DONE**: Unified state voor alle actie completion (scan/process/abort) - wacht op UI update completion
- [x] **ABORTED**: Operation cancelled, returning to IDLE (✅ Geïmplementeerd)
- [x] **EXIT_PAGE**: Page cleanup, saving state (behouden voor toekomst)

## **VERWIJDERDE STATES (V2.2):**
- ~~**IDLE_PROCESSING_DONE**~~ - Vervangen door **IDLE_ACTION_DONE**
- ~~**IDLE_AFTER_ABORT**~~ - Vervangen door **IDLE_ACTION_DONE**

## **NIEUWE STATES (V2.2):**
- **IDLE_SCAN_DONE** - Scan completed, ready to process (scan data available)
- **IDLE_ACTION_DONE** - Unified completion state for all actions

## **State Machine Flow Diagram:**

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    IDLE     │───▶│  SCANNING   │───▶│IDLE_ACTION_ │
│             │    │             │    │    DONE     │
│ ui_update:  │    │ ui_update:  │    │ ui_update:  │
│   STOPPED   │    │   STARTED   │    │  CONTINUES  │
└─────────────┘    └─────────────┘    └─────────────┘
       ▲                   │                   │
       │                   ▼                   ▼
       │            ┌─────────────┐    ┌─────────────┐
       │            │   ABORTED   │    │IDLE_SCAN_   │
       │            │             │    │    DONE     │
       │            │ ui_update:  │    │ ui_update:  │
       │            │ CONTINUES   │    │   STOPPED   │
       │            └─────────────┘    └─────────────┘
       │                   │                   │
       │                   └───────────────────┘
       │                                         │
       │                   ┌─────────────┐       │
       │                   │ PROCESSING  │       │
       │                   │             │       │
       │                   │ ui_update:  │       │
       │                   │   STARTED   │       │
       │                   └─────────────┘       │
       │                         │               │
       └─────────────────────────┴───────────────┘
```

### **Flow Transitions:**

**1. Normal Scan Flow:**
- `IDLE` → `SCANNING` → `IDLE_ACTION_DONE` → `IDLE_SCAN_DONE`

**2. Directory Change Flow:**
- `IDLE_SCAN_DONE` → `IDLE` (directory changed)

**3. Processing Flow:**
- `IDLE_SCAN_DONE` → `PROCESSING` → `IDLE_ACTION_DONE` → `IDLE`

**4. Abort Flows:**
- `SCANNING` → `ABORTED` → `IDLE_ACTION_DONE` → `IDLE`
- `PROCESSING` → `ABORTED` → `IDLE_ACTION_DONE` → `IDLE`

### **Flag Transitions per State:**

| State | Entry Flags | During Flags | Exit Flags | UI Update |
|-------|-------------|--------------|------------|-----------|
| **IDLE** | `ui_finished=true, action_finished=true` | - | `ui_finished=true, action_finished=true` | **STOPPED** |
| **SCANNING** | `ui_finished=true, action_finished=true` | `ui_finished→false, action_finished→false→true` | `ui_finished=false, action_finished=true` | **STARTED** |
| **PROCESSING** | `ui_finished=true, action_finished=true` | `ui_finished→false, action_finished→false→true` | `ui_finished=false, action_finished=true` | **STARTED** |
| **IDLE_ACTION_DONE** | `ui_finished=false, action_finished=true` | `ui_finished→true, action_finished=true` | `ui_finished=true, action_finished=true` | **CONTINUES** |
| **IDLE_SCAN_DONE** | `ui_finished=true, action_finished=true` | - | `ui_finished=true, action_finished=true` | **STOPPED** |
| **ABORTED** | `ui_finished=false, action_finished=true` | `ui_finished→true, action_finished=true` | `ui_finished=true, action_finished=true` | **CONTINUES** |

## **REFACTORING VOORDELEN (V2.2):**

### **Unified Action State:**
- **Eén state** (`IDLE_ACTION_DONE`) in plaats van drie verschillende states
- **Eén flag** (`action_finished_flag`) in plaats van meerdere specifieke flags
- **Consistente logica** voor alle actie completion scenarios

### **Vereenvoudigde State Machine:**
- **Minder states** = minder complexiteit
- **Uniforme flow** voor alle acties (scan, process, abort)
- **Eenvoudigere debugging** en onderhoud

### **Flag Management:**
- **Unified flag** (`action_finished_flag`) voor alle acties
- **Consistente clearing** in `IDLE_ACTION_DONE` → `IDLE` transition
- **Geen duplicatie** van flag management logica

### **Code Quality:**
- **Minder duplicatie** van state configuratie
- **Eenvoudigere UI update logic**
- **Betere maintainability** door unified approach

## Queue System Architecture (V2.2 - Volledig Geïmplementeerd):

### **Queue Types:**
- **result_queue**: Worker resultaten → Manager → UI updates
- **logging_queue**: Worker log messages → Manager → UI logging

### **Worker Communicatie:**
- **Dummy Workers**: Genereren resultaten en log messages
- **Result Processing**: `_process_worker_result()` verwerkt worker output
- **Log Processing**: `_process_worker_logs()` verwerkt log messages
- **UI Updates**: Real-time progress en log message display

### **Implementatie Status:**
- ✅ Queue system volledig functioneel
- ✅ Worker management compleet
- ✅ UI integration werkt perfect
- ✅ Logging integration werkt
- ✅ Abort support geïmplementeerd
- ✅ Statistics tracking werkt

## Parallel Processing States:
- [x] **PARALLEL_PROCESSING**: Currently processing files with parallel workers (via PROCESSING state)
- [x] **IDLE_ACTION_DONE**: Parallel processing complete, ready for new scan/process

## Geïmplementeerde Functionaliteit:

### **Globale Scan Counter Variabelen:**
- `yapmo_globals.scan_total_files` - Totaal aantal bestanden
- `yapmo_globals.scan_media_files` - Aantal media bestanden (images + videos)
- `yapmo_globals.scan_sidecars` - Aantal sidecar bestanden
- `yapmo_globals.scan_total_directories` - Totaal aantal directories

### **Parallel Processing Variabelen:**
- `yapmo_globals.parallel_workers_active` - Parallel workers zijn actief
- `yapmo_globals.worker_results_ready` - Worker resultaten beschikbaar in queue
- `yapmo_globals.worker_logs_ready` - Worker log messages beschikbaar in queue
- `yapmo_globals.max_workers` - Maximum aantal parallelle workers
- `yapmo_globals.worker_stats` - Statistieken per worker (files/sec, etc.)

### **File Collection During Scanning:**
- `_scan_directory_sync_with_updates(directory: str)` - Scanning met file collection
- `files_to_process = []` - Collects media file paths during scan
- `self.scanned_files = files_to_process` - Stores collected files for processing
- `self.last_scanned_directory = directory` - Stores scanned directory for validation
- Unicode support voor non-ASCII bestandsnamen via `os.walk()`
- File categorization op basis van config.json extensions
- Direct globale variabelen bijwerken tijdens scanning

### **File Processing Integration:**
- `_scan_files_for_processing(directory: str)` - Returns collected files from scan
- Simplified implementation: `return getattr(self, 'scanned_files', [])`
- No new scanning during processing - uses pre-collected files
- Directory validation ensures scan data matches current directory

### **State Machine Integratie:**
- SCANNING state start scanning proces na directory validatie
- IDLE_ACTION_DONE state toont scan resultaten via globale variabelen
- UI update code verwijderd (niet geïmplementeerd)
- EXIT_PAGE state behouden voor toekomstige navigatie detectie

### **Directory Change Detection:**
- `_on_directory_input_changed(event)` - Real-time directory input change detection
- NiceGUI `on_change` event handler for input field
- Clears `scanned_files` and `last_scanned_directory` when directory changes
- Transitions from `IDLE_SCAN_DONE` to `IDLE` when directory changes
- Forces new scan before processing can begin
- `_select_directory()` also triggers change detection via `_on_directory_input_changed(None)`

### **Abort Functionaliteit:**
- ABORTED state volledig geïmplementeerd en getest

### **Parallel Processing Functionaliteit:**
- ✅ **ParallelWorkerManager**: Volledig geïmplementeerd en functioneel
- ✅ **Dummy Workers**: Simuleren file processing met random timing
- ✅ **Queue System**: result_queue + logging_queue communicatie volledig werkend
- ✅ **UI Integration**: Real-time progress van parallel workers
- ✅ **Abort Support**: Stop alle workers via abort_queue
- ✅ **Performance Metrics**: Files/sec per worker, total throughput
- ✅ **Log Integration**: Worker log messages verschijnen in UI
- ✅ **Statistics**: Per-worker en totale statistieken worden bijgehouden
- Abort button in header (theme.py) met bevestigingsdialog
- Abort checks in scanning loops (os.walk en file processing)
- Flag management: abort_requested wordt correct gereset
- Performance optimalisatie: dictionary lookup voor file categorization
- Bug fixes: dubbele dialog, dialog close error, flag reset, UI message kleur

### **Performance Monitoring:**
- **Elapsed Time Tracking**: Start tijd vastleggen tijdens scanning start
- **Files/sec Metrics**: Performance berekening (total files / elapsed time)
- **Intelligent Time Formatting**: Automatische formatting (seconds/minutes/hours)
- **Logging Integration**: Performance metrics in scanning summary
- **Error Handling**: Veilige deling door nul voorkomen
- **User Feedback**: Concrete performance metrics voor gebruikers



## State: INITIALISATION
**UI Elements:**
- [x] All elements: disabled, loading state
- [x] `scan_state_label`: "Initializing..."
- [x] All progress indicators: hidden
- [x] All counters: "0"
- [x] Loading spinner: visible, active
- [x] `debug_current_state_label`: "State: initialisation"

**Wanneer kom je in INITIALISATION:**
- [x] **Page startup** - Eerste keer dat de pagina opent
- [x] **Page refresh** - Gebruiker drukt F5 of refresh
- [x] **Navigation terug** - Van andere pagina terug naar fill_db_v2
- [x] **Error recovery** - Na kritieke fout, pagina herstarten
- [x] **Session restore** - Browser herstelt sessie

**Wat gebeurt er in INITIALISATION:**
- [x] **UI elementen aanmaken** - Alle UI elementen initialiseren
- [x] **Config laden** - Configuratie uit config.json laden
- [x] **State herstellen** - Eventuele opgeslagen state herstellen
- [x] **Error checking** - Controleren op configuratie errors
- [x] **Dependencies check** - Controleren of alle benodigde bestanden bestaan

**Transitions:**
- [x] → IDLE: page loaded successfully
- [x] → EXIT_PAGE: initialization failed (kritieke fout)
- [x] ← INITIALISATION: page refresh (F5)
- [x] ← INITIALISATION: browser back/forward navigation
- [x] ← INITIALISATION: session restore

## State: IDLE
**UI Elements:**
- [x] `scan_select_directory`: `YAPMOTheme.create_button("SELECT DIRECTORY", self._select_directory, "secondary").enable()`
- [x] `scan_search_directory_input`: enabled, value from config
- [x] `scan_start_button`: `YAPMOTheme.create_button("START Scanning", self._start_scanning, "primary").enable()`
- [x] `scan_spinner`: disabled, hidden
- [x] `scan_state_label`: "not active"
- [x] `scan_total_files_label`: "0" (no scan data available)
- [x] `scan_media_files_label`: "0" (no scan data available)
- [x] `scan_sidecars_label`: "0" (no scan data available)
- [x] `scan_total_directories_label`: "0" (no scan data available)
- [x] `scan_details_button`: `YAPMOTheme.create_button("DETAILS", self._show_details, "secondary").disable()`
- [x] `processing_start_button`: `YAPMOTheme.create_button("START PROCESSING", self._start_processing, "primary").enable()`
- [x] `processing_progressbar`: value=0, hidden
- [x] `processing_progress_label`: "Processing: 0%"
- [x] `processing_files_processed_label`: "0" (no processing data available)
- [x] `processing_directories_processed_label`: "0" (no processing data available)
- [x] `processing_files_sec_label`: "0" (no processing data available)
- [x] `processing_directories_sec_label`: "0" (no processing data available)
- [x] `processing_time_to_finish_label`: "0" (no processing data available)
- [x] `debug_current_state_label`: "State: idle"

**Header Controls:**
- [x] ABORT button: disabled (no process running)
- [x] MENU button: enabled
- [x] EXIT button: enabled

**Transitions:**
- [x] → SCANNING: user clicks "START Scanning" + directory path is valid
- [x] → EXIT_PAGE: user navigates away
- [x] ← INITIALISATION: page refresh (F5)
- [x] ← INITIALISATION: browser back/forward navigation
- [x] ← IDLE_ACTION_DONE: **wanneer `ui_update_finished = True`**
  - [x] **Flag Clearing:** Clear `action_finished_flag = False` en `ui_update_finished = False`
  - [x] **UI Update Stop:** Stop UI update timer
  - [x] **State Transition:** → IDLE

## State: SCANNING
**UI Elements:**
- [x] `scan_select_directory`: `YAPMOTheme.create_button("SELECT DIRECTORY", self._select_directory, "secondary disabled").disable()`
- [x] `scan_search_directory_input`: disabled, current directory path
- [x] `scan_start_button`: `YAPMOTheme.create_button("SCANNING", self._start_scanning, "negative disabled").disable()`
- [x] `scan_spinner`: enabled, visible, red (ACTIVE)
- [x] `scan_state_label`: "scanning active"
- [x] `scan_total_files_label`: live updates from scan progress (MOMENTOPNAME)
- [x] `scan_media_files_label`: live updates from scan progress (MOMENTOPNAME)
- [x] `scan_sidecars_label`: live updates from scan progress (MOMENTOPNAME)
- [x] `scan_total_directories_label`: live updates from scan progress (MOMENTOPNAME)
- [x] `scan_details_button`: `YAPMOTheme.create_button("DETAILS", self._show_details, "secondary").disable()`
- [x] `processing_start_button`: `YAPMOTheme.create_button("START PROCESSING", self._start_processing, "primary").enable()`
- [x] `processing_progressbar`: value=0, hidden
- [x] `processing_progress_label`: "Processing: 0%"
- [x] `processing_files_processed_label`: "0" (no processing data available)
- [x] `processing_directories_processed_label`: "0" (no processing data available)
- [x] `processing_files_sec_label`: "0" (no processing data available)
- [x] `processing_directories_sec_label`: "0" (no processing data available)
- [x] `processing_time_to_finish_label`: "0" (no processing data available)
- [x] `debug_current_state_label`: "State: scanning"

**Header Controls:**
- [x] ABORT button: enabled (scan process running)
- [x] MENU button: disabled (process running)
- [x] EXIT button: disabled (process running)

**Transitions:**
- [x] → IDLE_ACTION_DONE: scan completed successfully
  - [x] **Scan Complete:** Scan proces is klaar
  - [x] **Flag Setting:** Zet `yapmo_globals.action_finished_flag = True`
  - [x] **State Transition:** → IDLE_ACTION_DONE
- [x] → ABORTED: ABORT dialog → Yes (scan cancelled)
- [x] → SCANNING: ABORT dialog → No (continue scanning)

## State: IDLE_ACTION_DONE
**Doel:** Unified state voor alle actie completion (scan/process/abort) - wacht op UI update completion
- **Flag Coordination:** Wachten op `ui_update_finished = True`
- **Safe Transition:** Voorbereiden voor veilige transitie naar IDLE
- **Flag Clearing:** Clear beide flags bij transition naar IDLE

**UI Elements:**
- [x] `scan_select_directory`: `YAPMOTheme.create_button("SELECT DIRECTORY", self._select_directory, "secondary").enable()` (zoals IDLE)
- [x] `scan_search_directory_input`: enabled, current directory path
- [x] `scan_start_button`: `YAPMOTheme.create_button("START Scanning", self._start_scanning, "primary").enable()` (nieuwe scan starten)
- [x] `scan_spinner`: disabled, hidden
- [x] `scan_state_label`: "scan complete"
- [x] `scan_total_files_label`: final scan results (KNOWN DATA)
- [x] `scan_media_files_label`: final scan results (KNOWN DATA)
- [x] `scan_sidecars_label`: final scan results (KNOWN DATA)
- [x] `scan_total_directories_label`: final scan results (KNOWN DATA)
- [x] `scan_details_button`: `YAPMOTheme.create_button("DETAILS", self._show_details, "secondary").disable()` (zoals IDLE)
- [x] `processing_start_button`: `YAPMOTheme.create_button("START PROCESSING", self._start_processing, "primary").enable()` (zoals IDLE)
- [x] `processing_progressbar`: value=0, hidden
- [x] `processing_progress_label`: "Processing: 0%"
- [x] `processing_files_processed_label`: "0" (no processing data available)
- [x] `processing_directories_processed_label`: "0" (no processing data available)
- [x] `processing_files_sec_label`: "0" (no processing data available)
- [x] `processing_directories_sec_label`: "0" (no processing data available)
- [x] `processing_time_to_finish_label`: "0" (no processing data available)
- [x] `debug_current_state_label`: "State: idle_action_done"

**Queue Management:**
- [x] Queue cleared after scan complete (TODO: implementatie)

**Header Controls:**
- [x] ABORT button: disabled (no process running)
- [x] MENU button: enabled
- [x] EXIT button: enabled

**Transitions:**
- [x] → PROCESSING: user clicks "START PROCESSING"
- [x] → IDLE: **wanneer `ui_update_finished = True`**
  - [x] **Flag Check:** Wacht op `yapmo_globals.ui_update_finished = True`
  - [x] **Flag Clearing:** Clear `action_finished_flag = False` en `ui_update_finished = False`
  - [x] **State Transition:** → IDLE
- [x] → EXIT_PAGE: user navigates away

## State: PROCESSING
**UI Elements:**
- [x] `scan_select_directory`: `YAPMOTheme.create_button("SELECT DIRECTORY", self._select_directory, "secondary").disable()`
- [x] `scan_search_directory_input`: disabled, current directory path
- [x] `scan_start_button`: `YAPMOTheme.create_button("START Scanning", self._start_scanning, "primary").disable()`
- [x] `scan_spinner`: disabled, hidden
- [x] `scan_state_label`: "processing active"
- [x] `scan_total_files_label`: final scan results (KNOWN DATA)
- [x] `scan_media_files_label`: final scan results (KNOWN DATA)
- [x] `scan_sidecars_label`: final scan results (KNOWN DATA)
- [x] `scan_total_directories_label`: final scan results (KNOWN DATA)
- [x] `scan_details_button`: `YAPMOTheme.create_button("DETAILS", self._show_details, "secondary").disable()`
- [x] `processing_start_button`: `YAPMOTheme.create_button("PROCESSING", self._start_processing, "primary").disable()`
- [x] `processing_progressbar`: visible, updates from processing progress (ACTIVE)
- [x] `processing_progress_label`: live updates from processing progress (MOMENTOPNAME)
- [x] `processing_files_processed_label`: live updates from processing progress (MOMENTOPNAME)
- [x] `processing_directories_processed_label`: live updates from processing progress (MOMENTOPNAME)
- [x] `processing_files_sec_label`: live updates from processing progress (MOMENTOPNAME)
- [x] `processing_directories_sec_label`: live updates from processing progress (MOMENTOPNAME)
- [x] `processing_time_to_finish_label`: live updates from processing progress (MOMENTOPNAME)
- [x] `debug_current_state_label`: "State: processing"

**Header Controls:**
- [x] ABORT button: enabled (processing running)
- [x] MENU button: enabled (process running)
- [x] EXIT button: enabled (process running)

**Transitions:**
- [x] → IDLE_ACTION_DONE: processing completed successfully
- [x] → ABORTED: ABORT dialog → Yes (processing cancelled)
- [x] → PROCESSING: ABORT dialog → No (continue processing)


## State: ABORTED
**UI Elements:**
- [x] All elements: disabled, aborting state
- [x] `scan_state_label`: "Aborting..."
- [x] All progress indicators: hidden
- [x] All counters: behoudt waarden van vorige scan (niet reset naar "0")
- [x] All buttons: disabled
- [x] `debug_current_state_label`: "State: aborted"

**Header Controls:**
- [x] ABORT button: disabled (abort in progress)
- [x] MENU button: disabled (abort in progress)
- [x] EXIT button: disabled (abort in progress)

**Transitions:**
- [x] → IDLE: abort cleanup completed (via flag coordination)


## State: EXIT_PAGE
**UI Elements:**
- All elements: disabled, cleanup state
- [ ] `scan_state_label`: "Saving state..."
- [ ] All progress indicators: hidden
- [ ] All counters: "0"
- [ ] `debug_current_state_label`: "State: exit_page"

**Header Controls:**
- [ ] ABORT button: disabled (exit in progress)
- [ ] MENU button: disabled (exit in progress)
- [ ] EXIT button: disabled (exit in progress)

**Transitions:**
- [ ] → (page closed): cleanup completed

## Flag-Based State Coordination

### **Waarom IDLE_ACTION_DONE State?**
De IDLE_ACTION_DONE state is essentieel voor:
- **Flag Coordination:** Wachten op `ui_update_finished = True`
- **Safe Transition:** Voorbereiden voor veilige transitie naar IDLE
- **Flag Clearing:** Clear beide flags bij transition naar IDLE
- **UI Update Stop:** IDLE state kan veilig ui_update stoppen zonder data verlies

### **SCANNING → IDLE_ACTION_DONE Transitie:**
1. **Scan Complete:** Scanning proces is afgelopen
2. **Flag Setting:** Zet `yapmo_globals.action_finished_flag = True`
3. **State Transition:** → IDLE_ACTION_DONE
4. **Purpose:** IDLE_ACTION_DONE wacht op UI update completion

### **IDLE_ACTION_DONE → IDLE Transitie:**
1. **Flag Check:** Wacht op `yapmo_globals.ui_update_finished = True`
2. **Flag Clearing:** Clear `action_finished_flag = False` en `ui_update_finished = False`
3. **State Transition:** → IDLE
4. **Safe Transition:** IDLE state kan veilig ui_update stoppen omdat flags gecleared zijn

### **UI Update Logic:**
- **Wanneer `action_finished_flag = True` EN state = `IDLE_ACTION_DONE`:**
  - Check of log queue leeg is
  - Als log queue leeg: Zet `yapmo_globals.ui_update_finished = True`
  - UI update is klaar met bijwerken
  - Transition naar `IDLE` state

## Proces Definitie

### **SCANNING is gereed wanneer:**
- [ ] **Alle directories** in de geselecteerde directory zijn gescand
- [ ] **Alle bestanden** zijn geïnventariseerd en gecategoriseerd
- [ ] **Scan resultaten** zijn opgeslagen (totaal files, media files, sidecars, directories)
- [ ] **Errors zijn afgehandeld** (gelogd, gebruiker geïnformeerd, of kritieke errors)
- [ ] **Scan data** is beschikbaar voor processing (ook met errors)

### **PROCESSING is gereed wanneer:**
- [ ] **Alle bestanden** uit de scan zijn verwerkt (succesvol of met error)
- [ ] **Database entries** zijn aangemaakt voor alle bestanden (succesvol of met error)
- [ ] **Metadata** is geëxtraheerd en opgeslagen (succesvol of met error)
- [ ] **Errors zijn afgehandeld** (gelogd, gebruiker geïnformeerd, of kritieke errors)
- [ ] **Processing resultaten** zijn opgeslagen (files/sec, directories/sec, etc.)

### **Error Handling:**
- [ ] **Non-kritieke errors** - Proces gaat door, errors worden gelogd
- [ ] **Kritieke errors** - Proces stopt, gebruiker wordt geïnformeerd
- [ ] **Error dialog** - Toont error details en opties (retry, abort, continue)
- [ ] **Error state** - Mogelijk nieuwe state voor error recovery

## ABORT Dialog Flow
**Alleen tijdens processen (SCANNING, FILE_PROCESSING):**
- [ ] ABORT button enabled in header
- [ ] ABORT → ABORT dialog appears
- [ ] **Dialog "No"** → Return to current state (process continues)
- [ ] **Dialog "Yes"** → ABORTED state (process cancelled)
- [x] ABORTED → IDLE_ACTION_DONE: cleanup and reset UI elements
- [ ] Clear all progress indicators
- [ ] Reset all counters to 0
- [ ] Show which state was aborted in scan_state_label
- [ ] Re-enable scan controls after cleanup

---

## **SAMENVATTING V2.2 REFACTORING:**

### **Wat is veranderd:**
1. **Unified Action State:** `IDLE_ACTION_DONE` vervangt `IDLE_SCAN_DONE`, `IDLE_PROCESSING_DONE`, en `IDLE_AFTER_ABORT`
2. **Unified Flag:** `action_finished_flag` vervangt de oude specifieke flags (`scanning_ready` en `processing_finished`)
3. **Vereenvoudigde Transitions:** Alle acties (scan/process/abort) gebruiken dezelfde completion flow
4. **Consistent Flag Management:** Eén plek voor flag clearing en state transitions

### **Voordelen:**
- **Minder complexiteit** - 3 states → 1 state
- **Minder duplicatie** - unified flag management
- **Eenvoudiger onderhoud** - consistent gedrag voor alle acties
- **Betere debugging** - uniforme flow voor alle scenarios

### **Implementatie Status:**
- ✅ **Code refactoring voltooid**
- ✅ **Alle states werken correct**
- ✅ **Flag management unified**
- ✅ **Details functionaliteit geïmplementeerd**
- ✅ **Documentatie bijgewerkt**
