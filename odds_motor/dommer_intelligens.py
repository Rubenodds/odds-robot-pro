import requests

def _h(*parts):
    return ".".join(parts)

HDR = {"User-Agent": "Mozilla/5.0"}
SITE_HOST = _h("site", "api", "espn", "com")
CORE_HOST = _h("sports", "core", "api", "espn", "com")

def _find_navn(obj):
    if isinstance(obj, dict):
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
    if not ev_id:
        return ""
    slugs = list(dict.fromkeys([slug or "all", "uefa.nations", "fifa.worldq.uefa", "all"]))
    for s_try in slugs:
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
    return ""
