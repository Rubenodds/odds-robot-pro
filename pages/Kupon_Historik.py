import streamlit as st
import sqlite3
from resultat_tjekker import opdater_historik

st.set_page_config(page_title="AI Kupon-Historik & Statistik", page_icon="📈", layout="centered")

st.title("📈 AI Kupon-Historik & Statistik")
st.write("Her kan du se alle dine gemte AI-kuponer og følge robottens langsigtede succesrate.")

# --- NYT: TRÆKKER AUTOMATISK DIN AUTO-RAPPORT IND I TOPPEN ---
opdater_historik.vis_auto_resultat_og_rapport()

st.write("---")
st.subheader("📋 Liste over dine gemte AI Kuponer")

# Henter den fulde liste ud af SQLite-databasen
try:
    conn = sqlite3.connect("odds_pro_hukommelse.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT dato, ligaer, forslag, odds_b365, anbefalet_side, status FROM kupon_historik ORDER BY id DESC")
    rækker = cursor.fetchall()
    conn.close()
    
    if not rækker:
        st.info("Ingen gemte kuponer fundet i databasen endnu. Generer en kupon på appen for at starte historikken!")
    else:
        for r in rækker:
            dato, ligaer, forslag, odds, side, status = r
            
            # Flot farvekode baseret på kampens status
            if status == "Vundet": status_visning = "🟢 Vundet"
            elif status == "Tabt": status_visning = "🔴 Tabt"
            else: status_visning = "⏳ Afventer"
            
            with st.expander(f"📅 Kupon fra {dato} - Odds: {odds:.2f} ({status_visning})"):
                st.write(f"🏆 **Anbefalet bookmaker:** {side}")
                st.write(f"⚽ **Aktive ligaer:** {ligaer}")
                st.write("🧱 **Robottens sammensatte forslag:**")
                
                # Splitter forslagene op, så de står som en flot liste
                for f in forslag.split(", "):
                    st.write(f" ➔ {f}")
except Exception as e:
    st.info("🧠 Hukommelsen initialiseres. Generer din første kupon på appen for at aktivere databasetabellerne.")
