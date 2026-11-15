import requests
import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from odds_motor import liga_favoritter, kamp_intelligens

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
    "UEFA - VM Kvalifikation": "fifa.worldq.uefa", "FIFA - Venskabskampe": "fifa.friendly",
}

def _parse_event(ev, liga, slug, nu, dk_tz, sete):
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
    ctx = kamp_intelligens.hurtig_kontekst(comp, hj, ud, slug)
    return {"id": ev_id, "label": f"{hj} vs {ud} ({liga} | {dk_dt.strftime('%d-%m %H:%M')})", "liga": liga, "hj": hj, "ud": ud, "dk_dt": dk_dt, "start": dk_dt.strftime("%d-%m-%Y kl. %H:%M"), "timer": round(max(0.1, diff), 2), "pct": 55.0, "ctx": ctx}

@st.cache_data(ttl=45, show_spinner=False)
def hent_kampe_v9(ligaer_tuple, timer_maks=24):
    dk_tz = ZoneInfo("Europe/Copenhagen")
    nu = datetime.now(dk_tz)
    datoer = [(nu + timedelta(days=d)).strftime("%Y%m%d") for d in range(5)]
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
                        if k := _parse_event(ev, liga, slug, nu, dk_tz, sete):
                            kampe.append(k)
            except Exception:
                continue
    return sorted(kampe, key=lambda x: x["dk_dt"])
