import streamlit as st
from odds_motor import byg_kupon

def begrundelse(k):
    if not isinstance(k, dict):
        return "Matematisk værdispil ud fra live kampdata og oddsbalance."
    ctx = k.get("ctx") or {}
    hj, ud = k.get("hj", "Hjemmehold"), k.get("ud", "Udehold")
    spil = ", ".join(k.get("kombinationer") or [k.get("spil") or k.get("valg") or "Valgt spil"])
    odds = k.get("b365") or k.get("odds") or 1.85
    dommer = ctx.get("dommer") or "Afventer dommer"
    vejr = ctx.get("vejr")
    v_txt = f"{vejr['temp']}°C, {vejr['vind']} m/s" if isinstance(vejr, dict) and "temp" in vejr else "Normalt kampvejr"
    skader = ctx.get("skader") or "Ingen kritiske skader meldt"
    return f"📊 {hj} vs {ud} ({spil} @ {odds}) | 🏁 Dommer: {dommer} | 🌤️ {v_txt} | 🏥 {skader}"

def _vaelg_marked_til_maal(k, maal_pr_kamp, kun_res=False):
    valgt = k.get("valgt_hold") or k.get("hj", "Hjemmehold")
    basis = float(k.get("b365") or k.get("odds") or 1.85)
    if kun_res:
        if maal_pr_kamp < 1.55:
            return f"{valgt} el. Uafgjort (1X/X2)", round(max(1.22, min(1.55, basis * 0.72)), 2)
        if maal_pr_kamp < 2.65:
            return f"{valgt} vinder (1X2)", round(max(1.55, min(2.65, basis)), 2)
        return f"{valgt} vinder med præcis 1 mål", round(max(2.70, min(6.50, maal_pr_kamp)), 2)
    if maal_pr_kamp < 1.45:
        return f"{valgt} el. Uafgjort & Over 1.5 mål", round(max(1.25, min(1.48, maal_pr_kamp)), 2)
    if maal_pr_kamp < 1.95:
        return f"{valgt} vinder & Over 1.5 mål", round(max(1.50, min(1.98, maal_pr_kamp)), 2)
    if maal_pr_kamp < 2.95:
        return f"{valgt} vinder & Begge hold scorer", round(max(2.05, min(2.95, maal_pr_kamp)), 2)
    return f"{valgt} vinder, Over 2.5 mål & Flest hjørnespark", round(max(3.00, min(12.0, maal_pr_kamp)), 2)

def _sikr_kamp(k, maal_pr_kamp=1.85, kun_res=False):
    ny = dict(k) if isinstance(k, dict) else {}
    valg, odds = _vaelg_marked_til_maal(ny, maal_pr_kamp, kun_res)
    pct = round(max(8.0, min(90.0, (100.0 / max(1.01, odds)) * 0.94)), 1)
    ny.setdefault("hj", ny.get("hjemme", "Hjemmehold"))
    ny.setdefault("ud", ny.get("ude", "Udehold"))
    ny.setdefault("liga", "Øvrige")
    ny.setdefault("start", "I dag")
    ny["spil"] = valg
    ny["odds"] = odds
    ny["b365"] = odds
    ny["unibet"] = round(max(1.05, odds - 0.03), 2)
    ny["ds"] = round(max(1.05, odds - 0.05), 2)
    ny["kombinationer"] = [valg]
    ny["vinderchance_pct"] = pct
    ny["pct"] = pct
    ny["stj"] = max(1, min(5, int(round((pct * odds) / 20.0))))
    ny["flm"] = max(1, min(5, int(round((100.0 - pct) / 17.0))))
    return ny

def byg_forslag(maal_liste, maks_odds=25.0, kun_res=False):
    liste = list(maal_liste or [])
    if not liste:
        return {"kampe": [], "total_odds": 1.0, "odds": 1.0}
    maal_pr_kamp = float(maks_odds) ** (1.0 / len(liste))
    forslag, samlet = [], 1.0
    for k in liste:
        ny = _sikr_kamp(k, maal_pr_kamp, kun_res)
        forslag.append(ny)
        samlet *= ny["b365"]
    return {"kampe": forslag, "total_odds": round(samlet, 2), "odds": round(samlet, 2)}
