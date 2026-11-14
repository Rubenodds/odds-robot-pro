import streamlit as st
from odds_motor import kamp_intelligens

def begrundelse(k):
    if not isinstance(k, dict):
        return "Matematisk værdispil ud fra live kampdata og oddsbalance."
    ctx = k.get("ctx") or {}
    hj = k.get("hj", "Hjemmehold")
    ud = k.get("ud", "Udehold")
    spil = k.get("spil", k.get("valg", "Valgt spil"))
    odds = k.get("odds", 1.85)
    dommer = ctx.get("dommer") or "Afventer dommer"
    vejr = ctx.get("vejr")
    v_txt = f"{vejr['temp']}°C, {vejr['vind']} m/s" if isinstance(vejr, dict) and "temp" in vejr else "Normalt kampvejr"
    skader = ctx.get("skader") or "Ingen kritiske skader meldt"
    return f"📊 {hj} vs {ud} ({spil} @ {odds}) | 🏁 Dommer: {dommer} | 🌤️ {v_txt} | 🏥 {skader}"

def beregn_kort(k):
    odds = float(k.get("odds", 1.85))
    ctx = k.get("ctx") or {}
    just = float(ctx.get("justering_pct", 0.0))
    pct = round(max(8.0, min(92.0, (100.0 / max(1.01, odds)) * 0.94 - (just * 0.6))), 1)
    stj = max(1, min(5, int(round((pct * odds) / 21.0))))
    flm = max(1, min(5, int(round((100.0 - pct) / 17.0))))
    return pct, stj, flm

def vis_kamp_kort(k, idx=0):
    pct, stj, flm = beregn_kort(k)
    medalje = ["🥇 ", "🥈 ", "🥉 "][idx] if idx < 3 else ""
    with st.container(border=True):
        st.markdown(f"**{medalje}{k.get('hj','')} - {k.get('ud','')}** | **{k.get('spil','')}** @ **{k.get('odds','')}**")
        st.caption(f"📊 Chance: **{pct}%** | {'⭐' * stj} | {'🔥' * flm}")
        st.caption(begrundelse(k))

def hent_alle_ligaer(kampe):
    return sorted({k.get("liga", "Øvrige") for k in (kampe or []) if k.get("liga")})
