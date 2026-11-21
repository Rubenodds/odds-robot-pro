import datetime
import json
import os
import re
import time
import requests

def _h(*parts):
    return ".".join(parts)

HDR = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "da-DK,da;q=0.9,en-US;q=0.8,en;q=0.7",
}
FOTMOB_HOST = _h("www", "fotmob", "com")
SOFA_HOST = _h("api", "sofascore", "com")
SITE_HOST = _h("site", "api", "espn", "com")
CACHE_STI = os.path.join("historik", "dommer_cache.json")

FOTMOB_LIGA_IDS = {
    "eng.1": 47, "eng.2": 48, "eng.3": 108, "eng.4": 109,
    "esp.1": 87, "esp.2": 140, "ger.1": 54, "ger.2": 146, "ger.3": 208,
    "ita.1": 55, "ita.2": 86, "fra.1": 53, "fra.2": 110,
    "den.1": 46, "den.2": 85, "nor.1": 59, "nor.2": 203,
    "swe.1": 67, "swe.2": 205, "ned.1": 57, "por.1": 61, "bel.1": 40,
    "sco.1": 64, "tur.1": 71, "sui.1": 69, "aut.1": 38, "pol.1": 196,
    "jpn.1": 223, "bra.1": 268, "arg.1": 112, "usa.1": 130,
    "uefa.champions": 42, "uefa.europa": 73, "uefa.nations": 9806,
}

_DOMMER_CACHE = {}
_LIGA_KAMPE_CACHE = {}


def _laes_disk_cache():
    if _DOMMER_CACHE:
        return
    if os.path.exists(CACHE_STI):
        try:
            with open(CACHE_STI, "r", encoding="utf-8") as f:
                _DOMMER_CACHE.update(json.load(f))
        except Exception:
            pass


def _gem_disk_cache():
    try:
        os.makedirs("historik", exist_ok=True)
        with open(CACHE_STI, "w", encoding="utf-8") as f:
            json.dump(_DOMMER_CACHE, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _hold_kerne(navn):
    stop = {
        "fc", "cf", "ac", "sc", "bk", "if", "fk", "sk", "cd", "ud", "rcd",
        "real", "club", "athletic", "united", "city", "town", "rovers",
        "wanderers", "wednesday", "albion", "sporting", "borussia", "eintracht",
        "hellas", "calcio", "munich", "munchen", "queens", "park", "vfl", "holstein",
    }
    dele = [re.sub(r"[^a-zA-ZæøåÆØÅ]", "", w).lower() for w in str(navn or "").split()]
    kerne = [w for w in dele if len(w) >= 4 and w not in stop]
    return next(iter(kerne), next((w for w in dele if len(w) >= 3), ""))


def _hent_liga_kampe(liga_id):
    nu = time.time()
    gemt = _LIGA_KAMPE_CACHE.get(liga_id)
    if gemt and (nu - gemt.get("ts", 0)) < 900:
        return gemt.get("kampe") or []
    try:
        lg = requests.get(f"https://{FOTMOB_HOST}/api/leagues", params={"id": liga_id}, headers=HDR, timeout=4).json()
        kampe = (((lg.get("matches") or {}).get("allMatches")) or [])
        if kampe:
            _LIGA_KAMPE_CACHE[liga_id] = {"ts": nu, "kampe": kampe}
        return kampe
    except Exception:
        return []


def _hent_fotmob_dommer(hj, ud, slug=""):
    hk, uk = _hold_kerne(hj), _hold_kerne(ud)
    if not hk or not uk:
        return ""
    match_id = None
    liga_id = FOTMOB_LIGA_IDS.get(str(slug or "").lower().strip())
    if liga_id:
        for m in _hent_liga_kampe(liga_id):
            hn = str(((m.get("home") or {}).get("name")) or "").lower()
            an = str(((m.get("away") or {}).get("name")) or "").lower()
            if (hk in hn or hk in an) and (uk in hn or uk in an):
                match_id = m.get("id")
                break
    if not match_id:
        try:
            s_url = f"https://{FOTMOB_HOST}/api/search/suggest"
            for term in (f"{hk} {uk}", hk, uk):
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
    if match_id:
        try:
            det = requests.get(f"https://{FOTMOB_HOST}/api/matchDetails", params={"matchId": match_id}, headers=HDR, timeout=4).json()
            info_box = (((det.get("content") or {}).get("matchFacts") or {}).get("infoBox") or {})
            navn = str((info_box.get("Referee") or {}).get("text") or "").strip()
            if navn:
                return navn
        except Exception:
            pass
    return ""


def _hent_sofascore_dommer(hj, ud):
    try:
        sofa_hdr = dict(HDR)
        sofa_hdr["Referer"] = "https://" + _h("www", "sofascore", "com") + "/"
        hk, uk = _hold_kerne(hj), _hold_kerne(ud)
        for q in (f"{hk} {uk}", hk):
            res = requests.get(f"https://{SOFA_HOST}/api/v1/search/events", params={"q": q}, headers=sofa_hdr, timeout=4).json()
            for ev in (res.get("events") or [])[:8]:
                hn = str((ev.get("homeTeam") or {}).get("name") or "").lower()
                an = str((ev.get("awayTeam") or {}).get("name") or "").lower()
                if (hk in hn or hk in an) and (uk in hn or uk in an):
                    det = requests.get(f"https://{SOFA_HOST}/api/v1/event/{ev.get('id')}", headers=sofa_hdr, timeout=4).json()
                    ref = (det.get("event") or {}).get("referee") or {}
                    navn = str(ref.get("name") or "").strip()
                    if navn:
                        gule, kampe = ref.get("yellowCards"), ref.get("games")
                        if gule and kampe and int(kampe) > 0:
                            return f"{navn} (snit {round(float(gule)/float(kampe), 1)} gule/kamp)"
                        return navn
    except Exception:
        pass
    return ""


def hent_dommer(hj, ud, ev_id="", slug="all", dt_iso="", liga=""):
    _laes_disk_cache()
    key = f"{_hold_kerne(hj)}|{_hold_kerne(ud)}"
    if key in _DOMMER_CACHE:
        return _DOMMER_CACHE[key]
    for fn in (lambda: _hent_fotmob_dommer(hj, ud, slug), lambda: _hent_sofascore_dommer(hj, ud)):
        fundet = fn()
        if fundet:
            _DOMMER_CACHE[key] = fundet
            _gem_disk_cache()
            return fundet
    return ""


def dommer_effekt(dommer, liga=""):
    if not dommer or "ikke" in str(dommer).lower():
        return 0.0, ""
    m = re.search(r"snit\s+(\d+(?:\.\d+)?)", str(dommer))
    if m and float(m.group(1)) >= 4.2:
        return 2.0, f"Kortglad dommer: {dommer}"
    return 1.0, f"Dommer {dommer} bekræftet"
