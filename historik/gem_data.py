import streamlit as st
import sqlite3
from resultat_tjekker import opdater_historik
from historik.gem_data import push_database_til_github, initier_database

st.set_page_config(page_title="AI Kupon-Historik & Statistik", page_icon="📈", layout="centered")

st.title("📈 AI Kupon-Historik & Statistik")
st.write("Her kan du se alle dine gemte AI-kuponer og følge robottens langsigtede succesrate.")

# --- BETA KONTROLRUM TIL LANGTIDSHUKOMMELSE ---
with st.sidebar:
    st.header("⚙️ Robot Beta-Kontrol")
    if st.button("🔌 Test Cloud-Synkronisering", type="secondary", use_container_width=True):
        initier_database()  # Sikrer at databasen eksisterer lokalt
        succes, besked = push_database_til_github()
        if succes:
            st.success(besked)
        else:
            st.error(besked)

# --- BEVARER AUTO-RAPPORTEN I TOPPEN ---
opdater_historik.vis_auto_resultat_og_rapport()

st.write("---")
st.subheader("📋 Liste over dine gemte AI Kuponer")

try:
    conn = sqlite3.connect("odds_pro_hukommelse.db")
    cursor = conn.cursor()
    cursor.execute("SELECT dato, ligaer, forslag, bookmaker_odds, anbefalet_side, status, styrke_stjerner FROM kupon_historik ORDER BY id DESC")
    rækker = cursor.fetchall()
    conn.close()
    
    if not rækker:
        st.info("Ingen gemte kuponer fundet i databasen endnu. Generer en kupon på appen for at starte historikken!")
    else:
        for r in rækker:
            dato, ligaer, forslag, bookmaker_odds, side, status, stjerner = r
            status_visning = "🟢 Vundet" if status == "Vundet" else "🔴 Tabt" if status == "Tabt" else "⏳ Afventer"
            stjerner_visning = "⭐" * int(stjerner) if stjerner else ""
            
            with st.expander(f"📅 {dato} - {status_visning} {stjerner_visning}"):
                st.write(f"🏆 **Anbefalet bookmaker:** {side}")
                st.write(f"📊 **Odds på tværs af markedet:** `{bookmaker_odds}`")
                st.write("---")
                
                kampe_liste = ligaer.split(", ")
                forslag_liste = forslag.split("; ")
                st.write("⚽ **Dine aktive kampe & spil:**")
                for i in range(len(kampe_liste)):
                    kamp_navn = kampe_liste[i] if i < len(kampe_liste) else "Ukendt kamp"
                    spil_navn = forslag_liste[i] if i < len(forslag_liste) else "Ukendt spil"
                    st.markdown(f"**{kamp_navn}** ➔ `{spil_navn}`")

except Exception as e:
    st.info("🧠 Hukommelsen initialiseres. Generer din første kupon på appen for at aktivere databasetabellerne.")
