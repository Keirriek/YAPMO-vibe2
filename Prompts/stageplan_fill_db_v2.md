# Stageplan Fill Database V2 - State Machine Implementatie

## Overzicht
Implementatie van state machine voor fill_db_page_v2 met focus op INITIALISATION en IDLE states. 
Gebruik van bestaande bouwblokken (logging_service_v2, core modules) zonder test/debug code.

## Fase 1: INITIALISATION State

### 1.1 Specs Updaten
- [ ] **State Machine Document**: ✅ Beschikbaar in yapmo_statemachine.md
- [ ] **UI Elements**: Alle elementen disabled, loading state
- [ ] **Transitions**: INITIALISATION → IDLE (page loaded), INITIALISATION → EXIT_PAGE (init failed)
- [ ] **Background Process**: Initialization timer voor config loading en dependency checks

### 1.2 Spec Checken
- [ ] **Config Loading**: Controleer config.json loading mechanisme
- [ ] **Dependency Check**: Verificeer bestaande bestanden en modules
- [ ] **Error Handling**: Definieer kritieke vs non-kritieke errors
- [ ] **UI Update Interval**: Gebruik ui_update_interval uit config.json

### 1.3 Bouwen
**Core Components:**
- [ ] `_set_state()` methode met state validation
- [ ] `_configure_ui_for_state()` voor INITIALISATION state
- [ ] `_process_initialization()` background process
- [ ] `_update_ui_from_process()` centralized update routine
- [ ] State transition manager met conditie checks
- [ ] `debug_current_state_label` UI element in debug sectie

**UI Configuration voor INITIALISATION:**
- [ ] Alle buttons: disabled
- [ ] scan_state_label: "Initializing..."
- [ ] Alle counters: "0"
- [ ] Loading spinner: visible, active
- [ ] Progress indicators: hidden
- [ ] debug_current_state_label: "State: initialisation"

### 1.4 Deel Test
- [ ] **State Transition**: INITIALISATION → IDLE
- [ ] **UI Elements**: Correct disabled/configured
- [ ] **Config Loading**: Succesvol laden van config.json
- [ ] **Error Handling**: Kritieke errors → EXIT_PAGE
- [ ] **Background Process**: Initialization timer werkt
- [ ] **Debug State Label**: Toont correct "State: initialisation"

### 1.5 Totale Test
- [ ] **Page Load**: Complete page load flow
- [ ] **Error Scenarios**: Config errors, missing dependencies
- [ ] **State Persistence**: State blijft correct na page refresh
- [ ] **Performance**: Geen memory leaks, snelle transitions

## Fase 2: IDLE State

### 2.1 Specs Updaten
- [ ] **UI Elements**: Scan controls enabled, processing controls disabled
- [ ] **Transitions**: IDLE → SCANNING (directory selected + valid path), IDLE → EXIT_PAGE (navigation)
- [ ] **Background Process**: Geen actieve processen, alleen UI updates

### 2.2 Spec Checken
- [ ] **Directory Selection**: Controleer bestaande directory selection mechanisme
- [ ] **Path Validation**: Verificeer path validation logic
- [ ] **Button States**: Correct enabled/disabled states
- [ ] **Queue Management**: Log en result queue processing

### 2.3 Bouwen
**Core Components:**
- [ ] `_configure_ui_for_state()` voor IDLE state
- [ ] `_select_directory()` directory selection handler
- [ ] `_validate_directory_path()` path validation
- [ ] Queue processing in `_update_ui_from_process()`
- [ ] `debug_current_state_label` updates bij state changes

**UI Configuration voor IDLE:**
- [ ] scan_select_directory: enabled
- [ ] scan_search_directory_input: enabled, value from config
- [ ] scan_start_button: "START Scanning", enabled
- [ ] scan_spinner: disabled, hidden
- [ ] scan_state_label: "not active"
- [ ] processing_start_button: disabled
- [ ] Alle counters: "0" (no data available)
- [ ] debug_current_state_label: "State: idle"

### 2.4 Deel Test
- [ ] **UI Elements**: Correct enabled/disabled states
- [ ] **Directory Selection**: File dialog werkt
- [ ] **Path Validation**: Valid/invalid paths correct afgehandeld
- [ ] **Button Logic**: START Scanning button enabled/disabled correct
- [ ] **Queue Processing**: Log en result queue correct verwerkt
- [ ] **Debug State Label**: Toont correct "State: idle"

### 2.5 Totale Test
- [ ] **Complete Flow**: INITIALISATION → IDLE
- [ ] **User Interaction**: Directory selection en validation
- [ ] **State Persistence**: State correct na page refresh
- [ ] **Error Handling**: Invalid paths, missing directories
- [ ] **Performance**: Snelle UI updates, geen blocking

## Fase 3: Queue Management & Background Processes

### 3.1 AFFECTS
- **INITIALISATION**: Queue initialization toevoegen
- **IDLE**: Queue processing toevoegen

### 3.2 Specs Updaten
- [ ] **Result Queue**: process_result messages met last_message optie
- [ ] **Log Queue**: log messages met last_message optie
- [ ] **Processing Order**: Eerst result queue, dan log queue
- [ ] **UI Updates**: ui_update_interval uit config.json
- [ ] **INITIALISATION**: Queue initialization mechanisme
- [ ] **IDLE**: Queue processing mechanisme

### 3.3 Spec Checken
- [ ] **Message Formats**: Controleer bestaande message formats in fill_db_new
- [ ] **Queue Access**: Verificeer queue access via yapmo_globals
- [ ] **Timer Management**: Controleer timer lifecycle management
- [ ] **INITIALISATION**: Controleer queue init mechanisme
- [ ] **IDLE**: Controleer queue processing mechanisme

