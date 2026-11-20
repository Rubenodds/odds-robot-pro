import requests
from odds_motor import dommer_intelligens

def _h(*parts):
    return ".".join(parts)

HDR = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)", "Accept": "application/json"}
SUM_HOST = _h("site", "api", "espn", "com")
WX_HOST = _h("api", "open-meteo", "com")
WTTR_HOST = _h("wttr", "in")

LIGA_TIL_SLUG = {
    "bundesliga": "ger.1", "2. bundesliga": "ger.2", "3. liga": "ger.3",
    "premier league": "eng.1", "championship": "eng.2", "league one": "eng.3", "league two": "eng.4",
    "la liga": "esp.1", "segunda": "esp.2", "laliga": "esp.1",
    "serie a": "ita.1", "serie b": "ita.2",
    "ligue 1": "fra.1", "ligue 2": "fra.2",
    "superliga": "den.1", "1. division": "den.2",
    "eredivisie": "ned.1", "primeira liga": "por.1", "pro league": "bel.1",
    "champions league": "uefa.champions", "europa league": "uefa.europa", "conference league": "uefa.europa.conf",
    "nations league": "uefa.nations",
}

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

def _gaet_slug(k, ctx):
    for cand in (ctx.get("slug"), k.get("liga_kode")):
        if cand and str(cand) not in ("all", "uefa.nations"):
            return str(cand)
    liga_txt = str(k.get("liga") or "").lower()
    for noegle, slug in LIGA_TIL_SLUG.items():
        if noegle in liga_txt:
            return slug
    return str(ctx.get("slug") or "ger.1")

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
    venue = comp.get("venue") or {}
    addr = venue.get("address") or {}
    by_navn = addr.get("city") or (next(iter(HOLD_BY[hj])) if hj in HOLD_BY else hj)
    return {
        "ev_id": str(comp.get("id") or ""), "slug": slug,
        "dt_iso": comp.get("date") or comp.get("startDate") or "",
        "by": by_navn, "hj_form": hj_form, "ud_form": ud_form,
        "dommer": "Ikke udpeget endnu", "h2h": "", "vejr": None, "skader": 0,
        "justering_pct": 0.0, "odds_raw": comp.get("odds") or [],
    }

def _hent_vejr_direkte(hj, by):
    info = HOLD_BY.get(hj)
    by_navn = by or hj
    if info:
        by_navn, lat, lon = info
        try:
            w = requests.get(f"https://{WX_HOST}/v1/forecast", params={"latitude": lat, "longitude": lon, "current": "temperature_2m,precipitation,wind_speed_10m"}, timeout=4).json()
            cur = w.get("current") or {}
            if "temperature_2m" in cur:
                tp, regn, vind = float(cur["temperature_2m"]), float(cur.get("precipitation", 0)), float(cur.get("wind_speed_10m", 0)) / 3.6
                eff = "Kraftig regn/blæst" if (regn >= 1.5 or vind >= 10) else ("Vådt/frisk vind" if (regn > 0.2 or vind >= 6.5) else "Tørt & roligt")
                return {"temp": round(tp, 1), "regn": round(regn, 1), "vind": round(vind, 1), "effekt": eff}
        except Exception:
            pass
    try:
        w2 = requests.get(f"https://{WTTR_HOST}/{by_navn}", params={"format": "j1"}, headers=HDR, timeout=5).json()
        c0 = next(iter(w2.get("current_condition") or []), {})
        if "temp_C" in c0:
            tp, regn, vind = float(c0["temp_C"]), float(c0.get("precipMM", 0)), float(c0.get("windspeedKmph", 0)) / 3.6
            eff = "Kraftig regn/blæst" if (regn >= 1.5 or vind >= 10) else ("Vådt/frisk vind" if (regn > 0.2 or vind >= 6.5) else "Tørt & roligt")
            return {"temp": round(tp, 1), "regn": round(regn, 1), "vind": round(vind, 1), "effekt": eff}
    except Exception:
        pass
    return None

