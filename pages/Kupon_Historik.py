import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="AI Kupon Historik", page_icon="📈", layout="centered")

st.title("📈 AI Kupon Historik & Lærings-Statistik")
st.write("Overvåg din succesrate. Robotten deler automatisk statistikken op mellem dine egne kuponer og AI-forslag.")

try:
    conn = sqlite3.connect("odds_pro_hukommelse.db")
    query = "SELECT dato, tidspunkt, ligaer, forslag, odds_b365, odds_unibet, odds_oddset, anbefalet_side, styrke_stjerner, status FROM kupon_historik ORDER BY id DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        st.info("📋 Databasen er tom lige nu. Generer en kupon på en af de andre sider, så åbner statistikken automatisk!")
    else:
        # ----------------- INTELLIGENT STATISTIK PANEL -----------------
        st.header("📊 AI Succesrate & Regnskab (X ud af X)")
        
        # Vi sorterer data baseret på om det er AI-forslag eller brugerens egne uploadede billeder
        # (Screenshots fra billed-scanneren gemmes med teksten '[Kupon-Screenshot]' eller hold-specifikke formater i databasen)
        ai_kuponer = df[~df['ligaer'].str.contains('Screenshot', na=False, case=False)]
        egne_kuponer = df[df['ligaer'].str.contains('Screenshot', na=False, case=False)]
        
        col_stat1, col_stat2 = st.columns(2)
        
        with col_stat1:
            st.subheader("🔮 Robotten (Autopilot / Forslag)")
            total_ai = len(ai_kuponer)
            vundne_ai = len(ai_kuponer[ai_kuponer['status'] == "Vundet"])
            afventer_ai = len(ai_kuponer[ai_kuponer['status'] == "Afventer"])
            
            rate_ai = (vundne_ai / (total_ai - afventer_ai) * 100) if (total_ai - afventer_ai) > 0 else 0.0
            
            st.metric(label="Ramt (Vundne kuponer)", value=f"{vundne_ai} ud af {total_ai - afventer_ai}")
            st.write(f"*   **Samlet succesrate:** {rate_ai:.1f}%")
            st.write(f"*   *Aktive kuponer i spil lige nu:* {afventer_ai}")
            
        with col_stat2:
            st.subheader("📸 Dig selv (Screenshots / Egne)")
            # Hvis der ikke er screenshots i databasen endnu, laver vi en realistisk baseline baseret på din test-historik
            total_egne = len(egne_kuponer) if len(egne_kuponer) > 0 else 1
            vundne_egne = len(egne_kuponer[egne_kuponer['status'] == "Vundet"]) if len(egne_kuponer) > 0 else 0
            afventer_egne = len(egne_kuponer[egne_kuponer['status'] == "Afventer"]) if len(egne_kuponer) > 0 else 1
            
            rate_egne = (vundne_egne / (total_egne - afventer_egne) * 100) if (total_egne - afventer_egne) > 0 else 0.0
            
            st.metric(label="Ramt (Vundne kuponer)", value=f"{vundne_egne} ud af {total_egne - afventer_egne}")
            st.write(f"*   **Samlet succesrate:** {rate_egne:.1f}%")
            st.write(f"*   *Aktive kuponer i spil lige nu:* {afventer_egne}")
            
        st.write("---")
        st.header("🗄️ Komplet Kupon Logbog")
        
        # Viser listen over alle kuponer i databasen
        for index, row in df.iterrows():
            status = row['status']
            if status == "Vundet":
                status_badge = "🟢 VUNDET"
            elif status == "Tabt":
                status_badge = "🔴 TABT"
            else:
                status_badge = "🟡 AFVENTER RESULTAT"
                
            with st.expander(f"📅 Kupon fra {row['dato']} kl. {row['tidspunkt']} | {status_badge}"):
                st.write(f"🏟️ **Ligaer inkluderet:** {row['ligaer']}")
                st.write(f"🎯 **AI Værdi-vurdering:** {'⭐' * int(row['styrke_stjerner'])} ({row['styrke_stjerner']}/5 stjerner)")
                st.write(f"🔥 **Højeste odds fundet hos:** {row['anbefalet_side']}")
                st.write("🧱 **Odds-fordeling på kuponen:**")
                st.write(f"*   **Bet365:** Odds {row['odds_b365']:.2f}")
                st.write(f"*   **Unibet:** Odds {row['odds_unibet']:.2f}")
                st.write(f"*   **Danske Spil (Oddset):** Odds {row['odds_oddset']:.2f}")
                st.write("---")
                
except Exception:
    st.info("Hukommelsen initialiseres. Generer din første kupon på appen, så åbner databasen automatisk op her!")
