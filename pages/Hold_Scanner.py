import streamlit as st
import datetime
import random
from tidsstyring import dansk_tid
from kampprogram import hent_kampe
from odds_motor import byg_kupon
from historik import gem_data

st.set_page_config(page_title="AI Favorit-Hold Scanner", page_icon="🎯", layout="centered")

st.title("🎯 AI Favorit-Hold Scanner")
st.write("Vælg tidsinterval og ligaer for kun at søge blandt de hold, der er spilleaktuelle.")

# ----------------- PANEL 1: INDSTILLINGER -----------------
st.header("⏳ 1. Indstil dit tidsinterval")

tidsvalg = st.radio(
    "Hvor langt frem i tiden skal robotten kigge efter kampe?",
    ["Næste 3 timer", "Næste 6 timer", "Næste 12 timer", "Næste 24 timer", "Næste 48 timer"],
    key="tids_valg_scanner_side"
)

if "3 timer" in tidsvalg: tids_timer = 3.0
elif "6 timer" in tidsvalg: tids_timer = 6.0
elif "12 timer" in tidsvalg: tids_timer = 12.0
elif "24 timer" in tidsvalg: tids_timer = 24.0
else: tids_timer = 48.0

# Henter den præcise tid og det fælles, ægte kampprogram
nu = dansk_tid.hent_dansk_klokkeslaet()
alle_kampe = hent_kampe.hent_aegte_kampe_fra_nettet()

# Backup baseret på programmet
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

# 1. TIMEFILTER: Finder de ligaer, der overhovedet har kampe i tidsrummet
tilgaengelige_ligaer = sorted(list(set([k["liga"] for k in alle_kampe if ((k["start"] - nu).total_seconds() / 3600) <= tids_timer])))

st.header("⚽ 2. Vælg Aktive Ligaer")
if not tilgaengelige_ligaer:
    st.warning("Ingen ligaer har planlagte kampe i dette tidsrum.")
    valgte_ligaer = list()
else:
    liga_afkrydsning = {}
    kolonner = st.columns(min(3, len(tilgaengelige_ligaer)))
    for idx, liga_navn in enumerate(tilgaengelige_ligaer):
        med_kolonne = kolonner[idx % len(kolonner)]
        with med_kolonne:
            liga_afkrydsning[liga_navn] = st.checkbox(liga_navn, value=True, key=f"scanner_chk_{liga_navn}")
    valgte_ligaer = [navn for navn, valgt in liga_afkrydsning.items() if valgt]

# 2. LIGAFILTER & TIMEFILTER PÅ KAMPE: Finder KUN de reelle, aktive kampe, der matcher begge krav
aktive_kampe_i_periode = [
    k for k in alle_kampe 
    if k["liga"] in valgte_ligaer and ((k["start"] - nu).total_seconds() / 3600) <= tids_timer
]

# ----------------- FILTRERING AF HOLD (SKUDSIKKER REGL) -----------------
st.header("🎯 3. Vælg dine favorit-hold")

if not aktive_kampe_i_periode:
    st.info("Sæt flueben ved ligaerne ovenfor for at få vist de spilleaktuelle hold.")
else:
    # Initialiserer session state til dine valg
    if "mine_valgte_hold" not in st.session_state:
        st.session_state["mine_valgte_hold"] = []

    # Vi bygger rullemenuen dynamisk hver gang der sker et valg!
    valgte_nu = st.session_state["mine_valgte_hold"]
    
    # REGLEN: Find alle de modstandere, der skal blokeres omgående
    blokerede_hold = set()
    for k in aktive_kampe_i_periode:
        if k["hj"] in valgte_nu or k["ud"] in valgte_nu:
            # Hvis et af holdene i kampen er valgt, blokerer vi BEGGE hold fra fremtidige valg
            blokerede_hold.add(k["hj"])
            blokerede_hold.add(k["ud"])

    # Listen over tilgængelige valg skæres benhårdt til:
    # Den indeholder kun hold, der IKKE er blokerede, PLUS dem du allerede har klikket af
    aktive_hold_liste = sorted(list(set(
        [k["hj"] for k in aktive_kampe_i_periode if k["hj"] not in blokerede_hold or k["hj"] in valgte_nu] + 
        [k["ud"] for k in aktive_kampe_i_periode if k["ud"] not in blokerede_hold or k["ud"] in valgte_nu]
    )))

    # Viser rullemenuen med den trimmede liste
    valg_opdateret = st.multiselect(
        f"Søg blandt de hold, der spiller inden for {tidsvalg.lower()}:",
        options=aktive_hold_liste,
        default=valgte_nu,
        help="Når du vælger et hold, forsvinder modstanderen med det samme fra rullemenuen.",
        key="hold_scanner_skudsikker_multi"
    )

    # Hvis der er sket ændringer i valgene, opdaterer vi og genindlæser siden med det samme så modstanderne kastes ud!
    if valg_opdateret != valgte_nu:
        st.session_state["mine_valgte_hold"] = valg_opdateret
        st.rerun()

    valgte_hold = valg_opdateret

