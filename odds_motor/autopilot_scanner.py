import math
import requests
import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from odds_motor import liga_favoritter, byg_kupon, kamp_intelligens
from historik import gem_data

HOST = "site.api." + "espn.com"
API = f"https://{HOST}/apis/site/v2/sports/soccer/{{}}/scoreboard"
HDR = {"User-Agent": "Mozilla/5.0"}
SLUGS = {
    "Danmark - Superliga": "den.1", "Danmark - 1. Division": "den.2", "Danmark - Pokalen": "den.cup",
    "England - Premier League": "eng.1", "England - Championship": "eng.2", "England - League One": "eng.3",
    "England - FA Cup": "eng.fa", "England - EFL Cup": "eng.league_cup",
    "Spanien - La Liga": "esp.1", "Spanien - Segunda División": "esp.2", "Spanien - Copa del Rey": "esp.copa_del_rey",
    "Italien - Serie A": "ita.1", "Italien - Serie B": "ita.2", "Italien - Coppa Italia": "ita.coppa_italia",
    "Tyskland - Bundesliga": "ger.1", "Tyskland - 2. Bundesliga": "ger.2", "Tyskland - DFB Pokal": "ger.dfb_pokal",
    "Frankrig - Ligue 1": "fra.1", "Frankrig - Ligue 2": "fra.2", "Frankrig - Coupe de France": "fra.coupe_de_france",
    "Norge - Eliteserien": "nor.1", "Norge - OBOS-ligaen": "nor.2", "Sverige - Allsvenskan": "swe.1",
    "Holland - Eredivisie": "ned.1", "Portugal - Liga Portugal": "por.1",
    "Brasilien - Serie A": "bra.1", "Brasilien - Serie B": "bra.2",
    "Japan - J1 League": "jpn.1", "Japan - J2 League": "jpn.2",
    "UEFA - Champions League": "uefa.champions", "UEFA - Europa League": "uefa.europa",
    "UEFA - Conference League": "uefa.europa.conf", "UEFA - Nations League": "uefa.nations",
    "UEFA - VM Kvalifikation": "fifa.worldq.uefa",
}
SLUG_TIL_LIGA = {v: k for k, v in SLUGS.items()}
MARKEDER = [
    "Standard (Mål / Kampvinder)", "Hjørnespark (Over/Under & Flest)", "Spillerskud & Skud på mål",
    "Tacklinger & Målmandsredninger", "Kort-sandsynlighed (Gule/Røde)", "Målscorer (Anytime/Første)", "Offsides",
]

def _parse_event(ev, liga, nu, dk_tz, sete):
    ev_id = ev.get("id")
    if not ev_id or ev_id in sete or (ev.get("status") or {}).get("type", {}).get("state") == "post":
        return None
    raw_dt = ev.get("date", "")
    if len(raw_dt) == 17 and raw_dt.endswith("Z"):
        raw_dt = raw_dt[:-1] + ":00Z"
    dk_dt = datetime.fromisoformat(raw_dt.replace("Z", "+00:00")).astimezone(dk_tz)
    diff = (dk_dt - nu).total_seconds() / 3600.0
    if diff <= -0.25:
        return None
    comp = next(iter(ev.get("competitions") or []), {})
    teams = comp.get("competitors") or []
    hj = next((c["team"]["displayName"] for c in teams if c.get("homeAway") == "home"), None)
    ud = next((c["team"]["displayName"] for c in teams if c.get("homeAway") == "away"), None)
    if not (hj and ud):
        return None
    sete.add(ev_id)
    try:
        ctx = kamp_intelligens.analyser_kamp_kontekst(comp, hj, ud)
        pct = round(max(35.0, min(95.0, byg_kupon.beregn_sandsynlighed_fra_odds(1.85) + ctx.get("justering_pct", 0.0))), 1)
    except Exception:
        ctx = {"justering_pct": 0.0, "hj_form": "Ukendt", "ud_form": "Ukendt", "dommer": "Afventer", "vejr": None}
        pct = 54.0
    return {"id": ev_id, "label": f"{hj} vs {ud} ({liga} | {dk_dt.strftime('%d-%m %H:%M')})", "liga": liga, "hj": hj, "ud": ud, "dk_dt": dk_dt, "start": dk_dt.strftime("%d-%m-%Y kl. %H:%M"), "timer": round(max(0.1, diff), 2), "pct": pct, "ctx": ctx}

