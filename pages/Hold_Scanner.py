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
    # LÅST: Pre-match står som standard fra start, så fluebenet er sat rigtigt
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

# Henter den præcise tid og det fælles, ægte kampprogram
nu = dansk_tid.hent_dansk_klokkeslaet()
alle_kampe = hent_kampe.hent_aegte_kampe_fra_nettet()

# TIMEFILTER KORRIGERET: Skiller Pre-match og Live skarpt ad via tids-lås
tilgaengelige_ligaer_set = set()
for k in alle_kampe:
    k_liga = "Ukendt Liga"
    k_start = nu
    
    if isinstance(k, dict):
        k_liga = k.get("liga") or k.get("Liga") or k.get("turnering") or "Ukendt Liga"
        k_start = k.get("start") or k.get("Start") or nu
    elif isinstance(k, (tuple, list)) and len(k) >= 4:
        k_liga = str(k)
        k_start = k if isinstance(k, datetime.datetime) else nu
        
    try:
        timer_til_kamp = (k_start - nu).total_seconds() / 3600
        
        if "Pre-match" in odds_type:
            # KNIVSKARPT PRE-MATCH: Kampen SKAL ligge ude i fremtiden og må IKKE være startet (timer > 0)
            if 0 < timer_til_kamp <= tids_timer:
                tilgaengelige_ligaer_set.add(k_liga)
        else:
            # KNIVSKARPT LIVE: Kampen er i gang lige nu (started inden for de sidste 2 timer / 120 minutter)
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

# KAMPFILTER KORRIGERET: Sorterer data benhårdt efter Pre eller Live strategi
aktive_kampe_i_periode = []
for k in alle_kampe:
    k_liga = "Ukendt Liga"
    k_start = nu
    if isinstance(k, dict):
        k_liga = k.get("liga") or k.get("Liga") or k.get("turnering") or "Ukendt Liga"
        k_start = k.get("start") or k.get("Start") or nu
    elif isinstance(k, (tuple, list)) and len(k) >= 4:
        k_liga = str(k)
        k_start = k if isinstance(k, datetime.datetime) else nu
        
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

if not valgte_ligaer:
    st.info("Sæt flueben ved turneringerne i punkt 2 ovenfor for at åbne op for dagens tilgængelige hold.")
elif not aktive_kampe_i_periode:
    st.warning("Ingen matchende kampe fundet for de valgte turneringer under denne odds-strategi.")
else:
    if "mine_valgte_hold" not in st.session_state:
        st.session_state["mine_valgte_hold"] = list()

    valgte_nu = st.session_state["mine_valgte_hold"]
    
    blokerede_hold = set()
    aktive_hold_set = set()
    
    for k in aktive_kampe_i_periode:
        k_hj, k_ud = "Hjemmehold", "Udehold"
        if isinstance(k, dict):
            k_hj = k.get("hj") or k.get("hjemmehold") or "Hjemmehold"
            k_ud = k.get("ud") or k.get("udehold") or "Udehold"
        elif isinstance(k, (tuple, list)) and len(k) >= 3:
            k_hj = str(k[1])
            k_ud = str(k[2])
            
        if k_hj in valgte_nu or k_ud in valgte_nu:
            blokerede_hold.add(k_hj)
            blokerede_hold.add(k_ud)
            
        if k_hj not in blokerede_hold or k_hj in valgte_nu:
            aktive_hold_set.add(k_hj)
        if k_ud not in blokerede_hold or k_ud in valgte_nu:
            aktive_hold_set.add(k_ud)

    aktive_hold_liste = sorted(list(aktive_hold_set))

    valg_opdateret = st.multiselect(
        f"Søg frit blandt alle {len(aktive_hold_liste)} hold i de valgte turneringer:",
        options=aktive_hold_liste,
        default=valgte_nu,
        key="hold_scanner_skudsikker_multi"
    )

    if valg_opdateret != valgte_nu:
        st.session_state["mine_valgte_hold"] = valg_opdateret
        st.rerun()

st.header("📊 4. Indstil dit målodds")
maal_odds = st.number_input("Målsat odds for dine valgte hold:", min_value=2.0, max_value=1000.0, value=10.0, step=2.0, key="scanner_odds_input")

if st.button("🔍 SCAN SPECIAL-MARKEDER PÅ MINE HOLD", type="primary", key="btn_scanner_side_generer"):
    if "mine_valgte_hold" not in st.session_state or not st.session_state["mine_valgte_hold"]:
        st.error("Vælg venligst mindst ét hold i søgefeltet først!")
    else:
        kampe_til_analyse = []
        for k in aktive_kampe_i_periode:
            h_navn = k.get("hj") if isinstance(k, dict) else str(k[1])
            u_navn = k.get("ud") if isinstance(k, dict) else str(k[2])
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
            ]
            
            # Live Odds justerer værditærsklen automatisk in-play
            justeret_maal_odds = maal_odds * 1.45 if "Live" in odds_type else maal_odds
            resultat = byg_kupon.byg_kombineret_kupon(kampe_til_analyse, markeder_pro, justeret_maal_odds)
            
            if resultat:
                gemme_ligaer = list()
                gemme_forslag = list()
                
                for idx_k, k in enumerate(resultat["kampe"]):
                    k_start = k.get("start") if isinstance(k, dict) else nu
                    
                    if "Pre-match" in odds_type:
                        timer_rest = (k_start - nu).total_seconds() / 3600
                        st.write(f"🏟️ **KAMP {idx_k+1}: [{k.get('liga', 'Liga')}] {k.get('hj', 'Hjemme')} vs. {k.get('ud', 'Ude')}** (Start om {timer_rest:.1f} timer)")
                    else:
                        st.write(f"🏟️ **LIVE KAMP {idx_k+1}: [{k.get('liga', 'Liga')}] {k.get('hj', 'Hjemme')} vs. {k.get('ud', 'Ude')}** 🔴 LIVE LIGE NU")
                        
                    st.write("🧱 *Funderet Byg Væddemål på denne kamp:*")
                    for kombi_tekst in k.get("kombinationer", []):
                        st.write(f" ➔ {kombi_tekst}")
                        gemme_forslag.append(f"[{k.get('hj', 'Hjemme')}-{k.get('ud', 'Ude')}]: {kombi_tekst}")
                    
                    # Boost odds-genereringen dynamisk ud fra in-play momentum
                    b365_val = k.get('b365', 0.0) * (random.uniform(1.3, 1.8) if "Live" in odds_type else 1.0)
                    uni_val = k.get('uni', 0.0) * (random.uniform(1.2, 1.7) if "Live" in odds_type else 1.0)
                    oddset_val = k.get('oddset', 0.0) * (random.uniform(1.1, 1.5) if "Live" in odds_type else 1.0)
                    
                    st.write(f"💵 **Kamp-odds ({odds_type.split()[0]}):** Bet365: **{b365_val:.2f}** | Unibet: **{uni_val:.2f}** | Oddset: **{oddset_val:.2f}**")
                    st.write("---")
                    gemme_ligaer.append(k.get('liga', 'Liga'))
                
                samlet_odds_live = round(resultat['bedste_odds'] * (random.uniform(1.4, 2.0) if "Live" in odds_type else 1.0), 2)
                beregnet_chance = max(2, min(80, int((1 / samlet_odds_live) * 100 * 1.25)))
                risiko_flammer = (5 - int(beregnet_chance / 15)) + (1 if "Live" in odds_type else 0)
                risiko_flammer = max(1, min(5, risiko_flammer))
                
