# Live Test Plan: UI State Machine Validatie

## **Overzicht**
Dit plan beschrijft de stappen om de state machine implementatie live te testen in de browser om te verifiëren dat alles foutloos werkt.

## **Test Omgeving Setup**

### **1. Applicatie Starten**
```bash
cd /workspaces/app
python main.py
```
- Open browser naar `http://localhost:8080`
- Navigeer naar "Fill Database New" pagina
- Verifieer dat de pagina correct laadt

### **2. Initial State Validatie**
**Verwachte State: IDLE**
- [ ] **Buttons**: 
  - Start Scanning: ENABLED (primary)
  - Start Processing: ENABLED (primary) 
  - Abort: DISABLED (warning)
  - Clear Log: ENABLED (secondary)
  - Menu: ENABLED (primary)
  - Exit: ENABLED (negative)
- [ ] **UI Elements**: Alleen logging elementen mogen zichtbaar zijn
- [ ] **Status**: Geen actieve processen

## **Test Scenario 1: Scanning Flow**

### **Stap 1.1: Start Scanning**
1. Klik op "START SCANNING" button
2. **Verwachte State: SCANNING**
3. **Verwachte Changes**:
   - [ ] Start Scanning button: DISABLED (negative) met tekst "SCANNING"
   - [ ] Abort button: ENABLED (warning)
   - [ ] Andere buttons: DISABLED
   - [ ] Scan status label: "scanning - DO NOT GO BACK IN THE BROWSER"
   - [ ] Scan progress bar: Actief
   - [ ] Scan count labels: Worden geüpdatet

### **Stap 1.2: Scanning Progress**
1. Wacht op scanning progress updates
2. **Verwachte Behavior**:
   - [ ] Scan progress bar vult zich
   - [ ] File counts worden geüpdatet
   - [ ] Log messages verschijnen
   - [ ] File processing elementen blijven ongewijzigd

### **Stap 1.3: Scanning Completion**
1. Wacht tot scanning voltooid is
2. **Verwachte State: IDLE_LAG**
3. **Verwachte Changes**:
   - [ ] Scan status label: "completed"
   - [ ] Scan progress bar: 100%
   - [ ] Final counts getoond
   - [ ] Abort button: Nog steeds ENABLED (queues kunnen nog verwerken)

### **Stap 1.4: Auto-transition naar IDLE**
1. Wacht tot alle queues leeg zijn
2. **Verwachte State: IDLE**
3. **Verwachte Changes**:
   - [ ] Abort button: DISABLED
   - [ ] Start buttons: ENABLED
   - [ ] Menu/Exit buttons: ENABLED

## **Test Scenario 2: File Processing Flow**

### **Stap 2.1: Start File Processing**
1. Klik op "START PROCESSING" button
2. **Verwachte State: FILE_PROCESSING**
3. **Verwachte Changes**:
   - [ ] Start Processing button: DISABLED (negative) met tekst "PROCESSING"
   - [ ] Abort button: ENABLED (warning)
   - [ ] Andere buttons: DISABLED
   - [ ] Processing progress bar: Actief
   - [ ] Processing count labels: Worden geüpdatet

### **Stap 2.2: File Processing Progress**
1. Wacht op processing progress updates
2. **Verwachte Behavior**:
   - [ ] Processing progress bar vult zich
   - [ ] Processing counts worden geüpdatet
   - [ ] Log messages verschijnen
   - [ ] Scan elementen blijven ongewijzigd

### **Stap 2.3: File Processing Completion**
1. Wacht tot processing voltooid is
2. **Verwachte State: IDLE_LAG**
3. **Verwachte Changes**:
   - [ ] Processing progress bar: 100%
   - [ ] Final processing counts getoond
   - [ ] Abort button: Nog steeds ENABLED

## **Test Scenario 3: Abort Functionaliteit**

### **Stap 3.1: Abort tijdens Scanning**
1. Start scanning
2. Klik op "ABORT" button tijdens scanning
3. **Verwachte State: IDLE**
4. **Verwachte Changes**:
   - [ ] Scan status: "aborted"
   - [ ] Alle buttons terug naar IDLE state
   - [ ] Scan counts gereset naar 0
   - [ ] Abort flags ingesteld

### **Stap 3.2: Abort tijdens File Processing**
1. Start file processing
2. Klik op "ABORT" button tijdens processing
3. **Verwachte State: IDLE**
4. **Verwachte Changes**:
   - [ ] Processing gestopt
   - [ ] Alle buttons terug naar IDLE state
   - [ ] Processing counts gereset

