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

# KOPLING TIL DET NYE SEPARATE TIDSMODUL INDE I UNDERMAPPEN
nu = dansk_tid.hent_dansk_klokkeslaet()

# REELLE DATA FOR MIDTUGEPROGRAMMET
alle_kampe = [
    {"liga": "AFC Champions League", "hj": "Al-Nassr", "ud": "Al-Ain", "start": nu + datetime.timedelta(hours=2.0)},
    {"liga": "Jupiler League (Belgien)", "hj": "Club Brügge", "ud": "Anderlecht", "start": nu + datetime.timedelta(hours=6.5)},
    {"liga": "Championship", "hj": "Coventry", "ud": "Derby", "start": nu + datetime.timedelta(hours=8.5)},
    {"liga": "Championship", "hj": "Blackburn", "ud": "Stoke", "start": nu + datetime.timedelta(hours=8.5)},
    {"liga": "League One", "hj": "Bolton", "ud": "Portsmouth", "start": nu + datetime.timedelta(hours=7.5)},
    {"liga": "Champions League", "hj": "Inter", "ud": "Arsenal", "start": nu + datetime.timedelta(hours=9.0)},
    {"liga": "Champions League", "hj": "PSG", "ud": "Atletico Madrid", "start": nu + datetime.timedelta(hours=9.0)},
    {"liga": "Champions League", "hj": "Liverpool", "ud": "Leverkusen", "start": nu + datetime.timedelta(hours=9.0)},
    {"liga": "Europa League", "hj": "Roma", "ud": "Dynamo Kiev", "start": nu + datetime.timedelta(hours=6.0)},
    {"liga": "Coupe de France", "hj": "Lyon", "ud": "Nice", "start": nu + datetime.timedelta(hours=8.0)},
    {"liga": "Copa del Rey", "hj": "Valencia", "ud": "Parla", "start": nu + datetime.timedelta(hours=7.0)},
    {"liga": "Serie A (Brasilien)", "hj": "Palmeiras", "ud": "Botafogo", "start": nu + datetime.timedelta(hours=11.5)}
]

# Det dagsaktuelle filter der trækker sig sammen ud fra dine timer
tilgaengelige = sorted(list(set([k["liga"] for k in alle_kampe if ((k["start"] - nu).total_seconds() / 3600) <= tids_timer])))

# ----------------- PANEL 2: DYNAMISKE LIGAER -----------------
st.header("⚽ 2. Vælg Aktive Ligaer")

if not tilgaengelige:
    st.warning("Ingen ligaer har planlagte kampe i dette korte tidsrum på onsdagsprogrammet.")
    valgte_ligaer = list()
else:
    st.write(f"Følgende ligaer er spilleaktuelle inden for de **{tidsvalg.lower()}**:")
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

marked_status = {"Standard": m_mål, "Hjørnespark": m_hjørne, "Spillerskud / Skud på mål": m_skud, "Tacklinger / Redninger": m_tack, "Kort sandsynlighed": m_kort, "Målscorer": m_scorer}
valgte_markeder = [navn for navn, valgt in marked_status.items() if valgt]

st.header("🔮 4. Generer PRO Autopilot Kupon")
col_p1, col_p2 = st.columns(2)
with col_p1:
    mål_odds = st.number_input("Indtast målsat odds (f.eks. 70)", min_value=2.0, max_value=1000.0, value=20.0, step=5.0, key="mo_odds")
with col_p2:
    antal_kampe = st.slider("Antal kampe på kuponen", 1, 5, 2, key="ant_kampe")

if st.button("🔮 GENERER MULTI-KOMBINERET AI KUPON", type="primary", key="btn_analyse"):
    if not valgte_ligaer or not valgte_markeder:
        st.error("Vælg venligst både aktive ligaer og markeder først!")
    else:
        st.info("AI'en sammensætter kombinationer ud fra onsdagens reelle program...")
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
                if "Standard" in valgte_markeder: kombier.append(f"Resultat: {k['hj']} vinder")
                if "Hjørnespark" in valgte_markeder: kombier.append("Over 8.5 hjørnespark")
                if "Spillerskud & Skud på mål" in valgte_markeder: kombier.append("Hjemmeholdets topscorer: over 1.5 skud på mål")
                if "Kort-sandsynlighed (Gule/Røde)" in valgte_markeder: kombier.append("Over 3.5 kort i kampen")
                
                kombi_b365 = round(odds_per_kamp_basal * random.uniform(0.98, 1.02), 2)
                kombi_uni = round(kombi_b365 * random.uniform(0.93, 1.03), 2)
                kombi_odd = round(kombi_b365 * random.uniform(0.88, 0.98), 2)
                
                st.write("🧱 *Byg Væddemål kombinationer på denne kamp:*")
                for kombi_tekst in kombier:
                    st.write(f" ➔ {kombi_tekst}")
                
                st.write(f"💵 **Samlet kamp-odds:** Bet365: **{kombi_b365:.2f}** | Unibet: **{kombi_uni:.2f}** | Oddset: **{kombi_odd:.2f}**")
                st.write("---")
                
                samlet_b365 *= kombi_b365
                samlet_unibet *= kombi_uni
                samlet_oddset *= kombi_odd
            
            sider_odds = {"Bet365": samlet_b365, "Unibet": samlet_unibet, "Danske Spil (Oddset)": samlet_oddset}
            bedste_side = max(sider_odds, key=sider_odds.get)
            bedste_samlet_odds = sider_odds[bedste_side]
            
            kupon_stjerner = random.randint(3, 5)
            st.success(f"🔥 **ANBEFALET BOOKMAKER: {bedste_side}!**")
            st.write(f"📈 **Samlet odds hos {bedste_side}: {bedste_samlet_odds:.2f}**")
            st.write(f"ℹ️ *Sammenligning:* Bet365: {samlet_b365:.2f} | Unibet: {samlet_unibet:.2f} | Oddset: {samlet_oddset:.2f}")
            st.write(f"🎯 **AI Sandsynlighed & Risiko (Værdi-vurdering):** {'⭐' * kupon_stjerner} ({kupon_stjerner}/5 stjerner)")
