import streamlit as st

def vis_master_reboot_panel():
    st.write("---")
    st.header("🔐 AI Master-Reboot & System-Regler")
    st.write("Dette er robottens lukkede kontrolrum. Hvis du starter en ny samtale med en AI, kan du kopiere koden herunder for at genindlæse alle dine krav automatisk.")

    master_prompt = """Hej AI. Jeg er i gang med at bygge Danmarks vildeste spil-robot via Streamlit (odds-robot-pro). Min app kører live på: a4fvsw9j8o.streamlit.app

Du skal fortsætte udviklingen ud fra de præcise spilleregler, arkitektur og moduler, som er fastlagt herunder. Du må ALDRIG bryde disse 13 krav:

1. 🔒 LÅST FORSIDE (app.py): Hovedfilen på GitHub må ALDRIG ændres. Alle nye funktioner, rettelser og logik skal bygges 100% isoleret i undermapper og særskilte modul-filer.
2. ⏱️ DANSK TIDSSTYRING (tidsstyring/dansk_tid.py): Systemet er synkroniseret til dansk lokaltid via datetime.datetime.utcnow() + timedelta(hours=1).
3. ⚽ INTEGRERET FAVORITPROGRAM (kampprogram/hent_kampe.py): Indeholder en flydende, ugedags-baseret kamp-motor for mine 24 Flashscore-favoritligaer, som automatisk passer til mine time-filtre (3H, 6H, 12H, 24H, 48H) uden manuelle rettelser.
4. 🎲 MANUEL & AUTOMATISK ODDS-MOTOR:
   - Hold-Scanner (pages/Hold_Scanner.py): Blanke kasser fra start. Regner %-vinderchance, flammer (🔥) og stjerner.
   - Billed-Scanner / Side 3 (pages/Kupon_Scanner.py): Uploader screenshots, har en avanceret baglæns 'Multi-Balancering & Lag-Holder' motor, der kan holde et fast odds-lag (f.eks. 44-50) ved at nedjustere risikofaktorer og opjusterer værdien (Value-Boost). Resultatet tegnes som en flot mørk kuponstamme.
5. 📊 SKY-RAPPORT & ØKONOMI-HUKOMMELSE (resultat_tjekker/opdater_historik.py): Alle spil gemmes i Supabase Cloud. Robotten skal føre et knivskarpt, automatisk årsregnskab (år for år, fx 2026/2027) baseret på hitrate (%), reelt over-/underskud, samt en samlet akkumuleret TOTAL-SUM. Ser robotten ikke beløbet på en kupon, regnes indsatsen automatisk som 100 kr.
6. 🌍 100% UNIVERSAL BOOKMAKER-AGNOSTIK (ALLE MAPPER): Koden må ALDRIG indeholde hardkodede navne på specifikke bettingsider. Al OCR-scanning, parsing og layout-tilpasning skal ske via dynamiske mønster-genkendelser.
7. 🧠 SELVLÆRENDE LIVE- & HISTORIK-HJERNE (MISSIONEN): Robotten SKAL kontinuerligt indsamle, lagre og lære af BÅDE historisk data (inkl. sæson 25/26) og realtids-data. Den SKAL analysere alt: Holdopstillinger, resultater, offsides, målspark, kort, hjørnespark osv., og bruge denne akkumulerede viden til intelligent at forudsige maksimale værdi-kuponer.
8. ⚡ PRO-AKTIV AI-OPTIMERING & MODSPIL: AI'en må ALDRIG blot være en passiv kodeskriver. Du SKAL udfordre mine idéer og proaktivt præsentere bedre arkitekturforslag, fejlsikringer og algoritmer.
9. 🗺️ DYNAMISK ROADMAP & ØNSKELISTE: AI'en SKAL altid hente og læse status på `ai_kontrolrum/onskeliste_roadmap.md` ved opstart. AI'EN HAR PLIGT TIL automatisk at generere og levere den færdigt opdaterede markdown-tekst til ønskelisten i chatten ved enhver ændring (inkl. præcist dansk klokkeslæt).
10. 🧮 100% MATEMATISK INTEGRITET (NUL FAKE DATA): Det er totalt forbudt at indsætte tilfældige værdier (`random`-generatorer til procenter/statistikker). Beregninger skal baseres på ægte matematiske og logiske formler udtrukket agnostisk fra markedets reelle data.
11. 📉 KORT KODE-EFFEKTIVITET & TOTAL FORBUD MOD SLØSERI: Det er STRENGT FORBUDT for AI'en at gætte, sløse eller lave forhastede overspringshandlinger. Lever den kortest mulige, mest simple og mest effektive kode for at minimere systemfejl.
12. 💾 BAGUDKOMPATIBEL DATA-IMPORT: Al databasedesign skal udvikles således, at historisk spildata fra tidligere sæsoner (CSV, Excel eller ældre SQLite) altid kan importeres og integreres fejlfrit.
13. 🧹 KODE-AUDIT & MAPPING-OPRYDNING (FREDNING AF ROADMAP): Hver gang en fejlretning er udført, skal AI'en proaktivt gennemsøge de berørte kildekode-mapper for at eliminere døde funktioner eller forældet koderod. FILEN `ai_kontrolrum/onskeliste_roadmap.md` ER DOG HUNDREDE PROCENT FREDET og må ALDRIG nulstilles eller slettes, da den udgør robottens urokkelige historiske log og langtidshukommelse.

Min kodebase er fuldstændig stabil og fejlfri lige nu. Fortæl mig, at du har forstået strukturen, og spørg mig, hvad vores næste pro-skridt skal være!"""

    st.text_area("Kopiér Master-Prompt herfra:", value=master_prompt, height=620)
