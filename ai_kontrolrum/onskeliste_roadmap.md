# 🗺️ Odds-Robot-Pro: Dynamisk Roadmap & Ønskeliste
**Senest opdateret:** Tirsdag d. 10. november 2026 kl. 22:38 (Dansk tid)

## ✅ Gennemførte Milepæle
- [x] **Låst forside (`app.py`):** 100 % isoleret modulær indlæsning etableret.
- [x] **Dansk tidsstyring (`tidsstyring/dansk_tid.py`):** Synkroniseret med `Europe/Copenhagen`.
- [x] **Favoritligaer (`odds_motor/liga_favoritter.py`):** Standardligaer + automatisk navnenormalisering.
- [x] **Mappe 1 (`odds_motor/autopilot_scanner.py`) — GODKENDT & LÅST:** Færdigopgraderet og godkendt live med `_hent_kampe_v9` samt interaktiv fluebens-kupon (`_vurder_kupon`), live genberegning af samlet odds, `%`-vinderchance, stjerner (`⭐`), risikoflammer (`🔥`) og aktiv "Spillet"-godkendelse til Supabase (10. nov 2026 kl. 22:38).

## 🚧 Aktuelt Fokus (I gang)
- [ ] **Mappe 2 (`odds_motor/manuel_scanner.py`):** Byg manuel kampvælger med blanke felter fra start, global holdsøgning med automatisk udelukkelse af modstanderholdet fra samme kamp (anti-dobbeltvalg), %-vinderchance, stjerner (`⭐`), risikoflammer (`🔥`) og "Spillet"-knap.

## 📋 Kommende Opgaver
- [ ] **Mappe 3 (Billed-Scanner):** Mønstergenkendelse af bookmaker-screenshots + interaktiv mørk kuponstamme med ret/tilføj-strategi og "Spillet"-godkendelse.
- [ ] **Mappe 4 (`/historik` & Supabase Cloud):** Ret `st.secrets` konfigurationen, automatisk årsregnskab (år for år), hitrate (%), permanent TOTAL-SUM og bagudkompatibel CSV/Excel/SQLite-import.
- [ ] **Selvlærende Live- & Historik-Hjerne:** Opsamling af holdopstillinger, offsides og målspark (inkl. sæson 25/26) til løbende værdioptimering.

## 💡 Ønskeliste & Arkitektur-idéer (Gemt til senere)
- [ ] **Automatisk ESPN Liga-Discovery:** Dynamisk hentning af samtlige aktive turnerings-slugs direkte fra ESPNs API, så nye ligaer aldrig kræver manuel tilføjelse i `SLUGS`.
- [ ] **Ekstra udvidelsesmappe til Mappe 1:** Eventuelle fremtidige ekstra-funktioner til Autopilot-scanneren bygges i et separat modul, så den godkendte `autopilot_scanner.py` forbliver urørt.