@st.cache_data(ttl=120, show_spinner=False)
def _hent_kampe_v9(ligaer_tuple):
    dk_tz = ZoneInfo("Europe/Copenhagen")
    nu = datetime.now(dk_tz)
    datoer = [(nu + timedelta(days=d)).strftime("%Y%m%d") for d in range(4)]
    kampe, sete = [], set()
    for liga in (set(ligaer_tuple) | set(SLUGS.keys())) - {"Landskampe - FIFA / UEFA"}:
        slug = SLUGS.get(liga) or SLUGS.get(liga_favoritter.normaliser_liga_navn(liga))
        if not slug:
            continue
        for d_str in datoer:
            try:
                r = requests.get(f"{API.format(slug)}?dates={d_str}", headers=HDR, timeout=5)
                if r.status_code == 200:
                    for ev in r.json().get("events", []):
                        if k := _parse_event(ev, liga, nu, dk_tz, sete):
                            kampe.append(k)
            except Exception:
                continue
    for d_str in datoer:
        try:
            r = requests.get(f"{API.format('all')}?dates={d_str}", headers=HDR, timeout=6)
            if r.status_code == 200:
                for ev in r.json().get("events", []):
                    links_txt = " ".join(lk.get("href", "") for lk in ev.get("links") or []).lower()
                    match_liga = next((orig for slug, orig in SLUG_TIL_LIGA.items() if f"/{slug}/" in links_txt or slug in links_txt), None)
                    if match_liga and (k := _parse_event(ev, match_liga, nu, dk_tz, sete)):
                        kampe.append(k)
        except Exception:
            continue
    return sorted(kampe, key=lambda x: x["dk_dt"])

def _vaelg_bedste_kombination(kandidater, min_o, max_o, max_kampe):
    sorteret = sorted(kandidater, key=lambda x: x["pct"], reverse=True)
    maal = round((min_o + max_o) / 2.0, 2)
    antal = next((n for n in range(1, min(len(sorteret), max_kampe) + 1) if 1.45 <= maal ** (1.0 / n) <= 3.20), min(len(sorteret), max_kampe))
    return sorteret[:antal], maal

def _vurder_kupon(valgte):
    odds_b365 = round(math.prod(float(k.get("b365", 1.85)) for k in valgte), 2)
    odds_uni = round(math.prod(float(k.get("unibet", k.get("b365", 1.85))) for k in valgte), 2)
    odds_odd = round(math.prod(float(k.get("oddset", k.get("b365", 1.85))) for k in valgte), 2)
    profiler = {"Bet365": odds_b365, "Unibet": odds_uni, "Danske Spil": odds_odd}
    bedste_side = max(profiler, key=profiler.get)
    bedste_odds = profiler[bedste_side]
    samlet_pct = round(max(1.0, min(95.0, math.prod(float(k.get("vinderchance_pct", 55.0)) / 100.0 for k in valgte) * 100.0)), 1)
    stjerner = 5 if samlet_pct >= 45 else (4 if samlet_pct >= 30 else (3 if samlet_pct >= 18 else (2 if samlet_pct >= 10 else 1)))
    flammer = 1 if bedste_odds < 4 else (2 if bedste_odds < 12 else (3 if bedste_odds < 30 else (4 if bedste_odds < 65 else 5)))
    return bedste_side, bedste_odds, odds_uni, odds_odd, samlet_pct, stjerner, flammer

