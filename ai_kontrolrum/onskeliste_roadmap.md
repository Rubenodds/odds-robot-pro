# 🗺️ Odds-Robot-Pro: Urokkeligt Master-Regelsæt & Fejlretning

## 🔒 FASTLÅSTE SYSTEM-REGLER & LOGIK (Må ALDRIG ændres)
1. **app.py er 100% låst:** Ingen ændringer i hovedfilen. Alt kodes i undermapper.
2. **Bookmaker-Agnostik:** Ingen hardkodede navne. Alt parses via mønstre.
3. **Permanent Hukommelse:** Supabase Cloud er robottens eneste hjerne.
4. **Indsats-Logik:** Standardindsats på 100 kr., hvis beløbet ikke ses på kuponen.
5. **Årsregnskab:** Data opdeles år for år (fx 2026/2027) + en permanent TOTAL-SUM.

## 🔴 AKUTTE FEJLRETNINGER (Trin for trin)

### 📸 TRIN 1: Billed-Scanner & Odds-Parsing (Kupon_Scanner.py)
- **Fejl:** Scanneren læser ikke det reelle billede ind korrekt og retter ikke oddsene til de rigtige tal. Den falder i stedet tilbage på gamle cacher/testdata.
- **Krav:** OCR-motoren skal trække råtekst ud, identificere holdene på kuponen, matche dem med de rigtige odds og spytte den rigtige mørke kuponstamme ud.

### 📊 TRIN 2: Visning af Historik (opdater_historik.py)
- **Fejl:** Kuponerne lander i forkerte mapper, og historik-siden viser cachet SQLite-fejl ved reboot.
- **Krav:** `vis_auto_resultat_og_rapport()` skal omskrives til at hente live-historik ud af Supabase.

---

## ✅ UDFØRTE OPGAVER & HISTORIK

### 📅 Mandag d. 9. november 2026
*   **Kl. 16:04 - API HTTP Rest-sikring implementeret i historikken:** Omskrevet `resultat_tjekker/opdater_historik.py` til rå HTTP POST-kald.
*   **Kl. 16:29 - Eliminering af 'random' i beregningsmotoren (`byg_kupon.py` UDFØRT):**
    *   *Hvad blev gjort:* Al tilfældig lodtrækning (`random.uniform` / `random.randint`) er fuldstændig fjernet fra spil-beregneren. Implementeret en reel margin-neutraliseret odds-konverteringsalgoritme (`beregn_sandsynlighed_fra_odds`).
    *   *Resultat:* Robotten foretager nu en 100% ægte matematisk udregning af `%-vinderchance`, flammer og stjerner baseret på holdenes reelle markedsmæssige styrkeforhold på tværs af alle bookmakere.
