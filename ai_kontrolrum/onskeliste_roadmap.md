# 🗺️ Odds-Robot-Pro: Dynamisk Roadmap & Ønskeliste
**Senest opdateret:** Tirsdag d. 10. november 2026 kl. 22:20 (Dansk tid)

## ✅ Gennemførte Milepæle
- [x] **Låst forside (`app.py`):** 100 % isoleret modulær indlæsning etableret.
- [x] **Dansk tidsstyring (`tidsstyring/dansk_tid.py`):** Synkroniseret med `Europe/Copenhagen`.
- [x] **Favoritligaer (`odds_motor/liga_favoritter.py`):** Standardligaer + automatisk navnenormalisering.
- [x] **Mappe 1 (`odds_motor/autopilot_scanner.py`):** Opgraderet til `_hent_kampe_v9` — små venskabslandskampe (`fifa.friendly`) er fjernet, så kun store landskampsturneringer (UEFA Nations League & VM Kvalifikation) samt klubturneringer indgår, og mobil-UX er forenklet til kompakt radiovalg (`Alle kampe i valgte ligaer` vs. `Håndpluk bestemte kampe`) (10. nov 2026 kl. 22:17).

## 🚧 Aktuelt Fokus (I gang)
- [ ] **Verificering af Mappe 1 live:** Godkend `odds_motor/autopilot_scanner.py` live på Streamlit og bekræft kupon-output ved klik på `🔍 FIND MEST SANDSYNLIGE KUPON`.
- [ ] **Mappe 2 (`odds_motor/manuel_scanner.py`):** Byg manuel kampvælger med blanke felter fra start, global holdsøgning med automatisk udelukkelse af modstanderholdet fra samme kamp (anti-dobbeltvalg), %-vinderchance, stjerner og risikoflammer (🔥).

## 📋 Kommende Opgaver
- [ ] **Mappe 3 (Billed-Scanner):** Mønstergenkendelse af bookmaker-screenshots + interaktiv mørk kuponstamme med ret/tilføj-strategi og "Spillet"-godkendelse.
- [ ] **Mappe 4 (`/historik` & Supabase Cloud):** Ret `st.secrets` konfigurationen, automatisk årsregnskab (år for år), hitrate (%), permanent TOTAL-SUM og bagudkompatibel CSV/Excel/SQLite-import.
- [ ] **Selvlærende Live- & Historik-Hjerne:** Opsamling af holdopstillinger, offsides og målspark (inkl. sæson 25/26) til løbende værdioptimering.

## 💡 Ønskeliste & Arkitektur-idéer (Gemt til senere)
- [ ] **Automatisk ESPN Liga-Discovery:** Dynamisk hentning af samtlige aktive turnerings-slugs direkte fra ESPNs API, så nye ligaer aldrig kræver manuel tilføjelse i `SLUGS`.
