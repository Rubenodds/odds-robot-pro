import streamlit as st
import datetime
import random
import dansk_tid

if "mobil_init" not in st.session_state:
    st.session_state["mobil_init"] = True

st.set_page_config(page_title="AI Multi-Robot Elite PRO", page_icon="⚡", layout="centered")

st.title("⚡ AI Multi-Robot & Odds-Scanner PRO")
st.write("Dansk tidsjustering, dynamiske liga-filtre og automatiske multi-kombinationer.")

# ----------------- PANEL 1: INDSTILLINGER -----------------
st.header("⏳ 1. Indstil din Kupon-bygger")

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

# ----------------- DYNAMISK KAMP-MOTOR -----------------
# Henter den præcise danske tid fra din forside-fil
nu = dansk_tid.hent_dansk_klokkeslaet()

# Kæmpe, tidløs pulje af simuleret live-data. Kampene rykker sig automatisk 
# i forhold til præcis det minut, du trykker på knappen – uanset ugedag!
alle_kampe = [
    {"liga": "AFC Champions League", "hj": "Al-Nassr", "ud": "Al-Ain", "start": nu + datetime.timedelta(hours=1.5)},
    {"liga": "J2 League (Japan)", "hj": "Yokohama FC", "ud": "Chiba", "start": nu + datetime.timedelta(hours=2.0)},
    {"liga": "EFL Cup", "hj": "Brentford", "ud": "Brighton", "start": nu + datetime.timedelta(hours=2.5)},
    {"liga": "Premier League", "hj": "Man City", "ud": "Arsenal", "start": nu + datetime.timedelta(hours=4.0)},
    {"liga": "Superligaen", "hj": "FCK", "ud": "Brøndby", "start": nu + datetime.timedelta(hours=4.5)},
    {"liga": "Europa League", "hj": "Roma", "ud": "Dynamo Kiev", "start": nu + datetime.timedelta(hours=5.5)},
    {"liga": "Jupiler League (Belgien)", "hj": "Club Brügge", "ud": "Anderlecht", "start": nu + datetime.timedelta(hours=5.8)},
    {"liga": "Copa del Rey", "hj": "Valencia", "ud": "Parla", "start": nu + datetime.timedelta(hours=7.0)},
    {"liga": "League One", "hj": "Bolton", "ud": "Portsmouth", "start": nu + datetime.timedelta(hours=7.5)},
    {"liga": "Coupe de France", "hj": "Lyon", "ud": "Nice", "start": nu + datetime.timedelta(hours=8.0)},
    {"liga": "Championship", "hj": "Coventry", "ud": "Derby", "start": nu + datetime.timedelta(hours=8.5)},
    {"liga": "Championship", "hj": "Blackburn", "ud": "Stoke", "start": nu + datetime.timedelta(hours=10.0)},
    {"liga": "Champions League", "hj": "Inter", "ud": "Arsenal", "start": nu + datetime.timedelta(hours=11.0)},
    {"liga": "Champions League", "hj": "PSG", "ud": "Atletico Madrid", "start": nu + datetime.timedelta(hours=11.5)},
    {"liga": "Champions League", "hj": "Liverpool", "ud": "Leverkusen", "start": nu + datetime.timedelta(hours=14.0)},
    {"liga": "LaLiga", "hj": "Real Madrid", "ud": "Barcelona", "start": nu + datetime.timedelta(hours=16.0)},
    {"liga": "Bundesliga", "hj": "Bayern München", "ud": "Dortmund", "start": nu + datetime.timedelta(hours=18.5)},
    {"liga": "Serie A (Italien)", "hj": "Inter", "ud": "Juventus", "start": nu + datetime.timedelta(hours=23.0)},
    {"liga": "Serie A (Brasilien)", "hj": "Palmeiras", "ud": "Botafogo", "start": nu + datetime.timedelta(hours=25.0)},
    {"liga": "League Two", "hj": "Wrexham", "ud": "Mansfield", "start": nu + datetime.timedelta(hours=29.0)},
    {"liga": "Betinia LIGA (1.div)", "hj": "OB", "ud": "Esbjerg", "start": nu + datetime.timedelta(hours=33.0)},
    {"liga": "CampoBet 2. Div", "hj": "Fremad Amager", "ud": "Aarhus Fremad", "start": nu + datetime.timedelta(hours=36.5)},
    {"liga": "Betano Pokalen", "hj": "Silkeborg", "ud": "Viborg", "start": nu + datetime.timedelta(hours=39.0)},
    {"liga": "Liga Portugal", "hj": "Porto", "ud": "Braga", "start": nu + datetime.timedelta(hours=41.0)},
    {"liga": "Æresdivisionen", "hj": "PSV", "ud": "Ajax", "start": nu + datetime.timedelta(hours=44.0)},
    {"liga": "LaLiga2", "hj": "Espanyol", "ud": "Zaragoza", "start": nu + datetime.timedelta(hours=46.0)},
    {"liga": "MLS (USA)", "hj": "Inter Miami", "ud": "LA Galaxy", "start": nu + datetime.timedelta(hours=47.5)}
]

# DET INTELLIGENTE FILTER: Viser KUN de ligaer under punkt 2, der reelt har kampe i tidsrummet
tilgaengelige = sorted(list(set([k["liga"] for k in alle_kampe if ((k["start"] - nu).total_seconds() / 3600) <= tids_timer])))

# ----------------- PANEL 2: DYNAMISKE LIGAER -----------------
st.header("⚽ 2. Vælg Aktive Ligaer")

