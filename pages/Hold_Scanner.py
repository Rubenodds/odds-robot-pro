import streamlit as st
import datetime
import random
from tidsstyring import dansk_tid
from kampprogram import hent_kampe
from odds_motor import byg_kupon
from historik import gem_data

st.set_page_config(page_title="AI Favorit-Hold Scanner", page_icon="🎯", layout="centered")

st.title("🎯 AI Favorit-Hold Scanner")
st.write("Vælg turneringer inden for dit tidsinterval for at få alle tilgængelige hold frem i søgemenuen.")

# ----------------- PANEL 1: INDSTILLINGER -----------------
st.header("⏳ 1. Indstil dit tidsinterval & Odds-type")

col_t1, col_t2 = st.columns(2)

with col_t1:
    tidsvalg = st.radio(
        "Tidsramme for kampe:",
        ["Næste 3 timer", "Næste 6 timer", "Næste 12 timer", "Næste 24 timer", "Næste 48 timer"],
        key="tids_valg_scanner_side"
    )

with col_t2:
    odds_type = st.radio(
        "Vælg odds-strategi:",
        ["Pre-match Odds 🛡️", "Live Odds (In-play) ⚡"],
        index=0,
        key="odds_type_scanner_side"
    )

if "3 timer" in tidsvalg: tids_timer = 3.0
elif "6 timer" in tidsvalg: tids_timer = 6.0
elif "12 timer" in tidsvalg: tids_timer = 12.0
elif "24 timer" in tidsvalg: tids_timer = 24.0
else: tids_timer = 48.0

nu = dansk_tid.hent_dansk_klokkeslaet()
alle_kampe = hent_kampe.hent_aegte_kampe_fra_nettet()

tilgaengelige_ligaer_set = set()
for k in alle_kampe:
    k_liga = "Ukendt Liga"
    k_start = nu
    
    if isinstance(k, dict):
        k_liga = k.get("liga") or k.get("Liga") or k.get("turnering") or "Ukendt Liga"
        k_start = k.get("start") or k.get("Start") or nu
        
    try:
        timer_til_kamp = (k_start - nu).total_seconds() / 3600
        if "Pre-match" in odds_type:
            if 0 < timer_til_kamp <= tids_timer:
                tilgaengelige_ligaer_set.add(k_liga)
        else:
            if -2.0 <= timer_til_kamp <= 0:
                tilgaengelige_ligaer_set.add(k_liga)
    except Exception:
        pass

tilgaengelige_ligaer = sorted(list(tilgaengelige_ligaer_set))

# ----------------- PANEL 2: DYNAMISKE LIGAER -----------------
st.header("⚽ 2. Vælg Aktive Turneringer")

if not tilgaengelige_ligaer:
    if "Pre-match" in odds_type:
        st.warning(f"Ingen kommende kampe fundet inden for de næste {int(tids_timer)} timer.")
    else:
        st.warning("Der er ingen kampe i gang live i dine favoritligaer lige nu.")
    valgte_ligaer = list()
else:
    st.write("Sæt kryds ved de turneringer, du vil søge hold i:")
    liga_afkrydsning = {}
    
    kolonner = st.columns(min(3, len(tilgaengelige_ligaer)))
    for idx, liga_navn in enumerate(tilgaengelige_ligaer):
        med_kolonne = kolonner[idx % len(kolonner)]
        with med_kolonne:
            liga_afkrydsning[liga_navn] = st.checkbox(liga_navn, value=False, key=f"scanner_chk_{liga_navn}")
            
    valgte_ligaer = [navn for navn, valgt in liga_afkrydsning.items() if valgt]

