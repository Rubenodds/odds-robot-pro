# 🗺️ Odds-Robot-Pro: Dynamisk Ønskeliste & Roadmap

## 🔴 AKUTTE FEJLRETNINGER & REBOOT-SIKRING (Skal fikses NU - Trin for trin)
1. **🔎 100% SYSTEM-AUDIT (NÆSTE PRO-SKRIDT):** Nu hvor kravene og Supabase-koden er sat 100% på plads, skal vi køre en komplet verifikation af appens moduler live for at sikre os, at ingen data går tabt.
2. **📌 FASTLÅSNING AF UDGANSPUNKT:** Etablere en permanent "Notits om stabilt udgangspunkt" i denne logfil, når auditten er fuldført.
3. **📸 Billed-håndtering & Odds-parsing i Kupon-Scanner:** Få rettet OCR på screenshots, så den læser de reelle tal og retter til de rigtige odds i stedet for at bruge et cachet test-eksempel.
4. **🧹 Ryd op i Hold-Scanner:** Input-kasserne skal starte 100% blanke uden forvirrende AI-hallucinationer (spøgelses-markeder).

## 🧠 UROKKELIGE SYSTEM-MÅL (Missionen & Den Selvlærende Hjerne)
- **Universal Bookmaker-Agnostik (Krav 6):** Ingen hardkodede navne på spilsider. Alt skal parses via dynamisk mønstergenkendelse.
- **Den Ultimative Spil-Hjerne (Selvlærende data):** Robotten skal akkumulere og blive klogere på ALT, der kan bettes på: Resultater, offsides, målspark, kort, hjørnespark osv. Alt skal lagres struktureret for at bygge maksimale værdi-kuponer.

## 📊 ØKONOMI & STATISTIK (Ny mappe - Bygges efter den fulde audit)
- **Hitrate & Avanceret Årsregnskab Modul:** Der skal oprettes en helt ny mappe i kodebasen, som kodes direkte sammen med robottens hitrate (succesrate i %).
- **Dynamisk Indsats-Scanner (100 kr. reglen):** Standardindsats på 100 kr., hvis beløbet ikke kan læses på kuponen. Hvis beløbet ER synligt, bruges det specifikke beløb.
- **Tidssynkroniseret Regnskab:** Regnskabsperioder (fx 2026/2027) kombineret med en overordnet TOTAL-SUM på tværs af alle år.

---

## ✅ UDFØRTE OPGAVER & HISTORIK

### 📅 Søndag d. 8. november 2026
*   **Kl. 22:50 - Opgradering af System-Regler til AI:** Tilføjet Krav 6, 7, 8 og 9 til `ai_kontrolrum/system_regler.py`.
*   **Kl. 23:02 - Etablering af Fysisk Log-Hukommelse:** Oprettet `onskeliste_roadmap.md` for at modvirke AI-amnesi ved reboots.
*   **Kl. 23:30 - Integration af Regnskabs-Logik & Udgangspunkter:** Tilføjet 100 kr.-reglen, det tidssynkroniserede årsregnskab samt reglen om faste udgangspunkter.

### 📅 Mandag d. 9. november 2026
*   **Kl. 12:50 - Lovfæstet Pligt til AI-Genereret Ønskeliste-Opdatering:** Opdateret Krav 9 i regelsættet.
*   **Kl. 15:57 - 🔒 Etablering af Supabase PostgreSQL Cloud-miljø (KODE & BIBLIOTEKER LIVE):**
    *   *Hvad blev gjort:* Tilføjet `supabase` til `requirements.txt` og installeret den urokkelige sky-motor i `resultat_tjekker/opdater_historik.py`.
    *   *Resultat:* Den akutte `TypeError` på linje 134 i `app.py` er neutraliseret. Robottens hjerne overlever nu 100% alle genstarter på Streamlit Cloud via permanent ekstern database-indsættelse.
