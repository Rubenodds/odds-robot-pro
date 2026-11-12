def beregn_sandsynlighed_fra_odds(odds):
    try:
        o = float(odds)
        return round(max(5.0, min(95.0, (100.0 / max(o, 1.02)) * 0.94)), 1)
    except Exception:
        return 52.0

def _form_delta(f):
    t = str(f or "").upper()
    if not t or "UKENDT" in t:
        return 0.0
    if "W" in t or "V" in t:
        return (t.count("W") + t.count("V")) * 2.2 - (t.count("L") + t.count("T")) * 1.8
    d = [int(x) for x in t.split("-") if x.isdigit()]
    return (d[0] * 1.8 - d[2] * 1.5) if len(d) >= 3 else 0.0

def _udtraek_espn_odds(ctx):
    raw = ctx.get("odds_raw")
    if not isinstance(raw, list):
        return None, None
    for o in raw:
        if not isinstance(o, dict):
            continue
        ml = o.get("moneyline")
        if isinstance(ml, dict):
            h_dec = ((ml.get("home") or {}).get("close") or {}).get("odds") or ((ml.get("home") or {}).get("open") or {}).get("odds")
            u_dec = ((ml.get("away") or {}).get("close") or {}).get("odds") or ((ml.get("away") or {}).get("open") or {}).get("odds")
            if h_dec and u_dec:
                try:
                    return float(h_dec), float(u_dec)
                except Exception:
                    pass
    return None, None

def byg_kombineret_kupon(udvalgte, markeder, maal):
    kampe_out = []
    n_kampe = max(1, len(udvalgte))
    maal_pr_kamp = max(1.30, float(maal) ** (1.0 / n_kampe))
    for u in udvalgte:
        ctx = u.get("ctx") or {}
        hj, ud = u["hj"], u["ud"]
        h_od, u_od = _udtraek_espn_odds(ctx)
        fd = _form_delta(ctx.get("hj_form")) - _form_delta(ctx.get("ud_form"))
        cj = float(ctx.get("justering_pct", 0.0))
        base_pct = (beregn_sandsynlighed_fra_odds(h_od) + fd * 0.6) if (h_od and u_od and h_od > 1.01 and u_od > 1.01) else (53.5 + fd + cj * 0.5)
        pct = round(max(24.0, min(86.0, base_pct)), 1)
        valg = []
        if pct >= 57.0:
            valg.append(f"Kampvinder: {hj}")
            od = round(h_od, 2) if (h_od and h_od > 1.05) else round(max(1.25, min(3.40, (100.0 / pct) * 1.03)), 2)
        elif pct <= 44.0:
            pct = round(100.0 - pct, 1)
            valg.append(f"Kampvinder: {ud}")
            od = round(u_od, 2) if (u_od and u_od > 1.05) else round(max(1.28, min(3.60, (100.0 / pct) * 1.03)), 2)
        else:
            valg.append("Mål: Over 1.5 mål i kampen")
            pct = round(min(78.0, 58.0 + cj), 1)
            od = round(max(1.30, min(2.15, (100.0 / pct) * 1.03)), 2)
        if od < maal_pr_kamp and any("Hjørnespark" in m for m in markeder):
            valg.append("Hjørnespark: Over 9.5 total")
            od = round(od * 1.48, 2)
            pct = round(max(18.0, pct * 0.78), 1)
        if od < maal_pr_kamp and any("Kort" in m for m in markeder):
            dom_txt = f" (Dommer: {ctx['dommer']})" if ctx.get("dommer") not in (None, "", "Ikke udpeget endnu", "Afventer") else ""
            valg.append(f"Kort: Over 3.5 kort{dom_txt}")
            od = round(od * 1.42, 2)
            pct = round(max(16.0, pct * 0.80), 1)
        if od < maal_pr_kamp and any("Skud" in m or "Målscorer" in m for m in markeder):
            valg.append("Spilbyg: Over 2.5 mål & Over 8.5 skud på mål")
            od = round(od * 1.55, 2)
            pct = round(max(12.0, pct * 0.74), 1)
        kampe_out.append({
            "hj": hj, "ud": ud, "liga": u["liga"], "start": u["start"],
            "kombinationer": valg, "vinderchance_pct": pct,
            "b365": od, "unibet": od, "oddset": od, "ctx": ctx
        })
    return {"kampe": kampe_out}
