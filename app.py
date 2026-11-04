import streamlit as st
import datetime
import random
import sqlite3

if "mobil_init" not in st.session_state:
    st.session_state["mobil_init"] = True

def init_database():
    conn = sqlite3.connect("odds_pro_hukommelse.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historik_pro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dato TEXT,
            tidspunkt TEXT,
            liga TEXT,
            hjemmehold TEXT,
            udehold TEXT,
            marked TEXT,
            spilforslag TEXT,
            odds REAL,
            status TEXT DEFAULT 'Afventer'
        )
    """)
    conn.commit()
    conn.close()

try:
    init_database()
except Exception:
    pass

st.set_page_config(page_title="AI Oddset Robot PRO", page_icon="⚡", layout="centered")

st.title("⚡ AI Oddset Multi-Robot PRO")
st.write("Avanceret live-simulering med tidsstyrede ligaer og special-markeder.")

# 1. Indstil Tidsramme
st.header("⏳ 1. Indstil Tidsramme")

tidsvalg = st.radio(
    "Hvor langt frem i tiden skal robotten kigge efter kampe?",
    ["Næste 3 timer", "Næste 6 timer", "Næste 12 timer", "Næste 24 timer", "Næste 48 timer"],
    key="tids_valg_key"
)

if "3 timer" in tidsvalg: tids_timer = 3.0
elif "6 timer" in tidsvalg: tids_timer = 6.0
elif "12 timer" in tidsvalg: tids_timer = 12.0
elif "24 timer" in tidsvalg: tids_timer = 24.0
else: tids_timer = 48.0

# INTENT DATA-MOTOR
nu = datetime.datetime.now()
alle_kampe = [
    {"liga": "Premier League", "hj": "Man City", "ud": "Arsenal", "start": nu + datetime.timedelta(hours=1.5)},
    {"liga": "Superligaen", "hj": "FCK", "ud": "Brøndby", "start": nu + datetime.timedelta(hours=2.5)},
    {"liga": "J2 League (Japan)", "hj": "Yokohama FC", "ud": "Chiba", "start": nu + datetime.timedelta(hours=1.0)},
    {"liga": "Betinia LIGA (1.div)", "hj": "OB", "ud": "Esbjerg", "start": nu + datetime.timedelta(hours=5.0)},
    {"liga": "Championship", "hj": "Leeds", "ud": "Burnley", "start": nu + datetime.timedelta(hours=5.0)},
    {"liga": "Ligue 1 (Frankrig)", "hj": "PSG", "ud": "Marseille", "start": nu + datetime.timedelta(hours=4.0)},
    {"liga": "Liga Portugal", "hj": "Benfica", "ud": "Sporting CP", "start": nu + datetime.timedelta(hours=6.0)},
    {"liga": "Allsvenskan", "hj": "Malmö FF", "ud": "Hammarby", "start": nu + datetime.timedelta(hours=8.0)},
    {"liga": "Serie A (Italien)", "hj": "Inter", "ud": "Juventus", "start": nu + datetime.timedelta(hours=9.5)},
    {"liga": "Champions League", "hj": "Real Madrid", "ud": "Man City", "start": nu + datetime.timedelta(hours=11.0)},
    {"liga": "Eliteserien (Norge)", "hj": "Bodø/Glimt", "ud": "Molde", "start": nu + datetime.timedelta(hours=11.5)},
    {"liga": "League One", "hj": "Bolton", "ud": "Portsmouth", "start": nu + datetime.timedelta(hours=14.0)},
    {"liga": "League Two", "hj": "Wrexham", "ud": "Stockport", "start": nu + datetime.timedelta(hours=16.5)},
    {"liga": "Æresdivisionen", "hj": "Ajax", "ud": "PSV", "start": nu + datetime.timedelta(hours=19.0)},
    {"liga": "FA Cup", "hj": "Man United", "ud": "Newcastle", "start": nu + datetime.timedelta(hours=22.0)},
    {"liga": "EFL Cup", "hj": "Tottenham", "ud": "West Ham", "start": nu + datetime.timedelta(hours=3.5)},
    {"liga": "LaLiga2", "hj": "Espanyol", "ud": "Zaragoza", "start": nu + datetime.timedelta(hours=25.0)},
    {"liga": "Copa del Rey", "hj": "Athletic Bilbao", "ud": "Real Betis", "start": nu + datetime.timedelta(hours=30.0)},
    {"liga": "Serie B (Italien)", "hj": "Palermo", "ud": "Sampdoria", "start": nu + datetime.timedelta(hours=34.0)},
    {"liga": "Betano Pokalen", "hj": "Silkeborg", "ud": "Viborg", "start": nu + datetime.timedelta(hours=36.0)},
    {"liga": "MLS (USA)", "hj": "Inter Miami", "ud": "LA Galaxy", "start": nu + datetime.timedelta(hours=42.0)},
    {"liga": "LaLiga", "hj": "Real Madrid", "ud": "Barcelona", "start": nu + datetime.timedelta(hours=44.0)}
]

# Filtrer ligaer så vi KUN viser dem der har kampe i tidsrummet
tilgaengelige_ligaer = sorted(list(set([k["liga"] for k in alle_kampe if ((k["start"] - nu).total_seconds() / 3600) <= tids_timer])))

# 2. Vælg Aktive Ligaer
st.header("⚽ 2. Vælg Aktive Ligaer")
st.write(f"Følgende ligaer har kampe tilgængelige inden for de **{tidsvalg.lower()}**:")

if not tilgaengelige_ligaer:
    st.warning("Ingen ligaer har planlagte kampe i dette korte tidsrum.")
    valgte_ligaer = []
else:
    liga_afkrydsning = {}
    kolonner = st.columns(min(3, len(tilgaengelige_ligaer)))
    for idx, liga_navn in enumerate(tilgaengelige_ligaer):
        med_kolonne = kolonner[idx % len(kolonner)]
        with med_kolonne:
            liga_afkrydsning[liga_navn] = st.checkbox(liga_navn, value=True, key=f"chk_{liga_navn}")
            
    valgte_ligaer = [navn for navn, valgt in liga_afkrydsning.items() if valgt]

# 3. Vælg Special-Markeder
st.header("📊 3. Vælg Special-Markeder")
col_m1, col_m2 = st.columns(2)
with col_m1:
    m_mål = st.checkbox("Standard (Mål / Kampvinder)", value=True, key="m_mal")
    m_hjørne = st.checkbox("Hjørnespark (Over/Under & Flest)", value=True, key="m_hjo")
    m_skud = st.checkbox("Spillerskud & Skud på mål", value=True, key="m_sku")
with col_m2:
    m_tack = st.checkbox("Tacklinger & Målmandsredninger", value=True, key="m_tac")
    m_kort = st.checkbox("Kort-sandsynlighed (Gule/Røde)", value=True, key="m_kor")
    m_scorer = st.checkbox("Målscorer (Anytime/Første)", value=True, key="m_sco")

marked_status = {"Standard": m_mål, "Hjørnespark": m_hjørne, "Spillerskud / Skud på mål": m_skud, "Tacklinger / Redninger": m_tack, "Kort sandsynlighed": m_kort, "Målscorer": m_scorer}
valgte_markeder = [navn for navn, valgt in marked_status.items() if valgt]

# 4. PRO AUTOPILOT
st.header("🔮 4. Generer PRO Autopilot Kupon")
col_p1, col_p2 = st.columns(2)
with col_p1:
    mål_odds = st.number_input("Indtast målsat odds", min_value=2.0, max_value=1000.0, value=15.0, step=5.0, key="mo_odds")
with col_p2:
    antal_kampe = st.slider("Antal kampe på kuponen", 2, 10, 3, key="ant_kampe")

if st.button("🚀 KØR AI PRO ANALYSE", type="primary", key="btn_analyse"):
    if not valgte_ligaer:
        st.error("Du skal vælge mindst én aktiv liga for at køre analysen!")
    elif not valgte_markeder:
        st.error("Du skal vælge mindst ét special-marked!")
    else:
        st.info("Kører avanceret tids- og statistik-analyse...")
        
        # BENHÅRD TIDSLÅS: Filtrerer kampene igennem, så de KUN må være under den valgte tidsgrænse
        filtrerede = [k for k in alle_kampe if k["liga"] in valgte_ligaer and ((k["start"] - nu).total_seconds() / 3600) <= tids_timer]
        
        if not filtrerede:
            st.warning("Ingen tilgængelige kampe matchede dine tids- og ligakrav.")
        else:
            valgte = random.sample(filtrerede, min(antal_kampe, len(filtrerede)))
            samlet_odds = 1.0
            
            st.subheader(f"📊 Din AI PRO Kupon ({tidsvalg})")
            for i, k in enumerate(valgte):
                marked = random.choice(valgte_markeder)
                
                if marked == "Hjørnespark": spil, o = "Over 8.5 hjørnespark i kampen", 1.65
                elif marked == "Spillerskud / Skud på mål": spil, o = "Byg spil: Topscorer skyder 1+ skud på mål", 1.85
                elif marked == "Tacklinger / Redninger": spil, o = "Byg spil: Midtbanegeneral laver 2+ tacklinger", 1.75
                elif marked == "Kort sandsynlighed": spil, o = "Over 3.5 kort i kampen", 1.60
                elif marked == "Målscorer": spil, o = "Hjemmeholdets angriber scorer", 2.20
                else: spil, o = f"Byg Væddemål: {k['hj']} vinder + Over 2.5 mål", 2.10
                
                justering = (mål_odds / 20.0) ** (1 / len(valgte))
                nyt_odds = round(o * max(0.8, min(justering, 2.2)), 2)
                timer_rest = (k["start"] - nu).total_seconds() / 3600
                
                st.write(f"⚽ **{i+1}. [{k['liga']}] {k['hj']} vs. {k['ud']}** (Kampstart om {timer_rest:.1f} timer)")
                st.write(f" ➔ **Marked:** {marked} | **Anbefaling:** {spil} (Odds {nyt_odds:.2f})")
                st.write("---")
                samlet_odds *= nyt_odds
                
            st.success(f"🔥 Kupon klar! Samlet odds ramte: {samlet_odds:.2f}")
