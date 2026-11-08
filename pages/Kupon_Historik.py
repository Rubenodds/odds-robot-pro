import streamlit as st
import sqlite3
from resultat_tjekker import opdater_historik

st.set_page_config(page_title="AI Kupon-Historik & Statistik", page_icon="📈", layout="centered")

st.title("📈 AI Kupon-Historik & Statistik")
st.write("Her kan du følge din reelle hitrate og dykke ned i robottens historiske spildata.")

# Automatisk afgørelse i baggrunden ved side-indlæsning
try:
    opdater_historik.afgoer_alle_afventende_kuponer_live()
except Exception:
    pass

# Henter kuponer direkte fra SQLite-databasen
rækker = []
try:
    conn = sqlite3.connect("odds_pro_hukommelse.db")
    cursor = conn.cursor()
    cursor.execute("SELECT dato, ligaer, forslag, bookmaker_odds, anbefalet_side, status, styrke_stjerner FROM kupon_historik ORDER BY id DESC")
    rækker = cursor.fetchall()
    conn.close()
except Exception:
    st.info("Hukommelsen initialiseres. Gem en kupon for at oprette databasetabellerne.")

if not rækker:
    st.info("Ingen gemte kuponer fundet i databasen endnu.")
else:
    # Opdeler data i tre lister baseret på reel status
    afventende_kuponer = [r for r in rækker if r[5] not in ["Vundet", "Tabt"]]
    vundne_kuponer = [r for r in rækker if r[5] == "Vundet"]
    tabte_kuponer = [r for r in rækker if r[5] == "Tabt"]
    
    # Opretter knivskarpe, professionelle faner til visningen
    fane_afventer, fane_vundet, fane_tabt = st.tabs(["⏳ Afventer", "🟢 Vundne Spil", "🔴 Tabte Spil"])
    
    def tegn_kupon_liste(pulje):
        if not pulje:
            st.write("*Ingen kuponer i denne kategori.*")
            return
        for r in pulje:
            dato, ligaer, forslag, bookmaker_odds, side, status, stjerner = r
            stjerner_visning = "⭐" * int(stjerner) if stjerner else ""
            
            odds_tekst = bookmaker_odds.split(': ')[-1] if ':' in str(bookmaker_odds) else str(bookmaker_odds)
            
            with st.expander(f"📅 {dato} | Odds: {odds_tekst} {stjerner_visning}"):
                st.markdown(f"**Platform:** `{side}`")
                st.markdown(f"**Markeds-odds:** `{bookmaker_odds}`")
                st.write("---")
                st.write("⚽ **Placerede specialmarkeder & spil:**")
                for spil in forslag.split("; "):
                    if spil.strip():
                        st.markdown(f"➔ `{spil.strip()}`")

    with fane_afventer:
        tegn_kupon_liste(afventende_kuponer)
        
    with fane_vundet:
        tegn_kupon_liste(vundne_kuponer)
        
    with fane_tabt:
        tegn_kupon_liste(tabte_kuponer)
