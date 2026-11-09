import streamlit as st

def vis_master_reboot_panel():
    st.write("---")
    st.header("🔐 AI Master-Reboot & System-Regler")
    st.write("Dette er robottens lukkede kontrolrum. Hvis du starter en ny samtale med en AI, kan du kopiere koden herunder for at genindlæse alle dine krav automatisk.")

    master_prompt = """Hej AI. Jeg er i gang med at bygge Danmarks vildeste spil-robot via Streamlit (odds-robot-pro). Min app kører live på: a4fvsw9j8o.streamlit.app

Du skal fortsætte udviklingen ud fra de præcise spilleregler, arkitektur, moduler og historik, som er fastlagt herunder. Du må ALDRIG bryde eller ændre disse urokkelige krav:

======================================================================
🔒 FASTLÅSTE SYSTEM-REGLER & LOGIK (Må ALDRIG ændres - Fundamentet)
======================================================================
* app.py er 100% låst: Ingen ændringer i hovedfilen. Alt kodes i undermapper.
* Bookmaker-Agnostik: Ingen hardkodede navne. Alt parses via mønstre.
* Permanent Hukommelse: Supabase Cloud er robottens eneste hjerne.
* Indsats-Logik: Standardindsats på 100 kr., hvis beløbet ikke ses på kuponen.
* Årsregnskab & Økonomi-Log: Knivskarpt regnskab år for år + en permanent TOTAL-SUM.
* Statistisk Total-Indsigt: Opsamling og læring af holdopstillinger, offsides, målspark osv.

======================================================================
✅ UDFØRTE OPGAVER & HISTORIK (Mandag d. 9. november 2026)
======================================================================
* Kl. 16:04 - API HTTP Rest-sikring implementeret i historikken: Omskrevet resultat_tjekker/opdater_historik.py.
* Kl. 16:29 - Eliminering af 'random' i beregningsmotoren (byg_kupon.py UDFØRT): Matematisk sandsynlighedsalgoritme.
* Kl. 16:34 - Lovfæstet Ufravigelig Matematisk Integritet (Krav 10 UDFØRT): Forbud mod tilfældighedsgeneratorer tilføjet.
* Kl. 16:36 - Fuldendelse af Master-Regler med Historisk Data-Import (Krav 12 UDFØRT): Sikring af historisk data-compatibilitet.
* Kl. 16:40 - 🔒 Eksplicit Fredning af Roadmap-loggen (Krav 13 OPGRADERET): Oprydningsregler mejslet i sten.
* Kl. 16:49 - ⏱️ System-Audit: Mappe 1 - Tidsstyring (GODKENDT & LÅST): Omskrevet tidsstyring/dansk_tid.py via zoneinfo.
* Kl. 16:55 - ⚽ System-Audit: Mappe 2 - Kampprogram (GODKENDT & LÅST): Dynamisk ugedags-motor installeret i kampprogram/hent_kampe.py.
* Kl. 17:05 - 📊 System-Audit: Mappe 3 - Resultat-Tjekker Fuldendt (GODKENDT & LÅST): Supabase REST-integration i resultat_tjekker/.
* Kl. 17:10 - 📸 System-Audit: TRIN 1 - Billed-Scanner Fuldendt (Kupon_Scanner.py GODKENDT & LÅST): Direkte cloud-forbindelse aktiveret.
* Kl. 17:15 - 🧹 Mappe-Audit: Mappe 5 - Totalsanering af Pages-mappen (UDFØRT & GODKENDT): Slettet forældede kontrolrums- og SQLite-filer.
* Kl. 17:21 - 🗑️ Mappe-Audit: Mappe 6 - Komplet terminering af Historik-mappe (UDFØRT & GODKENDT): Fjernet historik/ permanent.
* Kl. 17:39 - 🤖 Mappe-Audit: Mappe 7 - Totalsanering af Billed-Scanner-Motor (scanner_motor.py GODKENDT & LÅST): Udskiftet fup-data med regex layout parser.
* Kl. 18:46 - 🧹 Mappe-Audit: Mappe 8 - Eliminering af forældet Manuel Scanner (UDFØRT & GODKENDT): Slettet manuel_scanner/.
* Kl. 18:52 - 💀 Fuldstændig Terminering af Spøgelseshjerne (ai_hjerne.py UDFØRT & GODKENDT): Alt skjult SQLite-hukommelse og ulovlige random-funktioner udrenset.

======================================================================
👑 SYSTEMETS MASTER-REGELSET (PRO VINDING & BREDDE)
======================================================================
1. 🔒 LÅST FORSIDE (app.py): Hovedfilen på GitHub er 100% låst og må ALDRIG ændres. Alle nye funktioner, rettelser og logik skal bygges fuldstændig isoleret i undermapper.
2. ⏱️ DANSK TIDSSTYRING (tidsstyring/dansk_tid.py): Systemet er synkroniseret til dansk lokaltid via zoneinfo / normaltid.
3. ⚽ FODBOLDBREDDE UDEN BEGRÆNSNINGER: Robotten starter med fodbold og skal kunne foreslå og spille på ALT, hvad man overhovedet kan spille på. Den skal agnostisk indlæse alle 24 Flashscore-favoritligaer, herunder de danske turneringer (Superliga, Betinia LIGA, CampoBet 2. Division, Betano Pokalen) samt globale ligaer (Championship, Ligue 1/2/3, J2 League, OBOS-ligaen, Serie A/B osv.) uden hårde begrænsninger.
4. 📊 100% DYNAMISK MARKEDSPARSER: Beregningsmotoren må ALDRIG være låst til "Kampvinder". Den skal kunne håndtere alle specialmarkeder: Standard (Mål/Resultat), Hjørnespark (Over/Under/Flest), Spillerskud & Skud på mål, Tacklinger & Målmandsredninger, Kort-sandsynlighed (Gule/Røde) samt Målscorere (Anytime/Første).
5. 🎲 DE 3 SCURNINGSMAPPER & ODDS-LOGIK:
   - Mappe 1 (Autopilot Scanner): Scanner selv markedet bredt inden for den valgte tidszone efter bedst mulige odds. Den skal holde et fastsat odds-lag (f.eks. 44-50) ved at nedjustere risikofaktorer og opjustere værdien (Value-Boost). Valgfri på kampe og udfald.
   - Mappe 2 (Manuel Kamp Vælger): Gør nøjagtig det samme, men her vælger brugeren selv kampene, den skal finde udfald på, inden for de valgte ligaer. Blanke kasser fra start, søg et hvilket som helst hold frem, regner %-vinderchance, stjerner og risikoflammer (🔥).
   - Mappe 3 (Billed-Scanner / pages/Kupon_Scanner.py): Uploader screenshots, parser layout via regex mønster-genkendelse og tegner en mørk kuponstamme. Brugeren kan manuelt rette eller tilføje forslag til rettelser.
6. 💾 permanent CLOUD-HJERNE & REGNSKAB (Mappe 4 / /historik): Supabase Cloud via REST API er robottens eneste sandhedskilde. Fælles for Mappe 1, 2 og 3 er, at alle spil og manuelle rettelser SKAL kunne tilføjes til historikken, så de overlever en reboot permanent. Robotten fører et knivskarpt, automatisk årsregnskab (år for år) baseret på hitrate (%), reelt over-/underskud samt den akkumulerede TOTAL-SUM.
7. 🧠 SELVLÆRENDE LIVE-HJERNE: Robotten SKAL kontinuerligt opsamle, lagre og lære af BÅDE historisk data (inkl. sæson 25/26) og realtids-data. Den SKAL analysere alt (holdopstillinger, resultater, offsides, målspark osv.) og bruge denne viden til intelligent at forudsige maksimale værdi-kuponer og lære af sine fejl over tid.
8. ⚡ PRO-AKTIV AI-OPTIMERING & MODSPIL: AI'en må ALDRIG blot være en passiv kodeskriver. Du SKAL udfordre idéer og proaktivt præsentere bedre arkitekturforslag, fejlsikringer og algoritmer uden sløseri.
9. 🗺️ DYNAMISK ROADMAP & ØNSKELISTE: AI'en SKAL altid hente og læse status på `ai_kontrolrum/onskeliste_roadmap.md` ved opstart. AI'EN HAR PLIGT TIL automatisk at generere og levere den færdigt opdaterede markdown-tekst til ønskelisten i chatten ved enhver ændring (inkl. præcist dansk klokkeslæt).
10. 🧮 100% MATEMATISK INTEGRITET (NUL FAKE DATA): Det er totalt forbudt at indsætte tilfældige værdier (`random`-generatorer til procenter/statistikker). Beregninger skal baseres på ægte matematiske og logiske formler udtrukket agnostisk fra markedets reelle data.
11. 📉 TOTAL FORBUD MOD SLØSERI: Det er STRENGT FORBUDT for AI'en at gætte, sløse eller lave forhastede overspringshandlinger. Lever den kortest mulige, mest simple og mest effektive kode for at minimere systemfejl.
12. 💾 BAGUDKOMPATIBEL DATA-IMPORT: Al databasedesign skal udvikles således, at historisk spildata fra tidligere sæsoner (CSV, Excel eller ældre SQLite) altid kan importeres og integreres fejlfrit.
13. 🧹 KODE-AUDIT & MAPPING-OPRYDNING (FREDNING AF ROADMAP): Hver gang en fejlretning er udført, skal AI'en proaktivt gennemsøge de berørte kildekode-mapper for at eliminere døde funktioner eller forældet koderod. FILEN `ai_kontrolrum/onskeliste_roadmap.md` ER DOG HUNDREDE PROCENT FREDET og må ALDRIG nulstilles eller slettes, da den udgør robottens urokkelige historiske log og langtidshukommelse.

Når nye ønsker til mapper opstår, skal disse tilføjes til ønskesiden, og statuslinjen opdateres jævnligt, så vi ikke risikerer at fryse midt i en chat. Alle rettelser skal ske i undermapper uden ukoncentrerede fejl.

Konfigurationen er komplet samlet og låst fast. Fortæl mig, at du har indlæst dette fulde dokument!"""

    st.text_area("Kopiér Master-Prompt herfra:", value=master_prompt, height=620)
