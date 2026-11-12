import requests
from datetime import datetime
from zoneinfo import ZoneInfo

HDR = {"User-Agent": "Mozilla/5.0"}
SUM_URL = "https://espn.com{}/summary?event={}"

HOLD_KOORD = {
    "Albania": (41.3275, 19.8187), "Finland": (60.1699, 24.9384),
    "Czechia": (50.0755, 14.4378), "Czech Republic": (50.0755, 14.4378),
    "Spain": (40.4168, -3.7038), "England": (51.5074, -0.1278),
    "Croatia": (45.8150, 15.9819), "Denmark": (55.6761, 12.5683),
    "Sweden": (59.3293, 18.0686), "Norway": (59.9139, 10.7522),
    "Germany": (52.5200, 13.4050), "France": (48.8566, 2.3522),
    "Italy": (41.9028, 12.4964), "Portugal": (38.7223, -9.1393),
    "Netherlands": (52.3676, 4.9041), "Belgium": (50.8503, 4.3517),
    "Türkiye": (41.0082, 28.9784), "Turkey": (41.0082, 28.9784),
    "Scotland": (55.8642, -4.2518), "Wales": (51.4816, -3.1791),
    "Poland": (52.2297, 21.0122), "Austria": (48.2082, 16.3738),
    "Switzerland": (46.9480, 7.4474), "Serbia": (44.7866, 20.4489),
    "Ukraine": (50.4501, 30.5234), "Greece": (37.9838, 23.7275),
}

def hurtig_kontekst(comp, hj, ud, slug="all"):
    teams = comp.get("competitors") or []
    h_obj = next((c for c in teams if c.get("homeAway") == "home"), {})
    u_obj = next((c for c in teams if c.get("homeAway") == "away"), {})
    hj_form = h_obj.get("form") or next((r.get("summary") for r in (h_obj.get("records") or []) if r.get("type") == "total"), "Ukendt")
    ud_form = u_obj.get("form") or next((r.get("summary") for r in (u_obj.get("records") or []) if r.get("type") == "total"), "Ukendt")
    venue = comp.get("venue") or {}
    addr = venue.get("address") or {}
    return {
        "ev_id": str(comp.get("id") or ""), "slug": slug,
        "dt_iso": comp.get("date") or comp.get("startDate") or "",
        "by": addr.get("city") or hj, "stadion": venue.get("fullName", ""),
        "hj_form": hj_form, "ud_form": ud_form, "dommer": "Ikke udpeget endnu",
        "vejr": None, "skader": 0, "justering_pct": 0.0, "odds_raw": comp.get("odds") or [],
    }

def _hent_vejr_direkte(hj, by, dt_iso):
    if not dt_iso:
        return None
    try:
        koord = HOLD_KOORD.get(hj)
        if not koord and by:
            g = requests.get("https://open-meteo.com", params={"name": by, "count": 1, "format": "json"}, timeout=4).json()
            res = g.get("results") or []
            if res:
                koord = (res[0].get("latitude"), res[0].get("longitude"))
        if not koord:
            return None
        dk_dt = datetime.fromisoformat(dt_iso.replace("Z", "+00:00")).astimezone(ZoneInfo("Europe/Copenhagen"))
        t_str = dk_dt.strftime("%Y-%m-%dT%H:00")
        w = requests.get("https://open-meteo.com", params={"latitude": koord[0], "longitude": koord[1], "hourly": "temperature_2m,precipitation,windspeed_10m", "timezone": "Europe/Copenhagen"}, timeout=4).json()
        h = w.get("hourly") or {}
        if t_str in (h.get("time") or []):
            idx = h["time"].index(t_str)
            tp, regn, vind = h["temperature_2m"][idx], h["precipitation"][idx], h["windspeed_10m"][idx]
            eff = "Kraftig regn/blæst" if (regn >= 1.5 or vind >= 10) else ("Vådt/frisk vind" if (regn > 0.2 or vind >= 6.5) else "Tørt & roligt")
            return {"temp": round(tp, 1), "regn": round(regn, 1), "vind": round(vind / 3.6, 1), "effekt": eff}
    except Exception:
        pass
    return None

def _find_dommer(obj):
    if isinstance(obj, dict):
        if "officials" in obj and isinstance(obj["officials"], list) and obj["officials"]:
            o0 = obj["officials"][0]
            if isinstance(o0, dict):
                n = o0.get("displayName") or (o0.get("athlete") or {}).get("displayName")
                if n:
                    return n
        for v in obj.values():
            if res := _find_dommer(v):
                return res
    elif isinstance(obj, list):
        for item in obj:
            if res := _find_dommer(item):
                return res
    return None

def berig_valgte_kampe(kampe):
    for k in kampe:
        ctx = k.get("ctx") or {}
        ev_id = str(ctx.get("ev_id") or k.get("id") or "")
        slug = ctx.get("slug") or "uefa.nations"
        by = ctx.get("by") or k.get("hj", "")
        dt_iso = ctx.get("dt_iso") or (k.get("dk_dt").isoformat() if k.get("dk_dt") else "")
        if ev_id:
            for s_try in list(dict.fromkeys([slug, "uefa.nations", "all"])):
                try:
                    s = requests.get(SUM_URL.format(s_try, ev_id), headers=HDR, timeout=4).json()
                    if dom := _find_dommer(s):
                        ctx["dommer"] = dom
                    ctx["skader"] = sum(len(x.get("injuries") or []) for x in (s.get("injuries") or []))
                    if ctx["dommer"] != "Ikke udpeget endnu":
                        break
                except Exception:
                    continue
        ctx["vejr"] = _hent_vejr_direkte(k.get("hj", ""), by, dt_iso)
        just = (1.5 if ctx["vejr"] and ctx["vejr"]["effekt"] != "Tørt & roligt" else 0.0) + (1.0 if ctx["dommer"] != "Ikke udpeget endnu" else 0.0) + min(3.0, ctx.get("skader", 0) * 0.5)
        ctx["justering_pct"] = round(just, 1)
        k["ctx"] = ctx
    return kampe
