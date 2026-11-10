import importlib
import pkgutil
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from historik import gem_data
from odds_motor import autopilot_scanner, billed_parser

st.set_page_config(page_title="Odds Robot Pro", page_icon="🤖", layout="wide")

def dansk_tid():
    try:
        return datetime.now(ZoneInfo("Europe/Copenhagen")).strftime("%d-%m-%Y %H:%M")
    except Exception:
        return datetime.now().strftime("%d-%m-%Y %H:%M")

st.title("🤖 Odds Robot Pro")
st.write(f"Systemstatus: Supabase Aktiv | Dansk tid: {dansk_tid()} | Hovedfil Låst")

# Finder automatisk eventuelle fremtidige ekstra-mapper/moduler i 'udvidelser' uden at ændre app.py
ekstra_faner = []
try:
    import udvidelser
    for _, mod_navn, _ in pkgutil.iter_modules(udvidelser.__path__):
        mod = importlib.import_module(f"udvidelser.{mod_navn}")
        if hasattr(mod, "vis_modul"):
            titel = getattr(mod, "FANE_TITEL", f"➕ {mod_navn}")
            ekstra_faner.append((titel, mod.vis_modul))
except Exception:
    pass

fane_navne = [
    "🌐 1. Bred Automatisk Scanner",
    "⚽ 2. Manuel Hold Scanner",
    "📸 3. Kupon Scanner & Gemte",
    "📊 4. Statistik & Regnskab"
] + [t for t, _ in ekstra_faner]

faner = st.tabs(fane_navne)

# FANE 1: Bred Automatisk Scanner (Mappe 1)
with faner[0]:
    autopilot_scanner.vis_autopilot_scanner()

# FANE 2: Manuel Hold Scanner (Mappe 2 - næste trin i udviklingen)
with faner[1]:
    try:
        from odds_motor import manuel_scanner
        manuel_scanner.vis_manuel_scanner()
    except Exception:
        st.subheader("⚽ 2. Manuel Hold Scanner")
        soeg_hold = st.text_input("Søg efter et hvilket som helst hold eller liga:")
        valgt_udfald = st.text_input("Indtast ønsket spil/marked (f.eks. Over 8.5 hjørnespark):")
        manuelt_odds = st.number_input("Indtast odds:", min_value=1.01, value=2.50, step=0.10)
        if st.button("🚀 SPILLET (Gem manuelt spil i statistik)", key="btn_spillet_manuel"):
            if soeg_hold:
                gem_data.gem_kupon_i_historik(["Manuel"], [f"{soeg_hold}: {valgt_udfald}"], manuelt_odds, 0, 0, "Agnostisk", 5, 100.0)
                st.success(f"✓ '{soeg_hold}' er markeret som SPILLET og gemt i Supabase!")
                st.rerun()

# FANE 3: Kupon Scanner & Gemte Kuponer (Mappe 3)
with faner[2]:
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

# FANE 4: Statistik & Regnskab (Mappe 4)
with faner[3]:
    try:
        from historik import regnskab_visning
        regnskab_visning.vis_regnskab()
    except Exception:
        st.subheader("📊 Statistik & Økonomi Log (0-stillet start)")
        alle_spil = gem_data.hent_alle_kuponer()
        total_indsats = sum(float(s.get("indsats", 100.0)) for s in alle_spil) if alle_spil else 0.0
        antal_spil = len(alle_spil)
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Samlet Omsætning / Indsats", value=f"{total_indsats:.2f} kr.")
        with col2:
            st.metric(label="Antal Spillede Kuponer", value=f"{antal_spil} stk.")

# FREMTIDIGE EKSTRA FANER (Mappe 5, 6, 7 osv. indlæses automatisk herfra!)
for idx, (_, vis_fn) in enumerate(ekstra_faner, start=4):
    with faner[idx]:
        vis_fn()
