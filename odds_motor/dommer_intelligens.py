import datetime
import re
import requests

def _h(*parts):
    return ".".join(parts)

HDR = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "da-DK,da;q=0.9,en-US;q=0.8,en;q=0.7",
}
FOTMOB_HOST = _h("www", "fotmob", "com")
SITE_HOST = _h("site", "api", "espn", "com")
DDG_HOST = _h("html", "duckduckgo", "com")
BING_HOST = _h("www", "bing", "com")

FOTMOB_LIGA_IDS = {
    "eng.1": 47, "eng.2": 48, "eng.3": 108, "eng.4": 109,
    "esp.1": 87, "esp.2": 140,
    "ger.1": 54, "ger.2": 146,
    "ita.1": 55, "ita.2": 86,
    "fra.1": 53, "fra.2": 110,
    "den.1": 46, "den.2": 85,
    "ned.1": 57, "por.1": 61, "bel.1": 40,
    "uefa.champions": 42, "uefa.europa": 73,
}

_DOMMER_CACHE = {}

def _hold_noegleord(navn):
    stop = {
        "fc", "cf", "ac", "sc", "bk", "if", "fk", "sk", "cd", "ud", "rcd",
        "real", "club", "athletic", "united", "city", "town", "rovers",
        "wanderers", "wednesday", "albion", "sporting", "borussia", "eintracht",
        "hellas", "calcio", "munich", "munchen", "red", "diamonds", "sanga",
    }
    dele = [re.sub(r"[^a-zA-ZæøåÆØÅ]", "", w).lower() for w in str(navn or "").split()]
    kerne = [w for w in dele if len(w) >= 4 and w not in stop]
    return next(iter(kerne), next((w for w in dele if len(w) >= 3), ""))

def _hent_fotmob_dommer(hj, ud, slug=""):
    hk = _hold_noegleord(hj)
    uk = _hold_noegleord(ud)
    if not hk or not uk:
        return ""
    match_id = None

    # 1. Slå direkte op i FotMob ligaens kampprogram
    liga_id = FOTMOB_LIGA_IDS.get(str(slug or "").lower())
    if liga_id:
        try:
            lg = requests.get(f"https://{FOTMOB_HOST}/api/leagues", params={"id": liga_id}, headers=HDR, timeout=4).json()
            alle_kampe = (((lg.get("matches") or {}).get("allMatches")) or [])
            for m in alle_kampe:
                hn = str(((m.get("home") or {}).get("name")) or "").lower()
                an = str(((m.get("away") or {}).get("name")) or "").lower()
                if (hk in hn or hk in an) and (uk in hn or uk in an):
                    match_id = m.get("id")
                    if match_id:
                        break
        except Exception:
            pass

    # 2. Søg via FotMob search/suggest hvis ikke fundet via liga-id
    if not match_id:
        try:
            s_url = f"https://{FOTMOB_HOST}/api/search/suggest"
            for term in (f"{hj} {ud}", hj, ud):
                res = requests.get(s_url, params={"hits": 15, "lang": "en", "term": term}, headers=HDR, timeout=4).json()
                for grp in (res if isinstance(res, list) else []):
                    for sug in (grp.get("suggestions") or []):
                        if sug.get("type") == "match":
                            txt = str(sug.get("name") or "").lower()
                            if hk in txt and uk in txt:
                                match_id = sug.get("id")
                                break
                    if match_id:
                        break
                if match_id:
                    break
        except Exception:
            pass

    # 3. Hent dommer fra FotMob matchDetails
    if match_id:
        try:
            det = requests.get(f"https://{FOTMOB_HOST}/api/matchDetails", params={"matchId": match_id}, headers=HDR, timeout=4).json()
            info_box = (((det.get("content") or {}).get("matchFacts") or {}).get("infoBox") or {})
            ref_obj = info_box.get("Referee") or {}
            navn = str(ref_obj.get("text") or "").strip()
            if navn:
                return navn
        except Exception:
            pass
    return ""

