# 🗺️ Odds-Robot-Pro: Dynamisk Roadmap & Ønskeliste
**Senest opdateret:** Tirsdag d. 10. november 2026 kl. 22:00 (Dansk tid)

## ✅ Gennemførte Milepæle
- [x] **Låst forside (`app.py`):** 100 % isoleret modulær indlæsning etableret.
- [x] **Dansk tidsstyring (`tidsstyring/dansk_tid.py`):** Synkroniseret med `Europe/Copenhagen`.
- [x] **Favoritligaer (`odds_motor/liga_favoritter.py`):** Standardligaer + automatisk navnenormalisering.
- [x] **Mappe 1 (`odds_motor/autopilot_scanner.py`):** Opgraderet med `_hent_kampe_v8` (kombineret direkte slug-opslag + globalt `all`-feed uden forkert liganavns-kollision) samt lyn-flueben for **"☑️ Vælg alle aktive ligaer"** og **"☑️ Vælg alle kampe"** (10. nov 2026 kl. 22:00).

## 🚧 Aktuelt Fokus (I gang)
- [ ] **Verificering af Mappe 1 live:** Godkend `odds_motor/autopilot_scanner.py` live på Streamlit (tjek at Brasilien Serie B, UEFA Nations League, Copa del Rey m.fl. står med rigtigt navn og at fluebenene tømmer/fylder boksene med ét klik).
- [ ] **Mappe 2 (`odds_motor/manuel_scanner.py`):** Byg manuel kampvælger med blanke felter fra start, global holdsøgning, %-vinderchance, stjerner og risikoflammer (🔥).

## 📋 Kommende Opgaver
- [ ] **Mappe 3 (Billed-Scanner):** Mønstergenkendelse af bookmaker-screenshots + interaktiv mørk kuponstamme med ret/tilføj-strategi og "Spillet"-godkendelse.
- [ ] **Mappe 4 (`/historik` & Supabase Cloud):** Ret `st.secrets` konfigurationen, automatisk årsregnskab (år for år), hitrate (%), permanent TOTAL-SUM og bagudkompatibel CSV/Excel/SQLite-import.
- [ ] **Selvlærende Live- & Historik-Hjerne:** Opsamling af holdopstillinger, offsides og målspark (inkl. sæson 25/26) til løbende værdioptimering.

## 💡 Ønskeliste & Arkitektur-idéer (Gemt til senere)
- [ ] **Automatisk ESPN Liga-Discovery:** Dynamisk hentning af samtlige aktive turnerings-slugs direkte fra ESPNs API, så nye ligaer aldrig kræver manuel tilføjelse i `SLUGS`.
