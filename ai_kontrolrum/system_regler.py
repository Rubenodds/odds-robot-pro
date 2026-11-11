======================================================================
Odds-Robot-Pro: Urokkeligt Master-Regelsæt & Fejlretning
Status: Onsdag d. 11. november 2026 kl. 10:52 (Dansk tid)
======================================================================
🔒 FASTLÅSTE SYSTEM-REGLER & LOGIK (Må ALDRIG ændres)

app.py er 100% låst: Ingen ændringer i hovedfilen. Alt kodes i undermapper.
Bookmaker-Agnostik: Ingen hardkodede navne. Alt parses via mønstre.
Permanent Hukommelse: Supabase Cloud er robottens eneste hjerne.
Indsats-Logik: Standardindsats på 100 kr., hvis beløbet ikke ses på kuponen.
Årsregnskab & Økonomi-Log: Knivskarpt regnskab år for år + en permanent TOTAL-SUM.
Statistisk Total-Indsigt: Opsamling og læring af holdopstillinger, offsides, målspark osv.

======================================================================
🛡️ DE 15 UFRAVIGELIGE SYSTEM- & KVALITETSKRAV
======================================================================
1. 🔒 LÅST FORSIDE (app.py): Hovedfilen på GitHub er 100% låst og må ALDRIG ændres. Alle nye funktioner, rettelser og logik skal bygges fuldstændig isoleret i undermapper.
2. ⏱️ DANSK TIDSSTYRING (tidsstyring/dansk_tid.py): Systemet er synkroniseret til dansk lokaltid via zoneinfo / normaltid.
3. ⚽ FODBOLDBREDDE UDEN BEGRÆNSNINGER: Robotten starter med fodbold og skal kunne foreslå og spille på ALT, hvad man overhovedet kan spille på. Den skal agnostisk indlæse alle 24 Flashscore-favoritligaer, herunder de danske turneringer (Superliga, Betinia LIGA, CampoBet 2. Division, Betano Pokalen) samt globale ligaer (Championship, Ligue 1/2/3, J2 League, OBOS-ligaen, Serie A/B osv.) uden hårde begrænsninger.
4. 📊 100% DYNAMISK MARKEDSPARSER: Den skal kunne håndtere alle specialmarkeder: Standard (Mål/Resultat), Hjørnespark (Over/Under/Flest), Spillerskud & Skud på mål, Tacklinger & Målmandsredninger, Kort-sandsynlighed (Gule/Røde) samt Målscorere (Anytime/Første).
5. 🎲 DE 3 SCANNINGSMAPPER & ODDS-LOGIK:
   - Mappe 1 (Autopilot Scanner): Scanner markedet bredt efter bedst mulige odds inden for den valgte tidszone og et valgt odds-lag (f.eks. 44-50) via Value-Boost. Valgfri på kampe og udfald.
   - Mappe 2 (Manuel Kamp Vælger): Brugeren vælger selv kampene og udfaldene inden for de valgte ligaer. Blanke kasser fra start, søg et hvilket som helst hold frem (med automatisk udelukkelse af modstanderholdet i samme kamp, så samme opgør ikke kan vælges to gange), regner %-vinderchance, stjerner og risikoflammer (🔥).
   - Mappe 3 (Billed-Scanner): Uploader screenshots, parser layout via mønster-genkendelse og tegner en mørk kuponstamme med interaktiv ret/tilføj-strategi.
