import streamlit as st
from odds_motor import byg_kupon

def begrundelse(k):
    if not isinstance(k, dict):
        return "Matematisk værdispil ud fra live kampdata og oddsbalance."
    ctx = k.get("ctx") or {}
    hj, ud = k.get("hj", "Hjemmehold"), k.get("ud", "Udehold")
    spil = k.get("spil", k.get("valg", "Valgt spil"))
    odds = k.get("odds", 1.85)
    dommer = ctx.get("dommer") or "Afventer dommer"
    vejr = ctx.get("vejr")
    v_txt = f"{vejr['temp']}°C, {vejr['vind']} m/s" if isinstance(vejr, dict) and "temp" in vejr else "Normalt kampvejr"
    skader = ctx.get("skader") or "Ingen kritiske skader meldt"
    return f"📊 {hj} vs {ud} ({spil} @ {odds}) | 🏁 Dommer: {dommer} | 🌤️ {v_txt} | 🏥 {skader}"

def _sikr_kamp(k, kun_res=False):
    ny = dict(k) if isinstance(k, dict) else {}
    valg = ny.get("spil") or ny.get("valg") or ("1X2" if kun_res else "Over 1.5 mål")
    odds = float(ny.get("odds") or 1.85)
    pct = round(max(10.0, min(90.0, (100.0 / max(1.01, odds)) * 0.94)), 1)
    ny.setdefault("hj", ny.get("hjemme", "Hjemmehold"))
    ny.setdefault("ud", ny.get("ude", "Udehold"))
    ny["spil"] = valg
    ny["odds"] = odds
    ny["kombinationer"] = ny.get("kombinationer") or [f"{valg} (@ {odds})"]
    ny.setdefault("pct", pct)
    ny.setdefault("chance", pct)
    ny.setdefault("stj", max(1, min(5, int(round((pct * odds) / 21.0)))))
    ny.setdefault("flm", max(1, min(5, int(round((100.0 - pct) / 17.0)))))
    return ny

def byg_forslag(maal_liste, maks_odds=25.0, kun_res=False):
    res = byg_kupon.byg_forslag(maal_liste, maks_odds, kun_res=kun_res) if hasattr(byg_kupon, "byg_forslag") else None
    if isinstance(res, dict) and "kampe" in res:
        res["kampe"] = [_sikr_kamp(k, kun_res) for k in (res["kampe"] or [])]
        return res
    forslag, samlet = [], 1.0
    for k in (maal_liste or []):
        ny = _sikr_kamp(k, kun_res)
        if samlet * ny["odds"] <= float(maks_odds):
            forslag.append(ny)
            samlet *= ny["odds"]
    return {"kampe": forslag, "total_odds": round(samlet, 2), "odds": round(samlet, 2)}

def beregn_kort(k):
    ny = _sikr_kamp(k)
    return ny["pct"], ny["stj"], ny["flm"]
