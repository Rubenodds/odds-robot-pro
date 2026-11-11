# 🗺️ Odds-Robot-Pro: Dynamisk Roadmap & Ønskeliste
**Senest opdateret:** Onsdag d. 11. november 2026 kl. 10:52 (Dansk tid)

## ✅ Gennemførte Milepæle
- [x] **Låst forside (`app.py`):** 100 % isoleret modulær indlæsning etableret (`manuel_scanner.vis_manuel_scanner()` koblet på fane 2).
- [x] **Dansk tidsstyring (`tidsstyring/dansk_tid.py`):** Synkroniseret med `Europe/Copenhagen`.
- [x] **Favoritligaer (`odds_motor/liga_favoritter.py`):** Standardligaer + automatisk navnenormalisering.
- [x] **Mappe 1 (`odds_motor/autopilot_scanner.py`) — GODKENDT & LÅST:** Færdigopgraderet og godkendt live med `_hent_kampe_v9` samt interaktiv fluebens-kupon (`_vurder_kupon`), live genberegning af samlet odds, `%`-vinderchance, stjerner (`⭐`), risikoflammer (`🔥`) og aktiv "Spillet"-godkendelse til Supabase (10. nov 2026 kl. 22:38).

## 🚧 Aktuelt Fokus (I gang)
- [ ] **Mappe 2 (`odds_motor/manuel_scanner.py`) — OPGRADERET & KLAR TIL LIVE-TEST:** Udstyret med tids-slider (1–72T), kun aktive ligaer i tidsrammen + 1-kliks `⚡ Tilvælg alle aktive ligaer` (blank fra start), favorit-administration, global holdsøgning med anti-dobbeltvalg af modstanderholdet (`kamp_id`), 1-kliks `⚡ TILFØJ ALLE KAMPE FRA VALGTE LIGAER`, individuelle flueben pr. kuponvalg med live beregning af odds, `%`-vinderchance, stjerner (`⭐`), risikoflammer (`🔥`) og aktiv "Spillet"-godkendelse til Supabase (11. nov 2026 kl. 10:52).

## 📋 Kommende Opgaver
- [ ] **Mappe 3 (`odds_motor/billed_parser.py`):** Mønstergenkendelse af bookmaker-screenshots + interaktiv mørk kuponstamme med ret/tilføj-strategi og "Spillet"-godkendelse.
- [ ] **Mappe 4 (`/historik` & Supabase Cloud):** Ret `st.secrets` konfigurationen, automatisk årsregnskab (år for år), hitrate (%), permanent TOTAL-SUM og bagudkompatibel CSV/Excel/SQLite-import.
- [ ] **Selvlærende Live- & Historik-Hjerne:** Opsamling af holdopstillinger, offsides og målspark (inkl. sæson 25/26) til løbende værdioptimering.

## 💡 Ønskeliste & Arkitektur-idéer (Gemt til senere)
- [ ] **Automatisk ESPN Liga-Discovery:** Dynamisk hentning af samtlige aktive turnerings-slugs direkte fra ESPNs API, så nye ligaer aldrig kræver manuel tilføjelse i `SLUGS`.
- [ ] **Ekstra udvidelsesmappe til Mappe 1 (`udvidelser/`):** Eventuelle fremtidige ekstra-funktioner til Autopilot-scanneren bygges som modul i `udvidelser/`, så den godkendte `autopilot_scanner.py` og låste `app.py` forbliver urørte.
