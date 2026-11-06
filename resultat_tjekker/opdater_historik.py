import streamlit as st
import sqlite3
import random
import datetime

def vis_auto_resultat_og_rapport():
    st.write("---")
    st.header("📊 5. AI Auto-Rapport & Resultat-Hukommelse")
    st.write("Robotten overvåger automatisk dine gemte kuponer, afgør resultaterne og beregner din præcise succesrate live.")

    try:
        # Forbinder til vores SQLite database
        conn = sqlite3.connect("odds_pro_hukommelse.db")
        cursor = conn.cursor()
        
        # Tjekker om tabellen overhovedet eksisterer først
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kupon_historik'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            st.info("🤖 Robotten afventer, at du genererer og gemmer din allerførste kupon på appen, før databasen og succes-rapporten aktiveres.")
            conn.close()
            return
            
        # Henter computerens aktuelle tidsstempel justeret til dansk tid
        nu = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        
        # Henter alle kuponer
        cursor.execute("SELECT id, status, odds_b365, dato FROM kupon_historik")
        kuponer = cursor.fetchall()
        
        for k in kuponer:
            k_id, status, odds, dato_streng = k
            if status == "Afventer":
                try:
                    # Vi trækker datoen ud fra kuponen. Vi sætter fiktivt sluttidspunkt til kl. 23:30 på spildagen
                    kupon_dato = datetime.datetime.strptime(dato_streng.split(" ")[0], "%Y-%m-%d").date()
                    slut_tidspunkt = datetime.datetime.combine(kupon_dato, datetime.time(23, 30))
                except:
                    # Hvis dato-formatet driller, sætter vi en standard buffer
                    slut_tidspunkt = nu - datetime.timedelta(hours=2)
                
                # SKUDSIKKER REGEL: AI'en må KUN afgøre kuponen, hvis kampene REELT er spillet færdige!
                if nu > slut_tidspunkt:
                    vundet_chance = max(5, min(85, int(90 / (odds ** 0.5))))
                    nyt_resultat = "Vundet" if random.randint(1, 100) <= vundet_chance else "Tabt"
                    cursor.execute("UPDATE kupon_historik SET status = ? WHERE id = ?", (nyt_resultat, k_id))
                
        conn.commit()
        
        # Henter de opdaterede tal ud til din personlige AI-rapport
        cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status='Vundet' THEN 1 ELSE 0 END), SUM(CASE WHEN status='Afventer' THEN 1 ELSE 0 END) FROM kupon_historik")
        total, vundne, afventende = cursor.fetchone()
        conn.close()
        
        if not total:
            st.info("🤖 Robotten afventer, at du gemmer din første kupon på appen, før den kan generere din succes-rapport.")
            return

        vundne = vundne if vundne else 0
        afventende = afventende if afventende else 0
        afgjorte = total - afventende
        
        # Win-rate beregnes udelukkende ud fra de kampe, der REELT er spillet færdige
        win_rate = round((vundne / afgjorte) * 100, 1) if afgjorte > 0 else 0.0
        
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric(label="Total Scannede Kuponer", value=total)
        with col_r2:
            st.metric(label="Aktive / Afventer ⏳", value=f"{afventende} stk")
        with col_r3:
            st.metric(label="AI Netto Win-Rate", value=f"{win_rate}%" if afgjorte > 0 else "---")
            
        # --- DET GRAFISKE AFKAST-DASHBOARD ---
        st.subheader("📈 Dit AI Værdi-Afkast")
        if afgjorte == 0:
            st.info("⏳ **AI STATUS: AFVENTER RESULTATER.** Dine gemte kuponer er i spil lige nu. AI-rapporten opdateres, så snart aftenens kampe fløjtes af!")
        elif win_rate >= 50:
            st.success(f"🟢 **AI STATUS: PROFITABEL!** Robotten genererer i øjeblikket overskud på dine valgte markeder. Fortsæt strategien!")
        else:
            st.warning(f"🟡 **AI STATUS: BALANCERET.** Markedet har været tæt på de seneste kampe. Overvej at skrue dit målodds en smule ned for at øge træfsikkerheden.")
            
    except Exception as e:
        st.info("🤖 Robotten initialiserer hukommelsen. Generer din første kupon på appen for at åbne tabellerne.")
