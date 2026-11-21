import datetime
import json
import os
import re
import time
import requests

def _h(*parts):
    return ".".join(parts)

HDR = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15",
    "Accept": "application/json, text/html, */*",
}
SITE_HOST = _h("site", "api", "espn", "com")
CORE_HOST = _h("sports", "core", "api", "espn", "com")
TSDB_HOST = _h("www", "thesportsdb", "com")
BING_HOST = _h("www", "bing", "com")
CACHE_STI = os.path.join("historik", "dommer_cache.json")

_DOMMER_CACHE = {}
_SB_CACHE = {}


def _laes_disk():
    if _DOMMER_CACHE:
        return
    if os.path.exists(CACHE_STI):
        try:
            with open(CACHE_STI, "r", encoding="utf-8") as f:
                _DOMMER_CACHE.update(json.load(f))
        except Exception:
            pass


def _gem_disk():
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
        "hellas", "calcio", "munich", "munchen", "queens", "park", "afc", "mk",
    }
    dele = [re.sub(r"[^a-zA-ZæøåÆØÅ]", "", w).lower() for w in str(navn or "").split()]
    kerne = [w for w in dele if len(w) >= 4 and w not in stop]
    return next(iter(kerne), next((w for w in dele if len(w) >= 3), ""))


def _find_navn(obj):
    if isinstance(obj, dict):
        for rk in ("strOfficial", "referee", "Referee"):
            v = obj.get(rk)
            if isinstance(v, str) and len(v.strip()) > 3:
                return v.strip()
        offs = obj.get("officials")
        if isinstance(offs, list):
            for o in offs:
                if isinstance(o, dict):
                    n = o.get("displayName") or o.get("fullName") or (o.get("athlete") or {}).get("displayName")
                    if n and len(str(n).strip()) > 3:
                        return str(n).strip()
        for v in obj.values():
            if res := _find_navn(v):
                return res
    elif isinstance(obj, list):
        for it in obj:
            if res := _find_navn(it):
                return res
    return ""


def _hent_sb(slug, dato_sp):
    key = f"{slug}|{dato_sp}"
    nu = time.time()
    gemt = _SB_CACHE.get(key)
    if gemt and (nu - gemt.get("ts", 0)) < 600:
        return gemt.get("events") or []
    try:
        u = f"https://{SITE_HOST}/apis/site/v2/sports/soccer/{slug}/scoreboard"
        evs = requests.get(u, params={"dates": dato_sp}, headers=HDR, timeout=3).json().get("events") or []
        _SB_CACHE[key] = {"ts": nu, "events": evs}
        return evs
    except Exception:
        return []


def _hent_espn_dommer(hj, ud, ev_id="", slug=""):
    hk, uk = _hold_kerne(hj), _hold_kerne(ud)
    if not hk or not uk:
        return ""
    slugs = list(dict.fromkeys([s for s in (slug, "eng.1", "eng.2", "eng.3", "eng.4", "esp.1", "esp.2", "ger.1", "ger.2", "ita.1", "ita.2", "fra.1", "den.1", "nor.1", "swe.1", "ned.1", "por.1", "uefa.champions") if s and s != "all"]))

    if ev_id and slug and slug != "all":
        try:
            sm = requests.get(f"https://{SITE_HOST}/apis/site/v2/sports/soccer/{slug}/summary", params={"event": ev_id}, headers=HDR, timeout=3).json()
            if d := _find_navn(sm):
                return d
        except Exception:
            pass

    nu = datetime.date.today()
    dato_sp = f"{(nu - datetime.timedelta(days=1)).strftime('%Y%m%d')}-{(nu + datetime.timedelta(days=2)).strftime('%Y%m%d')}"

    for s_try in slugs:
        for ev in _hent_sb(s_try, dato_sp):
            for comp in (ev.get("competitions") or []):
                teams = comp.get("competitors") or []
                navne = [str((t.get("team") or {}).get("displayName") or "").lower() for t in teams]
                if any(hk in n for n in navne) and any(uk in n for n in navne):
                    if d := _find_navn(comp.get("officials") or []):
                        return d
                    fid = str(ev.get("id") or "")
                    if fid:
                        try:
                            sm2 = requests.get(f"https://{SITE_HOST}/apis/site/v2/sports/soccer/{s_try}/summary", params={"event": fid}, headers=HDR, timeout=3).json()
                            if d := _find_navn(sm2):
                                return d
                        except Exception:
                            pass
                        try:
                            cu = f"https://{CORE_HOST}/v2/sports/soccer/leagues/{s_try}/events/{fid}/competitions/{fid}/officials"
                            co = requests.get(cu, headers=HDR, timeout=3).json()
                            for it in (co.get("items") or []):
                                ref_u = it.get("$ref") if isinstance(it, dict) else ""
                                if ref_u:
                                    rd = requests.get(ref_u, headers=HDR, timeout=3).json()
                                    if n := (rd.get("displayName") or rd.get("fullName")):
                                        return str(n).strip()
                        except Exception:
                            pass
    return ""


def _hent_tsdb_og_web(hj, ud):
    try:
        r = requests.get(f"https://{TSDB_HOST}/api/v1/json/3/searchevents.php", params={"e": f"{hj}_vs_{ud}"}, headers=HDR, timeout=3).json()
        if d := _find_navn(r):
            return d
    except Exception:
        pass
    try:
        html = requests.get(f"https://{BING_HOST}/search", params={"q": f'"{hj}" "{ud}" referee'}, headers=HDR, timeout=3).text
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
        m = re.search(r"(?:Referee|Árbitro|Arbitro|Schiedsrichter)[:\s\-]+([A-ZÀ-Ž][a-zà-ž]+(?:\s+[A-ZÀ-Ž][a-zà-ž\.]+){1,2})", txt)
        if m and 5 <= len(m.group(1).strip()) <= 30:
            return m.group(1).strip()
    except Exception:
        pass
    return ""


def hent_dommer(hj, ud, ev_id="", slug="all", dt_iso="", liga=""):
    _laes_disk()
    key = f"{_hold_kerne(hj)}|{_hold_kerne(ud)}"
    if key in _DOMMER_CACHE:
        return _DOMMER_CACHE[key]
    fundet = _hent_espn_dommer(hj, ud, ev_id, slug) or _hent_tsdb_og_web(hj, ud)
    if fundet:
        _DOMMER_CACHE[key] = fundet
        _gem_disk()
        return fundet
    return ""


def dommer_effekt(dommer, liga=""):
    if not dommer or "ikke" in str(dommer).lower():
        return 0.0, ""
    return 1.0, f"Dommer {dommer} bekræftet"
