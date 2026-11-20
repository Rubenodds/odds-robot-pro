import datetime
import re
import requests
import streamlit as st

def _h(*parts):
    return ".".join(parts)

HDR = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)", "Accept": "application/json"}
SITE_HOST = _h("site", "api", "espn", "com")
CORE_HOST = _h("sports", "core", "api", "espn", "com")
TSDB_HOST = _h("www", "thesportsdb", "com")

def _find_navn(obj):
    if isinstance(obj, dict):
        for rk in ("strOfficial", "referee", "Referee"):
            v = obj.get(rk)
            if isinstance(v, str) and len(v.strip()) > 3:
                return v.strip()
        offs = obj.get("officials") or obj.get("items")
        if isinstance(offs, list):
            for o in offs:
                if isinstance(o, dict):
                    n = o.get("displayName") or o.get("fullName") or (o.get("athlete") or {}).get("displayName")
                    if n:
                        return str(n).strip()
        for v in obj.values():
            if res := _find_navn(v):
                return res
    elif isinstance(obj, list):
        for item in obj:
            if res := _find_navn(item):
                return res
    return ""

@st.cache_data(ttl=900, show_spinner=False)
def _hent_scoreboard_cached(slug, dato_sp):
    try:
        u = f"https://{SITE_HOST}/apis/site/v2/sports/soccer/{slug}/scoreboard"
        return requests.get(u, params={"dates": dato_sp}, headers=HDR, timeout=3).json()
    except Exception:
        return {}

@st.cache_data(ttl=900, show_spinner=False)
def _hent_summary_cached(slug, ev_id):
    try:
        u = f"https://{SITE_HOST}/apis/site/v2/sports/soccer/{slug}/summary"
        return requests.get(u, params={"event": ev_id}, headers=HDR, timeout=3).json()
    except Exception:
        return {}

@st.cache_data(ttl=900, show_spinner=False)
def hent_dommer(hj, ud, ev_id="", slug="all", dt_iso=""):
    kandidat_slugs = list(dict.fromkeys([s for s in (slug, "ger.1", "ger.2", "esp.1", "esp.2", "ita.1", "ita.2", "fra.1", "fra.2", "eng.1", "den.1") if s and s != "all"]))

    # 1. Tjek ESPN Summary på primær liga-slug
    if ev_id and slug and slug != "all":
        s = _hent_summary_cached(slug, ev_id)
        if dom := _find_navn(s):
            return dom

    # 2. Tjek ESPN Scoreboard (her ligger dagens kampdommere oftest)
    nu = datetime.date.today()
    dato_sp = f"{(nu - datetime.timedelta(days=1)).strftime('%Y%m%d')}-{(nu + datetime.timedelta(days=2)).strftime('%Y%m%d')}"
    hj_k = str(hj or "").lower().split().pop(0)[:4]
    ud_k = str(ud or "").lower().split().pop(0)[:4]

    for s_try in kandidat_slugs[:5]:
        sb = _hent_scoreboard_cached(s_try, dato_sp)
        for ev in (sb.get("events") or []):
            for comp in (ev.get("competitions") or []):
                teams = comp.get("competitors") or []
                navne = [(t.get("team") or {}).get("displayName", "").lower() for t in teams]
                if any(hj_k in n for n in navne) and any(ud_k in n for n in navne):
                    if dom := _find_navn(comp.get("officials") or []):
                        return dom
                    fundet_id = str(ev.get("id") or "")
                    if fundet_id:
                        s2 = _hent_summary_cached(s_try, fundet_id)
                        if dom := _find_navn(s2):
                            return dom

    # 3. Hurtig fallback til TheSportsDB
    try:
        r = requests.get(f"https://{TSDB_HOST}/api/v1/json/3/searchevents.php", params={"e": f"{hj}_vs_{ud}"}, headers=HDR, timeout=3).json()
        if dom := _find_navn(r):
            return dom
    except Exception:
        pass
    return ""

def dommer_effekt(dommer, liga=""):
    if not dommer:
        return 0.0, ""
    er_kortrig = any(x in str(liga).lower() for x in ("brasil", "copa", "libertadores", "spanien", "italien", "segunda", "serie"))
    if er_kortrig:
        return 1.5, f"Dommer {dommer} i kortrig turnering (øget kort-/straffepotentiale)"
    return 1.0, f"Dommer {dommer} bekræftet"
