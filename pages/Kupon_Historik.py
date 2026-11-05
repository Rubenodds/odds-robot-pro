import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="AI Kupon Historik", page_icon="📈", layout="centered")

st.title("📈 AI Kupon Historik & Læring")
st.write("Her kan du se alle de autopilot- og favoritkuponer, som robotten har gemt i sin database, samt status på dens AI-læring.")

st.header("🗄️ Din personlige kupon-database")

try:
    # Vi forbinder direkte til din SQLite-databasefil
    conn = sqlite3.connect("odds_pro_hukommelse.db")
    
    # Henter alle gemte kuponer ud, nyeste først
    query = "SELECT dato, tidspunkt, ligaer, odds_b365, odds_unibet, odds_oddset, anbefalet_side, styrke_stjerner, status FROM kupon_historik ORDER BY id DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        st.info("Databasen er tom lige nu. Gå til forsiden eller hold-scanneren og generer nogle kuponer, så dukker de op her med det samme!")
    else:
        st.write(f"📊 Robotten overvåger lige nu **{len(df)} gemte kuponer** i din historik:")
        st.write("---")
        
        for index, row in df.iterrows():
            # Farvekodning baseret på kuponens status
            status = row['status']
            if status == "Vundet":
                status_badge = "🟢 VUNDET"
            elif status == "Tabt":
                status_badge = "🔴 TABT"
            else:
                status_badge = "🟡 AFVENTER RESULTAT"
                
            # Opretter en flot visuel boks pr. kupon på telefonen
            with st.expander(f"📅 Kupon fra {row['dato']} kl. {row['tidspunkt']} | {status_badge}"):
                st.write(f"⚽ **Aktive ligaer:** {row['ligaer']}")
                st.write(f"🎯 **AI Værdi-vurdering:** {'⭐' * int(row['styrke_stjerner'])} ({row['styrke_stjerner']}/5 stjerner)")
                st.write(f"🔥 **Anbefalet bookmaker:** {row['anbefalet_side']}")
                
                st.write("🧱 **Sammenligning af odds på kuponen:**")
                st.write(f"*   **Bet365:** Odds {row['odds_b365']:.2f}")
                st.write(f"*   **Unibet:** Odds {row['odds_unibet']:.2f}")
                st.write(f"*   **Danske Spil (Oddset):** Odds {row['odds_oddset']:.2f}")
                st.write("---")
                
except Exception:
    st.info("Hukommelsen initialiseres. Generer din første kupon på appen, så åbner databasen automatisk op her!")