### 3.4 Bouwen
**Core Components:**
- [ ] `_process_result_queue()` met last_message detection
- [ ] `_process_log_queue()` met last_message detection
- [ ] `_update_ui_elements()` uit global variables
- [ ] `_check_state_transitions()` als laatste stap
- [ ] Timer management voor background processes

### 3.5 Deel Test
- [ ] **Queue Processing**: Correct verwerken van beide queues
- [ ] **Message Routing**: Log messages naar log queue, results naar handlers
- [ ] **Last Message**: Correct detection van process completion
- [ ] **UI Updates**: Real-time updates van counters en labels
- [ ] **INITIALISATION**: Test queue initialization
- [ ] **IDLE**: Test queue processing

### 3.6 Totale Test
- [ ] **Complete System**: Alle queues en UI updates geïntegreerd
- [ ] **Performance**: Geen queue overflow, snelle processing
- [ ] **Error Handling**: Queue errors correct afgehandeld
- [ ] **State Integration**: Queue processing geïntegreerd met state machine

## Fase 4: State Machine Integration

### 4.1 AFFECTS
- **INITIALISATION**: State transition logic toevoegen
- **IDLE**: State transition logic toevoegen
- **Queue Management**: State transition integration

### 4.2 Specs Updaten
- [ ] **Transition Matrix**: INITIALISATION ↔ IDLE transitions
- [ ] **Condition Checks**: Page loaded, config loaded, directory valid
- [ ] **Error States**: Kritieke errors → EXIT_PAGE
- [ ] **Background Process Lifecycle**: Start/stop op basis van state
- [ ] **INITIALISATION**: State transition conditions
- [ ] **IDLE**: State transition conditions
- [ ] **Queue Management**: State transition integration

### 4.3 Spec Checken
- [ ] **Transition Logic**: Controleer bestaande transition logic in fill_db_new
- [ ] **Condition Validation**: Verificeer condition checking mechanisme
- [ ] **Error Handling**: Controleer error handling patterns
- [ ] **INITIALISATION**: Controleer state transition logic
- [ ] **IDLE**: Controleer state transition logic
- [ ] **Queue Management**: Controleer state transition integration

### 4.4 Bouwen
**Core Components:**
- [ ] `StateTransitionManager` class met transition matrix
- [ ] `StateConditions` class met condition checks
- [ ] `BackgroundProcessManager` class voor process lifecycle
- [ ] Geïntegreerde state machine in `_update_ui_from_process()`

### 4.5 Deel Test
- [ ] **State Transitions**: Correct transitions tussen states
- [ ] **Condition Validation**: Correct checking van transition conditions
- [ ] **Process Management**: Correct start/stop van background processes
- [ ] **Error Handling**: Correct error state handling
- [ ] **INITIALISATION**: Test state transition logic
- [ ] **IDLE**: Test state transition logic
- [ ] **Queue Management**: Test state transition integration

### 4.6 Totale Test
- [ ] **Complete State Machine**: Alle states en transitions werken
- [ ] **User Workflows**: Complete user workflows van page load tot interaction
- [ ] **Error Scenarios**: Alle error scenarios correct afgehandeld
- [ ] **Performance**: Snelle state transitions, geen memory leaks

## Technische Details

### Queue Management
- **Result Queue**: `yapmo_globals.result_queue` - process_result messages
- **Log Queue**: `logging_service.get_ui_messages()` - log messages
- **Processing Order**: Result queue eerst, dan log queue
- **Last Message**: Special message type om process completion aan te geven

### UI Update Routine
```python
def _update_ui_from_process(self, process_name: str, process_data: dict) -> None:
    # 1. Process result queue (with last_message detection)
    self._process_result_queue()
    
    # 2. Process log queue (with last_message detection)  
    self._process_log_queue()
    
    # 3. Update UI elements from global variables
    self._update_ui_elements()
    
    # 4. Update progress indicators
    self._update_progress_indicators()
    
    # 5. Check state transitions (as last step)
    self._check_state_transitions()
```

### State Machine Architecture
- **Centralized State Management**: Eén `_set_state()` methode
- **UI Configuration**: `_configure_ui_for_state()` per state
- **Background Processes**: `BackgroundProcessManager` voor lifecycle
- **Transition Validation**: `StateTransitionManager` voor conditie checks

### Dependencies
- **logging_service_v2**: Voor log message handling
- **yapmo_globals**: Voor queue access en global variables
- **config.json**: Voor ui_update_interval en andere settings
- **NiceGUI**: Voor UI element management en timers

## Success Criteria
- [ ] ✅ INITIALISATION state werkt correct met loading en error handling
- [ ] ✅ IDLE state werkt correct met directory selection en validation
- [ ] ✅ Queue management werkt correct met last_message detection
- [ ] ✅ State machine transitions werken correct tussen INITIALISATION en IDLE
- [ ] ✅ UI updates zijn real-time en responsive
- [ ] ✅ Error handling is robust en user-friendly
- [ ] ✅ Performance is optimaal zonder memory leaks
- [ ] ✅ Code is clean zonder test/debug code

## Progress Tracking
**Fase 1 (INITIALISATION)**: 0/20 taken voltooid
**Fase 2 (IDLE)**: 0/20 taken voltooid  
**Fase 3 (Queue Management)**: 0/20 taken voltooid
**Fase 4 (State Machine)**: 0/16 taken voltooid
**Totaal**: 0/76 taken voltooid (0%)