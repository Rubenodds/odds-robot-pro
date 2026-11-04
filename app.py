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
st.write("Avanceret live-simulering med præcise tidsintervaller og special-markeder.")

st.header("⏳ 1. Indstil Tidsramme & Ligaer")

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

st.write("**Vælg dine aktive ligaer:**")

# Fordelt i 3 pæne kolonner til mobilen så du har ALT tilgængeligt
col_l1, col_l2, col_l3 = st.columns(3)
with col_l1:
    l_pl = st.checkbox("Premier League", value=True, key="pl")
    l_sl = st.checkbox("Superligaen", value=True, key="sl")
    l_ll = st.checkbox("LaLiga", value=True, key="ll")
    l_sa = st.checkbox("Serie A (Italien)", value=True, key="sa")
    l_bl = st.checkbox("Bundesliga", value=True, key="bl")
    l_ch = st.checkbox("Championship", value=True, key="ch")
    l_cl = st.checkbox("Champions League", value=True, key="cl")
    l_pk = st.checkbox("Betano Pokalen", value=True, key="pk")
with col_l2:
    l_lo = st.checkbox("League One", value=True, key="lo")
    l_lt = st.checkbox("League Two", value=True, key="lt")
    l_fa = st.checkbox("FA Cup", value=True, key="fa")
    l_efl = st.checkbox("EFL Cup", value=True, key="efl")
    l_bl2 = st.checkbox("Betinia LIGA (1.div)", value=True, key="bl2")
    l_c2d = st.checkbox("CampoBet 2. Div", value=True, key="c2d")
    l_ll2 = st.checkbox("LaLiga2", value=True, key="ll2")
    l_cdr = st.checkbox("Copa del Rey", value=True, key="cdr")
with col_l3:
    l_as = st.checkbox("Allsvenskan", value=True, key="as")
    l_es = st.checkbox("Eliteserien (Norge)", value=True, key="es")
    l_l1f = st.checkbox("Ligue 1 (Frankrig)", value=True, key="l1f")
    l_sb = st.checkbox("Serie B (Italien)", value=True, key="sb")
    l_lp = st.checkbox("Liga Portugal", value=True, key="lp")
    l_ad = st.checkbox("Æresdivisionen", value=True, key="ad")
    l_mls = st.checkbox("MLS (USA)", value=True, key="mls")
    l_j2 = st.checkbox("J2 League (Japan)", value=True, key="j2")

liga_status = {
    "Premier League": l_pl, "Superligaen": l_sl, "LaLiga": l_ll, "Serie A (Italien)": l_sa,
    "Bundesliga": l_bl, "Championship": l_ch, "Champions League": l_cl, "Betano Pokalen": l_pk,
    "League One": l_lo, "League Two": l_lt, "FA Cup": l_fa, "EFL Cup": l_efl,
    "Betinia LIGA (1.div)": l_bl2, "CampoBet 2. Div": l_c2d, "LaLiga2": l_ll2, "Copa del Rey": l_cdr,
    "Allsvenskan": l_as, "Eliteserien (Norge)": l_es, "Ligue 1 (Frankrig)": l_l1f, "Serie B (Italien)": l_sb,
    "Liga Portugal": l_lp, "Æresdivisionen": l_ad, "MLS (USA)": l_mls, "J2 League (Japan)": l_j2
}
valgte_ligaer = [navn for navn, valgt in liga_status.items() if valgt]

st.header("📊 2. Vælg Special-Markeder")
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

st.header("🔮 3. Generer PRO Autopilot Kupon")
col_p1, col_p2 = st.columns(2)
with col_p1:
    mål_odds = st.number_input("Indtast målsat odds", min_value=2.0, max_value=1000.0, value=15.0, step=5.0, key="mo_odds")
with col_p2:
    antal_kampe = st.slider("Antal kampe på kuponen", 2, 10, 5, key="ant_kampe")

