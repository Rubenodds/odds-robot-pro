# Odds-Robot-Pro: Urokkeligt Master-Regelsæt & Fejlretning

🔒 FASTLÅSTE SYSTEM-REGLER & LOGIK (Må ALDRIG ændres)

app.py er 100% låst: Ingen ændringer i hovedfilen. Alt kodes i undermapper.
Bookmaker-Agnostik: Ingen hardkodede navne. Alt parses via mønstre.
Permanent Hukommelse: Supabase Cloud er robottens eneste hjerne.
Indsats-Logik: Standardindsats på 100 kr., hvis beløbet ikke ses på kuponen.
Årsregnskab & Økonomi-Log: Knivskarpt regnskab år for år + en permanent TOTAL-SUM.
Statistisk Total-Indsigt: Opsamling og læring af holdopstillinger, offsides, målspark osv.

======================================================================
🗺️ DYNAMISK ROADMAP &ØNSKELISTE
======================================================================
*Status synkroniseret: Mandag d. 9. november 2026 kl. 22:43 (Dansk tid)*

### 📂 AKTUELT RE-BOOT SETUP & STATUS
1. 📁 **/tidsstyring (dansk_tid.py):** Dansk lokaltid via zoneinfo/normaltid. [LÅST & AKTIV]
2. 📁 **/kampprogram (hent_kampe.py):** Flydende net-feed for de 24 Flashscore-favoritligaer (Superliga, Betinia LIGA, CampoBet 2. Div, Championship, osv.) tilpasset time-filtre (3H til 48H). [SKAL GENOPBYGGES]
3. 📁 **/odds_motor (byg_kupon.py):** Kombi-motor baseret på reelle markedstal uden random. [LÅST]
4. 📁 **/historik (gem_data.py):** Robottens permanente sky-hjerne koblet direkte til Supabase REST API, som opsamler holdopstillinger, offsides, målspark og årsregnskab. [SKAL GENOPBYGGES]
5. 📁 **/pages (Hold_Scanner.py & Kupon_Scanner.py):**
   * *Mappe 1 (Autopilot):* Bred tidszone-scanner efter fastlagt odds-lag (44-50) med risikofaktorer og mørk kuponstamme.
   * *Mappe 2 (Manuel Hold-Scanner):* Blank fra start, søg hold frem for specifikke udfald, regner %-chance, stjerner og flammer (🔥).
   * *Mappe 3 (Billed-Scanner):* Visuel scanning med manuel rette- og gemmefunktion til skyen.

### 📝 NYE ØNSKER & FREMTIDIGE TILFØJELSER (Her tilføjer vi løbende)
* [ ] Tilføj status-indikator i Streamlit for at overvåge og forhindre frysninger midt i en chat.
* [ ] Udvidelse af de agnostiske mønster-parsere til at håndtere endnu flere obskure specialmarkeder.
