# **Refactoring Config**
## config.json
# Status: COMPLETED ✅
[x] Restructure config.json in sections: 
    - general
    - processing
    - logging
    - database
    - metadata_fields_file
    - metadata_fields_image
    - metadata_fields_video
    - metadata_write_image
    - metadata_write_video
    - paths
    - extensions
[ ] Checked & Approved


**Details:** 
- Alle velden en waarden behouden (geen wijzigingen)
- Source en version verplaatst naar general sectie
- General sectie uitgebreid met app_name, app_version, app_description
- Secties geordend volgens gewenste volgorde
- Metadata secties volledig ongewijzigd gebleven

# **Ruim  restanten op**
# Status: COMPLETED ✅
[x] Check of de definite van get_param(sectie, key) is
[x] check op get_param(secties, key) ook een list of dictionary (check even welke nodig is) kan terug geven. Zodat get_param(extensions,image_extensions ) netjes alle extensies terug geeft.
"extensions": {
    "image_extensions": [
      ".jpg",
      ".jpeg",
      ".png",
      ".tiff",
      ".raw",
      ".arw"
    ],
[x] Controleer alle programma files op het gebruikt van get_param met 1 parameter, zet die om in 2 parameters.
LET OP!! Zo dat er NIET weer een andere functie is voor het werken 1 parameter. Dus niet b.v. get_database_name of zoiets. We willen juist 1 algemene routine.
[x] controleer alle *.py files in /app en /app/pages op het juist gebruik van get_param(sectie,key)



## config.py
# Status: COMPLETED ✅
[x] match config.json
[x] general call get_section_metadata (section, key)
[x] general call set_section_metadata (section, key)
[x] voeg app_name, app_version, app_description toe
[ ] Checked & Approved

**Details:**
- create_default_config() bijgewerkt om nieuwe structuur te matchen
- get_version() aangepast om general sectie te gebruiken
- Nieuwe functies toegevoegd: get_app_name(), get_app_description()
- Main.py bijgewerkt om nieuwe config functies te gebruiken
- Alle secties correct ondersteund

# **UI config_page**
[ ] het structureren
[ ] debug tab ??

## Integration test
# Status: TODO
[ ] App working
[ ] UI Working