def _udtraek_h2h(s, hj, ud):
    try:
        h2h_blokke = s.get("headToHeadGames") or []
        alle_kampe = []
        for blok in h2h_blokke:
            alle_kampe.extend(blok.get("events") or [])
        if not alle_kampe:
            return ""
        hj_sejre, ud_sejre, uafgjort = 0, 0, 0
        seneste_res = []
        for ev in alle_kampe[:5]:
            comps = list(ev.get("competitors") or [])
            if len(comps) >= 2:
                c1 = comps.pop(0)
                c2 = comps.pop(0)
                n1 = (c1.get("team") or {}).get("displayName", "")
                n2 = (c2.get("team") or {}).get("displayName", "")
                s1 = int(float(c1.get("score") or 0))
                s2 = int(float(c2.get("score") or 0))
                if len(seneste_res) < 2:
                    seneste_res.append(f"{n1} {s1}-{s2} {n2}")
                if s1 == s2:
                    uafgjort += 1
                elif (s1 > s2 and hj.lower()[:5] in n1.lower()) or (s2 > s1 and hj.lower()[:5] in n2.lower()):
                    hj_sejre += 1
                else:
                    ud_sejre += 1
        snit_str = f" (senest: {', '.join(seneste_res)})" if seneste_res else ""
        return f"Sidste {len(alle_kampe[:5])}: {hj} {hj_sejre}V - {uafgjort}U - {ud} {ud_sejre}V{snit_str}"
    except Exception:
        return ""

def _udtraek_dommer_fra_summary(s):
    try:
        gi = s.get("gameInfo") or {}
        for off in (gi.get("officials") or []):
            navn = off.get("displayName") or off.get("fullName") or ""
            if navn:
                return navn
        header = s.get("header") or {}
        for comp in (header.get("competitions") or []):
            for off in (comp.get("officials") or []):
                navn = off.get("displayName") or off.get("fullName") or ""
                if navn:
                    return navn
    except Exception:
        pass
    return ""

def berig_valgte_kampe(kampe):
    kampe = list(kampe) if kampe else []
    for k in kampe:
        ctx = k.get("ctx") or {}
        ev_id = str(ctx.get("ev_id") or k.get("id") or "")
        slug = _gaet_slug(k, ctx)
        ctx["slug"] = slug
        dt_iso = ctx.get("dt_iso") or (k.get("dk_dt").isoformat() if k.get("dk_dt") else "")
        dommer = dommer_intelligens.hent_dommer(k.get("hj", ""), k.get("ud", ""), ev_id, slug, dt_iso)
        if ev_id:
            try:
                s = requests.get(f"https://{SUM_HOST}/apis/site/v2/sports/soccer/{slug}/summary", params={"event": ev_id}, headers=HDR, timeout=4).json()
                ctx["skader"] = sum(len(x.get("injuries") or []) for x in (s.get("injuries") or []))
                if not dommer or "ikke" in dommer.lower():
                    sum_dommer = _udtraek_dommer_fra_summary(s)
                    if sum_dommer:
                        dommer = sum_dommer
                h2h_txt = _udtraek_h2h(s, k.get("hj", ""), k.get("ud", ""))
                if h2h_txt:
                    ctx["h2h"] = h2h_txt
            except Exception:
                pass
        ctx["dommer"] = dommer or "Ikke udpeget endnu"
        ctx["vejr"] = _hent_vejr_direkte(k.get("hj", ""), ctx.get("by", ""))
        just = (1.5 if ctx["vejr"] and ctx["vejr"]["effekt"] != "Tørt & roligt" else 0.0) + (1.0 if "ikke" not in ctx["dommer"].lower() else 0.0) + min(3.0, ctx.get("skader", 0) * 0.5)
        ctx["justering_pct"] = round(just, 1)
        k["ctx"] = ctx
    return kampe
