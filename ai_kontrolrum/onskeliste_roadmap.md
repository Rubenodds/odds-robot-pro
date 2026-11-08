# 🗺️ Odds-Robot-Pro: Dynamisk Ønskeliste & Roadmap

## 🔴 AKUTTE FEJLRETNINGER (Skal fikses NU)
- **Fiks `TypeError` i `app.py` (Linje 134):** `gem_data.gem_kupon_i_historik` crasher på None-type/forkert format under lagring. Skal kodes robust i undermodulet uden at røre app.py.
- **Fjern "spøgelses-markeder" i Hold-Scanner:** Databasetabellerne spytter forvirrende AI-hallucinationer ud. Input-kasserne SKAL starte 100% blanke.
- **Rigtig billed-håndtering i Kupon-Scanner:** Få rettet OCR/parsing på råteksten fra scannet kupon (Viborg, Tottenham, Norwich), så systemet ikke falder tilbage på et cachet FCK-eksempel.

## 🧠 UROKKELIGE SYSTEM-MÅL (Missionen)
- **Universal Bookmaker-Agnostik (Krav 6):** Ingen hardkodede navne på spilsider. Alt skal parses via dynamisk mønstergenkendelse.
- **Selvlærende Data-Akkumulering (Krav 7):** Alt historisk data og scanningsresultater skal gemmes struktureret, så robotten kan generere mere sikre kuponer.
- **Live Statistik-Dashboard:** Automatisk opdatering af succesrate (%) live i appen, når en spildag afgøres.

---

## ✅ UDFØRTE OPGAVER & HISTORIK

### 📅 Søndag d. 8. november 2026
*   **Kl. 22:50 - Opgradering af System-Regler til AI:** 
    *   *Hvad blev gjort:* Tilføjet Krav 6 (Universal Bookmaker-Agnostik), Krav 7 (Selvlærende Data-Akkumulering), Krav 8 (Pro-aktiv AI-Optimering & Modspil) og Krav 9 (Dynamisk Roadmap-Pligt).
    *   *Resultat:* AI Master-Reboot panelet i `ai_kontrolrum/system_regler.py` er opdateret, så fremtidige AI-modeller tvinges til at læse denne ønskeliste og udfordre koden proaktivt.
*   **Kl. 23:02 - Etablering af Fysisk Log-Hukommelse (`onskeliste_roadmap.md`):**
    *   *Hvad blev gjort:* Oprettet denne roadmap-fil i `ai_kontrolrum/` for at modvirke AI-amnesi ved reboots.
