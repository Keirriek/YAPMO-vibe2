Nu op nieuw.
De ui_update werkt niet gedurende het doorlopen van de directories.
Om dat op te lossen wil ik het test_ui_update_debug gebruiken.
Kun je het volgende doen:
- ik wil test_ui_update_debug gebruiken
- in fill_db_new en bijbehorende files is alle test code door commentaar voorzien.
Als test_ui_update_debug echter hier routines uit nodig heeft, kun je die op ve volgende manier beschikbaar stellen:

- als het een enkele regel is die geactiveerd moet worden , moet de commentaar marker (#DEBUG_OFF of #TEST_AI_OFF) naar _ON gezet worden
- als het een blok regels is, moeten de begin (Start Bock ... ) en eind (End Block ....) rgele naar _ON gezet worden.
- Dan kun je de betreffende commentaar code regels activeren.

Dit betreft allen de fill_db_new file en files die deze file gebuikt.
Is deze procedure duidelijk?
Als je nog vragen hebt, stel die voor je gaat aanpassen. Bedankt.