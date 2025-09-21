## Algemene hoofd flow.

- Modulaire Pages opzetten
- UI structuur op te zetten.
- Main Page, Config Page, Fill DB Page
- algement mechanisme: Logging, Messaging, database ontwerp, Error handling
- DB manager structuur en logica
- File processing flow
- Process media finder, Process dir tree, fill db page functionaliteiten

## Het doel van mijn uiteindelijke applicatie is:

1 op een systeem alle media files vinden
2 alle resultaten in een database zetten
3 op basis van hash en metadata ontdubbelen en een set overhouden met de meest complete metadata. Hierbij ook automatisch onjuiste metadata herstellen.
4 op basis van een automatisch te generenen directory structuur alle media files ordenen. Bv. Jaar, Maand, Dag, Type, GPS info inleesbare vorm
5 alle media bestanden automatisch in deze structuur plaatsen, waarbij er veel zorg voor is dat er geen media bestanden of metadata verloren gaat.

enkele tools om dit proces te ondersteunen:

- Metadata page: foto met alle metadata die ook te wijzigen is
- SQL page. ik wil SQL statements in json format in een file opslaan en deze kunnen uitvoeren.

## Referenties die je kunt gebruiken om de best praktices te genereren.

https://github.com/zauberzeug/nicegui/tree/3df8b2b16eb7ac471cc36bf9498a3cd652e95bb9

## Communicatie protocol ###
 - Jij gaat NOOIT zonder mijn EXPLICIETE toestemming code of gegevens wijzingen
 - Jij doet NOOIT aannames, zonder die bij mij te verifieren
 - Als je onduidelijkheden of vragen hebt, stel je die VOOR je code of gegevens gaat aanpassen
 - VOORDAT je gaat aanpassen maak je ALTIJD een safepoint
 - Voordat je gaat aanpassen maak j eeerst een samenvatting van wat je gaat aanpassen en vraag je toestemming voor deze aanpassingen
 - Als je aanpassingen gedaan hebt, geeft je een samenvatting van wat je daadwerkelijk hebt verandert.
 - Als je tijdens het aanpssen merkt dat je een andere oplossing wilt gaan gebruiken dan je eerst dacht, vraag je eerst aan mij of ik het mee eense ben

#### BEGIN STAPPEN PLAN



## Basis technologie

- IDE Cursor, dus ook de restrictie dat er alleen extentie gebruikt kunnen worden die in de cursor marketplace beschikbaar gesteld zijn.
- ontwikkelen in een dev container. Hierbij wil ik graag aansluiten bij https://github.com/zauberzeug/nicegui/tree/3df8b2b16eb7ac471cc36bf9498a3cd652e95bb9/.devcontainer
- werken met Python en het UI framework Nicegui. Zie https://github.com/zauberzeug/nicegui/tree/3df8b2b16eb7ac471cc36bf9498a3cd652e95bb9/nicegui
- gebruik maken van Poetry

## Modulaire pages opzetten.

ik wil graag modulaire pages opzetten.
De applicatie zal ALTIJD starten door ./main.py aan te roepen. Bij voorkeur met "Poetry run python main.py"
Achtergond documentatie is: https://github.com/zauberzeug/nicegui/tree/3df8b2b16eb7ac471cc36bf9498a3cd652e95bb9/examples/modularization
Ik wil graag een advies over welke methode voor mij het meest passend is.
Als dat moeilijk te geven is, dan een voor/na delen overzicht van deze methoden.
[ ] Begrip welke methode het best passend is
[ ] Keuze van modulaire paging methodiek

## Algemene UI

Ik wil graag een algemene indeling van alle pagina's waarbij de volgende zaken overal doorgevoerd zijn:

    [ ] **ALLE UI teksten in het Engels**

# pagina structuur

    [ ] Top balk : afmetingen, kleur, standaard knoppen MENU, HOME, ABORT, EXIT
    [ ] Menu knop: positie, pagina's
    [ ] kleurstelling van de pagina onderdelen

# algemene knoppen.

    [ ] Navigatie: een menu icoon. Bij klink drop menu met alle beschikbare pagina's
    [ ] Exit: zie specificatie EXIT knop
    [ ] Abort: zie specificatie ABORT knop

## standarisatie van elementen

    [ ] knop
    [ ] label
    [ ] kaartje
    [ ] scroll window
    [ ] progress bar lineair
    [ ] progress bar circulair
    [ ] slider
    [ ] toggle switch
    [ ] checkbox
    [ ] input box single line
    [ ] input box multi line

## EXIT knop

    [ ] Altijd zichtbaar en enabled.
    [ ] Dialoog met Are you sure to quit? Yes / No
    [ ] alle parallel processen (die zijn er nu nog niet, maar die komen) netjes afsluiten
    [ ] alle thread processen (die zijn er nu nog niet, maar die komen) netjes afsluiten
    [ ] alle logging (die zijn er nu nog niet, maar die komen) netjes afsluiten
    [ ] alle database (die zijn er nu nog niet, maar die komen) netjes afsluiten
    [ ] alle pagina's (die zijn er nu nog niet, maar die komen) netjes afsluiten
    [ ] de totale applicatie netjes afsluiten

## ABORT knop

    [ ] Altijd zichtbaar,standaard **disabled**.
    [ ] Alleen **enabled** als er 1 of meerdere processing lopen.
    [ ] Als er geen processen meer lopen **weer disabled**
    [ ] Dialoog met Are you sure to quit? Yes / No
    [ ] alle parallel processen (die zijn er nu nog niet, maar die komen) netjes afsluiten
    [ ] alle thread processen (die zijn er nu nog niet, maar die komen) netjes afsluiten
    [ ] alle logging (die zijn er nu nog niet, maar die komen) netjes afsluiten
    [ ] alle database (die zijn er nu nog niet, maar die komen) netjes afsluiten
    [ ] alle pagina's (die zijn er nu nog niet, maar die komen) netjes afsluiten
    [ ] de totale applicatie netjes afsluiten

## Logging

    [ ] gebaseerd op Queing mechanisme
    [ ] INFO label: informatie voor de gebruiker
    [ ] WARNING label: Er gaat is niet goed, maar het process gaat wel door
    [ ] ERROR label: er gaat iets niet goed en het process kan niet doorgaan
    [ ] Parameter Log_enabled=True : alle logging False: Alleen label ERROR en WARNING LET op!! ALLE logging gaat ALTIJD naar de logfile
    [ ] Parameter Log_terminal=True logging komt ook in de terminal False: logging komt niet in de Terminal
    [ ] Parameter Log_clean=True De logfile wordt verwijder of gewist voor de processen beginnen
    [ ] Parameter log_file  Geeft filename van de log file
    [ ] Parameter log_path volledige path waar de logfile gemaakt kan worden

