import streamlit as st
import sqlite3
from resultat_tjekker import opdater_historik

st.set_page_config(page_title="AI Kupon-Historik & Statistik", page_icon="📈", layout="centered")

st.title("📈 AI Kupon-Historik & Statistik")
st.write("Her kan du se alle dine gemte AI-kuponer og følge robottens live-succesrate.")

# --- AUTOMATION: KØRER AUTOMATISK DET NYE LIVE API-TJEK I BAGGRUNDEN VED INDLÆSNING ---
try:
    opdater_historik.afgoer_alle_afventende_kuponer_live()
except Exception:
    pass

st.write("---")
st.subheader("📋 Liste over dine scannede & live-fundne kuponer")

try:
    conn = sqlite3.connect("odds_pro_hukommelse.db")
    cursor = conn.cursor()
    cursor.execute("SELECT dato, ligaer, forslag, bookmaker_odds, anbefalet_side, status, styrke_stjerner FROM kupon_historik ORDER BY id DESC")
    rækker = cursor.fetchall()
    conn.close()
    
    if not rækker:
        st.info("Ingen gemte kuponer fundet endnu. Scan et screenshot eller kør Hold-Scanneren for at starte!")
    else:
        for r in rækker:
            dato, ligaer, forslag, bookmaker_odds, side, status, stjerner = r
            
            if status == "Vundet": status_visning = "🟢 Vundet"
            elif status == "Tabt": status_visning = "🔴 Tabt"
            else: status_visning = "⏳ Afventer"
            
            stjerner_visning = "⭐" * int(stjerner) if stjerner else ""
            
            # PRO SIKKER VISNING: Trækker de samlede odds sikkert ud til overskriften
            odds_visning = "Dynamisk"
            if bookmaker_odds:
                odds_visning = bookmaker_odds.split(': ')[-1] if ':' in bookmaker_odds else bookmaker_odds
                
            with st.expander(f"📅 {dato} — {status_visning} | Odds: {odds_visning} {stjerner_visning}"):
                st.write(f"🏆 **Anbefalet bookmaker-platform:** {side}")
                st.write(f"📊 **Registrerede odds på tværs af markedet:** `{bookmaker_odds}`")
                st.write("---")
                
                # SIKKER SPLIT: Sørger for at specialmarkederne printes fejlfrit ud linje for linje
                forslag_liste = forslag.split("; ") if forslag else []
                st.write("⚽ **Dine placerede spil & specialmarkeder:**")
                
                for spil in forslag_liste:
                    if spil.strip():
                        st.markdown(f"➔ `{spil.strip()}`")

except Exception as e:
    st.info("🧠 Hukommelsen initialiseres. Gem en kupon for at aktivere statistikken.")
