# YAPMO State Machine - Fill Database V2

## State Machine Principe
**Elke state configureert ALLE UI elementen in één keer:**
- **Enabled/Disabled status** - Welke elementen actief zijn
- **Kleuren en captions** - Hoe elementen eruitzien
- **Zichtbaarheid** - Welke elementen zichtbaar zijn
- **Updates** - Welke elementen live updates krijgen
- **Data** - Welke data wordt getoond

**Voordelen:**
- **Centralized control** - Eén plek voor alle UI configuratie
- **Eenvoudige code** - [ ] `self._set_state(ApplicationState.SCANNING)`
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

## States:
- [ ] **INITIALISATION**: Page loading, setting up UI elements
- [ ] **IDLE**: Ready to scan, all controls available
- [ ] **SCANNING**: Currently scanning directory
- [ ] **IDLE_SCAN_DONE**: Scan complete, ready to process
- [ ] **FILE_PROCESSING**: Currently processing files
- [ ] **IDLE_PROCESSING_DONE**: Processing complete, ready for new scan
- [ ] **ABORTED**: Operation cancelled, returning to IDLE
- [ ] **IDLE_AFTER_ABORT**: After abort, showing which state was aborted
- [ ] **EXIT_PAGE**: Page cleanup, saving state

## RESET Functionaliteit:
- [ ] **scan_start_button** - Wordt "RESET" in IDLE_SCAN_DONE en IDLE_PROCESSING_DONE
- [ ] **RESET → IDLE** - Alle data wordt gewist, UI reset naar IDLE state
- [ ] **scan_start_button** - Wordt "START Scanning" in IDLE state

## State: INITIALISATION
**UI Elements:**
- [ ] All elements: disabled, loading state
- [ ] `scan_state_label`: "Initializing..."
- [ ] All progress indicators: hidden
- [ ] All counters: "0"
- [ ] Loading spinner: visible, active
- [ ] `debug_current_state_label`: "State: initialisation"

**Wanneer kom je in INITIALISATION:**
- [ ] **Page startup** - Eerste keer dat de pagina opent
- [ ] **Page refresh** - Gebruiker drukt F5 of refresh
- [ ] **Navigation terug** - Van andere pagina terug naar fill_db_v2
- [ ] **Error recovery** - Na kritieke fout, pagina herstarten
- [ ] **Session restore** - Browser herstelt sessie

**Wat gebeurt er in INITIALISATION:**
- [ ] **UI elementen aanmaken** - Alle UI elementen initialiseren
- [ ] **Config laden** - Configuratie uit config.json laden
- [ ] **State herstellen** - Eventuele opgeslagen state herstellen
- [ ] **Error checking** - Controleren op configuratie errors
- [ ] **Dependencies check** - Controleren of alle benodigde bestanden bestaan

**Transitions:**
- [ ] → IDLE: page loaded successfully
- [ ] → EXIT_PAGE: initialization failed (kritieke fout)
- [ ] ← INITIALISATION: page refresh (F5)
- [ ] ← INITIALISATION: browser back/forward navigation
- [ ] ← INITIALISATION: session restore

## State: IDLE
**UI Elements:**
- [ ] `scan_select_directory`: `YAPMOTheme.create_button("SELECT DIRECTORY", self._select_directory, "secondary").enable()`
- [ ] `scan_search_directory_input`: enabled, value from config
- [ ] `scan_start_button`: `YAPMOTheme.create_button("START Scanning", self._start_scanning, "primary").enable()`
- [ ] `scan_spinner`: disabled, hidden
- [ ] `scan_state_label`: "not active"
- [ ] `scan_total_files_label`: "0" (no scan data available)
- [ ] `scan_media_files_label`: "0" (no scan data available)
- [ ] `scan_sidecars_label`: "0" (no scan data available)
- [ ] `scan_total_directories_label`: "0" (no scan data available)
- [ ] `scan_details_button`: `YAPMOTheme.create_button("DETAILS", self._show_details, "secondary").disable()`
- [ ] `processing_start_button`: `YAPMOTheme.create_button("START PROCESSING", self._start_processing, "primary").disable()`
- [ ] `processing_progressbar`: value=0, hidden
- [ ] `processing_progress_label`: "Processing: 0%"
- [ ] `processing_files_processed_label`: "0" (no processing data available)
- [ ] `processing_directories_processed_label`: "0" (no processing data available)
- [ ] `processing_files_sec_label`: "0" (no processing data available)
- [ ] `processing_directories_sec_label`: "0" (no processing data available)
- [ ] `processing_time_to_finish_label`: "0" (no processing data available)
- [ ] `debug_current_state_label`: "State: idle"

