# 🗺️ Odds-Robot-Pro: Urokkeligt Master-Regelsæt & Fejlretning

## 🔒 FASTLÅSTE SYSTEM-REGLER & LOGIK (Må ALDRIG ændres)
1. **app.py er 100% låst:** Ingen ændringer i hovedfilen. Alt kodes i undermapper.
2. **Bookmaker-Agnostik:** Ingen hardkodede navne. Alt parses via mønstre.
3. **Permanent Hukommelse:** Supabase Cloud er robottens eneste hjerne.
4. **Indsats-Logik:** Standardindsats på 100 kr., hvis beløbet ikke ses på kuponen.
5. **Årsregnskab & Økonomi-Log:** Knivskarpt regnskab år for år + en permanent TOTAL-SUM.
6. **Statistisk Total-Indsigt:** Opsamling og læring af holdopstillinger, offsides, målspark osv.

## 🔴 AKUTTE FEJLRETNINGER (Trin for trin)

### 📸 TRIN 1: Billed-Scanner & Odds-Parsing (Kupon_Scanner.py)
- **Fejl:** Scanneren læser ikke det reelle billede ind korrekt og retter ikke oddsene til de rigtige tal. Den falder i stedet tilbage på gamle cacher/testdata.
- **Krav:** OCR-motoren skal trække råtekst ud, identificere holdene på kuponen, matche dem med de rigtige odds og spytte den rigtige mørke kuponstamme ud efter den kortest mulige kodelogik.

### 📊 TRIN 2: Visning af Historik (opdater_historik.py)
- **Fejl:** Kuponerne lander i forkerte mapper, og historik-siden viser cachet SQLite-fejl ved reboot.
- **Krav:** `vis_auto_resultat_og_rapport()` skal omskrives til at hente live-historik ud af Supabase.

---

## ✅ UDFØRTE OPGAVER & HISTORIK

### 📅 Mandag d. 9. november 2026
*   **Kl. 16:04 - API HTTP Rest-sikring implementeret i historikken:** Omskrevet `resultat_tjekker/opdater_historik.py` til rå HTTP POST-kald.
*   **Kl. 16:29 - Eliminering af 'random' i beregningsmotoren (`byg_kupon.py` UDFØRT):** Implementeret en reel margin-neutraliseret odds-konverteringsalgoritme.
*   **Kl. 16:34 - Lovfæstet Ufravigelig Matematisk Integritet (Krav 10 UDFØRT):** Forbud mod falske tilfældighedsgeneratorer tilføjet.
*   **Kl. 16:36 - Fuldendelse af Master-Regler med Historisk Data-Import (Krav 12 UDFØRT):** Sikring af historisk data-kompatibilitet.
*   **Kl. 16:40 - 🔒 Eksplicit Fredning af Roadmap-loggen (Krav 13 OPGRADERET):**
    *   *Hvad blev gjort:* Krav 13 i `system_regler.py` er blevet skærpet yderligere, så koderod renses i undermapperne, mens `onskeliste_roadmap.md` erklæres 100% beskyttet mod sletning.
