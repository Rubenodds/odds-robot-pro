# 🗺️ Odds-Robot-Pro: Dynamisk Ønskeliste & Roadmap

## 🔴 AKUTTE FEJLRETNINGER & REBOOT-SIKRING (Skal fikses NU)
- **🛑 STOP DATATAB VED REBOOT (Højeste Prioritet):** Appen må under INGEN omstændigheder glemme data, historik eller indstillinger, når Streamlit genstarter eller rebooter. API-integrationen, databasetokenet og SQLite-hukommelsen SKAL gøres 100% permanente og modstandsdygtige over for genstarter, så vi altid bevarer vores stabile udgangspunkt.
- **Fiks `TypeError` i `app.py` (Linje 134):** `gem_data.gem_kupon_i_historik` crasher på None-type/forkert format under lagring. Skal kodes robust i undermodulet uden at røre app.py.
- **Rigtig billed-håndtering og korrekte odds i Kupon-Scanner:** Få rettet OCR/parsing på råteksten fra det reelle uploadede screenshot (fx Viborg, Tottenham, Norwich). Robotten skal læse de faktiske tal og rette oddsene til de RIGTIGE odds i stedet for at falde tilbage på et cachet test-eksempel.
- **Fjern "spøgelses-markeder" i Hold-Scanner:** Databasetabellerne spytter forvirrende AI-hallucinationer ud (Billede 2,3,4). Input-kasserne SKAL starte 100% blanke.

## 🧠 UROKKELIGE SYSTEM-MÅL (Missionen & Den Selvlærende Hjerne)
- **Universal Bookmaker-Agnostik (Krav 6):** Ingen hardkodede navne på spilsider. Alt skal parses via dynamisk mønstergenkendelse.
- **Den Ultimative Spil-Hjerne (Selvlærende data):** Robotten skal akkumulere og blive klogere på ALT, der kan bettes på: Resultater, offsides, målspark, kort, hjørnespark osv. Alt skal lagres struktureret for at bygge maksimale værdi-kuponer.
- **System-Audit:** Når genstart-sikringen og scanneren virker, skal HELE appens eksisterende indhold tjekkes og verificeres skridt for skridt, før der bygges nye funktioner. Hver succesfuld milepæl fastlåses med en permanent "udgangspunkt-notits" i denne log.

## 📊 ØKONOMI & STATISTIK (Kommende Mappe)
- **Hitrate & Årsregnskab Modul:** Ny isoleret mappe koblet direkte med hitrate (%).
- **Automatisk Indsats-Logik:** Hvis scanneren IKKE kan se eller læse indsatsbeløbet på kuponen, skal robotten automatisk regne med en standardindsats på 100 kr. Hvis beløbet ER synligt, skal den registrere og bruge det specifikke beløb.
- **Tidssynkroniseret Regnskab:** Regnskabet skal køre år for år (f.eks. nyt regnskab starter for 2026, 2027 osv.), samtidig med at der føres en overordnet, akkumuleret TOTAL-SUM på tværs af alle år, som lægges sammen live.

---

## ✅ UDFØRTE OPGAVER & HISTORIK

### 📅 Søndag d. 8. november 2026
*   **Kl. 22:50 - Opgradering af System-Regler til AI:** 
    *   *Hvad blev gjort:* Tilføjet Krav 6 (Universal Bookmaker-Agnostik), Krav 7 (Selvlærende Data-Akkumulering), Krav 8 (Pro-aktiv AI-Optimering & Modspil) og Krav 9 (Dynamisk Roadmap-Pligt).
    *   *Resultat:* AI Master-Reboot panelet i `ai_kontrolrum/system_regler.py` er opdateret, så fremtidige AI-modeller tvinges til at læse denne ønskeliste og udfordre koden proaktivt.
*   **Kl. 23:02 - Etablering af Fysisk Log-Hukommelse (`onskeliste_roadmap.md`):**
    *   *Hvad blev gjort:* Oprettet denne roadmap-fil i `ai_kontrolrum/` indeholdende de rå og urokkelige ønsker om total-dataopsamling, nul datatab ved reboots og det avancerede årsregnskab.
