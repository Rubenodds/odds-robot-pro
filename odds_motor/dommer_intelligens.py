import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlunsplit

def _u(host, path):
    return urlunsplit(("https", host, path, "", ""))

HDR = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)", "Accept": "application/json"}
SUM_URL = _u("://espn.com", "/apis/site/v2/sports/soccer/{}/summary")
FOT_DAY = _u("://fotmob.com", "/api/matches")
FOT_M = _u("://fotmob.com", "/api/matchDetails")
TSDB_EV = _u("://thesportsdb.com", "/api/v1/json/3/searchevents.php")

ALIAS = {
    "czechia": "czech", "czech republic": "czech",
    "türkiye": "turkey", "turkey": "turkey",
    "bosnia and herzegovina": "bosnia", "republic of ireland": "ireland",
}

def _norm(navn):
    s = str(navn or "").strip().lower()
    return ALIAS.get(s, s)[:5]

def _find_rekursiv(obj):
    if isinstance(obj, dict):
        for rk in ("Referee", "referee", "strOfficial"):
            rv = obj.get(rk)
            if isinstance(rv, dict) and (rv.get("text") or rv.get("name")):
                return str(rv.get("text") or rv.get("name")).strip()
            if isinstance(rv, str) and len(rv.strip()) > 2:
                return rv.strip()
        for key in ("officials", "referees", "matchOfficials"):
            offs = obj.get(key)
            if isinstance(offs, list):
                for o in offs:
                    if isinstance(o, dict):
                        n = o.get("displayName") or o.get("fullName") or o.get("name") or (o.get("athlete") or {}).get("displayName")
                        if n:
                            return str(n).strip()
        for v in obj.values():
            if res := _find_rekursiv(v):
                return res
    elif isinstance(obj, list):
        for item in obj:
            if res := _find_rekursiv(item):
                return res
    return None

def hent_dommer(hj, ud, ev_id="", slug="all", dt_iso=""):
    if ev_id:
        for s_try in list(dict.fromkeys([slug or "all", "uefa.nations", "all"])):
            try:
                s = requests.get(SUM_URL.format(s_try), params={"event": ev_id}, headers=HDR, timeout=4).json()
                if dom := _find_rekursiv(s):
                    return dom
            except Exception:
                continue
    try:
        dato = (datetime.fromisoformat(dt_iso.replace("Z", "+00:00")).astimezone(ZoneInfo("Europe/Copenhagen")) if dt_iso else datetime.now(ZoneInfo("Europe/Copenhagen"))).strftime("%Y%m%d")
        d = requests.get(FOT_DAY, params={"date": dato}, headers=HDR, timeout=5).json()
        h_k, u_k = _norm(hj), _norm(ud)
        for lg in (d.get("leagues") or []):
            for m in (lg.get("matches") or []):
                hn = ((m.get("home") or {}).get("name") or "").lower()
                an = ((m.get("away") or {}).get("name") or "").lower()
                if h_k and u_k and h_k in hn and u_k in an and m.get("id"):
                    md = requests.get(FOT_M, params={"matchId": m["id"]}, headers=HDR, timeout=5).json()
                    if dom := _find_rekursiv(md):
                        return dom
    except Exception:
        pass
    try:
        r = requests.get(TSDB_EV, params={"e": f"{hj}_vs_{ud}"}, headers=HDR, timeout=4).json()
        if dom := _find_rekursiv(r):
            return dom
    except Exception:
        pass
    return "Ikke udpeget endnu"