6. 💾 PERMANENT CLOUD-HJERNE & REGNSKAB (Mappe 4 / /historik): Supabase Cloud via REST API er robottens eneste sandhedskilde. Alle spil og rettelser SKAL kunne tilføjes til historikken, så de overlever en reboot permanent. Robotten fører et knivskarpt, automatisk årsregnskab (år for år) baseret på hitrate (%), reelt over-/underskud samt den akkumulerede TOTAL-SUM. Standardindsats på 100 kr. håndhæves altid, hvis intet beløb findes.
7. 🧠 SELVLÆRENDE LIVE- & HISTORIK-HJERNE (MISSIONEN): Robotten SKAL kontinuerligt opsamle, lagre og lære af BÅDE historisk data (inkl. sæson 25/26) og realtids-data. Den SKAL analysere alt (holdopstillinger, resultater, offsides, målspark osv.) og bruge denne viden til intelligent at forudsige maksimale værdi-kuponer og lære af sine fejl over tid.
8. ⚡ PRO-AKTIV AI-OPTIMERING & MODSPIL: AI'en må ALDRIG blot være en passiv kodeskriver. Du SKAL udfordre mine idéer og proaktivt præsentere bedre arkitekturforslag, fejlsikringer og algoritmer uden sløseri. Forslag, der fravælges nu, gemmes på ønskelisten til senere.
9. 🗺️ DYNAMISK ROADMAP & ØNSKELISTE: AI'en SKAL altid hente og læse status på `ai_kontrolrum/onskeliste_roadmap.md` ved opstart. AI'EN HAR PLIGT TIL automatisk at generere og levere den færdigt opdaterede markdown-tekst til ønskelisten i chatten ved enhver ændring (inkl. præcist dansk klokkeslæt).
10. 🧮 100% MATEMATISK INTEGRITET (NUL FAKE DATA): Beregninger skal baseres på ægte matematiske og logiske formler udtrukket agnostisk fra markedets reelle data uden random-generatorer.
11. 📉 TOTAL FORBUD MOD SLØSERI: Det er STRENGT FORBUDT for AI'en at gætte, sløse eller lave forhastede overspringshandlinger. Lever den kortest mulige, mest simple og mest effektive kode.
12. 💾 BAGUDKOMPATIBEL DATA-IMPORT: Al databasedesign skal udvikles således, at historisk spildata fra tidligere sæsoner (CSV, Excel eller ældre SQLite) altid kan importeres og integreres fejlfrit.
13. 🧹 KODE-AUDIT & MAPPING-OPRYDNING (FREDNING AF ROADMAP): Hver gang en fejlretning er udført, skal AI'en proaktivt gennemsøge de berørte kildekode-mapper for at eliminere døde funktioner. FILEN `ai_kontrolrum/onskeliste_roadmap.md` ER HUNDREDE PROCENT FREDET og må ALDRIG nulstilles eller slettes.
14. 🔄 AUTOMATISK OPDATERING AF AI REBOOT-KODE: Hver gang et problem er løst eller en opgave er udført, SKAL AI'en automatisk levere en opdateret kopiér-kode (Master-Prompt) med den nyeste status, så brugeren altid har en frisk nøgle til en ny AI-samtale.
15. 👤 BRUGER-ISOLATION & AKTIV GODKENDELSE ("SPILLET"-KNAP): Appen skal starte 100 % 0-stillet på økonomi og statistik (0,00 kr.) til offentlig brug. Scannede billeder og forslag må ALDRIG gemmes i statistikken automatisk, men kun når brugeren aktivt trykker på knappen "Spillet".

======================================================================
📍 AKTUEL STATUS (Onsdag d. 11. november 2026 kl. 10:52)
======================================================================
* `app.py` er 100 % låst med dynamisk modul-indlæsning (`manuel_scanner.vis_manuel_scanner()` på fane 2).
* `odds_motor/autopilot_scanner.py` (Mappe 1) er GODKENDT OG LÅST live med `_hent_kampe_v9`, individuelle flueben pr. kuponforslag, live vurdering af samlet odds, `%`-vinderchance, stjerner (`⭐`), risikoflammer (`🔥`) samt `🚀 SPILLET`-knap til Supabase.
* `odds_motor/manuel_scanner.py` (Mappe 2) er opgraderet med tids-slider (1–72T), filtrering på kun aktive ligaer i tidsrammen + 1-kliks `⚡ Tilvælg alle aktive ligaer` (blank fra start), favorit-styring, global holdsøgning med anti-dobbeltvalg af modstanderholdet (`kamp_id`), 1-kliks `⚡ TILFØJ ALLE KAMPE FRA VALGTE LIGAER`, individuelle flueben pr. kuponvalg med live vurdering af odds, `%`-vinderchance, stjerner (`⭐`), risikoflammer (`🔥`) og aktiv `🚀 SPILLET`-knap til Supabase.
* `ai_kontrolrum/onskeliste_roadmap.md` er opdateret (Onsdag d. 11. november 2026 kl. 10:52).
* Næste trin: Læg den opdaterede `odds_motor/manuel_scanner.py` på GitHub, godkend Mappe 2 live på Streamlit, og fortsæt derefter til Mappe 3 (`odds_motor/billed_parser.py`).
