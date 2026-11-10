import requests
import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from odds_motor import liga_favoritter, byg_kupon, kamp_intelligens
from historik import gem_data

FEEDS = {
    "Danmark - Superliga": "https://espn.com",
    "England - Premier League": "https://espn.com",
    "England - Championship": "https://espn.com",
    "Spanien - La Liga": "https://espn.com",
    "Italien - Serie A": "https://espn.com",
    "Tyskland - Bundesliga": "https://espn.com",
    "Frankrig - Ligue 1": "https://espn.com",
    "Norge - Eliteserien": "https://espn.com",
    "Sverige - Allsvenskan": "https://espn.com",
    "Holland - Eredivisie": "https://espn.com",
    "Portugal - Liga Portugal": "https://espn.com",
    "Japan - J1 League": "https://espn.com",
    "UEFA - Champions League": "https://espn.com",
    "UEFA - Europa League": "https://espn.com",
}

MARKEDER = [
    "Standard (Mål / Kampvinder)", "Hjørnespark (Over/Under & Flest)",
    "Spillerskud & Skud på mål", "Tacklinger & Målmandsredninger",
    "Kort-sandsynlighed (Gule/Røde)", "Målscorer (Anytime/Første)", "Offsides",
]

@st.cache_data(ttl=300, show_spinner=False)
def _hent_kampe(ligaer_tuple):
    dk_tz = ZoneInfo("Europe/Copenhagen")
    nu = datetime.now(dk_tz)
    d_str = f"{nu.strftime('%Y%m%d')}-{(nu + timedelta(days=3)).strftime('%Y%m%d')}"
    kampe = []
    for liga in ligaer_tuple:
        url = FEEDS.get(liga)
        if not url:
            continue
        try:
            for ev in requests.get(f"{url}?dates={d_str}", timeout=5).json().get("events", []):
                if ev.get("status", {}).get("type", {}).get("state") != "pre":
                    continue
                dk_dt = datetime.fromisoformat(ev["date"].replace("Z", "+00:00")).astimezone(dk_tz)
                diff = (dk_dt - nu).total_seconds() / 3600.0
                if diff <= 0:
                    continue
                comp = ev.get("competitions", [{}])
                teams = comp.get("competitors", [])
                hj = next((c["team"]["displayName"] for c in teams if c.get("homeAway") == "home"), None)
                ud = next((c["team"]["displayName"] for c in teams if c.get("homeAway") == "away"), None)
                if hj and ud:
                    ctx = kamp_intelligens.analyser_kamp_kontekst(comp, hj, ud)
                    pct = round(max(35.0, min(95.0, byg_kupon.beregn_sandsynlighed_fra_odds(1.85) + ctx["justering_pct"])), 1)
                    kampe.append({"liga": liga, "hj": hj, "ud": ud, "dk_dt": dk_dt, "start": dk_dt.strftime("%d-%m-%Y kl. %H:%M"), "timer": round(diff, 2), "pct": pct, "ctx": ctx})
        except Exception:
            pass
    return sorted(kampe, key=lambda x: x["dk_dt"])

def vis_autopilot_scanner():
    st.subheader("🌐 1. Autopilot Scanner (Form, H2H, Dommer & Vejr)")
    favs = liga_favoritter.hent_favorit_ligaer()
    c1, c2 = st.columns(2)
    timer = c1.slider("⏱️ Tidsramme frem (timer):", 1, 72, 12, key="auto_timer")
    min_o, max_o = c2.slider("🎯 Ønsket odds-lag:", 2.0, 200.0, (20.0, 50.0), key="auto_odds")

    alle_kampe = _hent_kampe(tuple(favs))
    aktive = [k for k in alle_kampe if 0 < k["timer"] <= timer]
    aktive_ligaer = sorted(list({k["liga"] for k in aktive}))

    if aktive_ligaer:
        valgte_ligaer = st.multiselect(f"🏆 Ligaer med kampe inden for {timer}T:", aktive_ligaer, default=aktive_ligaer, key="auto_ligaer")
    else:
        valgte_ligaer = []
        naeste = f" Næste kamp: **{alle_kampe['hj']} vs {alle_kampe['ud']}** ({alle_kampe['start']})." if alle_kampe else ""
        st.info(f"📭 Ingen favoritligaer har kampe inden for **{timer} timer**.{naeste}")

    with st.expander(f"⚙️ Administrer favoritter ({len(favs)} aktive)"):
        ny = st.text_input("➕ Ny favoritliga:", key="auto_ny")
        if st.button("Gem favorit", key="auto_add") and liga_favoritter.tilfoej_ny_favorit_liga(ny):
            st.rerun()
        fjern = st.selectbox("🗑️ Fjern liga:", favs, key="auto_del_sel")
        if st.button("Fjern liga", key="auto_del") and liga_favoritter.fjern_favorit_liga(fjern):
            st.rerun()

    markeder = st.multiselect("📊 Specialmarkeder:", MARKEDER, default=MARKEDER[:3], key="auto_mark")
    if st.button("🔍 SCAN MARKEDET NU", type="primary", key="btn_scan") and valgte_ligaer and markeder:
        kand = sorted([k for k in aktive if k["liga"] in valgte_ligaer], key=lambda x: x["pct"], reverse=True)
        udv = kand[:min(len(kand), 5 if max_o >= 25 else 3)]
        kupon = byg_kupon.byg_kombineret_kupon(udv, markeder, round((min_o + max_o) / 2.0, 2))
        for i, k_obj in enumerate(kupon["kampe"]):
            k_obj["ctx"] = udv[i]["ctx"]
        st.session_state["auto_kupon"] = kupon

    kupon = st.session_state.get("auto_kupon")
    if kupon:
        for i, k in enumerate(kupon["kampe"], 1):
            ctx = k.get("ctx", {})
            v = ctx.get("vejr")
            v_txt = f"{v['temp']}°C, {v['vind']} m/s ({v['effekt']})" if v else "Afventer"
            st.write(f"**{i}. {k['hj']} vs {k['ud']}** ({k['liga']} | **{k['start']}**)")
            st.caption(f"Spil: {', '.join(k['kombinationer'])} | Odds: {k['b365']} | Chance: {k['vinderchance_pct']}% | Form: {ctx.get('hj_form')} vs {ctx.get('ud_form')} | Dommer: {ctx.get('dommer')} | Vejr: {v_txt}")
        st.info(f"⭐ {'⭐' * kupon['styrke']} | Bedste profil: {kupon['bedste_side']} | Samlet odds: **{kupon['bedste_odds']}**")
        indsats = st.number_input("Indsats (kr.):", min_value=1.0, value=100.0, step=10.0, key="auto_kr")
        if st.button("🚀 SPILLET (Gem i Supabase)", type="primary", key="btn_auto_spillet"):
            if gem_data.gem_kupon_i_historik(list({k["liga"] for k in kupon["kampe"]}), [f"{k['hj']} - {k['ud']} [{k['start']}]" for k in kupon["kampe"]], kupon["bedste_odds"], kupon["samlet_unibet"], kupon["samlet_oddset"], kupon["bedste_side"], kupon["styrke"], indsats):
                st.success("✓ Kupon gemt som SPILLET!")
                st.rerun()
