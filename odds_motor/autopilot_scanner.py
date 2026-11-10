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
    "England - FA Cup": "https://espn.com",
    "Spanien - La Liga": "https://espn.com",
    "Spanien - Copa del Rey": "https://espn.com",
    "Italien - Serie A": "https://espn.com",
    "Italien - Coppa Italia": "https://espn.com",
    "Tyskland - Bundesliga": "https://espn.com",
    "Tyskland - DFB Pokal": "https://espn.com",
    "Frankrig - Ligue 1": "https://espn.com",
    "Norge - Eliteserien": "https://espn.com",
    "Sverige - Allsvenskan": "https://espn.com",
    "Holland - Eredivisie": "https://espn.com",
    "Portugal - Liga Portugal": "https://espn.com",
    "Japan - J1 League": "https://espn.com",
    "UEFA - Champions League": "https://espn.com",
    "UEFA - Europa League": "https://espn.com",
    "Landskampe - FIFA / UEFA": "https://espn.com",
}

MARKEDER = [
    "Standard (Mål / Kampvinder)", "Hjørnespark (Over/Under & Flest)",
    "Spillerskud & Skud på mål", "Tacklinger & Målmandsredninger",
    "Kort-sandsynlighed (Gule/Røde)", "Målscorer (Anytime/Første)", "Offsides",
]

def _find_url(liga_navn):
    norm = liga_favoritter.normaliser_liga_navn(liga_navn)
    if norm in FEEDS:
        return FEEDS[norm]
    for k, v in FEEDS.items():
        if liga_navn.lower() in k.lower() or k.lower() in liga_navn.lower():
            return v
    return None

@st.cache_data(ttl=180, show_spinner=False)
def _hent_kampe(ligaer_tuple):
    dk_tz = ZoneInfo("Europe/Copenhagen")
    nu = datetime.now(dk_tz)
    d_str = f"{nu.strftime('%Y%m%d')}-{(nu + timedelta(days=3)).strftime('%Y%m%d')}"
    kampe = []
    for liga in ligaer_tuple:
        url = _find_url(liga)
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
                comps = ev.get("competitions", [])
                comp = comps[0] if comps else {}
                teams = comp.get("competitors", [])
                hj = next((c["team"]["displayName"] for c in teams if c.get("homeAway") == "home"), None)
                ud = next((c["team"]["displayName"] for c in teams if c.get("homeAway") == "away"), None)
                if hj and ud:
                    ctx = kamp_intelligens.analyser_kamp_kontekst(comp, hj, ud)
                    pct = round(max(35.0, min(95.0, byg_kupon.beregn_sandsynlighed_fra_odds(1.85) + ctx["justering_pct"])), 1)
                    label = f"{hj} vs {ud} ({liga} | {dk_dt.strftime('%d-%m %H:%M')})"
                    kampe.append({"label": label, "liga": liga, "hj": hj, "ud": ud, "dk_dt": dk_dt, "start": dk_dt.strftime("%d-%m-%Y kl. %H:%M"), "timer": round(diff, 2), "pct": pct, "ctx": ctx})
        except Exception:
            pass
    return sorted(kampe, key=lambda x: x["dk_dt"])

def _vaelg_bedste_kombination(kandidater, min_o, max_o, max_kampe):
    """Udvælger de mest sandsynlige kampe, hvis samlede odds rammer bedst ind i [min_o, max_o]."""
    sorteret = sorted(kandidater, key=lambda x: x["pct"], reverse=True)
    maal_odds = round((min_o + max_o) / 2.0, 2)
    bedste_antal = min(len(sorteret), max_kampe)
    for antal in range(1, min(len(sorteret), max_kampe) + 1):
        odds_pr_kamp = maal_odds ** (1.0 / antal)
        if 1.45 <= odds_pr_kamp <= 3.20:
            bedste_antal = antal
            break
    return sorteret[:bedste_antal], maal_odds

def vis_autopilot_scanner():
    st.subheader("🌐 1. Autopilot Scanner (Højeste Sandsynlighed til Valgt Odds)")
    favs = list(liga_favoritter.hent_favorit_ligaer())
    if st.checkbox("🌍 Inkludér Landskampe (FIFA / UEFA)", value=False, key="auto_landskampe"):
        if "Landskampe - FIFA / UEFA" not in favs:
            favs.append("Landskampe - FIFA / UEFA")

    c1, c2, c3 = st.columns(3)
    timer = c1.slider("⏱️ Tidsramme (timer):", 1, 72, 12, key="auto_timer")
    min_o, max_o = c2.slider("🎯 Ønsket odds-lag:", 2.0, 200.0, (20.0, 50.0), key="auto_odds")
    max_kampe = c3.slider("🎫 Maks. kampe på kupon:", 1, 12, 4, key="auto_max_kampe")

    alle_kampe = _hent_kampe(tuple(favs))
    aktive = [k for k in alle_kampe if 0 < k["timer"] <= timer]
    aktive_ligaer = sorted(list({k["liga"] for k in aktive}))

    if aktive_ligaer:
        valgte_ligaer = st.multiselect(f"🏆 Vælg ligaer med kampe ({len(aktive_ligaer)} aktive i {timer}T):", aktive_ligaer, default=aktive_ligaer, key="auto_ligaer")
        filtrerede = [k for k in aktive if k["liga"] in valgte_ligaer]
        valgte_labels = st.multiselect(f"⚽ Vælg kampe ({len(filtrerede)} tilgængelige):", [k["label"] for k in filtrerede], default=[k["label"] for k in filtrerede], key="auto_kampe_valgt")
        kandidater = [k for k in filtrerede if k["label"] in valgte_labels]
    else:
        kandidater = []
        naeste = f" Næste kamp: **{alle_kampe[0]['hj']} vs {alle_kampe[0]['ud']}** ({alle_kampe[0]['start']})." if alle_kampe else ""
        st.info(f"📭 Ingen aktive ligaer har kampe inden for **{timer} timer**.{naeste}")

    with st.expander(f"⚙️ Administrer favoritter ({len(liga_favoritter.hent_favorit_ligaer())} faste)"):
        ny = st.text_input("➕ Ny favoritliga:", key="auto_ny")
        if st.button("Gem favorit", key="auto_add") and liga_favoritter.tilfoej_ny_favorit_liga(ny):
            st.cache_data.clear()
            st.rerun()
        fjern = st.selectbox("🗑️ Fjern liga:", liga_favoritter.hent_favorit_ligaer(), key="auto_del_sel")
        if st.button("Fjern liga", key="auto_del") and liga_favoritter.fjern_favorit_liga(fjern):
            st.cache_data.clear()
            st.rerun()

    markeder = st.multiselect("📊 Specialmarkeder:", MARKEDER, default=MARKEDER[:3], key="auto_mark")
    b1, b2 = st.columns(2)
    scan_bedste = b1.button("🔍 FIND MEST SANDSYNLIGE KUPON", type="primary", key="btn_scan")
    scan_alle = b2.button("⚡ SCAN ALLE VALGTE KAMPE", key="btn_scan_alle")

    if (scan_bedste or scan_alle) and kandidater and markeder:
        if scan_alle:
            udv = sorted(kandidater, key=lambda x: x["pct"], reverse=True)
            maal_odds = round((min_o + max_o) / 2.0, 2)
        else:
            udv, maal_odds = _vaelg_bedste_kombination(kandidater, min_o, max_o, max_kampe)
        kupon = byg_kupon.byg_kombineret_kupon(udv, markeder, maal_odds)
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