**Header Controls:**
- [ ] ABORT button: disabled (no process running)
- [ ] MENU button: enabled
- [ ] EXIT button: enabled

**Transitions:**
- [ ] → SCANNING: user clicks "START Scanning" + directory path is valid
- [ ] → EXIT_PAGE: user navigates away
- [ ] ← INITIALISATION: page refresh (F5)
- [ ] ← INITIALISATION: browser back/forward navigation

## State: SCANNING
**UI Elements:**
- [ ] `scan_select_directory`: `YAPMOTheme.create_button("SELECT DIRECTORY", self._select_directory, "secondary").disable()`
- [ ] `scan_search_directory_input`: disabled, current directory path
- [ ] `scan_start_button`: `YAPMOTheme.create_button("START Scanning", self._start_scanning, "primary").disable()`
- [ ] `scan_spinner`: enabled, visible, red (ACTIVE)
- [ ] `scan_state_label`: "scanning..."
- [ ] `scan_total_files_label`: live updates from scan progress (MOMENTOPNAME)
- [ ] `scan_media_files_label`: live updates from scan progress (MOMENTOPNAME)
- [ ] `scan_sidecars_label`: live updates from scan progress (MOMENTOPNAME)
- [ ] `scan_total_directories_label`: live updates from scan progress (MOMENTOPNAME)
- [ ] `scan_details_button`: `YAPMOTheme.create_button("DETAILS", self._show_details, "secondary").disable()`
- [ ] `processing_start_button`: `YAPMOTheme.create_button("START PROCESSING", self._start_processing, "primary").disable()`
- [ ] `processing_progressbar`: value=0, hidden
- [ ] `processing_progress_label`: "Processing: 0%"
- [ ] `processing_files_processed_label`: "0" (no processing data available)
- [ ] `processing_directories_processed_label`: "0" (no processing data available)
- [ ] `processing_files_sec_label`: "0" (no processing data available)
- [ ] `processing_directories_sec_label`: "0" (no processing data available)
- [ ] `processing_time_to_finish_label`: "0" (no processing data available)
- [ ] `debug_current_state_label`: "State: scanning"

**Header Controls:**
- [ ] ABORT button: enabled (scan process running)
- [ ] MENU button: disabled (process running)
- [ ] EXIT button: disabled (process running)

**Transitions:**
- [ ] → IDLE_SCAN_DONE: scan completed successfully
- [ ] → ABORTED: ABORT dialog → Yes (scan cancelled)
- [ ] → SCANNING: ABORT dialog → No (continue scanning)

## State: IDLE_SCAN_DONE
**UI Elements:**
- [ ] `scan_select_directory`: `YAPMOTheme.create_button("SELECT DIRECTORY", self._select_directory, "secondary").enable()`
- [ ] `scan_search_directory_input`: enabled, current directory path
- [ ] `scan_start_button`: `YAPMOTheme.create_button("RESET", self._reset_all, "negative").enable()`
- [ ] `scan_spinner`: disabled, hidden
- [ ] `scan_state_label`: "scan complete"
- [ ] `scan_total_files_label`: final scan results (KNOWN DATA)
- [ ] `scan_media_files_label`: final scan results (KNOWN DATA)
- [ ] `scan_sidecars_label`: final scan results (KNOWN DATA)
- [ ] `scan_total_directories_label`: final scan results (KNOWN DATA)
- [ ] `scan_details_button`: `YAPMOTheme.create_button("DETAILS", self._show_details, "secondary").enable()`
- [ ] `processing_start_button`: `YAPMOTheme.create_button("START PROCESSING", self._start_processing, "primary").enable()`
- [ ] `processing_progressbar`: value=0, hidden
- [ ] `processing_progress_label`: "Processing: 0%"
- [ ] `processing_files_processed_label`: "0" (no processing data available)
- [ ] `processing_directories_processed_label`: "0" (no processing data available)
- [ ] `processing_files_sec_label`: "0" (no processing data available)
- [ ] `processing_directories_sec_label`: "0" (no processing data available)
- [ ] `processing_time_to_finish_label`: "0" (no processing data available)
- [ ] `debug_current_state_label`: "State: idle_scan_done"