aktive_kampe_i_periode = []
for k in alle_kampe:
    k_liga = "Ukendt Liga"
    k_start = nu
    if isinstance(k, dict):
        k_liga = k.get("liga") or k.get("Liga") or k.get("turnering") or "Ukendt Liga"
        k_start = k.get("start") or k.get("Start") or nu
        
    try:
        timer_til_kamp = (k_start - nu).total_seconds() / 3600
        if k_liga in valgte_ligaer:
            if "Pre-match" in odds_type:
                if 0 < timer_til_kamp <= tids_timer:
                    aktive_kampe_i_periode.append(k)
            else:
                if -2.0 <= timer_til_kamp <= 0:
                    aktive_kampe_i_periode.append(k)
    except Exception:
        pass

# ----------------- DYNAMISK SØGNING BLANDT HOLD -----------------
st.header("🎯 3. Vælg dine favorit-hold")

if "mine_valgte_hold" not in st.session_state:
    st.session_state["mine_valgte_hold"] = list()

if not valgte_ligaer:
    st.info("Sæt flueben ved turneringerne i punkt 2 ovenfor for at åbne op for dagens tilgængelige hold.")
elif not aktive_kampe_i_periode:
    st.warning("Ingen matchende kampe fundet for de valgte turneringer under denne odds-strategi.")
else:
    blokerede_hold = set()
    aktive_hold_set = set()
    
    for k in aktive_kampe_i_periode:
        k_hj, k_ud = "Hjemmehold", "Udehold"
        if isinstance(k, dict):
            k_hj = k.get("hj") or k.get("hjemmehold") or "Hjemmehold"
            k_ud = k.get("ud") or k.get("udehold") or "Udehold"
            
        if k_hj in st.session_state["mine_valgte_hold"] or k_ud in st.session_state["mine_valgte_hold"]:
            blokerede_hold.add(k_hj)
            blokerede_hold.add(k_ud)
            
        aktive_hold_set.add(k_hj)
        aktive_hold_set.add(k_ud)

    aktive_hold_liste = sorted(list(aktive_hold_set))

    # FORBEDRET CACHE-SIKRING: Inkluderer altid allerede valgte hold i options, så de ikke slettes
    for hold in st.session_state["mine_valgte_hold"]:
        if hold not in aktive_hold_liste:
            aktive_hold_liste.append(hold)
    aktive_hold_liste = sorted(aktive_hold_liste)

    valg_opdateret = st.multiselect(
        f"Søg frit blandt alle {len(aktive_hold_liste)} hold i de valgte turneringer:",
        options=aktive_hold_liste,
        default=st.session_state["mine_valgte_hold"],
        key="hold_scanner_skudsikker_multi"
    )

    if valg_opdateret != st.session_state["mine_valgte_hold"]:
        st.session_state["mine_valgte_hold"] = valg_opdateret
        st.rerun()

st.header("📊 4. Indstil dit målodds")
maal_odds = st.number_input("Målsat odds for dine valgte hold:", min_value=2.0, max_value=1000.0, value=10.0, step=2.0, key="scanner_odds_input")

if st.button("🔍 SCAN SPECIAL-MARKEDER PÅ MINE HOLD", type="primary", key="btn_scanner_side_generer"):
    if not st.session_state["mine_valgte_hold"]:
        st.error("Vælg venligst mindst ét hold i søgefeltet først!")
    else:
        kampe_til_analyse = []
        for k in aktive_kampe_i_periode:
            h_navn = k.get("hj") if isinstance(k, dict) else "Hjemmehold"
            u_navn = k.get("ud") if isinstance(k, dict) else "Udehold"
            if h_navn in st.session_state["mine_valgte_hold"] or u_navn in st.session_state["mine_valgte_hold"]:
                kampe_til_analyse.append(k)
        
        if not kampe_til_analyse:
            st.warning("De valgte hold matcher ikke det aktuelle program.")
        else:
            st.subheader("📊 Eksklusiv AI Analyse af dine hold:")
            st.write("---")
            
            markeder_pro = [
                "Standard (Mål / Kampvinder)", "Hjørnespark (Over/Under & Flest)", 
                "Spillerskud & Skud på mål", "Tacklinger & Målmandsredninger",
                "Indkast-analyse", "Frispark & Disciplin", "Offsides"
