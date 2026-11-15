import math
from odds_motor.kamp_intelligens import til_decimal_odds, berig_valgte_kampe

def beregn_sandsynlighed_fra_odds(odds):
    try:
        o = til_decimal_odds(odds)
        return round(max(5.0, min(95.0, (100.0 / max(o, 1.02)) * 0.94)), 1) if o > 1.01 else 52.0
    except Exception:
        return 52.0

def _form_delta(f):
    t = str(f or "").upper()
    if not t or "UKENDT" in t:
        return 0.0
    if "W" in t or "V" in t:
        return (t.count("W") + t.count("V")) * 2.2 - (t.count("L") + t.count("T")) * 1.8
    d = [int(x) for x in t.split("-") if x.isdigit()]
    return (d * 1.8 - d * 1.5) if len(d) >= 3 else 0.0

def _udtraek_espn_odds(ctx):
    for o in (ctx.get("odds_raw") or []):
        if isinstance(o, dict) and isinstance(o.get("moneyline"), dict):
            ml = o["moneyline"]
            h_raw = ((ml.get("home") or {}).get("close") or {}).get("odds") or ((ml.get("home") or {}).get("open") or {}).get("odds")
            u_raw = ((ml.get("away") or {}).get("close") or {}).get("odds") or ((ml.get("away") or {}).get("open") or {}).get("odds")
            h_dec, u_dec = til_decimal_odds(h_raw), til_decimal_odds(u_raw)
            if h_dec > 1.01 and u_dec > 1.01:
                return h_dec, u_dec
    return None, None

def _har_skud_marked(liga):
    l = str(liga or "").lower()
    return not any(x in l for x in ("nations", "kval", "venskab", "friendly", "world", "2. division", "obos", "j2"))

def byg_kombineret_kupon(udvalgte, markeder=None, maal=2.0, runde=0, min_o=None, max_o=None):
    udvalgte, markeder = list(udvalgte or []), list(markeder or [])
    if not udvalgte:
        return {"kampe": []}
    berig_valgte_kampe(udvalgte)
    loft = float(max_o) + 5.0 if max_o else float(maal) * 1.20
    maal_pr_kamp = max(1.28, float(maal or 2.0) ** (1.0 / len(udvalgte)))
    kampe_out, samlet_nu = [], 1.0

    for idx, u in enumerate(udvalgte):
        ctx = u.get("ctx") or {}
        hj, ud, liga = u["hj"], u["ud"], u.get("liga", "")
        h_od, u_od = _udtraek_espn_odds(ctx)
        fd = _form_delta(ctx.get("hj_form")) - _form_delta(ctx.get("ud_form"))
        cj = float(ctx.get("justering_pct", 0.0))
        base_pct = (beregn_sandsynlighed_fra_odds(h_od) + fd * 0.6) if (h_od and u_od) else (53.5 + fd + cj * 0.5)
        pct = round(max(24.0, min(86.0, base_pct)), 1)
        valg, har_maal = [], False

        if pct >= 56.0 and (runde + idx) % 3 != 2:
            valg.append(f"Kampvinder: {hj}")
            od = round(h_od, 2) if (h_od and h_od > 1.05) else round(max(1.32, min(3.40, (100.0 / pct) * 1.05)), 2)
        elif pct <= 44.0 and (runde + idx) % 3 != 2:
            pct = round(100.0 - pct, 1)
            valg.append(f"Kampvinder: {ud}")
            od = round(u_od, 2) if (u_od and u_od > 1.05) else round(max(1.35, min(3.60, (100.0 / pct) * 1.05)), 2)
        else:
            har_maal = True
            if maal_pr_kamp >= 1.95 and samlet_nu * 1.90 <= loft:
                valg.append("Mål: Over 2.5 mål i kampen")
                pct = round(min(62.0, 48.0 + cj), 1)
                od = round(max(1.75, min(2.35, (100.0 / pct) * 1.05)), 2)
            else:
                valg.append("Mål: Over 1.5 mål i kampen")
                pct = round(min(78.0, 62.0 + cj), 1)
                od = round(max(1.26, min(1.55, (100.0 / pct) * 1.04)), 2)

        if od < maal_pr_kamp and samlet_nu * od * 1.58 <= loft and any("Hjørnespark" in m for m in markeder):
            valg.append("Hjørnespark: Over 9.5 total")
            od, pct = round(od * 1.58, 2), round(max(18.0, pct * 0.76), 1)
        if od < maal_pr_kamp and samlet_nu * od * 1.50 <= loft and any("Kort" in m for m in markeder):
            dom = ctx.get("dommer")
            dom_txt = f" (Dommer: {dom})" if dom not in (None, "", "Ikke udpeget endnu", "Afventer") else ""
            valg.append(f"Kort: Over 3.5 kort{dom_txt}")
            od, pct = round(od * 1.50, 2), round(max(16.0, pct * 0.78), 1)
        if od < maal_pr_kamp and samlet_nu * od * 1.55 <= loft and _har_skud_marked(liga) and any("Skud" in m or "Målscorer" in m for m in markeder):
            valg.append("Spilbyg: Over 8.5 skud på mål i kampen")
            od, pct = round(od * 1.55, 2), round(max(14.0, pct * 0.74), 1)
        elif od < maal_pr_kamp and not har_maal and samlet_nu * od * 1.72 <= loft:
            valg.append("Mål: Begge hold scorer (Ja)")
            od, pct = round(od * 1.72, 2), round(max(14.0, pct * 0.72), 1)

        samlet_nu *= od
        kampe_out.append({
            "hj": hj, "ud": ud, "liga": liga, "start": u["start"],
            "kombinationer": valg, "vinderchance_pct": pct,
            "b365": od, "unibet": round(od * 0.98, 2), "oddset": round(od * 0.97, 2), "ctx": ctx
        })
    return {"kampe": kampe_out}