**Header Controls:**
- [ ] ABORT button: disabled (no process running)
- [ ] MENU button: enabled
- [ ] EXIT button: enabled

**Transitions:**
- [ ] → FILE_PROCESSING: user clicks "START PROCESSING"
- [ ] → IDLE: user clicks "RESET" (clear all data)
- [ ] → EXIT_PAGE: user navigates away

## State: FILE_PROCESSING
**UI Elements:**
- [ ] `scan_select_directory`: `YAPMOTheme.create_button("SELECT DIRECTORY", self._select_directory, "secondary").disable()`
- [ ] `scan_search_directory_input`: disabled, current directory path
- [ ] `scan_start_button`: `YAPMOTheme.create_button("START Scanning", self._start_scanning, "primary").disable()`
- [ ] `scan_spinner`: disabled, hidden
- [ ] `scan_state_label`: "scan complete"
- [ ] `scan_total_files_label`: final scan results (KNOWN DATA)
- [ ] `scan_media_files_label`: final scan results (KNOWN DATA)
- [ ] `scan_sidecars_label`: final scan results (KNOWN DATA)
- [ ] `scan_total_directories_label`: final scan results (KNOWN DATA)
- [ ] `scan_details_button`: `YAPMOTheme.create_button("DETAILS", self._show_details, "secondary").enable()`
- [ ] `processing_start_button`: `YAPMOTheme.create_button("START PROCESSING", self._start_processing, "primary").disable()`
- [ ] `processing_progressbar`: enabled, visible, updates from processing progress (ACTIVE)
- [ ] `processing_progress_label`: live updates from processing progress (MOMENTOPNAME)
- [ ] `processing_files_processed_label`: live updates from processing progress (MOMENTOPNAME)
- [ ] `processing_directories_processed_label`: live updates from processing progress (MOMENTOPNAME)
- [ ] `processing_files_sec_label`: live updates from processing progress (MOMENTOPNAME)
- [ ] `processing_directories_sec_label`: live updates from processing progress (MOMENTOPNAME)
- [ ] `processing_time_to_finish_label`: live updates from processing progress (MOMENTOPNAME)
- [ ] `debug_current_state_label`: "State: file_processing"

**Header Controls:**
- [ ] ABORT button: enabled (processing running)
- [ ] MENU button: disabled (process running)
- [ ] EXIT button: disabled (process running)

**Transitions:**
- [ ] → IDLE_PROCESSING_DONE: processing completed successfully
- [ ] → ABORTED: ABORT dialog → Yes (processing cancelled)
- [ ] → FILE_PROCESSING: ABORT dialog → No (continue processing)

## State: IDLE_PROCESSING_DONE
**UI Elements:**
- [ ] `scan_select_directory`: `YAPMOTheme.create_button("SELECT DIRECTORY", self._select_directory, "secondary").enable()`
- [ ] `scan_search_directory_input`: enabled, current directory path
- [ ] `scan_start_button`: `YAPMOTheme.create_button("RESET", self._reset_all, "negative").enable()`
- [ ] `scan_spinner`: disabled, hidden
- [ ] `scan_state_label`: "Processing complete"
- [ ] `scan_total_files_label`: final scan results (KNOWN DATA)
- [ ] `scan_media_files_label`: final scan results (KNOWN DATA)
- [ ] `scan_sidecars_label`: final scan results (KNOWN DATA)
- [ ] `scan_total_directories_label`: final scan results (KNOWN DATA)
- [ ] `scan_details_button`: `YAPMOTheme.create_button("DETAILS", self._show_details, "secondary").enable()`
- [ ] `processing_start_button`: `YAPMOTheme.create_button("START PROCESSING", self._start_processing, "primary").enable()`
- [ ] `processing_progressbar`: value=100, visible, green
- [ ] `processing_progress_label`: "Processing: 100% (Complete)"
- [ ] `processing_files_processed_label`: final processing results (KNOWN DATA)
- [ ] `processing_directories_processed_label`: final processing results (KNOWN DATA)
- [ ] `processing_files_sec_label`: final processing results (KNOWN DATA)
- [ ] `processing_directories_sec_label`: final processing results (KNOWN DATA)
- [ ] `processing_time_to_finish_label`: "Complete" (KNOWN DATA)
- [ ] `debug_current_state_label`: "State: idle_processing_done"

