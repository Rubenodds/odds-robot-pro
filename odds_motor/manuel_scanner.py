import streamlit as st
from odds_motor import autopilot_scanner as ap
from odds_motor import byg_kupon, liga_favoritter
from historik import gem_data

def _form_score(f):
    if not f or any(w in str(f).lower() for w in ("ingen", "ukendt")):
        return 0.0
    t = str(f).upper()
    if "W" in t or "V" in t:
        return (t.count("W") + t.count("V")) * 1.5 - (t.count("L") + t.count("T")) * 1.2
    d = [int(x) for x in t.split("-") if x.isdigit()]
    return (d[0] * 1.5) - (d[2] * 1.2) if len(d) >= 3 else 0.0

def _begrundelse(k, res=False):
    pct = float(k.get("vinderchance_pct") or k.get("pct") or 55.0)
    ctx = k.get("ctx") or {}
    hf, uf, dom, fok = str(ctx.get("hj_form", "")), str(ctx.get("ud_form", "")), str(ctx.get("dommer", "")), k.get("valgt_hold")
    dele = [f"Fokus på **{fok}** ({pct:.1f}% chance)" if fok else (f"**{k['hj']}** har statistisk overtag ({pct:.1f}%)" if pct >= 58 else (f"**{k['ud']}** stærkest ude ({pct:.1f}%)" if pct <= 44 else f"Jævnbyrdigt opgør ({pct:.1f}% chance)"))]
    if hf and uf and not any(w in (hf + uf).lower() for w in ("ingen", "ukendt")):
        dele.append(f"form {hf} mod {uf}")
    if not res and dom and not any(w in dom.lower() for w in ("afventer", "ikke offentliggjort")):
        dele.append(f"dommer {dom} trækker kort op")
    return "💡 *Begrundelse:* " + ", ".join(dele) + "."

def _byg_forslag(udvalgte, maal, kun_res=False):
    try:
        hist = gem_data.hent_alle_kuponer() or []
        vundne = sum(1 for s in hist if str(s.get("status", "")).lower() in ("vundet", "won", "gevinst"))
        h_just = round(((vundne / len(hist)) - 0.5) * 6.0, 1) if (hist and vundne > 0) else 0.0
    except Exception:
        h_just = 0.0
    if not kun_res:
        try:
            kup = byg_kupon.byg_kombineret_kupon(udvalgte, ap.MARKEDER, maal)
            if isinstance(kup, dict) and kup.get("kampe"):
                for ko, uo in zip(kup["kampe"], udvalgte):
                    ko["ctx"] = uo.get("ctx", {})
                    if uo.get("valgt_hold"):
                        ko["valgt_hold"] = uo["valgt_hold"]
                    ko["begrundelse"] = _begrundelse(ko, False)
                return kup
        except Exception:
            pass
    out = []
    for u in udvalgte:
        kp = dict(u)
        ctx = kp.get("ctx") or {}
        fok = kp.get("valgt_hold")
        fd = _form_score(ctx.get("hj_form")) - _form_score(ctx.get("ud_form"))
        cj = float(ctx.get("justering_pct", 0.0))
        st_pct = max(25.0, min(85.0, float(kp.get("pct", 55.0)) + fd + cj + h_just))
        if kun_res:
            if fok == kp["hj"] or (not fok and st_pct >= 57.0):
                cf, rp = ("2-0", round(min(24.0, st_pct * 0.28), 1)) if st_pct >= 68 else (("2-1", round(min(21.0, st_pct * 0.26), 1)) if st_pct >= 61.5 else ("1-0", round(min(19.5, st_pct * 0.25), 1)))
                f_txt = [f"Resultatspil: {kp['hj']} vinder ({cf})"]
            elif fok == kp["ud"] or (not fok and st_pct <= 45.0):
                us = 100.0 - st_pct
                cf, rp = ("0-2", round(min(22.0, us * 0.27), 1)) if us >= 66 else (("1-2", round(min(19.5, us * 0.25), 1)) if us >= 59 else ("0-1", round(min(18.0, us * 0.24), 1)))
                f_txt = [f"Resultatspil: {kp['ud']} vinder ({cf})"]
            else:
                cf, rp = ("0-0", 14.5) if abs(fd) < 1.5 and 48 <= st_pct <= 53 else ("1-1", round(15.0 + (55.0 - abs(50.0 - st_pct)) * 0.08, 1))
                f_txt = [f"Resultatspil: Uafgjort ({cf})"]
            od = round(max(4.5, min(14.0, (100.0 / max(rp, 8.0)) * 1.08)), 2)
            kp["vinderchance_pct"] = rp
        else:
            f_txt = [f"Kampvinder / DNB: {fok}" if fok else (f"Kampvinder: {kp['hj']}" if st_pct >= 58 else (f"Kampvinder: {kp['ud']}" if st_pct <= 44 else "Standard: Over 1.5 mål"))]
            if cj >= 1.5:
                f_txt.append("Hjørnespark: Over 8.5 total")
            dom = str(ctx.get("dommer", ""))
            if dom and not any(w in dom.lower() for w in ("afventer", "ikke offentliggjort")):
                f_txt.append("Kort: Over 3.5 kort")
            od = round(max(1.35, min(3.6, (100.0 / max(st_pct, 30.0)) * 1.04)), 2)
            kp["vinderchance_pct"] = round(st_pct, 1)
        kp["b365"], kp["unibet"], kp["oddset"] = od, round(od * 0.98, 2), round(od * 0.95, 2)
        kp["kombinationer"], kp["begrundelse"] = f_txt, _begrundelse(kp, kun_res)
        out.append(kp)
    return {"kampe": out}

