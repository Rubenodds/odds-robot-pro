import streamlit as st
import datetime
import random
from tidsstyring import dansk_tid
from kampprogram import hent_kampe
from odds_motor import byg_kupon

st.set_page_config(page_title="AI Favorit-Hold Scanner", page_icon="🎯", layout="centered")

st.title("🎯 AI Favorit-Hold Scanner")
st.write("Søg og vælg specifikke hold, du vil have robotten til at analysere special-markeder på.")

# Henter den præcise tid og det fælles kampprogram
nu = dansk_tid.hent_dansk_klokkeslaet()
alle_kampe = hent_kampe.hent_aegte_kampe_fra_nettet()

# Backup hvis net-feedet loader i baggrunden
if not alle_kampe:
    alle_kampe = [
        {"liga": "Champions League", "hj": "Inter", "ud": "Arsenal", "start": nu + datetime.timedelta(hours=2.0)},
        {"liga": "Champions League", "hj": "PSG", "ud": "Atletico Madrid", "start": nu + datetime.timedelta(hours=2.0)},
        {"liga": "Champions League", "hj": "Liverpool", "ud": "Leverkusen", "start": nu + datetime.timedelta(hours=2.0)},
        {"liga": "Championship", "hj": "Coventry", "ud": "Derby", "start": nu + datetime.timedelta(hours=1.5)},
        {"liga": "Championship", "hj": "Blackburn", "ud": "Stoke", "start": nu + datetime.timedelta(hours=1.5)},
        {"liga": "League One", "hj": "Bolton", "ud": "Portsmouth", "start": nu + datetime.timedelta(hours=0.5)},
        {"liga": "Europa League", "hj": "Roma", "ud": "Dynamo Kiev", "start": nu + datetime.timedelta(hours=4.0)},
        {"liga": "Coupe de France", "hj": "Lyon", "ud": "Nice", "start": nu + datetime.timedelta(hours=5.0)}
    ]

# Samler alle unikke holdnavne fra programmet
alle_hold = sorted(list(set([k["hj"] for k in alle_kampe] + [k["ud"] for k in alle_kampe])))

st.header("⚽ 1. Vælg dine favorithold")
valgte_hold = st.multiselect(
    "Søg og vælg ét eller flere hold på tværs af alle ligaer:",
    options=alle_hold,
    help="Robotten vil udelukkende kigge efter kampe, hvor disse hold spiller."
)

st.header("📊 2. Indstil dine krav")
col_o1, col_o2 = st.columns(2)
with col_o1:
    maal_odds = st.number_input("Målsat odds for dine valg:", min_value=2.0, max_value=1000.0, value=10.0, step=2.0)
with col_o2:
    st.write("")
    st.write("*Robotten kombinerer hold-specialmarkeder (skud, tacklinger, kort, hjørnespark) hos bookmakerne.*")

if st.button("🔍 SCAN SPECIAL-MARKEDER PÅ MINE HOLD", type="primary"):
    if not valgte_hold:
        st.error("Vælg venligst mindst ét hold i søgefeltet først!")
    else:
        # Filtrerer programmet så vi KUN har kampe med de valgte hold
        scannede_kampe = [k for k in alle_kampe if k["hj"] in valgte_hold or k["ud"] in valgte_hold]
        
        if not scannede_kampe:
            st.warning("Ingen af dine valgte hold har planlagte kampe i det dagsaktuelle program lige nu.")
        else:
            st.subheader(f"📊 Eksklusiv AI Analyse af dine hold:")
            st.write("---")
            
            # Bruger den fælles odds-motor til at bygge rene hold-kombinationer
            markeder_backup = ["Standard (Mål / Kampvinder)", "Hjørnespark (Over/Under & Flest)", "Spillerskud & Skud på mål", "Tacklinger & Målmandsredninger"]
            resultat = byg_kupon.byg_kombineret_kupon(scannede_kampe, markeder_backup, maal_odds)
            
            if resultat:
                for idx_k, k in enumerate(resultat["kampe"]):
                    timer_rest = (k["start"] - nu).total_seconds() / 3600
                    st.write(f"🏟️ **KAMP {idx_k+1}: [{k['liga']}] {k['hj']} vs. {k['ud']}** (Start om {timer_rest:.1f} timer)")
                    st.write("🧱 *Funderet Byg Væddemål på denne kamp:*")
                    for kombi_tekst in k["kombinationer"]:
                        st.write(f" ➔ {kombi_tekst}")
                    st.write(f"💵 **Kamp-odds:** Bet365: **{k['b365']:.2f}** | Unibet: **{k['uni']:.2f}** | Oddset: **{k['oddset']:.2f}**")
                    st.write("---")
                
                st.success(f"🔥 **BEDSTE BOOKMAKER FOR DINE FAVORITTER: {resultat['bedste_side']}!**")
                st.write(f"📈 **Samlet odds for kuponen: {resultat['bedste_odds']:.2f}**")