**Header Controls:**
- [ ] ABORT button: disabled (no process running)
- [ ] MENU button: enabled
- [ ] EXIT button: enabled

**Transitions:**
- [ ] → FILE_PROCESSING: user clicks "START PROCESSING" (re-process)
- [ ] → IDLE: user clicks "RESET" (clear all data)
- [ ] → EXIT_PAGE: user navigates away

## State: ABORTED
**UI Elements:**
- [ ] All elements: disabled, aborting state
- [ ] `scan_state_label`: "Aborting operation..."
- [ ] All progress indicators: hidden
- [ ] All counters: reset to "0"
- [ ] All buttons: disabled
- [ ] [ ] `debug_current_state_label`: "State: aborted"

**Header Controls:**
- [ ] ABORT button: disabled (abort in progress)
- [ ] MENU button: disabled (abort in progress)
- [ ] EXIT button: disabled (abort in progress)

**Transitions:**
- [ ] → IDLE_AFTER_ABORT: abort cleanup completed

## State: IDLE_AFTER_ABORT
**UI Elements:**
- [ ] `scan_select_directory`: `YAPMOTheme.create_button("SELECT DIRECTORY", self._select_directory, "secondary").enable()`
- [ ] `scan_search_directory_input`: enabled, current directory path
- [ ] `scan_start_button`: `YAPMOTheme.create_button("START Scanning", self._start_scanning, "primary").enable()`
- [ ] `scan_spinner`: disabled, hidden
- [ ] `scan_state_label`: "Operation aborted from [PREVIOUS_STATE]"
- [ ] `scan_total_files_label`: "0" (no scan data available)
- [ ] `scan_media_files_label`: "0" (no scan data available)
- [ ] `scan_sidecars_label`: "0" (no scan data available)
- [ ] `scan_total_directories_label`: "0" (no scan data available)
- [ ] `scan_details_button`: `YAPMOTheme.create_button("DETAILS", self._show_details, "secondary").disable()`
- [ ] `processing_start_button`: `YAPMOTheme.create_button("START PROCESSING", self._start_processing, "primary").disable()`
- [ ] `processing_progressbar`: value=0, hidden
- [ ] `processing_progress_label`: "Processing: 0%"
- [ ] `processing_files_processed_label`: "0" (no processing data available)
- [ ] `processing_directories_processed_label`: "0" (no processing data available)
- [ ] `processing_files_sec_label`: "0" (no processing data available)
- [ ] `processing_directories_sec_label`: "0" (no processing data available)
- [ ] `processing_time_to_finish_label`: "0" (no processing data available)
- [ ] `debug_current_state_label`: "State: idle_after_abort"

**Header Controls:**
- [ ] ABORT button: disabled (no process running)
- [ ] MENU button: enabled
- [ ] EXIT button: enabled

**Transitions:**
- [ ] → SCANNING: user clicks "START Scanning" (new scan)
- [ ] → EXIT_PAGE: user navigates away
- [ ] → INITIALISATION: page refresh or navigation back

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
- [ ] ABORTED → IDLE_AFTER_ABORT: cleanup and reset UI elements
- [ ] Clear all progress indicators
- [ ] Reset all counters to 0
- [ ] Show which state was aborted in scan_state_label
- [ ] Re-enable scan controls after cleanup
