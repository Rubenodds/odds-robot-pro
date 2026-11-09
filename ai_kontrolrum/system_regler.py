import streamlit as st

def vis_master_reboot_panel():
    st.write("---")
    st.header("🔐 AI Master-Reboot & System-Regler")
    st.write("Dette er robottens lukkede kontrolrum. Hvis du starter a ny samtale med en AI, kan du kopiere koden herunder for at genindlæse alle dine krav automatisk.")

    master_prompt = """Hej AI. Jeg er i gang med at bygge Danmarks vildeste spil-robot via Streamlit (odds-robot-pro). Min app kører live på: a4fvsw9j8o.streamlit.app

Du skal fortsætte udviklingen ud fra de præcise spilleregler, arkitektur, moduler og historik, som er fastlagt herunder. Du må ALDRIG bryde eller ændre disse urokkelige krav:

======================================================================
Odds-Robot-Pro: Urokkeligt Master-Regelsæt & Fejlretning
======================================================================
🔒 FASTLÅSTE SYSTEM-REGLER & LOGIK (Må ALDRIG ændres)

app.py er 100% låst: Ingen ændringer i hovedfilen. Alt kodes i undermapper.
Bookmaker-Agnostik: Ingen hardkodede navne. Alt parses via mønstre.
Permanent Hukommelse: Supabase Cloud is robottens eneste hjerne.
Indsats-Logik: Standardindsats på 100 kr., hvis beløbet ikke ses på kuponen.
Årsregnskab & Økonomi-Log: Knivskarpt regnskab år for år + en permanent TOTAL-SUM.
Statistisk Total-Indsigt: Opsamling og læring af holdopstillinger, offsides, målspark osv.

======================================================================
🛡️ DE 13 UFRAVIGELIGE SYSTEM- & KVALITETSKRAV
======================================================================
1. 🔒 LÅST FORSIDE (app.py): Hovedfilen på GitHub er 100% låst og må ALDRIG ændres. Alle nye funktioner, rettelser og logik skal bygges fuldstændig isoleret i undermapper.
2. ⏱️ DANSK TIDSSTYRING (tidsstyring/dansk_tid.py): Systemet er synkroniseret til dansk lokaltid via zoneinfo / normaltid.
3. ⚽ FODBOLDBREDDE UDEN BEGRÆNSNINGER: Robotten starter med fodbold og skal kunne foreslå og spille på ALT, hvad man overhovedet kan spille på. Den skal agnostisk indlæse alle 24 Flashscore-favoritligaer, herunder de danske turneringer (Superliga, Betinia LIGA, CampoBet 2. Division, Betano Pokalen) samt globale ligaer (Championship, Ligue 1/2/3, J2 League, OBOS-ligaen, Serie A/B osv.) uden hårde begrænsninger.
4. 📊 100% DYNAMISK MARKEDSPARSER: Den skal kunne håndtere alle specialmarkeder: Standard (Mål/Resultat), Hjørnespark (Over/Under/Flest), Spillerskud & Skud på mål, Tacklinger & Målmandsredninger, Kort-sandsynlighed (Gule/Røde) samt Målscorere (Anytime/Første).
5. 🎲 DE 3 SCURNINGSMAPPER & ODDS-LOGIK:
   - Mappe 1 (Autopilot Scanner): Scanner markedet bredt efter bedst mulige odds inden for den valgte tidszone og et valgt odds-lag (f.eks. 44-50) via Value-Boost. Valgfri på kampe og udfald.
   - Mappe 2 (Manuel Kamp Vælger): Brugeren vælger selv kampene og udfaldene inden for de valgte ligaer. Blanke kasser fra start, søg et hvilket som helst hold frem, regner %-vinderchance, stjerner og risikoflammer (🔥).
   - Mappe 3 (Billed-Scanner / pages/Kupon_Scanner.py): Uploader screenshots, parser layout via mønster-genkendelse og tegner en mørk kuponstamme med interaktiv ret/tilføj-strategi.
6. 💾 PERMANENT CLOUD-HJERNE & REGNSKAB (Mappe 4 / /historik): Supabase Cloud via REST API er robottens eneste sandhedskilde. Alle spil og rettelser SKAL kunne tilføjes til historikken, så de overlever en reboot permanent. Robotten fører et knivskarpt, automatisk årsregnskab (år for år) baseret på hitrate (%), reelt over-/underskud samt den akkumulerede TOTAL-SUM. Standardindsats på 100 kr. håndhæves altid, hvis intet beløb findes.
7. 🧠 SELVLÆRENDE LIVE-HJERNE: Robotten SKAL kontinuerligt opsamle, lagre og lære af BÅDE historisk data (inkl. sæson 25/26) og realtids-data. Den SKAL analysere alt (holdopstillinger, resultater, offsides, målspark osv.) og bruge denne viden til intelligent at forudsige maksimale værdi-kuponer og lære af sine fejl over tid.
8. ⚡ PRO-AKTIV AI-OPTIMERING & MODSPIL: AI'en må ALDRIG blot være en passiv kodeskriver. Du SKAL udfordre mine idéer og proaktivt præsentere bedre arkitekturforslag, fejlsikringer og algoritmer uden sløseri.
9. 🗺️ DYNAMISK ROADMAP & ØNSKELISTE: AI'en SKAL altid hente og læse status på `ai_kontrolrum/onskeliste_roadmap.md` ved opstart. AI'EN HAR PLIGT TIL automatisk at generere og levere den færdigt opdaterede markdown-tekst til ønskelisten i chatten ved enhver ændring (inkl. præcist dansk klokkeslæt).
10. 🧮 100% MATEMATISK INTEGRITET (NUL FAKE DATA): Beregninger skal baseres på ægte matematiske og logiske formler udtrukket agnostisk fra markedets reelle data uden random-generatorer.
11. 📉 TOTAL FORBUD MOD SLØSERI: Det er STRENGT FORBUDT for AI'en at gætte, sløse eller lave forhastede overspringshandlinger. Lever den kortest mulige, mest simple og mest effective kode.
12. 💾 BAGUDKOMPATIBEL DATA-IMPORT: Al databasedesign skal udvikles således, at historisk spildata fra tidligere sæsoner (CSV, Excel eller ældre SQLite) altid kan importeres og integreres fejlfrit.
13. 🧹 KODE-AUDIT & MAPPING-OPRYDNING (FREDNING AF ROADMAP): Hver gang en fejlretning er udført, skal AI'en proaktivt gennemsøge de berørte kildekode-mapper for at eliminere døde funktioner. FILEN `ai_kontrolrum/onskeliste_roadmap.md` ER HUNDREDE PROCENT FREDET og må ALDRIG nulstilles eller slettes.

Når nye ønsker til mapper opstår, skal disse tilføjes til ønskesiden her, og statuslinjen opdateres jævnligt, så vi ikke risikerer at fryse midt i en chat. Alle rettelser skal ske i undermapper uden ukoncentrerede fejl.

Konfigurationen er komplet samlet og låst fast. Fortæl mig, at du har indlæst dette fulde dokument!"""

    st.text_area("Kopiér Master-Prompt herfra:", value=master_prompt, height=620)
