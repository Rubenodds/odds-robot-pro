import datetime
import re
import requests
import streamlit as st

def _h(*parts):
    return ".".join(parts)

HDR = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "da-DK,da;q=0.9,en-US;q=0.8,en;q=0.7",
}
SITE_HOST = _h("site", "api", "espn", "com")
FOTMOB_HOST = _h("www", "fotmob", "com")
SOFA_HOST = _h("api", "sofascore", "com")
DDG_HOST = _h("html", "duckduckgo", "com")

def _find_navn(obj):
    if isinstance(obj, dict):
        ref = obj.get("referee")
        if isinstance(ref, dict):
            n = ref.get("text") or ref.get("name") or ref.get("fullName")
            if n and len(str(n).strip()) > 3:
                return str(n).strip()
        elif isinstance(ref, str) and len(ref.strip()) > 3:
            return ref.strip()
        for rk in ("strOfficial", "Referee"):
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

def _hold_noegleord(navn):
    stop = {"fc", "cf", "ac", "sc", "bk", "if", "fk", "sk", "cd", "ud", "rcd", "real", "club", "athletic", "united", "city", "town", "rovers", "wanderers", "wednesday", "albion"}
    dele = [re.sub(r"[^a-zA-ZæøåÆØÅ]", "", w).lower() for w in str(navn or "").split()]
    kerne = [w for w in dele if len(w) >= 4 and w not in stop]
    return next(iter(kerne), next((w for w in dele if len(w) >= 3), ""))

@st.cache_data(ttl=900, show_spinner=False)
def _hent_fotmob_dommer(hj, ud):
    try:
        hk = _hold_noegleord(hj)
        uk = _hold_noegleord(ud)
        if not hk or not uk:
            return ""
        s_url = f"https://{FOTMOB_HOST}/api/search/suggest"
        res = requests.get(s_url, params={"hits": 8, "lang": "en", "term": f"{hj} {ud}"}, headers=HDR, timeout=4).json()
        match_id = None
        for grp in (res if isinstance(res, list) else []):
            for sug in (grp.get("suggestions") or []):
                if sug.get("type") == "match":
                    txt = str(sug.get("name") or "").lower()
                    if hk in txt and uk in txt:
                        match_id = sug.get("id")
                        break
            if match_id:
                break
        if not match_id:
            res2 = requests.get(s_url, params={"hits": 10, "lang": "en", "term": hj}, headers=HDR, timeout=4).json()
            for grp in (res2 if isinstance(res2, list) else []):
                for sug in (grp.get("suggestions") or []):
                    if sug.get("type") == "match":
                        txt = str(sug.get("name") or "").lower()
                        if hk in txt and uk in txt:
                            match_id = sug.get("id")
                            break
                if match_id:
                    break
        if match_id:
            det = requests.get(f"https://{FOTMOB_HOST}/api/matchDetails", params={"matchId": match_id}, headers=HDR, timeout=4).json()
            ref_obj = (((det.get("content") or {}).get("matchFacts") or {}).get("infoBox") or {}).get("Referee") or {}
            navn = str(ref_obj.get("text") or "").strip()
            if navn:
                return navn
    except Exception:
        pass
    return ""

@st.cache_data(ttl=900, show_spinner=False)
def _hent_sofascore_dommer(hj, ud):
    try:
        sofa_hdr = dict(HDR)
        sofa_hdr["Referer"] = "https://" + _h("www", "sofascore", "com") + "/"
        sofa_hdr["Origin"] = "https://" + _h("www", "sofascore", "com")
        hk = _hold_noegleord(hj)
        uk = _hold_noegleord(ud)
        res = requests.get(f"https://{SOFA_HOST}/api/v1/search/events", params={"q": f"{hj} {ud}"}, headers=sofa_hdr, timeout=4).json()
        for ev in (res.get("events") or [])[:5]:
            hn = str((ev.get("homeTeam") or {}).get("name") or "").lower()
            an = str((ev.get("awayTeam") or {}).get("name") or "").lower()
            if (hk in hn or hk in an) and (uk in hn or uk in an):
                ev_id = ev.get("id")
                if ev_id:
                    det = requests.get(f"https://{SOFA_HOST}/api/v1/event/{ev_id}", headers=sofa_hdr, timeout=4).json()
                    ref_navn = (((det.get("event") or {}).get("referee") or {}).get("name") or "").strip()
                    if ref_navn:
                        return ref_navn
    except Exception:
        pass
    return ""

@st.cache_data(ttl=900, show_spinner=False)
def _hent_ddg_dommer(hj, ud):
    try:
        q = f'"{hj}" "{ud}" referee'
        html = requests.post(f"https://{DDG_HOST}/html/", data={"q": q}, headers=HDR, timeout=4).text
        m = re.search(r"(?:Referee|Árbitro|Arbitro|Schiedsrichter)[:\s]+([A-ZÀ-Ž][a-zà-ž]+(?:\s+[A-ZÀ-Ž][a-zà-ž\.]+){1,2})", html)
        if m and 5 <= len(m.group(1).strip()) <= 32:
            return m.group(1).strip()
    except Exception:
        pass
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
    # 1. FotMob (samme datakilde som Flashscore - har dommere på næsten alle kampe)
    if fm_dom := _hent_fotmob_dommer(hj, ud):
        return fm_dom

    # 2. Sofascore med korrekte headers
    if sofa_dom := _hent_sofascore_dommer(hj, ud):
        return sofa_dom

    # 3. ESPN Summary på primær liga-slug
    if ev_id and slug and slug != "all":
        s = _hent_summary_cached(slug, ev_id)
        if dom := _find_navn(s):
            return dom

    # 4. ESPN Scoreboard
    kandidat_slugs = list(dict.fromkeys([s for s in (slug, "esp.1", "esp.2", "ger.1", "ger.2", "ita.1", "ita.2", "fra.1", "eng.1", "eng.2", "eng.3", "den.1") if s and s != "all"]))
    nu = datetime.date.today()
    dato_sp = f"{(nu - datetime.timedelta(days=1)).strftime('%Y%m%d')}-{(nu + datetime.timedelta(days=2)).strftime('%Y%m%d')}"
    hj_k = _hold_noegleord(hj)
    ud_k = _hold_noegleord(ud)

    for s_try in kandidat_slugs[:4]:
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

    # 5. DuckDuckGo websøgning som sidste sikkerhedsnet
    if ddg_dom := _hent_ddg_dommer(hj, ud):
        return ddg_dom

    return ""

def dommer_effekt(dommer, liga=""):
    if not dommer:
        return 0.0, ""
    er_kortrig = any(x in str(liga).lower() for x in ("brasil", "copa", "libertadores", "spanien", "italien", "segunda", "serie", "la liga"))
    if er_kortrig:
        return 1.5, f"Dommer {dommer} i kortrig turnering (øget kort-/straffepotentiale)"
    return 1.0, f"Dommer {dommer} bekræftet"
