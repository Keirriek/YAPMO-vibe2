# Mijn AI Prompt algemeen Startbestand

## Handige links

- geef mij aan als je een link niet kunt benaderen.
  @https://github.com/zauberzeug/nicegui.git
  @https://github.com/zauberzeug/nicegui
  @https://github.com/syejing/nicegui-reference-cn
  @https://github.com/CrystalWindSnake/ex4nicegui
  @https://github.com/zauberzeug/nicegui/tree/main/examples
  @https://github.com/CVxTz/nicegui?tab=readme-ov-file
  @https://github.com/zigai/nicegui-extensions/tree/master/nicegui_ext
  @https://github.com/zauberzeug/nicegui/tree/3df8b2b16eb7ac471cc36bf9498a3cd652e95bb9 Deze is zeer belangrijk!!!!
  @https://github.com/zauberzeug/nicegui/tree/3df8b2b16eb7ac471cc36bf9498a3cd652e95bb9/.cursor/rules Deze is zeer belangrijk !!!

## Algemene prompt-aanwijzingen

- Geef altijd codevoorbeelden in Python.
- Gebruik korte, duidelijke uitleg.
- Voeg waar mogelijk een link naar de officiële documentatie toe.
- Leg complexe concepten uit met een eenvoudig voorbeeld.
- Antwoord in het Nederlands tenzij anders gevraagd.

## 🔍 Misverstanden voorkomen - ALTIJD DOEN:

### Voor elke technische command/implementatie:

1. **Documentatie eerst**: Altijd `--help` of officiële docs checken voordat je commands voorstelt
2. **Opties uitleggen**: Leg het verschil uit tussen verschillende flags/opties (bijv. `--with` vs `--only`)
3. **Intentie verifiëren**: Vraag "Bedoel je [A] of [B]?" bij onduidelijke requirements
4. **Test eerst**: Gebruik `--dry-run` of vergelijkbare test-opties waar mogelijk
5. **Valideer resultaat**: Leg uit hoe je het resultaat kunt controleren

### Poetry specifiek:

- `--with GROUP`: Main dependencies + GROUP dependencies (meestal gewenst)
- `--only GROUP`: Alleen GROUP dependencies (zelden gewenst)
- `--without GROUP`: Main dependencies zonder GROUP dependencies
- Bij twijfel: vraag of main dependencies ook gewenst zijn

### Docker/DevContainer specifiek:

- Specificeer waar commands uitgevoerd worden (Dockerfile vs docker-compose vs postCreate)
- Leg voor- en nadelen uit van verschillende implementaties
- Controleer of volume mounts correct zijn voor commands

### Algemeen:

- Bij onduidelijke requirements: **stel specifieke vragen** i.p.v. aannames maken
- Geef altijd **meerdere opties** met uitleg wanneer er verschillende benaderingen zijn
- **Verifieer begrip** voordat je implementeert: "Klopt dit wat je bedoelt?"
- Voer niet meer uit dan ik vraag, Als je goede suggesties hebt, stel die dan eerste voor
- Als ik een aanpassing wil en jij hebt je bedenking daarover met als reden **bijvoorbeeld** - erg gecomliceerde oplossing of aanpak - zeer grote aanpassing in eens - niet heel erg gangbaar voor zo ver jij weet - risico op performance problemen - risico op stabiliteit problemen
  Dan verwacht ik dat je gemotiveerd je bedenkingen aangeeft. En dat je een alternatief voorstelt

## Algemene voorwaarden:

- ik werk met cursor en ik wil alleen extenties gebruiken die in de cursor marketplace beschikbaar zijn.
- ik wil graag werken met docker en docker compose. Alle docker gerelateerde files il ik graag in de folder .devcontainer
- ik wil graag dat de gebruiker in de devcontainer niet root is, maar de gebruiker vscode. Let er speciaal op de binnen de devcontainer de rechten van cursor.exe zostaan dat vscode de juiste rechten heeft.
- ik wil een python applicatie ontwikkelen

## Voor elke stap/aanpassing - Controleer en Valideer:

### Voor uitvoering:

- [ ] Alle algemene voorwaarden gelezen
- [ ] Bestaande configuratie gecontroleerd
- [ ] Stap-specifieke eisen begrepen
- [ ] Eerdere problemen/context meegenomen
- [ ] **Command documentatie gecontroleerd**
- [ ] **Intentie geverifieerd met gebruiker**

### Na uitvoering:

- [ ] Resultaat voldoet aan alle voorwaarden
- [ ] Geen 'name' gebruikt
- [ ] vscode gebruiker correct ingesteld
- [ ] Docker bestanden in .devcontainer folder
- [ ] Cursor-compatibel
- [ ] **Command werkt zoals bedoeld**
- [ ] **Validatie-instructies gegeven**

## Context tracking - Onthoud altijd:

- Eerdere build problemen (zoals oneindig duren)
- Welke configuratie eerder werkte/niet werkte
- Cache status en wanneer zonder cache nodig is
- Eerdere fouten en oplossingen
- Voorkeuren die je hebt uitgesproken

## Communicatie stijl:

- Anticipateer op basis van eerdere context
- Geef direct het beste advies zonder vragen
- Herinner jezelf aan eerdere problemen
- Wees proactief in plaats van reactief

## ZEER belangrijke aandachtspunten:

- Als je testen uitvoert, doe dat altijd van uit de directory waar main.py staat.
- Als je vragen hebt, stel die ALTIJD VOORDAT je aanpassingen aan de code documentatie
- Houd rekening met de regels van linter en ruff b.v. code regels<= 88
