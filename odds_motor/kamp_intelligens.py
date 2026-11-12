import requests
from urllib.parse import urlunsplit

def _u(host, path):
    return urlunsplit(("https", host, path, "", ""))

HDR = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)", "Accept": "application/json"}
SUM_URL = _u("site.api.espn.com", "/apis/site/v2/sports/soccer/{}/summary?event={}")
WX_URL = _u("api.open-meteo.com", "/v1/forecast")
WTTR_HOST = "wttr.in"
FOT_S = _u("www.fotmob.com", "/api/search/suggest?term={}")
FOT_M = _u("www.fotmob.com", "/api/matchDetails?matchId={}")

HOLD_BY = {
    "Albania": ("Tirana", 41.3275, 19.8187), "Finland": ("Helsinki", 60.1699, 24.9384),
    "Czechia": ("Prague", 50.0755, 14.4378), "Czech Republic": ("Prague", 50.0755, 14.4378),
    "Spain": ("Madrid", 40.4168, -3.7038), "England": ("London", 51.5074, -0.1278),
    "Croatia": ("Zagreb", 45.8150, 15.9819), "Denmark": ("Copenhagen", 55.6761, 12.5683),
    "Sweden": ("Stockholm", 59.3293, 18.0686), "Norway": ("Oslo", 59.9139, 10.7522),
    "Germany": ("Berlin", 52.5200, 13.4050), "France": ("Paris", 48.8566, 2.3522),
    "Italy": ("Rome", 41.9028, 12.4964), "Portugal": ("Lisbon", 38.7223, -9.1393),
    "Netherlands": ("Amsterdam", 52.3676, 4.9041), "Belgium": ("Brussels", 50.8503, 4.3517),
    "Türkiye": ("Istanbul", 41.0082, 28.9784), "Turkey": ("Istanbul", 41.0082, 28.9784),
    "Scotland": ("Glasgow", 55.8642, -4.2518), "Wales": ("Cardiff", 51.4816, -3.1791),
    "Poland": ("Warsaw", 52.2297, 21.0122), "Austria": ("Vienna", 48.2082, 16.3738),
    "Switzerland": ("Bern", 46.9480, 7.4474), "Serbia": ("Belgrade", 44.7866, 20.4489),
}

def til_decimal_odds(val):
    try:
        o = float(str(val).replace(",", ".").replace("+", "").strip())
        if o <= -100:
            return round(1.0 + (100.0 / abs(o)), 2)
        if o >= 100:
            return round(1.0 + (o / 100.0), 2)
        return round(o, 2) if o > 1.0 else 0.0
    except Exception:
        return 0.0

def _find_dommer(obj):
    if isinstance(obj, dict):
        for key in ("officials", "referees", "matchOfficials"):
            offs = obj.get(key)
            if isinstance(offs, list):
                for o in offs:
                    if isinstance(o, dict):
                        n = o.get("displayName") or o.get("fullName") or o.get("name") or (o.get("athlete") or {}).get("displayName")
                        if n:
                            return str(n)
        for v in obj.values():
            if res := _find_dommer(v):
                return res
    elif isinstance(obj, list):
        for item in obj:
            if res := _find_dommer(item):
                return res
    return None

def _hent_dommer_backup(hj, ud):
    try:
        r = requests.get(FOT_S.format(f"{hj} {ud}"), headers=HDR, timeout=4).json()
        for grp in (r if isinstance(r, list) else []):
            for sug in (grp.get("suggestions") or []):
                if sug.get("type") == "match" and sug.get("id"):
                    m = requests.get(FOT_M.format(sug["id"]), headers=HDR, timeout=4).json()
                    ref = (((m.get("content") or {}).get("matchFacts") or {}).get("infoBox") or {}).get("Referee") or {}
                    if ref.get("text"):
                        return str(ref["text"])
    except Exception:
        pass
    return None

