import re
import requests

def _h(*parts):
    return ".".join(parts)

HDR = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)"}
SITE_HOST = _h("site", "api", "espn", "com")
CORE_HOST = _h("sports", "core", "api", "espn", "com")
TSDB_HOST = _h("www", "thesportsdb", "com")
BING_HOST = _h("www", "bing", "com")

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

def hent_dommer(hj, ud, ev_id="", slug="all", dt_iso=""):
    if ev_id:
        for s_try in list(dict.fromkeys([slug or "all", "bra.1", "bra.2", "uefa.nations", "fifa.worldq.uefa", "all"])):
            try:
                u1 = f"https://{SITE_HOST}/apis/site/v2/sports/soccer/{s_try}/summary"
                s = requests.get(u1, params={"event": ev_id}, headers=HDR, timeout=4).json()
                if dom := _find_navn(s):
                    return dom
            except Exception:
                pass
            try:
                u2 = f"https://{CORE_HOST}/v2/sports/soccer/leagues/{s_try}/events/{ev_id}/competitions/{ev_id}/officials"
                c = requests.get(u2, headers=HDR, timeout=4).json()
                if dom := _find_navn(c):
                    return dom
                for it in (c.get("items") or []):
                    ref_u = it.get("$ref") if isinstance(it, dict) else ""
                    if ref_u:
                        d = requests.get(ref_u, headers=HDR, timeout=3).json()
                        if n := (d.get("displayName") or d.get("fullName")):
                            return str(n).strip()
            except Exception:
                pass
    try:
        r = requests.get(f"https://{TSDB_HOST}/api/v1/json/3/searchevents.php", params={"e": f"{hj}_vs_{ud}"}, headers=HDR, timeout=4).json()
        if dom := _find_navn(r):
            return dom
    except Exception:
        pass
    try:
        q = f'"{hj}" "{ud}" referee OR arbitro'
        html = requests.get(f"https://{BING_HOST}/search", params={"q": q}, headers=HDR, timeout=4).text
        m = re.search(r"(?:Referee|Árbitro|Arbitro)[:\s]+([A-ZÀ-Ž][a-zà-ž]+(?:\s+[A-ZÀ-Ž][a-zà-ž\.]+){1,2})", html)
        if m and len(m.group(1).strip()) >= 5:
            return m.group(1).strip()
    except Exception:
        pass
    return ""

def dommer_effekt(dommer, liga=""):
    if not dommer:
        return 0.0, ""
    er_sydamerika = any(x in str(liga).lower() for x in ("brasil", "copa", "libertadores", "spanien", "italien"))
    if er_sydamerika:
        return 1.5, f"Dommer {dommer} i kortrig turnering (øget kort-/straffepotentiale)"
    return 1.0, f"Dommer {dommer} bekræftet"
