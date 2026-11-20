import datetime
import requests

def _h(*parts):
    return ".".join(parts)

HDR = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
SUM_HOST = _h("site", "api", "espn", "com")
WX_HOST = _h("api", "open-meteo", "com")
WTTR_HOST = _h("wttr", "in")

LIGA_TIL_SLUG = {
    "bundesliga": "ger.1", "2. bundesliga": "ger.2", "premier league": "eng.1",
    "championship": "eng.2", "la liga": "esp.1", "laliga": "esp.1",
    "serie a": "ita.1", "ligue 1": "fra.1", "ligue 2": "fra.2",
    "superliga": "den.1", "1. division": "den.2", "eredivisie": "ned.1",
    "primeira liga": "por.1", "pro league": "bel.1", "champions league": "uefa.champions",
    "europa league": "uefa.europa", "nations league": "uefa.nations",
}

HOLD_BY = {
    "Albania": ("Tirana", 41.33, 19.82), "Finland": ("Helsinki", 60.17, 24.94),
    "Czechia": ("Prague", 50.08, 14.44), "Spain": ("Madrid", 40.42, -3.70),
    "England": ("London", 51.51, -0.13), "Croatia": ("Zagreb", 45.82, 15.98),
    "Denmark": ("Copenhagen", 55.68, 12.57), "Sweden": ("Stockholm", 59.33, 18.07),
    "Norway": ("Oslo", 59.91, 10.75), "Germany": ("Berlin", 52.52, 13.41),
    "France": ("Paris", 48.86, 2.35), "Italy": ("Rome", 41.90, 12.50),
    "Portugal": ("Lisbon", 38.72, -9.14), "Netherlands": ("Amsterdam", 52.37, 4.90),
    "Belgium": ("Brussels", 50.85, 4.35), "Turkey": ("Istanbul", 41.01, 28.98),
    "Scotland": ("Glasgow", 55.86, -4.25), "Poland": ("Warsaw", 52.23, 21.01),
}

def _gaet_slug(k, ctx):
    for cand in (ctx.get("slug"), k.get("liga_kode")):
        if cand and str(cand) not in ("all", "uefa.nations"):
            return str(cand)
    liga_txt = str(k.get("liga") or "").lower()
    for noegle, slug in LIGA_TIL_SLUG.items():
        if noegle in liga_txt:
            return slug
    return "den.1"

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

def hurtig_kontekst(comp, hj, ud, slug="all"):
    teams = comp.get("competitors") or []
    h_obj = next((c for c in teams if c.get("homeAway") == "home"), {})
    u_obj = next((c for c in teams if c.get("homeAway") == "away"), {})
    hj_form = h_obj.get("form") or next((r.get("summary") for r in (h_obj.get("records") or []) if r.get("type") == "total"), "Ukendt")
    ud_form = u_obj.get("form") or next((r.get("summary") for r in (u_obj.get("records") or []) if r.get("type") == "total"), "Ukendt")
    addr = (comp.get("venue") or {}).get("address") or {}
    by_navn = addr.get("city") or (next(iter(HOLD_BY[hj])) if hj in HOLD_BY else hj)
    return {"ev_id": str(comp.get("id") or ""), "slug": slug, "dt_iso": comp.get("date") or "", "by": by_navn, "hj_form": hj_form, "ud_form": ud_form, "dommer": "Ikke udpeget endnu", "h2h": "", "vejr": None, "skader": 0, "justering_pct": 0.0, "odds_raw": comp.get("odds") or []}

