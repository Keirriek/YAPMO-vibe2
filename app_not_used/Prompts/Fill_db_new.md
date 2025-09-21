Ik wil een nieuwe pagina fill_db_new.py hebben.
Deze komt in ./app/pages/
Deze pagine wil ik stap voor stap opbouwen.

# Stap 1: leege pagina.
- bouw de pagina volgens de style en met gebruik van themes.py
- de inhoud is leeg
- voeg de pagina toe aan main.py en main_page.py
- voeg de pagina toe aan de menu knop.

# Stap 2: Test proces opbouwen
Alle elementen conform de elementen_page
- maak een input tekst ui element : count
- maak een input tekst ui element: unit
- maak een zandloper spinner element
- maak een tekst label: result
- maak een start knop

# Stap 3: UI test kaartje
Alle elementen conform de elementen_page
- maak een nieuw kaartje met label UI
- maak een tekst element: current
- maakt een element: timer
Bij TestProcess:
- maak input tekst element: file1
- maak input tekst element: file2

# Stap 4: test logica
Maak de volgende logica
- bij start proces gebeurt het volgende:
- er is een loop die Count x doorlopen:
- file1 wordt geopend
- File1 wordt weer gesloten
- Unit komt de grootte van de file1
- file2 wordt geopend
- File2 wordt weer gesloten
- Unit komt de grootte van de file2

# Stap 5: scan process
Nu wil ik graag dat het scnap process uit /workspaces/app/pages/test_traverse_page.py in fill_db_new komt.
De werking moet als volgt zijn:
- alle huidige code van de pagina, inclusief UI mag verwijdered worden
- Alle code gerelateerd aan de scan functie toegevoegd worden
Echter met de volgende beperkingen:
- GEEN UI gerelateerde code
- GEEN logging gerelateerde code
- GEEN Error handling gerelateerde code
- GEEN output fields
- Een start processing knop om het process te starten
max_workers = 20 Hard gecodeerd.
de search directory is een text input veld

