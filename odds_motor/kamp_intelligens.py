import requests
from datetime import datetime
from zoneinfo import ZoneInfo

HDR = {"User-Agent": "Mozilla/5.0"}
SUM_URL = "https://espn.com{}"

def hurtig_kontekst(comp, hj, ud):
    teams = comp.get("competitors") or []
    h_obj = next((c for c in teams if c.get("homeAway") == "home"), {})
    u_obj = next((c for c in teams if c.get("homeAway") == "away"), {})
    hj_form = h_obj.get("form") or next((r.get("summary") for r in (h_obj.get("records") or []) if r.get("type") == "total"), "Ukendt")
    ud_form = u_obj.get("form") or next((r.get("summary") for r in (u_obj.get("records") or []) if r.get("type") == "total"), "Ukendt")
    venue = comp.get("venue") or {}
    addr = venue.get("address") or {}
    return {
        "ev_id": str(comp.get("id") or ""),
        "dt_iso": comp.get("date") or comp.get("startDate") or "",
        "by": addr.get("city") or "",
        "land": addr.get("country") or "",
        "stadion": venue.get("fullName", ""),
        "hj_form": hj_form,
        "ud_form": ud_form,
        "dommer": "Ikke udpeget endnu",
        "vejr": None,
        "skader": 0,
        "justering_pct": 0.0,
        "odds_raw": comp.get("odds") or [],
    }

def _hent_vejr(by, land, dt_iso):
    if not by or not dt_iso:
        return None
    try:
        q = f"{by}, {land}" if land else by
        g = requests.get("https://open-meteo.com", params={"name": q, "count": 1, "format": "json"}, timeout=3).json()
        res = (g.get("results") or [{}])
        lat, lon = res.get("latitude"), res.get("longitude")
        if lat is None or lon is None:
            return None
        dk_dt = datetime.fromisoformat(dt_iso.replace("Z", "+00:00")).astimezone(ZoneInfo("Europe/Copenhagen"))
        t_str = dk_dt.strftime("%Y-%m-%dT%H:00")
        w = requests.get("https://open-meteo.com", params={"latitude": lat, "longitude": lon, "hourly": "temperature_2m,precipitation,windspeed_10m", "timezone": "Europe/Copenhagen"}, timeout=3).json()
        h = w.get("hourly") or {}
        if t_str in (h.get("time") or []):
            idx = h["time"].index(t_str)
            tp, regn, vind = h["temperature_2m"][idx], h["precipitation"][idx], h["windspeed_10m"][idx]
            eff = "Kraftig regn/blæst" if (regn >= 1.5 or vind >= 10) else ("Vådt/frisk vind" if (regn > 0.2 or vind >= 6.5) else "Tørt & roligt")
            return {"temp": round(tp, 1), "regn": round(regn, 1), "vind": round(vind / 3.6, 1), "effekt": eff}
    except Exception:
        pass
    return None

def berig_valgte_kampe(kampe):
    for k in kampe:
        ctx = k.get("ctx") or {}
        ev_id, by, land = ctx.get("ev_id"), ctx.get("by", ""), ctx.get("land", "")
        if ev_id:
            try:
                s = requests.get(SUM_URL.format(ev_id), headers=HDR, timeout=3).json()
                gi = s.get("gameInfo") or {}
                offs = gi.get("officials") or []
                if offs and offs.get("displayName"):
                    ctx["dommer"] = offs["displayName"]
                addr2 = (gi.get("venue") or {}).get("address") or {}
                by = addr2.get("city") or by
                land = addr2.get("country") or land
                ctx["skader"] = sum(len(x.get("injuries") or []) for x in (s.get("injuries") or []))
            except Exception:
                pass
        ctx["vejr"] = _hent_vejr(by, land, ctx.get("dt_iso"))
        just = (1.5 if ctx["vejr"] and ctx["vejr"]["effekt"] != "Tørt & roligt" else 0.0) + (1.0 if ctx["dommer"] != "Ikke udpeget endnu" else 0.0) + min(3.0, ctx.get("skader", 0) * 0.5)
        ctx["justering_pct"] = round(just, 1)
        k["ctx"] = ctx
    return kampe
