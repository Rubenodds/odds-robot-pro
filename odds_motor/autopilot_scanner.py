import math
import requests
import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from tidsstyring import dansk_tid
from odds_motor import liga_favoritter, byg_kupon, kamp_intelligens, manuel_hjaelp as mh
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
    comp["id"] = ev_id
    teams = comp.get("competitors") or []
    hj = next((c["team"]["displayName"] for c in teams if c.get("homeAway") == "home"), None)
    ud = next((c["team"]["displayName"] for c in teams if c.get("homeAway") == "away"), None)
    if not (hj and ud):
        return None
    sete.add(ev_id)
    ctx = kamp_intelligens.hurtig_kontekst(comp, hj, ud)
    return {"id": ev_id, "label": f"{hj} vs {ud} ({liga} | {dk_dt.strftime('%d-%m %H:%M')})", "liga": liga, "hj": hj, "ud": ud, "dk_dt": dk_dt, "start": dk_dt.strftime("%d-%m-%Y kl. %H:%M"), "timer": round(max(0.1, diff), 2), "pct": 55.0, "ctx": ctx}

@st.cache_data(ttl=120, show_spinner=False)
def _hent_kampe_v9(ligaer_tuple, timer_maks=24):
    dk_tz = ZoneInfo("Europe/Copenhagen")
    nu = datetime.now(dk_tz)
    dage = max(1, min(6, int((timer_maks // 24) + 2)))
    datoer = [(nu + timedelta(days=d)).strftime("%Y%m%d") for d in range(dage)]
    kampe, sete = [], set()
    for liga in (set(ligaer_tuple) | set(SLUGS.keys())) - {"Landskampe - FIFA / UEFA"}:
        slug = SLUGS.get(liga) or SLUGS.get(liga_favoritter.normaliser_liga_navn(liga))
        if not slug:
            continue
        for d_str in datoer:
            try:
                r = requests.get(f"{API.format(slug)}?dates={d_str}", headers=HDR, timeout=4)
                if r.status_code == 200:
                    for ev in r.json().get("events", []):
                        if k := _parse_event(ev, liga, nu, dk_tz, sete):
                            kampe.append(k)
            except Exception:
                continue
    return sorted(kampe, key=lambda x: x["dk_dt"])

def _vurder_kupon(valgte):
    o1 = round(math.prod(float(k.get("b365", 1.85)) for k in valgte), 2)
    o2 = round(math.prod(float(k.get("unibet", o1)) for k in valgte), 2)
    o3 = round(math.prod(float(k.get("oddset", o1)) for k in valgte), 2)
    prof = {"Bet365": o1, "Unibet": o2, "Danske Spil": o3}
    side = max(prof, key=prof.get)
    bo = prof[side]
    sp = round(max(1.0, min(95.0, math.prod(float(k.get("vinderchance_pct", 55.0)) / 100.0 for k in valgte) * 100.0)), 1)
    stj = 5 if sp >= 45 else (4 if sp >= 30 else (3 if sp >= 18 else (2 if sp >= 10 else 1)))
    flm = 1 if bo < 4 else (2 if bo < 12 else (3 if bo < 30 else (4 if bo < 65 else 5)))
    return side, bo, o2, o3, sp, stj, flm

def vis_autopilot_scanner():
    st.subheader("🌐 1. Autopilot Scanner (Form, H2H, Dommer & Vejr)")
    favs = list(liga_favoritter.hent_favorit_ligaer())
    timer = dansk_tid.vaelg_tidsramme("auto", standard=12)
    c1, c2 = st.columns(2)
    min_o, max_o = c1.slider("🎯 Ønsket odds-lag:", 2.0, 200.0, (20.0, 50.0), key="auto_odds")
    max_kampe = c2.number_input("🎫 Maks. kampe:", min_value=1, max_value=12, value=4, step=1, key="auto_max_kampe")

    alle = _hent_kampe_v9(tuple(favs), timer)
    aktive = [k for k in alle if 0 < k["timer"] <= timer]
    ligaer = sorted({k["liga"] for k in aktive})

    if ligaer:
        v_ligaer = st.multiselect(f"🏆 Aktive turneringer ({len(ligaer)} i {timer}T):", ligaer, default=ligaer, key="auto_ligaer")
        filt = [k for k in aktive if k["liga"] in v_ligaer]
        valg_mode = st.radio("🎯 Kampvalg:", [f"Alle kampe i valgte ligaer ({len(filt)} stk.)", "Håndpluk bestemte kampe"], horizontal=True, key="auto_mode")
        kandidater = [k for k in filt if k["label"] in st.multiselect("⚽ Søg kampe:", [k["label"] for k in filt], key="auto_k_v")] if valg_mode == "Håndpluk bestemte kampe" else filt
    else:
        kandidater = []
        f1 = next(iter(alle), None)
        st.info(f"📭 Ingen kampe inden for **{timer} timer**." + (f" Næste: **{f1['hj']} vs {f1['ud']}** ({f1['start']})." if f1 else ""))

    markeder = st.multiselect("📊 Specialmarkeder:", MARKEDER, default=MARKEDER[:3], key="auto_mark")
    b1, b2 = st.columns(2)
    if b1.button("🔍 FIND MEST SANDSYNLIGE KUPON", type="primary", key="btn_scan") or b2.button("⚡ SCAN ALLE VALGTE KAMPE", key="btn_scan_alle"):
        if not kandidater or not markeder:
            st.warning("⚠️ Vælg både kampe og specialmarkeder.")
        else:
            maal = round((min_o + max_o) / 2.0, 2)
            udv = kandidater if st.session_state.get("btn_scan_alle") else kandidater[:next((n for n in range(1, min(len(kandidater), max_kampe) + 1) if 1.45 <= maal ** (1.0 / n) <= 3.20), min(len(kandidater), max_kampe))]
            udv = kamp_intelligens.berig_valgte_kampe(udv)
            kupon = byg_kupon.byg_kombineret_kupon(udv, markeder, maal)
            for ko, uo in zip(kupon["kampe"], udv):
                ko["ctx"] = uo["ctx"]
            st.session_state["auto_kupon"] = kupon

    if kupon := st.session_state.get("auto_kupon"):
        st.markdown("### 🎫 Vælg hvilke forslag der skal med på kuponen:")
        valgte = []
        for i, k in enumerate(kupon["kampe"]):
            ctx = k.get("ctx", {})
            v = ctx.get("vejr")
            v_txt = f"{v['temp']}°C, {v['vind']} m/s ({v['effekt']})" if v else "Afventer"
            if st.checkbox(f"{i+1}. {k['hj']} vs {k['ud']} — {', '.join(k['kombinationer'])} (Odds: {k['b365']} | Chance: {k['vinderchance_pct']}%)", value=True, key=f"kupon_chk_{i}_{k['hj']}_{k['ud']}"):
                valgte.append(k)
            st.caption(f"📍 {k['liga']} | **{k['start']}** | Form: {ctx.get('hj_form')} vs {ctx.get('ud_form')} | Dommer: {ctx.get('dommer')} | Vejr: {v_txt}")
            st.caption(mh.begrundelse(k))
        if valgte:
            side, bo, uo, oo, sp, stj, flm = _vurder_kupon(valgte)
            vp = round(sp - round(100.0 / max(bo, 1.01), 1), 1)
            st.info(f"📊 **{len(valgte)}/{len(kupon['kampe'])} valg** | Odds: **{bo}** ({side}) | Chance: **{sp}%** | Værdi: {'⭐'*stj} ({vp:+.1f}%) | Risiko: {'🔥'*flm}")
            st.success(f"🧠 **Robottens vurdering:** **{len(valgte)} spil** til samlet odds **{bo:.2f}** ({side}) med **{sp:.1f}%** modelchance ({vp:+.1f}% edge).")
            kr = st.number_input("Indsats (kr.):", min_value=1.0, value=100.0, step=10.0, key="auto_kr")
            if st.button("🚀 SPILLET (Gem valgte i Supabase)", type="primary", key="btn_auto_spillet"):
                if gem_data.gem_kupon_i_historik(list({k["liga"] for k in valgte}), [f"{k['hj']} - {k['ud']} ({', '.join(k['kombinationer'])}) [{k['start']}]" for k in valgte], bo, uo, oo, side, stj, kr):
                    st.success("Kupon gemt i Supabase!")
        else:
            st.warning("Vælg mindst 1 kamp.")