st.header("📊 4. Indstil dit målodds")
maal_odds = st.number_input("Målsat odds for dine valgte hold:", min_value=2.0, max_value=1000.0, value=10.0, step=2.0, key="scanner_odds_input")

if st.button("🔍 SCAN SPECIAL-MARKEDER PÅ MINE HOLD", type="primary", key="btn_scanner_side_generer"):
    if not st.session_state["mine_valgte_hold"]:
        st.error("Vælg venligst mindst ét hold i søgefeltet først!")
    else:
        kampe_til_analyse = [k for k in aktive_kampe_i_periode if k["hj"] in st.session_state["mine_valgte_hold"] or k["ud"] in st.session_state["mine_valgte_hold"]]
        
        if not kampe_til_analyse:
            st.warning("De valgte hold spiller ikke i de markerede ligaer inden for dette tidsinterval.")
        else:
            st.subheader(f"📊 Eksklusiv AI Analyse af dine hold:")
            st.write("---")
            
            markeder_pro = ["Standard (Mål / Kampvinder)", "Hjørnespark (Over/Under & Flest)", "Spillerskud & Skud på mål", "Tacklinger & Målmandsredninger"]
            resultat = byg_kupon.byg_kombineret_kupon(kampe_til_analyse, markeder_pro, maal_odds)
            
            if resultat:
                gemme_ligaer = list()
                gemme_forslag = list()
                
                for idx_k, k in enumerate(resultat["kampe"]):
                    timer_rest = (k["start"] - nu).total_seconds() / 3600
                    st.write(f"🏟️ **KAMP {idx_k+1}: [{k['liga']}] {k['hj']} vs. {k['ud']}** (Start om {timer_rest:.1f} timer)")
                    st.write("🧱 *Funderet Byg Væddemål på denne kamp:*")
                    for kombi_tekst in k["kombinationer"]:
                        st.write(f" ➔ {kombi_tekst}")
                        gemme_forslag.append(f"[{k['hj']}-{k['ud']}]: {kombi_tekst}")
                    st.write(f"💵 **Kamp-odds:** Bet365: **{k['b365']:.2f}** | Unibet: **{k['uni']:.2f}** | Oddset: **{k['oddset']:.2f}**")
                    st.write("---")
                    gemme_ligaer.append(k["liga"])
                
                st.success(f"🔥 **BEDSTE BOOKMAKER FOR DINE FAVORITTER: {resultat['bedste_side']}!**")
                st.write(f"📈 **Samlet odds for dine valg hos {resultat['bedste_side']}: {resultat['bedste_odds']:.2f}**")
                st.write(f"ℹ️ *Sammenligning:* Bet365: {resultat['samlet_b365']:.2f} | Unibet: {resultat['samlet_unibet']:.2f} | Oddset: {resultat['samlet_oddset']:.2f}")
                st.write(f"🎯 **AI Sandsynlighed & Risiko (Værdi-vurdering):** {'⭐' * resultat['styrke']} ({resultat['styrke']}/5 stjerner)")
                
                gem_data.gem_kupon_i_historik(gemme_ligaer, gemme_forslag, resultat["samlet_b365"], resultat["samlet_unibet"], resultat["samlet_oddset"], resultat["bedste_side"], resultat["styrke"])
                st.info("🧠 Favorit-kupon gemt i AI-historikken!")
