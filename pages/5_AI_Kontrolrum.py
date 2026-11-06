import streamlit as st

st.set_page_config(page_title="AI Live Kontrolrum", page_icon="⚙️", layout="centered")

st.title("⚙️ AI Live Kontrolrum & Regelsæt")
st.write("Her kan du se og kopiere robottens aktive systemregler, prompts og hukommelses-arkitektur.")

# --- HER LIGGER DINE SYSTEMREGLER DIREKTE SIKRET ---
regler_tekst = """# AI KONTROL-SYSTEM: ODDS ROBOT ELITE PRO
# ===================================================
# REGEL 1: 100% lokal opdatering af moduler i sub-mapper.
# REGEL 2: Forsiden (app.py) er låst, medmindre andet er aftalt.
# REGEL 3: Vinderchancer (%) og risikoflammer (flammer) skal altid udregnes.
# REGEL 4: Kupon-historikken skal tracke og gemme alle data lokalt i SQLite.
# REGEL 5: Kamp-tidsfiltre skal altid synkronisere direkte med det aktuelle ur.
"""

st.subheader("📋 Aktive Systemregler")
st.write("Klik på ikonet i øverste højre hjørne af boksen herunder for at kopiere alt:")

# Tegner den professionelle kodeboks med indbygget kopi-ikon
st.code(regler_tekst, language="python")
