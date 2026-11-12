import re
import requests

def _h(*parts):
    return ".".join(parts)

HDR = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)", "x-fsign": "SW9D1eZo"}
FS_HOST = _h("d", "flashscore", "com")
ESPN_WEB = _h("site", "web", "api", "espn", "com")

ALIAS = {
    "czechia": "czech", "czech republic": "czech",
    "türkiye": "turkey", "turkey": "turkey",
    "bosnia and herzegovina": "bosnia", "republic of ireland": "ireland",
}

def _norm(s):
    t = re.sub(r"[^a-z0-9 ]", "", str(s or "").lower()).strip()
    return ALIAS.get(t, t)[:6]

def _find_espn_dommer(obj):
    if isinstance(obj, dict):
        offs = obj.get("officials")
        if isinstance(offs, list):
            for o in offs:
                if isinstance(o, dict):
                    n = o.get("displayName") or o.get("fullName") or (o.get("athlete") or {}).get("displayName")
                    if n:
                        return str(n).strip()
        for v in obj.values():
            if res := _find_espn_dommer(v):
                return res
    elif isinstance(obj, list):
        for item in obj:
            if res := _find_espn_dommer(item):
                return res
    return ""

def _flashscore_dommer(hj, ud):
    try:
        feed = requests.get(f"https://{FS_HOST}/x/feed/f_1_0_1_en_1", headers=HDR, timeout=5).text
        hk, uk = _norm(hj), _norm(ud)
        for blk in feed.split("~AA÷"):
            m_id = blk.split("¬", 1)
            h_m = re.search(r"AE÷([^¬]+)", blk)
            a_m = re.search(r"AF÷([^¬]+)", blk)
            if not (m_id and h_m and a_m):
                continue
            hn, an = _norm(h_m.group(1)), _norm(a_m.group(1))
            if hk and uk and (hk in hn or hn in hk) and (uk in an or an in uk):
                det = requests.get(f"https://{FS_HOST}/x/feed/dc_1_{m_id}", headers=HDR, timeout=5).text
                ref = re.search(r"MI÷Referee¬(?:ML÷|MN÷)?([^¬~]+)", det)
                if ref and len(ref.group(1).strip()) > 2:
                    return ref.group(1).strip()
    except Exception:
        pass
    return ""

def hent_dommer(hj, ud, ev_id="", slug="all", dt_iso=""):
    if dom_fs := _flashscore_dommer(hj, ud):
        return dom_fs
    if ev_id:
        for s_try in list(dict.fromkeys([slug or "all", "uefa.nations", "all"])):
            try:
                u = f"https://{ESPN_WEB}/apis/site/v2/sports/soccer/{s_try}/summary"
                s = requests.get(u, params={"event": ev_id}, headers={"User-Agent": HDR["User-Agent"]}, timeout=4).json()
                if dom := _find_espn_dommer(s):
                    return dom
            except Exception:
                continue
    return ""
