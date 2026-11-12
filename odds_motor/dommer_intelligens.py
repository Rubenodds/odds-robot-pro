import re
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

def _h(*parts):
    return ".".join(parts)

HDR = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)", "Accept": "application/json"}
SUM_HOST = _h("site", "api", "espn", "com")
LS_HOST = _h("prod-public-api", "livescore", "com")
TSDB_HOST = _h("www", "thesportsdb", "com")

ALIAS = {
    "czechia": "czech", "czech republic": "czech",
    "türkiye": "turkey", "turkey": "turkey",
    "operário pr": "operario", "são bernardo": "sao bernardo",
}

def _norm(navn):
    s = re.sub(r"[^a-z0-9 ]", "", str(navn or "").lower()).strip()
    return ALIAS.get(s, s)[:6]

def _find_rekursiv(obj):
    if isinstance(obj, dict):
        for rk in ("Referee", "referee", "strOfficial", "RefNm"):
            rv = obj.get(rk)
            if isinstance(rv, dict) and (rv.get("text") or rv.get("name") or rv.get("Nm")):
                return str(rv.get("text") or rv.get("name") or rv.get("Nm")).strip()
            if isinstance(rv, str) and len(rv.strip()) > 2:
                return rv.strip()
        for key in ("officials", "referees", "matchOfficials", "Refs"):
            offs = obj.get(key)
            if isinstance(offs, list):
                for o in offs:
                    if isinstance(o, dict):
                        n = o.get("displayName") or o.get("fullName") or o.get("name") or o.get("Nm") or (o.get("athlete") or {}).get("displayName")
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

def _livescore_dommer(hj, ud, dato):
    try:
        u = f"https://{LS_HOST}/v1/api/app/date/soccer/{dato}/1?countryCode=DK&locale=en"
        d = requests.get(u, headers=HDR, timeout=5).json()
        hk, uk = _norm(hj), _norm(ud)
        for stg in (d.get("Stages") or []):
            for ev in (stg.get("Events") or []):
                t1 = _norm(((ev.get("T1") or [{}])[0]).get("Nm", ""))
                t2 = _norm(((ev.get("T2") or [{}])[0]).get("Nm", ""))
                if hk and uk and (hk in t1 or t1 in hk) and (uk in t2 or t2 in uk) and ev.get("Eid"):
                    info = requests.get(f"https://{LS_HOST}/v1/api/app/scoreboard/soccer/{ev['Eid']}?locale=en", headers=HDR, timeout=5).json()
                    if dom := _find_rekursiv(info):
                        return dom
    except Exception:
        pass
    return None

def hent_dommer(hj, ud, ev_id="", slug="all", dt_iso=""):
    if ev_id:
        for s_try in list(dict.fromkeys([slug or "all", "uefa.nations", "all"])):
            try:
                u = f"https://{SUM_HOST}/apis/site/v2/sports/soccer/{s_try}/summary"
                s = requests.get(u, params={"event": ev_id}, headers=HDR, timeout=4).json()
                if dom := _find_rekursiv(s):
                    return dom
            except Exception:
                continue
    dato = (datetime.fromisoformat(dt_iso.replace("Z", "+00:00")).astimezone(ZoneInfo("Europe/Copenhagen")) if dt_iso else datetime.now(ZoneInfo("Europe/Copenhagen"))).strftime("%Y%m%d")
    if dom_ls := _livescore_dommer(hj, ud, dato):
        return dom_ls
    try:
        r = requests.get(f"https://{TSDB_HOST}/api/v1/json/3/searchevents.php", params={"e": f"{hj}_vs_{ud}"}, headers=HDR, timeout=4).json()
        if dom := _find_rekursiv(r):
            return dom
    except Exception:
        pass
    return "Ikke udpeget endnu"