def hurtig_kontekst(comp, hj, ud, slug="all"):
    teams = comp.get("competitors") or []
    h_obj = next((c for c in teams if c.get("homeAway") == "home"), {})
    u_obj = next((c for c in teams if c.get("homeAway") == "away"), {})
    hj_form = h_obj.get("form") or next((r.get("summary") for r in (h_obj.get("records") or []) if r.get("type") == "total"), "Ukendt")
    ud_form = u_obj.get("form") or next((r.get("summary") for r in (u_obj.get("records") or []) if r.get("type") == "total"), "Ukendt")
    venue = comp.get("venue") or {}
    addr = venue.get("address") or {}
    by_navn = addr.get("city") or (next(iter(HOLD_BY[hj])) if hj in HOLD_BY else hj)
    return {
        "ev_id": str(comp.get("id") or ""), "slug": slug,
        "dt_iso": comp.get("date") or comp.get("startDate") or "",
        "by": by_navn, "hj_form": hj_form, "ud_form": ud_form,
        "dommer": _find_dommer(comp) or "Ikke udpeget endnu",
        "vejr": None, "skader": 0, "justering_pct": 0.0, "odds_raw": comp.get("odds") or [],
    }

def _hent_vejr_direkte(hj, by):
    info = HOLD_BY.get(hj)
    by_navn = by or hj
    if info:
        by_navn, lat, lon = info
        try:
            w = requests.get(WX_URL, params={"latitude": lat, "longitude": lon, "current": "temperature_2m,precipitation,wind_speed_10m"}, timeout=4).json()
            cur = w.get("current") or {}
            if "temperature_2m" in cur:
                tp, regn, vind = float(cur["temperature_2m"]), float(cur.get("precipitation", 0)), float(cur.get("wind_speed_10m", 0)) / 3.6
                eff = "Kraftig regn/blæst" if (regn >= 1.5 or vind >= 10) else ("Vådt/frisk vind" if (regn > 0.2 or vind >= 6.5) else "Tørt & roligt")
                return {"temp": round(tp, 1), "regn": round(regn, 1), "vind": round(vind, 1), "effekt": eff}
        except Exception:
            pass
    try:
        w2 = requests.get(_u(WTTR_HOST, f"/{by_navn}"), params={"format": "j1"}, headers=HDR, timeout=5).json()
        c0 = next(iter(w2.get("current_condition") or []), {})
        if "temp_C" in c0:
            tp, regn, vind = float(c0["temp_C"]), float(c0.get("precipMM", 0)), float(c0.get("windspeedKmph", 0)) / 3.6
            eff = "Kraftig regn/blæst" if (regn >= 1.5 or vind >= 10) else ("Vådt/frisk vind" if (regn > 0.2 or vind >= 6.5) else "Tørt & roligt")
            return {"temp": round(tp, 1), "regn": round(regn, 1), "vind": round(vind, 1), "effekt": eff}
    except Exception:
        pass
    return None

def berig_valgte_kampe(kampe):
    kampe = list(kampe) if kampe else []
    for k in kampe:
        ctx = k.get("ctx") or {}
        ev_id = str(ctx.get("ev_id") or k.get("id") or "")
        slug = ctx.get("slug") or "uefa.nations"
        if ev_id:
            for s_try in list(dict.fromkeys([slug, "uefa.nations", "all"])):
                try:
                    s = requests.get(SUM_URL.format(s_try, ev_id), headers=HDR, timeout=4).json()
                    if dom := _find_dommer(s):
                        ctx["dommer"] = dom
                    ctx["skader"] = sum(len(x.get("injuries") or []) for x in (s.get("injuries") or []))
                    if ctx.get("dommer") not in (None, "", "Ikke udpeget endnu"):
                        break
                except Exception:
                    continue
        if ctx.get("dommer") in (None, "", "Ikke udpeget endnu"):
            if dom_b := _hent_dommer_backup(k.get("hj", ""), k.get("ud", "")):
                ctx["dommer"] = dom_b
        ctx["vejr"] = _hent_vejr_direkte(k.get("hj", ""), ctx.get("by", ""))
        just = (1.5 if ctx["vejr"] and ctx["vejr"]["effekt"] != "Tørt & roligt" else 0.0) + (1.0 if ctx["dommer"] != "Ikke udpeget endnu" else 0.0) + min(3.0, ctx.get("skader", 0) * 0.5)
        ctx["justering_pct"] = round(just, 1)
        k["ctx"] = ctx
    return kampe