def _gemt_fokus():
    if "man_gemte_fokus" not in st.session_state:
        raw = st.query_params.get("fokus_ligaer", "")
        st.session_state["man_gemte_fokus"] = [x for x in raw.split("|") if x] if raw else []
    return st.session_state["man_gemte_fokus"]

def _opdater_fokus(ligaer):
    if st.session_state.get("man_husk_favorit", False):
        nu = [l for l in ligaer if st.session_state.get(f"man_liga_chk_{l}", False)]
        samlet = sorted(set(nu + [l for l in _gemt_fokus() if l not in ligaer]))
        st.session_state["man_gemte_fokus"] = samlet
        st.query_params["fokus_ligaer"] = "|".join(samlet)
    else:
        st.session_state["man_gemte_fokus"] = []
        if "fokus_ligaer" in st.query_params:
            del st.query_params["fokus_ligaer"]

def vis_manuel_scanner():
    st.subheader("⚽ 2. Manuel Liga- & Klub-Scanner (Alle Spilmarkeder)")
    favs = list(liga_favoritter.hent_favorit_ligaer())
    c1, c2, c3 = st.columns(3)
    timer = c1.slider("⏱️ Tidsramme frem (timer):", 1, 72, 48, key="man_timer")
    min_o, max_o = c2.slider("🎯 Ønsket odds-lag:", 2.0, 200.0, (10.0, 40.0), key="man_odds")
    max_kampe = c3.slider("🎫 Maks. kampe på kupon:", 1, 12, 4, key="man_max_kampe")
    alle = ap._hent_kampe_v9(tuple(favs))
    aktive = [k for k in alle if 0 < k["timer"] <= timer]
    ligaer = sorted({k["liga"] for k in aktive})
    if not ligaer:
        st.info(f"📭 Ingen aktive ligaer inden for **{timer} timer**.")
        return
    gemte = _gemt_fokus()
    st.markdown(f"### 🏆 Vælg ligaer med flueben ({len(ligaer)} aktive i {timer}T):")
    husk = st.checkbox("📌 Husk mine valgte fokus-ligaer fast", value=len(gemte) > 0, key="man_husk_favorit", on_change=_opdater_fokus, args=(ligaer,))
    for l in ligaer:
        if f"man_liga_chk_{l}" not in st.session_state:
            st.session_state[f"man_liga_chk_{l}"] = (l in gemte) if gemte else False
    v_ligaer, cols = [], st.columns(3)
    for i, l in enumerate(ligaer):
        with cols[i % 3]:
            if st.checkbox(f"📌 {l}" if (husk and l in gemte) else l, key=f"man_liga_chk_{l}", on_change=_opdater_fokus, args=(ligaer,)):
                v_ligaer.append(l)
    pulje = [k for k in aktive if k["liga"] in v_ligaer]
    klubber = st.multiselect("🔎 Søg eller vælg klubnavne:", sorted({k["hj"] for k in pulje} | {k["ud"] for k in pulje}), default=[], placeholder="Skriv klubnavn...", key="man_klub_rullemenu")
    kand = []
    for k in pulje:
        if not klubber or k["hj"] in klubber or k["ud"] in klubber:
            kp = dict(k)
            if klubber and (k["hj"] in klubber) != (k["ud"] in klubber):
                kp["valgt_hold"] = k["hj"] if k["hj"] in klubber else k["ud"]
            kand.append(kp)
    st.caption(f"📊 **{len(kand)} kampe** i spil.")
    b1, b2 = st.columns(2)
    k_alle = b1.button(f"🔍 BEREGN KUPON ({len(kand)} kampe)", type="primary", use_container_width=True, key="btn_man_scan")
    k_res = b2.button("🎯 KUN RESULTATSPIL (1X2 / Cifre)", use_container_width=True, key="btn_man_resultat")
    if k_alle or k_res:
        if not kand:
            st.warning("⚠️ Sæt flueben ved mindst én liga ovenfor.")
        else:
            udv, maal = ap._vaelg_bedste_kombination(kand, min_o, max_o, max_kampe) if (len(kand) > max_kampe and not klubber) else (kand[:max_kampe], round((min_o + max_o) / 2.0, 2))
            st.session_state["man_kupon"] = _byg_forslag(udv, maal, k_res)
    if kupon := st.session_state.get("man_kupon"):
        st.markdown("### 🎫 Din Kupon (Accepter / fjern forslag med flueben):")
        valgte = []
        for i, k in enumerate(kupon["kampe"]):
            fok = f" [{k['valgt_hold']}]" if k.get("valgt_hold") else ""
            if st.checkbox(f"{i+1}. {k['hj']} vs {k['ud']}{fok} — {', '.join(k['kombinationer'])} (Odds: {k['b365']} | {k['vinderchance_pct']}%)", value=True, key=f"man_k_chk_{i}_{k['hj']}"):
                valgte.append(k)
            st.caption(k.get("begrundelse", _begrundelse(k)))
        if valgte:
            side, s_o, u_o, o_o, s_pct, stj, flm = ap._vurder_kupon(valgte)
            imp = round(100.0 / max(s_o, 1.01), 1)
            val_p = round(s_pct - imp, 1)
            v1, v2, v3 = st.columns(3)
            v1.metric("🎯 Chance", f"{s_pct:.1f}%", f"Marked: {imp:.1f}%")
            v2.metric("⭐ Værdi", "⭐" * stj, f"{val_p:+.1f}% edge")
            v3.metric("🔥 Risiko", "🔥" * flm, f"{len(valgte)}/{len(kupon['kampe'])} valg")
            st.info(f"Kuponen har **{len(valgte)} spil** til samlet odds **{s_o:.2f}** ({side}). Vurderet chance er **{s_pct:.1f}%** ({val_p:+.1f}% edge).")
            top3 = sorted([("Bet365", float(s_o)), ("Unibet", float(u_o)), ("Danske Spil", float(o_o))], key=lambda x: x[1], reverse=True)
            t1, t2, t3 = st.columns(3)
            t1.metric(f"🥇 Guld: {top3[0][0]}", f"{top3[0][1]:.2f}x")
            t2.metric(f"🥈 Sølv: {top3[1][0]}", f"{top3[1][1]:.2f}x")
            t3.metric(f"🥉 Bronze: {top3[2][0]}", f"{top3[2][1]:.2f}x")
            indsats = st.number_input("Indsats (kr.):", min_value=1.0, value=100.0, step=10.0, key="man_kr")
            if st.button("🚀 SPILLET (Gem i Supabase)", type="primary", use_container_width=True, key="btn_man_spillet"):
                try:
                    res = gem_data.gem_kupon_i_historik(list({k["liga"] for k in valgte}), [f"{k['hj']} - {k['ud']} ({', '.join(k['kombinationer'])})" for k in valgte], s_o, u_o, o_o, side, stj, indsats)