def _hent_vejr_direkte(hj, by):
    info = HOLD_BY.get(hj)
    by_navn = by or hj
    if info:
        by_navn, lat, lon = info
        try:
            cur = requests.get(f"https://{WX_HOST}/v1/forecast", params={"latitude": lat, "longitude": lon, "current": "temperature_2m,precipitation,wind_speed_10m"}, timeout=4).json().get("current") or {}
            if "temperature_2m" in cur:
                tp, regn, vind = float(cur["temperature_2m"]), float(cur.get("precipitation", 0)), float(cur.get("wind_speed_10m", 0)) / 3.6
                eff = "Kraftig regn/blæst" if (regn >= 1.5 or vind >= 10) else ("Vådt/frisk vind" if (regn > 0.2 or vind >= 6.5) else "Tørt & roligt")
                return {"temp": round(tp, 1), "regn": round(regn, 1), "vind": round(vind, 1), "effekt": eff}
        except Exception:
            pass
    try:
        c0 = next(iter(requests.get(f"https://{WTTR_HOST}/{by_navn}", params={"format": "j1"}, headers=HDR, timeout=4).json().get("current_condition") or []), {})
        if "temp_C" in c0:
            tp, regn, vind = float(c0["temp_C"]), float(c0.get("precipMM", 0)), float(c0.get("windspeedKmph", 0)) / 3.6
            eff = "Kraftig regn/blæst" if (regn >= 1.5 or vind >= 10) else ("Vådt/frisk vind" if (regn > 0.2 or vind >= 6.5) else "Tørt & roligt")
            return {"temp": round(tp, 1), "regn": round(regn, 1), "vind": round(vind, 1), "effekt": eff}
    except Exception:
        pass
    return None

def _udtraek_h2h(s, hj, ud):
    try:
        alle = [ev for b in (s.get("headToHeadGames") or []) for ev in (b.get("events") or [])]
        if not alle:
            return ""
        hv, uv, uaf, sen = 0, 0, 0, []
        hk = str(hj or "").lower().split().pop(0)[:4]
        for ev in alle[:5]:
            cs = list(ev.get("competitors") or [])
            if len(cs) >= 2:
                c1, c2 = cs.pop(0), cs.pop(0)
                n1, n2 = (c1.get("team") or {}).get("displayName", ""), (c2.get("team") or {}).get("displayName", "")
                s1, s2 = int(float(c1.get("score") or 0)), int(float(c2.get("score") or 0))
                if len(sen) < 2:
                    sen.append(f"{n1} {s1}-{s2} {n2}")
                if s1 == s2:
                    uaf += 1
                elif (s1 > s2 and hk in n1.lower()) or (s2 > s1 and hk in n2.lower()):
                    hv += 1
                else:
                    uv += 1
        return f"Sidste {len(alle[:5])} indbyrdes: {hj} {hv}V - {uaf}U - {ud} {uv}V" + (f" (senest: {', '.join(sen)})" if sen else "")
    except Exception:
        return ""

def berig_valgte_kampe(kampe):
    res = list(kampe) if kampe else []
    for k in res:
        try:
            ctx = dict(k.get("ctx") or {})
            ev_id = str(ctx.get("ev_id") or k.get("id") or "")
            slug = _gaet_slug(k, ctx)
            ctx["slug"] = slug
            dommer = ""
            try:
                from odds_motor import dommer_intelligens
                dommer = dommer_intelligens.hent_dommer(k.get("hj", ""), k.get("ud", ""), ev_id, slug, ctx.get("dt_iso") or "") or ""
            except Exception:
                pass
            if ev_id:
                try:
                    s = requests.get(f"https://{SUM_HOST}/apis/site/v2/sports/soccer/{slug}/summary", params={"event": ev_id}, headers=HDR, timeout=4).json()
                    ctx["skader"] = sum(len(x.get("injuries") or []) for x in (s.get("injuries") or []))
                    if not dommer or "ikke" in dommer.lower():
                        offs = ((s.get("gameInfo") or {}).get("officials") or [])
                        dommer = next((o.get("displayName") or o.get("fullName") or "" for o in offs if o.get("displayName") or o.get("fullName")), dommer)
                    ctx["h2h"] = _udtraek_h2h(s, k.get("hj", ""), k.get("ud", "")) or ctx.get("h2h", "")
                except Exception:
                    pass
            ctx["dommer"] = dommer or "Ikke udpeget endnu"
            ctx["vejr"] = _hent_vejr_direkte(k.get("hj", ""), ctx.get("by", ""))
            ctx["justering_pct"] = round((1.5 if ctx["vejr"] and ctx["vejr"]["effekt"] != "Tørt & roligt" else 0.0) + (1.0 if "ikke" not in ctx["dommer"].lower() else 0.0) + min(3.0, ctx.get("skader", 0) * 0.5), 1)
            k["ctx"] = ctx
        except Exception:
            k.setdefault("ctx", {"dommer": "Ikke udpeget endnu", "h2h": "", "vejr": None})
    return res
