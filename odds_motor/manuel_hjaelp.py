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

def byg_forslag(maal_liste, maks_odds=25.0, kun_res=False):
    if hasattr(byg_kupon, "byg_forslag"):
        res = byg_kupon.byg_forslag(maal_liste, maks_odds, kun_res=kun_res)
        if isinstance(res, dict) and "kampe" in res:
            return res
    forslag, samlet = [], 1.0
    for k in (maal_liste or []):
        valg = k.get("valg") or k.get("spil") or ("1X2" if kun_res else "Over 1.5 mål")
        odds = float(k.get("odds") or 1.85)
        if samlet * odds <= float(maks_odds):
            ny = dict(k)
            ny["spil"] = valg
            ny["kombinationer"] = ny.get("kombinationer") or [valg]
            ny["odds"] = odds
            forslag.append(ny)
            samlet *= odds
    return {"kampe": forslag, "total_odds": round(samlet, 2), "odds": round(samlet, 2)}

def beregn_kort(k):
    odds = float(k.get("odds", 1.85))
    ctx = k.get("ctx") or {}
    just = float(ctx.get("justering_pct", 0.0))
    pct = round(max(8.0, min(92.0, (100.0 / max(1.01, odds)) * 0.94 - (just * 0.6))), 1)
    stj = max(1, min(5, int(round((pct * odds) / 21.0))))
    flm = max(1, min(5, int(round((100.0 - pct) / 17.0))))
    return pct, stj, flm
