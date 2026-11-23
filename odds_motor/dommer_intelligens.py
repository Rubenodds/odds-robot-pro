import datetime
import re
import urllib.parse
import requests

def _h(*p):
    return ".".join(p)

HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0 Safari/537.36", "Accept": "application/json"}
ESPN_H = _h("site", "api", "espn", "com")
FOT_H = _h("www", "fotmob", "com")
SDB_H = _h("www", "thesportsdb", "com")
_DOMMER_CACHE = {}


def _ren(navn):
    txt = str(navn or "").lower().replace("ø", "o").replace("æ", "ae").replace("å", "aa").replace("é", "e").replace("ü", "u")
    stop = {"fc", "cf", "ac", "sc", "bk", "if", "fk", "sk", "cd", "ud", "rcd", "afc", "club", "real", "rovers", "united", "city", "fortuna"}
    dele = [re.sub(r"[^a-z0-9]", "", w) for w in txt.split()]
    kerne = [w for w in dele if len(w) >= 4 and w not in stop]
    return next(iter(kerne), next((w for w in dele if len(w) >= 3), ""))


def _espn_dommer(hj, ud, ev_id="", slug=""):
    try:
        hk, uk = _ren(hj), _ren(ud)
        if ev_id:
            s_use = slug if (slug and slug != "all") else "all"
            sm = requests.get(f"https://{ESPN_H}/apis/site/v2/sports/soccer/{s_use}/summary", params={"event": ev_id}, headers=HDR, timeout=3).json()
            for off in ((sm.get("gameInfo") or {}).get("officials") or []):
                if n := str(off.get("displayName") or off.get("fullName") or "").strip():
                    return n
        nu = datetime.date.today()
        d_sp = f"{(nu - datetime.timedelta(days=1)).strftime('%Y%m%d')}-{(nu + datetime.timedelta(days=2)).strftime('%Y%m%d')}"
        for s_try in list(dict.fromkeys([s for s in (slug, "den.1", "esp.2", "nor.1", "swe.1", "eng.1", "eng.2", "ita.1", "esp.1", "ger.1", "fra.1") if s and s != "all"]))[:7]:
            sb = requests.get(f"https://{ESPN_H}/apis/site/v2/sports/soccer/{s_try}/scoreboard", params={"dates": d_sp}, headers=HDR, timeout=2.5).json()
            for ev in (sb.get("events") or []):
                for comp in (ev.get("competitions") or []):
                    navne = [_ren((t.get("team") or {}).get("displayName") or "") for t in (comp.get("competitors") or [])]
                    if any(hk in n or n in hk for n in navne if n) and any(uk in n or n in uk for n in navne if n):
                        for off in (comp.get("officials") or []):
                            if n := str(off.get("displayName") or off.get("fullName") or "").strip():
                                return n
    except Exception:
        pass
    return ""


def _web_dommer(hj, ud):
    hk, uk = _ren(hj), _ren(ud)
    if not hk or not uk:
        return ""
    try:
        q = urllib.parse.quote(f"{hk} {uk}")
        sg = requests.get(f"https://{FOT_H}/api/search/suggest?term={q}", headers=HDR, timeout=3).json()
        for grp in (sg if isinstance(sg, list) else []):
            for sug in (grp.get("suggestions") or []):
                if sug.get("type") == "match":
                    mid = str(sug.get("id") or "")
                    if mid:
                        md = requests.get(f"https://{FOT_H}/api/matchDetails?matchId={mid}", headers=HDR, timeout=3).json()
                        ref = ((md.get("content") or {}).get("matchFacts") or {}).get("infoBox", {}).get("Referee") or {}
                        if navn := str(ref.get("text") or "").strip():
                            return navn
    except Exception:
        pass
    try:
        r = requests.get(f"https://{SDB_H}/api/v1/json/3/searchevents.php?e={urllib.parse.quote(f'{hk}_vs_{uk}')}", headers=HDR, timeout=2.5).json()
        for ev in (r.get("event") or [])[:5]:
            ref = str(ev.get("strReferee") or "").strip()
            if len(ref) >= 5 and " " in ref:
                return ref
    except Exception:
        pass
    return ""


def hent_dommer(hj, ud, ev_id="", slug="all", dt_iso="", liga=""):
    key = f"{_ren(hj)}|{_ren(ud)}"
    if key in _DOMMER_CACHE:
        return _DOMMER_CACHE[key]
    fundet = _espn_dommer(hj, ud, ev_id, slug) or _web_dommer(hj, ud)
    if fundet:
        try:
            from udvidelser.historik_statistik import hent_dommer_profil
            p = hent_dommer_profil(fundet)
            if p and p.get("kort_snit"):
                fundet = f"{fundet} ({p['kort_snit']} kort/kamp)"
        except Exception:
            pass
        _DOMMER_CACHE[key] = fundet
    return fundet


def dommer_effekt(dommer, liga="", hj="", ud=""):
    if not dommer or "ikke" in str(dommer).lower():
        return 0.0, ""
    return 1.0, f"Dommer {dommer} bekræftet"