## **Test Scenario 4: UI Element Protection**

### **Stap 4.1: Scan Element Protection**
1. Start file processing
2. **Verwachte Behavior**:
   - [ ] Scan progress updates worden genegeerd
   - [ ] Scan status label blijft ongewijzigd
   - [ ] Scan count labels blijven ongewijzigd
   - [ ] Log messages: "Scan progress update ignored - wrong state"

### **Stap 4.2: Processing Element Protection**
1. Start scanning
2. **Verwachte Behavior**:
   - [ ] File processing updates worden genegeerd
   - [ ] Processing progress bar blijft ongewijzigd
   - [ ] Processing count labels blijven ongewijzigd
   - [ ] Log messages: "File processing update ignored - wrong state"

## **Test Scenario 5: Edge Cases**

### **Stap 5.1: Rapid State Changes**
1. Start scanning
2. Onmiddellijk start file processing (zou moeten falen)
3. **Verwachte Behavior**:
   - [ ] File processing start wordt genegeerd
   - [ ] Scanning blijft actief
   - [ ] Log messages over conflicterende states

### **Stap 5.2: Multiple Abort Clicks**
1. Start scanning
2. Klik meerdere keren op ABORT
3. **Verwachte Behavior**:
   - [ ] Alleen eerste abort wordt verwerkt
   - [ ] Geen errors of crashes
   - [ ] State blijft IDLE

### **Stap 5.3: Browser Refresh tijdens Actieve State**
1. Start scanning
2. Refresh browser
3. **Verwachte Behavior**:
   - [ ] Applicatie herstart in IDLE state
   - [ ] Geen actieve processen
   - [ ] UI correct geïnitialiseerd

## **Test Scenario 6: Performance en Responsiveness**

### **Stap 6.1: UI Responsiveness**
1. Start scanning
2. **Verwachte Behavior**:
   - [ ] UI blijft responsive tijdens scanning
   - [ ] Buttons reageren onmiddellijk
   - [ ] Log scroll area werkt correct
   - [ ] Geen UI freezing

### **Stap 6.2: Memory Usage**
1. Start en stop meerdere scans
2. **Verwachte Behavior**:
   - [ ] Geen memory leaks
   - [ ] UI update timers correct gestopt
   - [ ] Queues correct geleegd

## **Success Criteria**

### **✅ Alle Tests Slagen Als:**
- [ ] Alle state transitions werken correct
- [ ] UI elementen worden correct beschermd per state
- [ ] Abort functionaliteit werkt vanuit alle states
- [ ] Geen crashes of errors tijdens testing
- [ ] UI blijft responsive tijdens alle operaties
- [ ] Log messages zijn duidelijk en informatief
- [ ] Auto-transitions werken correct (IDLE_LAG → IDLE)

### **❌ Test Faalt Als:**
- [ ] State transitions niet werken
- [ ] UI elementen worden geüpdatet in verkeerde state
- [ ] Abort functionaliteit faalt
- [ ] UI wordt unresponsive
- [ ] Errors of crashes optreden
- [ ] Log messages zijn verwarrend of ontbreken

## **Test Rapport Template**

```
=== LIVE TEST RAPPORT ===
Datum: [DATUM]
Tester: [NAAM]
Applicatie Versie: [VERSIE]

TEST RESULTATEN:
□ Test Scenario 1: Scanning Flow - [PASS/FAIL]
□ Test Scenario 2: File Processing Flow - [PASS/FAIL]
□ Test Scenario 3: Abort Functionaliteit - [PASS/FAIL]
□ Test Scenario 4: UI Element Protection - [PASS/FAIL]
□ Test Scenario 5: Edge Cases - [PASS/FAIL]
□ Test Scenario 6: Performance - [PASS/FAIL]

GENERAL RESULT: [PASS/FAIL]

OPGEMERKTE PROBLEMEN:
- [Probleem 1]
- [Probleem 2]

AANBEVELINGEN:
- [Aanbeveling 1]
- [Aanbeveling 2]
```

## **Volgende Stappen na Testing**

1. **Als alle tests slagen**: State machine implementatie is succesvol
2. **Als tests falen**: Problemen identificeren en oplossen
3. **Documentatie updaten**: Op basis van test resultaten
4. **Production readiness**: Evalueren of implementatie klaar is voor productie

---

**Belangrijk**: Test dit plan systematisch en documenteer alle bevindingen. Alleen door live testing kunnen we bevestigen dat de state machine implementatie daadwerkelijk foutloos werkt.
