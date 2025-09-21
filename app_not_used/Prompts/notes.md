# Database punten:

- Er wordt een grote directory onderzocht : hierbij is threading nodig omdat anders NiceGui de connectie verliest.
- In elke directory moeten alle media files metadata gegevens via Exiftool opgehaald worden en in de database gezet worden. Ik vermoed dat we daar een Pool met workers zullen gaan gebruiken.

[ ] Database_Manager impact:
[ ] Path storage: Database moet UTF-8 ondersteunen (SQLite doet dit standaard)
[ ] Query escaping: Bij het zoeken naar bestanden met vreemde karakters
[ ] Hash matching: Bestandspaden moeten exact matchen
Dit is geen probleem, maar wel iets om rekening mee te houden in de implementatie.

# Centrale progress

1: Mijn idee is om ook een centraal "Progress kaartje" te gaan maken. Dat is voor een van de volgende stappen, tenzij jij nu zegt dat we dat eerst moeten maken. Het idee is een kaartje met de volgende elementen:

- heartbeat indicator : b.v. circulaire progress bar, die dtsseds voolloppt en dan weer leeg loopt.
- progres bar: parameters: start, eind, step en die dan een "schop" krijgen met x steps.
- progress display met 1 tot 4 velden met een titel en value. Deze kan dan een update krijgen met veld nummer, waarde,
- ui-director waarin je aangeeft welke van de bovenstaande elementen zichtbaar is.

Ha ha, dit is echt een goed communicatie proces tussen ons, mijn complimenten.

Punt 1: OK
Punt 2: Event driven communicatieIk wil het liefst update tijdgestuurd. Met een update parameter in config.json.
Punt 3: SQLite is it
Punt 4: Exiftool met vreemde karakters: Wil je daar dan EXTRA op letten
Punt 5: geen batch processing
Punt 6: Dat kanik niet beoordelen, dat is te technisch. Maar ik vertrouw je.

Je vragen:
vraag 1: Mijn idee is om ook een centraal "Progress kaartje" te gaan maken. En tijdgebaseerd een update te geven. Met een paramater in config.json.
Dat is voor een van de volgende
 s
 tappen, TENZIJ jij nu zegt dat we dat eerst moeten maken. Het idee is een kaartje met de volgende elementen:

- heartbeat indicator : b.v. circulaire progress bar, die dtsseds voolloppt en dan weer leeg loopt.
- progres bar: parameters: start, eind, step en die dan een "schop" krijgen met x steps.
- progress display met 1 tot 4 velden met een titel en value. Deze kan dan een update krijgen met veld nummer, waarde,
- ui-director waarin je aangeeft welke van de bovenstaande elementen zichtbaar is.

vraag 2: Doorgaan, maar ABORT moet wel enabled zijn. Zodat de gebruiker het netjes kan afbreken.
Daarbij moet er SPECIAAL rekening gehgouden worden met eventuele parallele processen en threads.
vraag 3: Ik dacht dat een SQLite database single user is, dus als een process een write aan het doen is er sowieso geen andere proces een read kan doen. Maar afgezien van dat.
Ik denk dat database locking tijdens write altijd een veilige en goede manier van werken is. Ik neem aan een database lock een ander proces gewoon even laat wachten. Voor de veiligheid lijkt me bewaking van de locktijd wel een aanbeveling. Maar wat is jou mening?

Ik verwacht nog antwoorden, voor je gaat aanpassen. Als jij ook nog vragen hebt, stel die ook nog voor je gaat aanpassen.



=============================
1: Ik ben niet zo'n fan van Batch verwerking in dit soort projecten. Het maakt een heleboel overhead, terwijl ik denk dat je heel weinig performance winst hebt. De meeste tijd gaat zitten in Disk I/O van de directory en de files en  Exiftool . Een database record schrijven gaat meestal super snel. Daarnaarst gan je zaken inmemory bufferen. En ook dat vraag overhead en  goed nadenken over allerlei edge cases. Dus nee. ik ben NIET overtuigd dat batch werken hier de oplossing is.
2: max-workers=32 Mijn maximale CPU belasting (let op de config parameter bestaat al!!)
3: Niet speciaal, behalve da tik denk dat Batch verwerking weinig bijdraagt.
4: Het is single user, single database, multi processing
5: Log melding type WARNING en verder gaan. Let op!!! Er is een config parameter use_exiftool=false. Dus op dit moment kun je heel de exiftool code overslaan.

Ik denk dat Old-1 en Base beide optie B gekozen hebben. Maar ik vraag ook duidelijk jou advies (mede met de antwoorden).

Ik kijk uit naar je aangepaste voorstel en je argumentatie.
=================================
Ik wil graag weten:
- wat doet de applicatie op welk moment, want ik snap echt niet wat er zolang gebeurt.

Kun jij eerst even de code bestuderen en kijken of mijn visie juist is?
Volgens mij gebeurt het volgende:
-Start
- initialisatie van alle processen, variabelen etc. [is zeer snel]
- User kiest directory
- Scan process intialisatie , geen parallel meschanismes 
- Scan proces loopt [langdurig, scant alle directories] Tijden Scanproces
--- nicegui_update_interval timer loopt periodiek af met:
-------- houdt de connectie met browser, UI processen, Abort knop checken, Exit knop checken, etc. levend
--- ui_update timer loopt periodiek af met:
--------- Werk Scan kaartje bij
--------- houdt spinner actief
--------- message queue wordt bekeken en verwerkt in log messages
---- log count bereik waarde voor log_count_update:
---------- er wordt een log regel gemaakt.
- Scan proces is gereed:
-- log queue wordt geleegd en samenvatting logs 
-- Scan kaartje krijgt laatste update
-- Process kaartje wordt vrijgegeven
----------- Process knop enabled
- Wachten op starten Processing

- Start Processing: initialisatie [snel]
---- Paralle processen intialiseren
- Processing [lang]
--- alle directories worden doorlopen [erg veel]
-------per file een paralel proces starten [snel]
----------- parallele proces : JSON maken en in de JSON list plaatsen [weinig] Later Exiftoof dat kan langer duren
--- nicegui_update_interval timer loopt periodiek af met:
-------- houdt de connectie met browser, UI processen, Abort knop checken, Exit knop checken, etc. levend
--- ui_update timer loopt periodiek af met:
--------- Werk Processing kaartje bij: Progress bar en Progress info Regel [zeer snel]
--------- houdt spinner actief
--------- message queue wordt bekeken en verwerkt in log messages
---- log count bereik waarde voor log_count_update:
---------- er wordt een log regel gemaakt.
- Processing gereed
-- alle parallele processen eindigen
-- alle queues leegmaken en samenvattings log
-- Processing kaartje laatste update

Als DIT de flow is.......Dan is er NERGENS een pange tijd waarin er geen UI update is:
Tijdens Scan process: Scan kaartje updates : WERKT
Tijdens Processing : Progress Bar en Process info regel : WERKT

Maar TUSSEN deze 2 zit een gigantische tijd.

Ik wil graag weten wat er in die tijd gebeurt. Daarom hebben we debug statements toegevoegd..
En om die later eenvoudig weer te kunnen opruimen , zijn die gemarkeerd met #DEBUG commentaar.


Als je nog vragen hebt, stel die dan. Ik wil niet dat je nu al code gaat aanpassen. Bedankt

========================================
echo "hallo"
