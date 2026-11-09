import streamlit as st

st.set_page_config(page_title="Hold Scanner Pro", page_icon="⚽", layout="wide")

st.title("⚽ 1. Vælg hold manuelt og bestem robot-væddemål")
st.subheader("Her styrer du præcis, hvilke kampe robotten skal bygge kuponer på.")

# FASTLÅSTE SYSTEM MARKEDER - Parentes lukket korrekt her:
markeder_pro = [
    "Fuldtid - Resultat",
    "Begge hold scorer",
    "Over/Under Mål",
    "Cifre"
]

st.write("### Aktive specialmarkeder indlæst:")
for marked in markeder_pro:
    st.info(f"✓ {marked}")

# TODO: Indlæs dagens kampprogram via undermapper.hent_kampe herunder
st.warning("Marker de hold du ønsker at fastlåse til din næste kuponbygning.")
