# 🗺️ Odds-Robot-Pro: Dynamisk Ønskeliste & Roadmap

## 🔴 AKUTTE FEJLRETNINGER & REBOOT-SIKRING (Skal fikses NU - Trin for trin)
1. **🔒 MIGRERING TIL PERMANENT CLOUD-DATABASE (Højeste Prioritet):** GitHub API-synkroniseringen blokerer for lagring. Vi skal skifte fra lokal SQLite til en ekstern gratis Cloud-database (fx Supabase), så data overlever reboots uden fil-konflikter.
2. **🔎 100% SYSTEM-AUDIT:** Tjekke og verificere HELE appens indhold skridt for skridt (Hold-Scanner, Kupon-Scanner, tidsstyring og ligaer).
3. **📌 FASTLÅSNING AF UDGANSPUNKT:** Fastlægge en permanent "Notits om stabilt udgangspunkt".

---

## ✅ UDFØRTE OPGAVER & HISTORIK

### 📅 Mandag d. 9. november 2026
*   **Kl. 15:30 - Analyse af GitHub API Lagrings-blokering:**
    *   *Udfordring:* Testen viste, at synkronisering via GitHub API blokerer for den primære lagring og fejler. SQLite-filer på Streamlit Cloud er konstateret ustabile.
    *   *Beslutning:* Skift af strategi til en dedikeret ekstern cloud-database for at sikre 100% urokkelig hukommelse.
