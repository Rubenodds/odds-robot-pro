# 🗺️ Odds-Robot-Pro: Dynamisk Ønskeliste & Roadmap

## 🔴 AKUTTE FEJLRETNINGER & REBOOT-SIKRING (Skal fikses NU - Trin for trin)
1. **🔒 REDNING AF API & DATABASE-TOKEN (Absolut første skridt):** Det tidligere oprettede API-token og database-integration skal lokaliseres, rettes og aktiveres. Appen må under INGEN omstændigheder miste historik eller nulstille databasen ved reboot/genstart. 
2. **🔎 100% SYSTEM-AUDIT (Gøres umiddelbart efter database-fix):** Når data-lagringen er 100% stabil ved genstart, SKAL vi stoppe op. Vi skal tjekke og verificere HELE appens indhold skridt for skridt (Hold-Scanner, Kupon-Scanner, tidsstyring og ligaer), før der overhovedet må bygges nye funktioner.
3. **📌 FASTLÅSNING AF UDGANSPUNKT:** Efter system-auditten noterer vi præcist i denne fil, at ALT virker efter dit ønske, og hvordan det virker. Dette danner en permanent "Notits om stabilt udgangspunkt", så vi ALTID kan rulle tilbage til dette præcise punkt, hvis noget fejler senere.
4. **📸 Billed-håndtering & Odds-parsing i Kupon-Scanner:** Få rettet OCR på screenshots (fx Viborg, Tottenham, Norwich), så den læser de reelle tal og retter til de rigtige odds i stedet for at bruge et cachet test-eksempel.
5. **🧹 Ryd op i Hold-Scanner:** Input-kasserne skal starte 100% blanke uden forvirrende AI-hallucinationer (spøgelses-markeder).

## 🧠 UROKKELIGE SYSTEM-MÅL (Missionen & Den Selvlærende Hjerne)
- **Universal Bookmaker-Agnostik (Krav 6):** Ingen hardkodede navne på spilsider. Alt skal parses via dynamisk mønstergenkendelse.
- **Den Ultimative Spil-Hjerne (Selvlærende data):** Robotten skal akkumulere og blive klogere på ALT, der kan bettes på: Resultater, offsides, målspark, kort, hjørnespark osv. Alt skal lagres struktureret for at bygge maksimale værdi-kuponer.

## 📊 ØKONOMI & STATISTIK (Ny mappe - Bygges efter den fulde audit)
- **Hitrate & Avanceret Årsregnskab Modul:** Der skal oprettes en helt ny mappe i kodebasen, som kodes direkte sammen med robottens hitrate (succesrate i %).
- **Dynamisk Indsats-Scanner (100 kr. reglen):** 
  - Hvis robotten *ikke* kan se eller læse det spillede beløb på kuponen, skal den automatisk sætte indsatsen til **100 kr.** som standard.
  - Hvis robotten *kan* se beløbet, skal den bruge det reelle beløb og automatisk trække/lægge det til i årsregnskabet.
- **Tidssynkroniseret Regnskab:** Regnskabet skal køre skarpt opdelt år for år (fx regnskabsperioden 2026/2027 starter nu).
- **Akkumuleret Total-Sum:** Systemet skal automatisk gemme og ligge tallene fra alle år sammen, så der altid vises en samlet total-sum over robottens levetid.

---

## ✅ UDFØRTE OPGAVER & HISTORIK

### 📅 Søndag d. 8. november 2026
*   **Kl. 22:50 - Opgradering af System-Regler til AI:** 
    *   *Hvad blev gjort:* Tilføjet Krav 6 (Universal Bookmaker-Agnostik), Krav 7 (Selvlærende Data-Akkumulering), Krav 8 (Pro-aktiv AI-Optimering & Modspil) og Krav 9 (Dynamisk Roadmap-Pligt).
    *   *Resultat:* AI Master-Reboot panelet i `ai_kontrolrum/system_regler.py` er opdateret, så fremtidige AI-modeller tvinges til at læse denne ønskeliste og udfordre koden proaktivt.
*   **Kl. 23:02 - Etablering af Fysisk Log-Hukommelse (`onskeliste_roadmap.md`):**
    *   *Hvad blev gjort:* Oprettet denne roadmap-fil i `ai_kontrolrum/` indeholdende de rå og urokkelige ønsker om total-dataopsamling, nul datatab ved reboots og det avancerede årsregnskab.
*   **Kl. 23:25 - Fastlåsning af Rækkefølge (Trin 1: Database-fix, Trin 2: Fuld System-Audit):**
    *   *Hvad blev gjort:* Tilføjet den absolutte betingelse om, at database-API'en skal virke først, og at intet nyt må kodes, før hele appen er testet igennem skridt for skridt.
*   **Kl. 23:30 - Integration af Regnskabs-Logik & Udgangspunkter:**
    *   *Hvad blev gjort:* Tilføjet 100 kr.-reglen, det tidssynkroniserede årsregnskab (2026/2027) + totalsum, samt reglen om altid at lave en fastlåst "Notits om stabilt udgangspunkt".
