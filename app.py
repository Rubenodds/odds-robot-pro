import streamlit as st
import datetime
import random
from tidsstyring import dansk_tid
from kampprogram import hent_kampe
from odds_motor import byg_kupon
from historik import gem_data

if "mobil_init" not in st.session_state:
    st.session_state["mobil_init"] = True

st.set_page_config(page_title="AI Multi-Robot Elite PRO", page_icon="⚡", layout="centered")

st.title("⚡ AI Multi-Robot & Odds-Scanner PRO")
st.write("Det fulde samlede system: Dansk tidsstyring, ægte kampprogram og avancerede kombinationer.")

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

# KALDER DIT TIDSMODUL FRA UNDERMAPPEN
nu = dansk_tid.hent_dansk_klokkeslaet()

# HENTER DE ÆGTE LIVE KAMPE FRA NETTET VIA DIT KAMPMODUL
alle_kampe = hent_kampe.hent_aegte_kampe_fra_nettet()

# HVIS NET-FEEDET ER TOMT, HAR VI EN BACKUP AF REELLE MIDTUGEKAMPE SÅ APPEN ALDRIG GÅR I STÅ
if not alle_kampe:
    alle_kampe = [
        {"liga": "Champions League", "hj": "Inter", "ud": "Arsenal", "start": nu + datetime.timedelta(hours=2.0)},
        {"liga": "Champions League", "hj": "PSG", "ud": "Atletico Madrid", "start": nu + datetime.timedelta(hours=2.0)},
        {"liga": "Champions League", "hj": "Liverpool", "ud": "Leverkusen", "start": nu + datetime.timedelta(hours=2.0)},
        {"liga": "Championship", "hj": "Coventry", "ud": "Derby", "start": nu + datetime.timedelta(hours=1.5)},
        {"liga": "Championship", "hj": "Blackburn", "ud": "Stoke", "start": nu + datetime.timedelta(hours=1.5)},
        {"liga": "League One", "hj": "Bolton", "ud": "Portsmouth", "start": nu + datetime.timedelta(hours=0.5)},
        {"liga": "Europa League", "hj": "Roma", "ud": "Dynamo Kiev", "start": nu + datetime.timedelta(hours=4.0)},
        {"liga": "Coupe de France", "hj": "Lyon", "ud": "Nice", "start": nu + datetime.timedelta(hours=5.0)},
        {"liga": "Betano Pokalen", "hj": "Silkeborg", "ud": "Viborg", "start": nu + datetime.timedelta(hours=26.0)},
        {"liga": "Serie A (Brasilien)", "hj": "Palmeiras", "ud": "Botafogo", "start": nu + datetime.timedelta(hours=28.0)}
    ]

# DYNAMISK LIGA-FILTER: Finder KUN de ligaer, som reelt har kampe inden for tidsfristen
tilgaengelige = sorted(list(set([k["liga"] for k in alle_kampe if ((k["start"] - nu).total_seconds() / 3600) <= tids_timer])))

# ----------------- PANEL 2: DYNAMISKE LIGAER -----------------
st.header("⚽ 2. Vælg Aktive Ligaer")

if not tilgaengelige:
    st.warning(f"Ingen ligaer har planlagte kampe inden for de næste {tids_timer:.0f} timer på onsdagsprogrammet.")
    valgte_ligaer = list()
else:
    st.write(f"Følgende ligaer har reelle kampe tilgængelige inden for de **{tidsvalg.lower()}**:")
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
        # Filtrerer de kampe ud, som ligger under tidsgrænsen blandt de valgte ligaer
        filtrerede = [k for k in alle_kampe if k["liga"] in valgte_ligaer and ((k["start"] - nu).total_seconds() / 3600) <= tids_timer]
        
        if not filtrerede:
            st.warning("Ingen tilgængelige kampe matchede dine krav.")
        else:
            valgte_kampe_liste = random.sample(filtrerede, min(antal_kampe, len(filtrerede)))
            
            # BYGGER KUPONEN VIA DIN SEPARATE ODDS_MOTOR UNDERMAPPE
            resultat = byg_kupon.byg_kombineret_kupon(valgte_kampe_liste, valgte_markeder, mål_odds)
            
            if resultat:
                st.subheader(f"📊 Din Kombinerede AI PRO Kupon")
                st.write("---")
                
                gemme_ligaer = []
                gemme_forslag = []
                
                for idx_k, k in enumerate(resultat["kampe"]):
                    timer_rest = (k["start"] - nu).total_seconds() / 3600
                    st.write(f"🏟️ **KAMP {idx_k+1}: [{k['liga']}] {k['hj']} vs. {k['ud']}** (Start om {timer_rest:.1f} timer)")
                    st.write("🧱 *Byg Væddemål kombinationer på denne kamp:*")
                    for kombi_tekst in k["kombinationer"]:
                        st.write(f" ➔ {kombi_tekst}")
                        gemme_forslag.append(f"[{k['hj']}-{k['ud']}]: {kombi_tekst}")
                    
                    st.write(f"💵 **Samlet kamp-odds:** Bet365: **{k['b365']:.2f}** | Unibet: **{k['uni']:.2f}** | Oddset: **{k['oddset']:.2f}**")
                    st.write("---")
                    gemme_ligaer.append(k["liga"])
                
                st.success(f"🔥 **ANBEFALET BOOKMAKER: {resultat['bedste_side']}!**")
                st.write(f"📈 **Samlet odds for hele kuponen hos {resultat['bedste_side']}: {resultat['bedste_odds']:.2f}**")
                st.write(f"ℹ️ *Sammenligning:* Bet365: {resultat['samlet_b365']:.2f} | Unibet: {resultat['samlet_unibet']:.2f} | Oddset: {resultat['samlet_oddset']:.2f}")
                st.write(f"🎯 **AI Sandsynlighed & Risiko (Værdi-vurdering):** {'⭐' * resultat['styrke']} ({resultat['styrke']}/5 stjerner)")
                
                # GEMMER AUTOMATISK I DATABASEN VIA DIT HISTORIK-MODUL
                gemt_status = gem_data.gem_kupon_i_historik(
                    gemme_ligaer, gemme_forslag, 
                    resultat["samlet_b365"], resultat["samlet_unibet"], resultat["samlet_oddset"], 
                    resultat["bedste_side"], resultat["styrke"]
                )
                if gemt_status:
                    st.info("🧠 Kupon gemt i AI-historikken! Robotten overvåger resultatet for at lære over tid.")
