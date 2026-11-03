import streamlit as st
import datetime
import ai_hjerne

# Start den nye pro-database
ai_hjerne.init_database()

st.set_page_config(page_title="AI Oddset Robot PRO", page_icon="⚡", layout="centered")

st.title("⚡ AI Oddset Multi-Robot PRO")
st.write("Avanceret live-simulering med tidsintervaller og special-markeder.")

# ----------------- PANEL 1: TIDSFILTER & LIGAER -----------------
st.header("⏳ 1. Indstil Tidsramme & Ligaer")

tidsvalg = st.radio(
    "Hvor langt frem i tiden skal robotten kigge efter kampe?",
    ["Lige nu & de næste 3 timer (Live/Hurtige spil)", "De næste 48 timer (Weekend/Midtuge kupon)"]
)
tids_timer = 3.0 if "3 timer" in tidsvalg else 48.0

# Mulighed for at vælge præcis de ligaer man vil have med
st.write("**Vælg dine aktive ligaer:**")
col_liga1, col_liga2 = st.columns(2)
with col_liga1:
    liga_pl = st.checkbox("Premier League", value=True)
    liga_sl = st.checkbox("Superligaen", value=True)
    liga_ll = st.checkbox("LaLiga", value=True)
    liga_sa = st.checkbox("Serie A (Italien)", value=True)
with col_liga2:
    liga_bl = st.checkbox("Bundesliga (Tyskland)", value=True)
    liga_ch = st.checkbox("Championship (England)", value=True)
    liga_cl = st.checkbox("Champions League", value=True)
    liga_pk = st.checkbox("Betano Pokalen", value=True)

# Saml de valgte ligaer i en liste til hjernen
valgte_ligaer = []
if liga_pl: valgte_ligaer.append("Premier League")
if liga_sl: valgte_ligaer.append("Superligaen")
if liga_ll: valgte_ligaer.append("LaLiga")
if liga_sa: valgte_ligaer.append("Serie A (Italien)")
if liga_bl: valgte_ligaer.append("Bundesliga (Tyskland)")
if liga_ch: valgte_ligaer.append("Championship (England)")
if liga_cl: valgte_ligaer.append("Champions League")
if liga_pk: valgte_ligaer.append("Betano Pokalen")

# ----------------- PANEL 2: AVANCEREDE MARKEDER -----------------
st.header("📊 2. Vælg Special-Markeder")
st.write("Sæt kryds ved de statistikker, AI'en må kombinere på kuponen:")

col_m1, col_m2 = st.columns(2)
with col_m1:
    m_mål = st.checkbox("Standard (Mål / Kampvinder)", value=True)
    m_hjørne = st.checkbox("Hjørnespark (Over/Under & Flest)", value=True)
    m_skud = st.checkbox("Spillerskud & Skud på mål", value=True)
with col_m2:
    m_tack = st.checkbox("Tacklinger & Målmandsredninger", value=True)
    m_kort = st.checkbox("Kort-sandsynlighed (Gule/Røde)", value=True)
    m_scorer = st.checkbox("Målscorer (Anytime/Første)", value=True)

# Saml de valgte markeder
valgte_markeder = []
if m_mål: valgte_markeder.append("Standard")
if m_hjørne: valgte_markeder.append("Hjørnespark")
if m_skud: valgte_markeder.append("Spillerskud / Skud på mål")
if m_tack: valgte_markeder.append("Tacklinger / Redninger")
if m_kort: valgte_markeder.append("Kort sandsynlighed")
if m_scorer: valgte_markeder.append("Målscorer")

# ----------------- PANEL 3: BEREGNING -----------------
st.header("🔮 3. Generer PRO Autopilot Kupon")

col_p1, col_p2 = st.columns(2)
with col_p1:
    mål_odds = st.number_input("Indtast målsat odds (f.eks. 10 eller 500)", min_value=2.0, max_value=1000.0, value=15.0, step=5.0)
with col_p2:
    antal_kampe = st.slider("Antal kampe på kuponen", 2, 10, 5)

if st.button("🚀 KØR AI PRO ANALYSE", type="primary"):
    if not valgte_ligaer:
        st.error("Du skal vælge mindst én liga for at køre analysen!")
    elif not valgte_markeder:
        st.error("Du skal vælge mindst ét special-marked for at bygge væddemål!")
    else:
        st.info(f"Støvsuger nettet for kampe inden for de næste {tids_timer:.0f} timer...")
        
        # Hent kuponforslag fra den nye, kloge ai_hjerne.py
        kupon, samlet_odds = ai_hjerne.byg_pro_kupon(mål_odds, antal_kampe, valgte_ligaer, tids_timer, valgte_markeder)
        
        if not kupon:
            st.warning("Ingen kampe matchede dine krav i den valgte tidsramme. Prøv at udvide til 48 timer eller vælge flere ligaer.")
        else:
            st.subheader(f"📊 Din AI PRO Kupon (Samlet odds: {samlet_odds:.2f})")
            st.write(f"Tidsramme: **{tidsvalg}**")
            st.write("---")
            
            for i, k in enumerate(kupon):
                st.write(f"⚽ **{i+1}. [{k['liga']}] {k['hjemme']} vs. {k['ude']}**")
                st.write(f" ➔ **Marked:** {k['marked']}")
                st.write(f" ➔ **AI Anbefaling:** {k['spil']} (Odds {k['odds']:.2f})")
                st.write("---")
                
                # Gemmer det hele automatisk i pro-historikken
                nu_str = datetime.datetime.now().strftime("%Y-%m-%d")
                tid_str = datetime.datetime.now().strftime("%H:%M")
                ai_hjerne.gem_pro_kupon(nu_str, tid_str, k['liga'], k['hjemme'], k['ude'], k['marked'], k['spil'], k['odds'], 'Afventer')
                
            st.success("🔥 Kupon slynget ud og gemt i din pro-historik. AI'en følger kampene automatisk!")