if st.button("🚀 KØR AI PRO ANALYSE", type="primary", key="btn_analyse"):
    if not valgte_ligaer or not valgte_markeder:
        st.error("Vælg venligst både ligaer og markeder først!")
    else:
        st.info(f"Søger efter kampe der starter inden for de næste {tids_timer:.0f} timer...")
        nu = datetime.datetime.now()
        
        alle_kampe = [
            {"liga": "Premier League", "hj": "Man City", "ud": "Arsenal", "start": nu + datetime.timedelta(hours=1.5)},
            {"liga": "Superligaen", "hj": "FCK", "ud": "Brøndby", "start": nu + datetime.timedelta(hours=2.5)},
            {"liga": "Betinia LIGA (1.div)", "hj": "OB", "ud": "Esbjerg", "start": nu + datetime.timedelta(hours=2.0)},
            {"liga": "CampoBet 2. Div", "hj": "Fremad Amager", "ud": "Aarhus Fremad", "start": nu + datetime.timedelta(hours=5.5)},
            {"liga": "Ligue 1 (Frankrig)", "hj": "PSG", "ud": "Marseille", "start": nu + datetime.timedelta(hours=4.0)},
            {"liga": "Allsvenskan", "hj": "Malmö FF", "ud": "Hammarby", "start": nu + datetime.timedelta(hours=8.0)},
            {"liga": "Eliteserien (Norge)", "hj": "Bodø/Glimt", "ud": "Molde", "start": nu + datetime.timedelta(hours=11.5)},
            {"liga": "Championship", "hj": "Leeds", "ud": "Burnley", "start": nu + datetime.timedelta(hours=5.0)},
            {"liga": "Serie A (Italien)", "hj": "Inter", "ud": "Juventus", "start": nu + datetime.timedelta(hours=9.5)},
            {"liga": "Champions League", "hj": "Real Madrid", "ud": "Man City", "start": nu + datetime.timedelta(hours=11.0)},
            {"liga": "League One", "hj": "Bolton", "ud": "Portsmouth", "start": nu + datetime.timedelta(hours=14.0)},
            {"liga": "League Two", "hj": "Wrexham", "ud": "Stockport", "start": nu + datetime.timedelta(hours=16.5)},
            {"liga": "FA Cup", "hj": "Man United", "ud": "Newcastle", "start": nu + datetime.timedelta(hours=22.0)},
            {"liga": "EFL Cup", "hj": "Tottenham", "ud": "West Ham", "start": nu + datetime.timedelta(hours=3.5)},
            {"liga": "LaLiga2", "hj": "Espanyol", "ud": "Zaragoza", "start": nu + datetime.timedelta(hours=25.0)},
            {"liga": "Copa del Rey", "hj": "Athletic Bilbao", "ud": "Real Betis", "start": nu + datetime.timedelta(hours=30.0)},
            {"liga": "Serie B (Italien)", "hj": "Palermo", "ud": "Sampdoria", "start": nu + datetime.timedelta(hours=34.0)},
            {"liga": "Liga Portugal", "hj": "Benfica", "ud": "Sporting CP", "start": nu + datetime.timedelta(hours=6.0)},
            {"liga": "Æresdivisionen", "hj": "Ajax", "ud": "PSV", "start": nu + datetime.timedelta(hours=19.0)},
            {"liga": "MLS (USA)", "hj": "Inter Miami", "ud": "LA Galaxy", "start": nu + datetime.timedelta(hours=42.0)},
            {"liga": "J2 League (Japan)", "hj": "Yokohama FC", "ud": "Chiba", "start": nu + datetime.timedelta(hours=1.0)},
            {"liga": "Betano Pokalen", "hj": "Silkeborg", "ud": "Viborg", "start": nu + datetime.timedelta(hours=36.0)},
            {"liga": "LaLiga", "hj": "Real Madrid", "ud": "Barcelona", "start": nu + datetime.timedelta(hours=44.0)}
        ]
        
        filtrerede = [k for k in alle_kampe if k["liga"] in valgte_ligaer and ((k["start"] - nu).total_seconds() / 3600) <= tids_timer]
        
        if not filtrerede:
            st.warning(f"Ingen kampe fundet inden for de næste {tids_timer:.0f} timer for de valgte ligaer. Prøv et større tidsinterval eller vælg flere ligaer.")
        else:
            valgte = random.sample(filtrerede, min(antal_kampe, len(filtrerede)))
            samlet_odds = 1.0
            
            st.subheader(f"📊 Din AI PRO Kupon (Maks {tids_timer:.0f} timer til kampstart)")
            for i, k in enumerate(valgte):
                marked = random.choice(valgte_markeder)
                
                if marked == "Hjørnespark": spil, o = "Over 8.5 hjørnespark i kampen", 1.65
                elif marked == "Spillerskud & Skud på mål": spil, o = "Byg spil: Topscorer skyder 1+ skud på mål", 1.85
                elif marked == "Tacklinger & Målmandsredninger": spil, o = "Byg spil: Midtbanegeneral laver 2+ tacklinger", 1.75
                elif marked == "Kort-sandsynlighed (Gule/Røde)": spil, o = "Over 3.5 kort i kampen", 1.60
                elif marked == "Målscorer": spil, o = "Hjemmeholdets angriber scorer", 2.20
                else: spil, o = f"Byg Væddemål: {k['hj']} vinder + Over 2.5 mål", 2.10
                
                justering = (mål_odds / 20.0) ** (1 / len(valgte))
                nyt_odds = round(o * max(0.8, min(justering, 2.2)), 2)
                timer_rest = (k["start"] - nu).total_seconds() / 3600
                
                st.write(f"⚽ **{i+1}. [{k['liga']}] {k['hj']} vs. {k['ud']}** (Starter om {timer_rest:.1f} timer)")
                st.write(f" ➔ **Marked:** {marked} | **Anbefaling:** {spil} (Odds {nyt_odds:.2f})")
                st.write("---")
                samlet_odds *= nyt_odds
                
