import streamlit as st
import sqlite3
from resultat_tjekker import opdater_historik

st.set_page_config(page_title="AI Kupon-Historik & Statistik", page_icon="📈", layout="centered")

st.title("📈 AI Kupon-Historik & Statistik")
st.write("Her kan du se alle dine gemte AI-kuponer og følge robottens langsigtede succesrate.")

# --- AUTOMATION: KØRER DIT AUTOMATISKE DEEP-STATS API-TJEK I BAGGRUNDEN VED SIDE-INDLÆSNING ---
opdater_historik.afgoer_alle_afventende_kuponer_live()

# --- BEVARER 100%: TRÆKKER AUTOMATISK DIN AUTO-RAPPORT IND I TOPPEN ---
opdater_historik.vis_auto_resultat_og_rapport()

st.write("---")
st.subheader("📋 Liste over dine gemte AI Kuponer")

# Henter den fulde liste ud af SQLite-databasen ud fra den nye dynamiske struktur
try:
    conn = sqlite3.connect("odds_pro_hukommelse.db")
    cursor = conn.cursor()
    
    # Henter de korrekte kolonner (inklusive den nye bookmaker_odds og styrke_stjerner)
    cursor.execute("SELECT dato, ligaer, forslag, bookmaker_odds, anbefalet_side, status, styrke_stjerner FROM kupon_historik ORDER BY id DESC")
    rækker = cursor.fetchall()
    conn.close()
    
    if not rækker:
        st.info("Ingen gemte kuponer fundet i databasen endnu. Generer en kupon på appen for at starte historikken!")
    else:
        for r in rækker:
            dato, ligaer, forslag, bookmaker_odds, side, status, stjerner = r
            
            # Flot farvekode baseret på kampens status
            if status == "Vundet": status_visning = "🟢 Vundet"
            elif status == "Tabt": status_visning = "🔴 Tabt"
            else: status_visning = "⏳ Afventer"
            
            # Viser kuponen i en flot expander med stjerner direkte i titlen
            stjerner_visning = "⭐" * int(stjerner) if stjerner else ""
            with st.expander(f"📅 {dato} - {status_visning} {stjerner_visning}"):
                st.write(f"🏆 **Anbefalet bookmaker:** {side}")
                st.write(f"📊 **Odds på tværs af markedet:** `{bookmaker_odds}`")
                st.write("---")
                
                # Splitter dine kampe og forslag op, så they står parvis snorlige under hinanden
                kampe_liste = ligaer.split(", ")
                forslag_liste = forslag.split("; ")
                
                st.write("⚽ **Dine aktive kampe & spil:**")
                for i in range(len(kampe_liste)):
                    kamp_navn = kampe_liste[i] if i < len(kampe_liste) else "Ukendt kamp"
                    spil_navn = forslag_liste[i] if i < len(forslag_liste) else "Ukendt spil"
                    st.markdown(f"**{kamp_navn}** ➔ `{spil_navn}`")

except Exception as e:
    st.info("🧠 Hukommelsen initialiseres. Generer din første kupon på appen for at aktivere databasetabellerne.")
