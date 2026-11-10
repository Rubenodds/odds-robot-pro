import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from historik import gem_data
from odds_motor import billed_parser

st.set_page_config(page_title="Odds Robot Pro", page_icon="🤖", layout="wide")

def dansk_tid():
    try:
        return datetime.now(ZoneInfo("Europe/Copenhagen")).strftime("%d-%m-%Y %H:%M")
    except Exception:
        return datetime.now().strftime("%d-%m-%Y %H:%M")

st.title("🤖 Odds Robot Pro")
st.write(f"Systemstatus: Supabase Aktiv | Dansk tid: {dansk_tid()} | Hovedfil Låst")

fane1, fane2, fane3, fane4 = st.tabs([
    "🌐 1. Bred Automatisk Scanner", 
    "⚽ 2. Manuel Hold Scanner", 
    "📸 3. Kupon Scanner & Gemte", 
    "📊 4. Statistik & Regnskab"
])

# FANE 1: Bred Automatisk Scanner
with fane1:
    st.subheader("🌐 Automatisk scanner inden for tidsramme")
    timer = st.slider("Tidsramme for scanning (timer):", 1, 48, 6)
    min_o, max_o = st.slider("Ønsket odds-interval:", 2.0, 200.0, (20.0, 50.0))
    
    st.info(f"Scanner markedet bredt for de næste {timer} timer i odds-laget {min_o} - {max_o}...")
    if st.button("🚀 SPILLET (Føj automatisk kupon til statistik)", key="btn_spillet_auto"):
        gem_data.gem_kupon_i_historik(["Autopilot"], [f"Bred Scan ({timer}H)"], (min_o+max_o)/2, 0, 0, "Agnostisk", 4, 100.0)
        st.success("✓ Autopilot-kupon er markeret som SPILLET og logget i Supabase!")
        st.rerun()

# FANE 2: Manuel Hold Scanner
with fane2:
    st.subheader("⚽ Manuel Hold Scanner")
    soeg_hold = st.text_input("Søg efter et hvilket som helst hold eller liga:")
    valgt_udfald = st.text_input("Indtast ønsket spil/marked (f.eks. Over 8.5 hjørnespark):")
    manuelt_odds = st.number_input("Indtast odds:", min_value=1.01, value=2.50, step=0.10)
    
    if st.button("🚀 SPILLET (Gem manuelt spil i statistik)", key="btn_spillet_manuel"):
        if soeg_hold:
            gem_data.gem_kupon_i_historik(["Manuel"], [f"{soeg_hold}: {valgt_udfald}"], manuelt_odds, 0, 0, "Agnostisk", 5, 100.0)
            st.success(f"✓ '{soeg_hold}' er markeret som SPILLET og gemt i Supabase!")
            st.rerun()

# FANE 3: Kupon Scanner & Gemte Kuponer
with fane3:
    st.subheader("📸 Kupon Scanner & Gemte Kuponer")
    billed_parser.vis_billed_scanner()
    
    st.markdown("---")
    st.write("### 📂 Gemte Spillede Kuponer (Hentet fra Supabase):")
    alle_spil = gem_data.hent_alle_kuponer()
    if alle_spil:
        for s in alle_spil:
            st.write(f"🎫 **{s.get('kampe')}** | Odds: `{s.get('odds')}` | Indsats: `{s.get('indsats', 100)} kr.`")
    else:
        st.info("Ingen spillede kuponer i databasen endnu (0-stillet start).")

# FANE 4: Statistik & Regnskab (0-stillet udgangspunkt til offentlig brug)
with fane4:
    st.subheader("📊 Statistik & Økonomi Log (0-stillet start)")
    alle_spil = gem_data.hent_alle_kuponer()
    
    total_indsats = sum(float(s.get("indsats", 100.0)) for s in alle_spil) if alle_spil else 0.0
    antal_spil = len(alle_spil)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Samlet Omsætning / Indsats", value=f"{total_indsats:.2f} kr.")
    with col2:
        st.metric(label="Antal Spillede Kuponer", value=f"{antal_spil} stk.")
        
    st.write("---")
    st.write("- Statistisk indsigt (holdopstillinger, offsides, målspark) opsamles automatisk i Supabase ved afvikling.")