def _hent_espn_dommer(hj, ud, ev_id="", slug=""):
    try:
        hk = _hold_noegleord(hj)
        uk = _hold_noegleord(ud)
        kandidat_slugs = list(dict.fromkeys([s for s in (slug, "eng.1", "eng.2", "eng.3", "esp.1", "esp.2", "ger.1", "ger.2", "ita.1", "ita.2", "fra.1", "den.1") if s and s != "all"]))
        if ev_id and slug and slug != "all":
            sm = requests.get(f"https://{SITE_HOST}/apis/site/v2/sports/soccer/{slug}/summary", params={"event": ev_id}, headers=HDR, timeout=3).json()
            for off in ((sm.get("gameInfo") or {}).get("officials") or []):
                n = str(off.get("displayName") or off.get("fullName") or "").strip()
                if n:
                    return n
        nu = datetime.date.today()
        dato_sp = f"{(nu - datetime.timedelta(days=1)).strftime('%Y%m%d')}-{(nu + datetime.timedelta(days=2)).strftime('%Y%m%d')}"
        for s_try in kandidat_slugs[:5]:
            sb = requests.get(f"https://{SITE_HOST}/apis/site/v2/sports/soccer/{s_try}/scoreboard", params={"dates": dato_sp}, headers=HDR, timeout=3).json()
            for ev in (sb.get("events") or []):
                for comp in (ev.get("competitions") or []):
                    teams = comp.get("competitors") or []
                    navne = [(t.get("team") or {}).get("displayName", "").lower() for t in teams]
                    if any(hk in n for n in navne) and any(uk in n for n in navne):
                        for off in (comp.get("officials") or []):
                            n = str(off.get("displayName") or off.get("fullName") or "").strip()
                            if n:
                                return n
                        fid = str(ev.get("id") or "")
                        if fid:
                            sm2 = requests.get(f"https://{SITE_HOST}/apis/site/v2/sports/soccer/{s_try}/summary", params={"event": fid}, headers=HDR, timeout=3).json()
                            for off in ((sm2.get("gameInfo") or {}).get("officials") or []):
                                n = str(off.get("displayName") or off.get("fullName") or "").strip()
                                if n:
                                    return n
    except Exception:
        pass
    return ""

def _udtraek_navn_fra_tekst(html):
    renset = re.sub(r"<[^>]+>", " ", str(html or ""))
    renset = re.sub(r"\s+", " ", renset)
    for pat in (
        r"(?:Referee|Dommer|Árbitro|Arbitro|Schiedsrichter|Arbitre)[:\s\-]+([A-ZÀ-Ž][a-zà-ž]+(?:\s+[A-ZÀ-Ž][a-zà-ž\.]+){1,2})",
        r"([A-ZÀ-Ž][a-zà-ž]+\s+[A-ZÀ-Ž][a-zà-ž]+)\s+(?:will referee|is the referee|officiates|dømmer)",
    ):
        m = re.search(pat, renset)
        if m:
            kandidat = m.group(1).strip()
            forbudt = {"Stadium", "Venue", "Date", "Time", "Kickoff", "League", "Match", "Report", "Preview", "Live", "Score", "Stats", "Lineups"}
            if 5 <= len(kandidat) <= 32 and not any(w in kandidat for w in forbudt):
                return kandidat
    return ""

def _hent_web_dommer(hj, ud):
    q = f'"{hj}" "{ud}" referee'
    try:
        html = requests.post(f"https://{DDG_HOST}/html/", data={"q": q}, headers=HDR, timeout=3).text
        if navn := _udtraek_navn_fra_tekst(html):
            return navn
    except Exception:
        pass
    try:
        html2 = requests.get(f"https://{BING_HOST}/search", params={"q": q}, headers=HDR, timeout=3).text
        if navn := _udtraek_navn_fra_tekst(html2):
            return navn
    except Exception:
        pass
    return ""

def hent_dommer(hj, ud, ev_id="", slug="all", dt_iso=""):
    cache_key = f"{str(hj).lower().strip()}|{str(ud).lower().strip()}"
    if cache_key in _DOMMER_CACHE:
        return _DOMMER_CACHE[cache_key]

    for fn in (
        lambda: _hent_fotmob_dommer(hj, ud, slug),
        lambda: _hent_espn_dommer(hj, ud, ev_id, slug),
        lambda: _hent_web_dommer(hj, ud),
    ):
        fundet = fn()
        if fundet:
            _DOMMER_CACHE[cache_key] = fundet
            return fundet

    return ""

def dommer_effekt(dommer, liga=""):
    if not dommer or "ikke" in str(dommer).lower():
        return 0.0, ""
    er_kortrig = any(x in str(liga).lower() for x in ("brasil", "copa", "libertadores", "spanien", "italien", "segunda", "serie", "la liga"))
    if er_kortrig:
        return 1.5, f"Dommer {dommer} i kortrig turnering (øget kort-/straffepotentiale)"
    return 1.0, f"Dommer {dommer} bekræftet"