if not tilgaengelige:
    st.warning("Ingen ligaer har planlagte kampe i dette korte tidsrum på programmet.")
    valgte_ligaer = list()
else:
    st.write(f"Følgende ligaer har kampe tilgængelige inden for de **{tidsvalg.lower()}**:")
    liga_afkrydsning = {}
    kolonner = st.columns(min(3, len(tilgaengelige)))
    
    for idx, liga_navn in enumerate(tilgaengelige):
        med_kolonne = kolonner[idx % len(kolonner)]
        with med_kolonne:
            liga_afkrydsning[liga_navn] = st.checkbox(liga_navn, value=True, key=f"chk_{liga_navn}")
            
    valgte_ligaer = [navn for navn, valgt in liga_afkrydsning.items() if valgt]

# ----------------- PANEL 3: SPECIAL-MARKEDER -----------------
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

marked_status = {"Standard (Mål / Kampvinder)": m_mål, "Hjørnespark (Over/Under & Flest)": m_hjørne, "Spillerskud & Skud på mål": m_skud, "Tacklinger & Målmandsredninger": m_tack, "Kort-sandsynlighed (Gule/Røde)": m_kort, "Målscorer (Anytime/Første)": m_scorer}
valgte_markeder = [navn for navn, valgt in marked_status.items() if valgt]

# ----------------- PANEL 4: PRO AUTOPILOT KUPON -----------------
st.header("🔮 4. Generer PRO Autopilot Kupon")
col_p1, col_p2 = st.columns(2)
with col_p1:
    mål_odds = st.number_input("Indtast målsat odds", min_value=2.0, max_value=1000.0, value=20.0, step=5.0, key="mo_odds")
with col_p2:
    antal_kampe = st.slider("Antal kampe på kuponen", 1, 5, 2, key="ant_kampe")

if st.button("🔮 GENERER MULTI-KOMBINERET AI KUPON", type="primary", key="btn_analyse"):
    if not valgte_ligaer or not valgte_markeder:
        st.error("Vælg venligst både aktive ligaer og markeder først!")
    else:
        st.info("AI'en sammensætter komplekse kombinationer og rammer målodds...")
        filtrerede = [k for k in alle_kampe if k["liga"] in valgte_ligaer and ((k["start"] - nu).total_seconds() / 3600) <= tids_timer]
        
        if not filtrerede:
            st.warning("Ingen tilgængelige kampe matchede dine krav.")
        else:
            valgte_kampe_liste = random.sample(filtrerede, min(antal_kampe, len(filtrerede)))
            
            st.subheader(f"📊 Din Kombinerede AI PRO Kupon")
            st.write("---")
            
            samlet_b365, samlet_unibet, samlet_oddset = 1.0, 1.0, 1.0
            odds_per_kamp_basal = mål_odds ** (1 / len(valgte_kampe_liste))
            
            for idx_k, k in enumerate(valgte_kampe_liste):
                timer_rest = (k["start"] - nu).total_seconds() / 3600
                st.write(f"🏟️ **KAMP {idx_k+1}: [{k['liga']}] {k['hj']} vs. {k['ud']}** (Start om {timer_rest:.1f} timer)")
                
                kombier = list()
                pool_standard = [f"Resultat: {k['hj']} vinder", f"Byg spil: Halvleg/Fuldtid - {k['hj']}/{k['hj']}", "Begge hold scorer: JA"]
                pool_hjoerne = ["Over 9.5 hjørnespark i kampen", f"Flest hjørnespark til {k['hj']}", "Under 11.5 hjørnespark samlet"]
                pool_skud = [f"Byg spil: {k['hj']} topscorer over 1.5 skud på mål", f"Byg spil: Udeholdets kantspiller får 1+ skud på mål", "Over 8.5 skud på mål samlet"]
                pool_tack = ["Byg spil: Defensiv midtbane laver 3+ tacklinger", "Målmand laver over 3.5 redninger", "Over 14.5 tacklinger i kampen"]
                pool_kort = ["Over 4.5 gule kort i kampen", "Hjemmeholdet får over 1.5 kort", "Byg spil: Kampens midtbanegeneral får kort"]
                pool_scorer = [f"Byg spil: {k['hj']} angriber scorer anytime", f"Byg spil: {k['ud']} topscorer laver mål eller assist", "Over 2.5 mål i kampen"]
                
                if "Standard (Mål / Kampvinder)" in valgte_markeder: kombier.append(random.choice(pool_standard))
                if "Hjørnespark (Over/Under & Flest)" in valgte_markeder: kombier.append(random.choice(pool_hjoerne))
                if "Spillerskud & Skud på mål" in valgte_markeder: kombier.append(random.choice(pool_skud))
                if "Tacklinger & Målmandsredninger" in valgte_markeder: kombier.append(random.choice(pool_tack))
                if "Kort-sandsynlighed (Gule/Røde)" in valgte_markeder: kombier.append(random.choice(pool_kort))
                if "Målscorer (Anytime/Første)" in valgte_markeder: kombier.append(random.choice(pool_scorer))
                
                vis_kombier = random.sample(kombier, min(random.randint(2, 4), len(kombier))) if len(kombier) > 2 else kombier
                
                kombi_b365 = round(odds_per_kamp_basal * random.uniform(0.98, 1.02), 2)
                kombi_uni = round(kombi_b365 * random.uniform(0.93, 1.03), 2)
                kombi_odd = round(kombi_b365 * random.uniform(0.88, 0.98), 2)
                
                st.write("🧱 *Byg Væddemål kombinationer på denne kamp:*")
                for kombi_tekst in vis_kombier:
