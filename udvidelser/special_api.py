import json, os, requests
import streamlit as st

LAERT_FIL = "udvidelser/laert_special_data.json"
LIGA_MAP = {
    "eng.1": "soccer_epl", "eng.2": "soccer_efl_champ", "esp.1": "soccer_spain_la_liga",
    "ger.1": "soccer_germany_bundesliga", "ita.1": "soccer_italy_serie_a",
    "fra.1": "soccer_france_ligue_one", "den.1": "soccer_denmark_superliga",
    "uefa.champions": "soccer_uefa_champs_league", "uefa.europa": "soccer_uefa_europa_league",
    "uefa.nations": "soccer_uefa_nations_league", "fifa.worldq.uefa": "soccer_fifa_world_cup_qualifiers_europe"
}
ALLE_API_MARKEDER = (
    "h2h,spreads,totals,btts,draw_no_bet,double_chance,h2h_h1,totals_h1,"
    "player_goal_scorer_anytime,player_shots_on_target,player_shots,player_assists"
)

def oversaet_da(tekst):
    erstat = {"Over": "Over", "Under": "Under", "Yes": "Ja", "No": "Nej", "Draw": "Uafgjort", "Home": "Hjemmesejr", "Away": "Udesejr", "1st Half": "1. halvleg"}
    res = str(tekst)
    for eng, da in erstat.items():
        res = res.replace(eng, da)
    return res

def hent_startopstilling(espn_id, liga_kode="eng.1"):
    if not espn_id:
        return []
    url = f"https://espn.com{liga_kode}/summary?event={espn_id}"
    try:
        data = requests.get(url, timeout=5).json()
        return [p.get("athlete", {}).get("displayName", "") for h in data.get("rosters", []) for p in h.get("roster", []) if p.get("starter") and p.get("athlete", {}).get("displayName")]
    except Exception:
        return []

def _gem_laert(liga_kode, poster):
    if not poster:
        return
    os.makedirs("udvidelser", exist_ok=True)
    db = {}
    if os.path.exists(LAERT_FIL):
        try:
            with open(LAERT_FIL, "r", encoding="utf-8") as f:
                db = json.load(f)
        except Exception:
            db = {}
    db[liga_kode] = poster[:25]
    with open(LAERT_FIL, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

@st.cache_data(ttl=1800, show_spinner=False)
def hent_kamp_tilbud(liga_kode, event_id="", api_noegle=""):
    sport = LIGA_MAP.get(liga_kode)
    if not api_noegle or not sport:
        return _laes_fallback(liga_kode), None, "Selvlærende historik (0 kreditter brugt)"
    base = f"https://the-odds-api.com{sport}"
    url = f"{base}/events/{event_id}/odds" if event_id else f"{base}/odds"
    params = {"apiKey": api_noegle, "regions": "eu", "markets": ALLE_API_MARKEDER, "oddsFormat": "decimal"}
    try:
        r = requests.get(url, params=params, timeout=7)
        rest = r.headers.get("x-requests-remaining")
        if r.status_code == 200:
            raw = r.json()
            data = [raw] if isinstance(raw, dict) else raw
            _gem_laert(liga_kode, data)
            return data, rest, "Live Bookmaker API (Dansk)"
    except Exception:
        pass
    return _laes_fallback(liga_kode), 0, "Selvlærende historik (API-fallback)"

def _laes_fallback(liga_kode):
    if os.path.exists(LAERT_FIL):
        try:
            with open(LAERT_FIL, "r", encoding="utf-8") as f:
                return json.load(f).get(liga_kode, [])
        except Exception:
            pass
    return []