def vis_autopilot_scanner():
    st.subheader("🌐 1. Autopilot Scanner (Form, H2H, Dommer & Vejr)")
    favs = list(liga_favoritter.hent_favorit_ligaer())

    c1, c2, c3 = st.columns(3)
    timer = c1.slider("⏱️ Tidsramme frem (timer):", 1, 72, 48, key="auto_timer")
    min_o, max_o = c2.slider("🎯 Ønsket odds-lag:", 2.0, 200.0, (20.0, 50.0), key="auto_odds")
    max_kampe = c3.slider("🎫 Maks. kampe på kupon:", 1, 12, 4, key="auto_max_kampe")

    alle = _hent_kampe_v9(tuple(favs))
    aktive = [k for k in alle if 0 < k["timer"] <= timer]
    ligaer = sorted({k["liga"] for k in aktive})

    if ligaer:
        v_ligaer = st.multiselect(f"🏆 Aktive turneringer ({len(ligaer)} i {timer}T):", ligaer, default=ligaer, key="auto_ligaer")
        filt = [k for k in aktive if k["liga"] in v_ligaer]
        valg_mode = st.radio("🎯 Kampvalg:", [f"Alle kampe i valgte ligaer ({len(filt)} stk.)", "Håndpluk bestemte kampe"], horizontal=True, key="auto_mode")
        if valg_mode == "Håndpluk bestemte kampe":
            v_labels = st.multiselect("⚽ Søg og vælg dine kampe:", [k["label"] for k in filt], default=[], key="auto_kampe_valgt")
            kandidater = [k for k in filt if k["label"] in v_labels]
        else:
            kandidater = filt
    else:
        kandidater = []
        foerste = next(iter(alle), None)
        naeste = f" Næste kamp: **{foerste['hj']} vs {foerste['ud']}** ({foerste['start']})." if foerste else ""
        st.info(f"📭 Ingen turneringer har kampe inden for **{timer} timer**.{naeste}")

    with st.expander(f"⚙️ Administrer favoritter ({len(favs)} aktive)"):
        ny = st.text_input("➕ Ny favoritliga:", key="auto_ny")
        if st.button("Gem favorit", key="auto_add") and liga_favoritter.tilfoej_ny_favorit_liga(ny):
            st.cache_data.clear()
            st.rerun()
        fjern = st.selectbox("🗑️ Fjern liga:", favs, key="auto_del_sel")
        if st.button("Fjern liga", key="auto_del") and liga_favoritter.fjern_favorit_liga(fjern):
            st.cache_data.clear()
            st.rerun()

    markeder = st.multiselect("📊 Specialmarkeder:", MARKEDER, default=MARKEDER[:3], key="auto_mark")
    b1, b2 = st.columns(2)
    if (b1.button("🔍 FIND MEST SANDSYNLIGE KUPON", type="primary", key="btn_scan") or b2.button("⚡ SCAN ALLE VALGTE KAMPE", key="btn_scan_alle")):
        if not kandidater:
            st.warning("⚠️ Vælg mindst én kamp eller liga først.")
        elif not markeder:
            st.warning("⚠️ Vælg mindst ét specialmarked først.")
        else:
            udv, maal = (sorted(kandidater, key=lambda x: x["pct"], reverse=True), round((min_o + max_o) / 2.0, 2)) if st.session_state.get("btn_scan_alle") else _vaelg_bedste_kombination(kandidater, min_o, max_o, max_kampe)
            kupon = byg_kupon.byg_kombineret_kupon(udv, markeder, maal)
            for k_obj, u_obj in zip(kupon["kampe"], udv):
                k_obj["ctx"] = u_obj["ctx"]
            st.session_state["auto_kupon"] = kupon

    if kupon := st.session_state.get("auto_kupon"):
        st.markdown("### 🎫 Vælg hvilke forslag der skal med på kuponen:")
        valgte_kampe = []
        for i, k in enumerate(kupon["kampe"]):
            ctx = k.get("ctx", {})
            v = ctx.get("vejr")
            v_txt = f"{v['temp']}°C, {v['vind']} m/s ({v['effekt']})" if v else "Afventer"
            titel = f"{i+1}. {k['hj']} vs {k['ud']} — {', '.join(k['kombinationer'])} (Odds: {k['b365']} | Chance: {k['vinderchance_pct']}%)"
            if st.checkbox(titel, value=True, key=f"kupon_chk_{i}_{k['hj']}_{k['ud']}"):
                valgte_kampe.append(k)
