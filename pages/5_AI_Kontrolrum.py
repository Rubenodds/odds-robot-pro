import streamlit as st
from ai_kontrolrum import system_regler

st.set_page_config(page_title="AI Live Kontrolrum", page_icon="⚙️", layout="centered")

st.title("⚙️ AI Live Kontrolrum & Regelsæt")
st.write("Her kan du se og kopiere robottens aktive systemregler, prompts og hukommelses-arkitektur.")

# Kalder funktionen fra din nye undermappe, som spytter koden ud i en lukket boks med kopi-ikon
system_regler.vis_aktuelle_system_regler()
