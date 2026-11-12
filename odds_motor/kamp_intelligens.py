import requests
from datetime import datetime
from zoneinfo import ZoneInfo

HDR = {"User-Agent": "Mozilla/5.0"}
SUM_URL = "https://espn.com{}/summary?event={}"

HOLD_BYER = {
    "Albania": "Tirana", "Finland": "Helsinki", "Czechia": "Prague", "Czech Republic": "Prague",
    "Spain": "Madrid", "England": "London", "Croatia": "Zagreb", "Denmark": "Copenhagen",
    "Sweden": "Stockholm", "Norway": "Oslo", "Germany": "Berlin", "France": "Paris",
    "Italy": "Rome", "Portugal": "Lisbon", "Netherlands": "Amsterdam", "Belgium": "Brussels",
    "Türkiye": "Istanbul", "Turkey": "Istanbul", "Armenia": "Yerevan", "Cyprus": "Nicosia",
    "Scotland": "Glasgow", "Wales": "Cardiff", "Poland": "Warsaw", "Austria": "Vienna",
    "Switzerland": "Bern", "Serbia": "Belgrade", "Ukraine": "Kyiv", "Greece": "Athens",
}

def hurtig_kontekst(comp, hj, ud, slug="all"):
    teams = comp.get("competitors") or []
    h_obj = next((c for c in teams if c.get("homeAway") == "home"), {})
    u_obj = next((c for c in teams if c.get("homeAway") == "away"), {})
    hj_form = h_obj.get("form") or next((r.get("summary") for r in (h_obj.get("records") or []) if r.get("type") == "total"), "Ukendt")
    ud_form = u_obj.get("form") or next((r.get("summary") for r in (u_obj.get("records") or []) if r.get("type") == "total"), "Ukendt")
    venue = comp.get("venue") or {}
    addr = venue.get("address") or {}
    by = addr.get("city") or HOLD_BYER.get(hj) or hj
    return {
        "ev_id": str(comp.get("id") or ""), "slug": slug,
        "dt_iso": comp.get("date") or comp.get("startDate") or "",
        "by": by, "land": addr.get("country") or "", "stadion": venue.get("fullName", ""),
        "hj_form": hj_form, "ud_form": ud_form, "dommer": "Ikke udpeget endnu",
        "vejr": None, "skader": 0, "justering_pct": 0.0, "odds_raw": comp.get("odds") or [],
    }

def _hent_vejr(by, land, dt_iso):
    if not by or not dt_iso:
        return None
    try:
        g = requests.get("https://open-meteo.com", params={"name": by, "count": 1, "format": "json"}, timeout=4).json()
        res_list = g.get("results") or []
        if not res_list:
            return None
        lat, lon = res_list.get("latitude"), res_list.get("longitude")
        dk_dt = datetime.fromisoformat(dt_iso.replace("Z", "+00:00")).astimezone(ZoneInfo("Europe/Copenhagen"))
        t_str = dk_dt.strftime("%Y-%m-%dT%H:00")
        w = requests.get("https://open-meteo.com", params={"latitude": lat, "longitude": lon, "hourly": "temperature_2m,precipitation,windspeed_10m", "timezone": "Europe/Copenhagen"}, timeout=4).json()
        h = w.get("hourly") or {}
        if t_str in (h.get("time") or []):
            idx = h["time"].index(t_str)
            tp, regn, vind = h["temperature_2m"][idx], h["precipitation"][idx], h["windspeed_10m"][idx]
            eff = "Kraftig regn/blæst" if (regn >= 1.5 or vind >= 10) else ("Vådt/frisk vind" if (regn > 0.2 or vind >= 6.5) else "Tørt & roligt")
            return {"temp": round(tp, 1), "regn": round(regn, 1), "vind": round(vind / 3.6, 1), "effekt": eff}
    except Exception:
        pass
    return None

def _find_dommer(s):
    gi = s.get("gameInfo") or {}
    h_comp = next(iter((s.get("header") or {}).get("competitions") or []), {})
    for offs in (gi.get("officials") or [], h_comp.get("officials") or []):
        if isinstance(offs, list) and offs and isinstance(offs, dict):
            navn = offs.get("displayName") or (offs.get("athlete") or {}).get("displayName")
            if navn:
                return navn
    return None

def berig_valgte_kampe(kampe):
    for k in kampe:
        ctx = k.get("ctx") or {}
        ev_id = str(ctx.get("ev_id") or k.get("id") or "")
        slug = ctx.get("slug") or "uefa.nations"
        by = ctx.get("by") or HOLD_BYER.get(k.get("hj", "")) or k.get("hj", "")
        dt_iso = ctx.get("dt_iso") or (k.get("dk_dt").isoformat() if k.get("dk_dt") else "")
        if ev_id:
            for s_try in list(dict.fromkeys([slug, "uefa.nations", "all"])):
                try:
                    s = requests.get(SUM_URL.format(s_try, ev_id), headers=HDR, timeout=4).json()
                    if dom := _find_dommer(s):
                        ctx["dommer"] = dom
                    addr2 = ((s.get("gameInfo") or {}).get("venue") or {}).get("address") or {}
                    if addr2.get("city"):
                        by = addr2["city"]
                    ctx["skader"] = sum(len(x.get("injuries") or []) for x in (s.get("injuries") or []))
                    if ctx["dommer"] != "Ikke udpeget endnu":
                        break
                except Exception:
                    continue
        ctx["by"] = by
        ctx["vejr"] = _hent_vejr(by, "", dt_iso)
        just = (1.5 if ctx["vejr"] and ctx["vejr"]["effekt"] != "Tørt & roligt" else 0.0) + (1.0 if ctx["dommer"] != "Ikke udpeget endnu" else 0.0) + min(3.0, ctx.get("skader", 0) * 0.5)
        ctx["justering_pct"] = round(just, 1)
        k["ctx"] = ctx
    return kampe
