import streamlit as st
import os

st.set_page_config(page_title="AI Live Kontrolrum", page_icon="⚙️", layout="centered")

st.title("⚙️ AI Live Kontrolrum & Regelsæt")
st.write("Her kan du se og kopiere robottens aktive systemregler, prompts og hukommelses-arkitektur.")

st.subheader("📋 Aktive Systemregler (100% Dynamisk Opdateret)")
st.write("Klik på ikonet i øverste højre hjørne af boksen herunder for at kopiere alt:")

# HENTER DINE REGLER LIVE FRA FILEN INDE I MAPPEN System_regler.py
regler_sti = "ai_kontrolrum/system_regler.py"

if os.path.exists(regler_sti):
    with open(regler_sti, "r", encoding="utf-8") as f:
        aktuelle_regler = f.read()
else:
    # Backup-regler hvis filen læses under genstart
    aktuelle_regler = """# AI KONTROL-SYSTEM: ODDS ROBOT ELITE PRO
# ===================================================
# REGEL 1: 100% lokal opdatering af moduler i sub-mapper.
# REGEL 2: Forsiden (app.py) er låst, medmindre andet er aftalt.
# REGEL 3: Vinderchancer (%) og risikoflammer (flammer) skal altid udregnes.
# REGEL 4: Kupon-historikken skal tracke og gemme alle data lokalt i SQLite.
# REGEL 5: Kamp-tidsfiltre skal altid synkronisere direkte med det aktuelle ur.
"""

# Tegner den professionelle kodeboks med indbygget kopi-ikon, som nu opdaterer sig selv!
st.code(aktuelle_regler, language="python")
