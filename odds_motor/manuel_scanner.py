import streamlit as st
from odds_motor import autopilot_scanner as ap
from odds_motor import byg_kupon, liga_favoritter
from historik import gem_data

def _hent_historik_statistik():
    try:
        historik = gem_data.hent_alle_kuponer() or []
        antal = len(historik)
        if antal == 0:
            return {"antal": 0, "justering": 0.0}
        vundne = sum(1 for s in historik if str(s.get("status", "")).lower() in ("vundet", "won", "gevinst"))
        justering = round(((vundne / antal) - 0.50) * 6.0, 1) if vundne > 0 else 0.0
        return {"antal": antal, "justering": justering}
    except Exception:
        return {"antal": 0, "justering": 0.0}

def _beregn_form_score(form_str):
    if not form_str or "ingen" in str(form_str).lower() or "ukendt" in str(form_str).lower():
        return 0.0
    txt = str(form_str).upper()
    if "W" in txt or "V" in txt:
        return (txt.count("W") + txt.count("V")) * 1.5 - (txt.count("L") + txt.count("T")) * 1.2
    dele = [int(x) for x in txt.split("-") if x.isdigit()]
    return (dele[0] * 1.5) - (dele[2] * 1.2) if len(dele) >= 3 else 0.0

def _lav_kamp_begrundelse(kamp, kun_resultat=False):
    pct = float(kamp.get("vinderchance_pct") or kamp.get("pct") or 55.0)
    ctx = kamp.get("ctx") or {}
    hj_form, ud_form, dommer = str(ctx.get("hj_form", "")), str(ctx.get("ud_form", "")), str(ctx.get("dommer", ""))
    fokus = kamp.get("valgt_hold")
    dele = []
    if fokus:
        dele.append(f"Fokus på **{fokus}** ud fra dit klubvalg ({pct:.1f}% chance)")
    elif pct >= 58.0:
        dele.append(f"**{kamp['hj']}** har statistisk overtag ({pct:.1f}% chance)")
    elif pct <= 44.0:
        dele.append(f"**{kamp['ud']}** vurderes stærkest på udebane ({pct:.1f}% chance)")
    else:
        dele.append(f"Jævnbyrdigt opgør ({pct:.1f}% chance for valgte udfald)")
    if hj_form and "ingen" not in hj_form.lower() and "ukendt" not in hj_form.lower() and ud_form and "ingen" not in ud_form.lower():
        dele.append(f"seneste form er {hj_form} mod {ud_form}")
    if not kun_resultat and dommer and "afventer" not in dommer.lower() and "ikke offentliggjort" not in dommer.lower():
        dele.append(f"dommer {dommer} trækker kort-snittet op")
    return "💡 *Begrundelse:* " + ", ".join(dele) + "."

def _byg_spilbare_forslag(udvalgte, maal_odds, kun_resultat=False):
    hist = _hent_historik_statistik()
    if not kun_resultat:
        try:
            kupon = byg_kupon.byg_kombineret_kupon(udvalgte, ap.MARKEDER, maal_odds)
            if isinstance(kupon, dict) and kupon.get("kampe"):
                for k_obj, u_obj in zip(kupon["kampe"], udvalgte):
                    k_obj["ctx"] = u_obj.get("ctx", {})
                    if u_obj.get("valgt_hold"):
                        k_obj["valgt_hold"] = u_obj["valgt_hold"]
                    k_obj["begrundelse"] = _lav_kamp_begrundelse(k_obj, False)
                return kupon
        except Exception:
            pass
    kampe_resultat = []
    for u in udvalgte:
        kopi = dict(u)
        basis_pct = float(kopi.get("pct", 55.0))
        ctx = kopi.get("ctx") or {}
        fokus = kopi.get("valgt_hold")
        form_diff = _beregn_form_score(ctx.get("hj_form")) - _beregn_form_score(ctx.get("ud_form"))
        ctx_just = float(ctx.get("justering_pct", 0.0))
        styrke = max(25.0, min(85.0, basis_pct + form_diff + ctx_just + hist["justering"]))
        forslag = []
        if kun_resultat:
            if fokus == kopi["hj"] or (not fokus and styrke >= 57.0):
                ciffer, res_pct = ("2-0", round(min(24.0, styrke * 0.28), 1)) if styrke >= 68.0 else (("2-1", round(min(21.0, styrke * 0.26), 1)) if styrke >= 61.5 else ("1-0", round(min(19.5, styrke * 0.25), 1)))
                forslag.append(f"Resultatspil: {kopi['hj']} vinder ({ciffer})")
            elif fokus == kopi["ud"] or (not fokus and styrke <= 45.0):
                ude_s = 100.0 - styrke
                ciffer, res_pct = ("0-2", round(min(22.0, ude_s * 0.27), 1)) if ude_s >= 66.0 else (("1-2", round(min(19.5, ude_s * 0.25), 1)) if ude_s >= 59.0 else ("0-1", round(min(18.0, ude_s * 0.24), 1)))
                forslag.append(f"Resultatspil: {kopi['ud']} vinder ({ciffer})")
            else:
                ciffer, res_pct = ("0-0", 14.5) if abs(form_diff) < 1.5 and 48.0 <= styrke <= 53.0 else ("1-1", round(15.0 + (55.0 - abs(50.0 - styrke)) * 0.08, 1))
                forslag.append(f"Resultatspil: Uafgjort ({ciffer})")
            odds_est = round(max(4.50, min(14.00, (100.0 / max(res_pct, 8.0)) * 1.08)), 2)
            kopi["b365"], kopi["unibet"], kopi["oddset"] = odds_est, round(odds_est * 0.98, 2), round(odds_est * 0.95, 2)
            kopi["vinderchance_pct"] = res_pct
        else:
            if fokus:
                forslag.append(f"Kampvinder / DNB: {fokus}")
            elif styrke >= 58.0:
                forslag.append(f"Kampvinder: {kopi['hj']}")
            elif styrke <= 44.0:
                forslag.append(f"Kampvinder: {kopi['ud']}")
            else:
                forslag.append("Standard: Over 1.5 mål i kampen")
            if ctx_just >= 1.5:
                forslag.append("Hjørnespark: Over 8.5 total")
            dommer = str(ctx.get("dommer", ""))
            if dommer and "afventer" not in dommer.lower() and "ikke offentliggjort" not in dommer.lower():
                forslag.append("Kort-sandsynlighed: Over 3.5 kort")
            odds_est = round(max(1.35, min(3.60, (100.0 / max(styrke, 30.0)) * 1.04)), 2)
            kopi["b365"], kopi["unibet"], kopi["oddset"] = odds_est, round(odds_est * 0.98, 2), round(odds_est * 0.95, 2)
            kopi["vinderchance_pct"] = round(styrke, 1)
        kopi["kombinationer"] = forslag
        kopi["begrundelse"] = _lav_kamp_begrundelse(kopi, kun_resultat)
        kampe_resultat.append(kopi)
    return {"kampe": kampe_resultat}

def _hent_gemte_fokus_ligaer():
    if "man_gemte_fokus" in st.session_state:
        return st.session_state["man_gemte_fokus"]
    raw = st.query_params.get("fokus_ligaer", "")
    gemte = [x for x in raw.split("|") if x] if raw else []
    st.session_state["man_gemte_fokus"] = gemte
    return gemte

def _opdater_fokus_hukommelse(aktive_ligaer):
    if st.session_state.get("man_husk_favorit", False):
        valgte_nu = [l for l in aktive_ligaer if st.session_state.get(f"man_liga_chk_{l}", False)]
        tidligere = [l for l in _hent_gemte_fokus_ligaer() if l not in aktive_ligaer]
        samlet = sorted(set(valgte_nu + tidligere))
        st.session_state["man_gemte_fokus"] = samlet
        st.query_params["fokus_ligaer"] = "|".join(samlet)
    else:
        st.session_state["man_gemte_fokus"] = []
        if "fokus_ligaer" in st.query_params:
            del st.query_params["fokus_ligaer"]

def _lav_kupon_forklaring(valgte_kampe, bedste_side, samlet_o, samlet_pct, value_pct, flammer):
    risiko_map = {1: "lav risiko (🔥)", 2: "moderat risiko (🔥🔥)", 3: "mellem-høj risiko (🔥🔥🔥)", 4: "høj risiko (🔥🔥🔥🔥)", 5: "meget høj risiko (🔥🔥🔥🔥🔥)"}
    vaerdi_tekst = f"positiv spilværdi (+{value_pct:.1f}% over bookmakerens vurdering)" if value_pct > 0 else f"tæt på markedsodds ({value_pct:.1f}% edge)"
    return f"Kuponen samler **{len(valgte_kampe)} spilbare forslag** til samlet odds **{samlet_o:.2f}** hos **{bedste_side}**. Robotten vurderer den samlede chance til **{samlet_pct:.1f}%**, hvilket giver **{vaerdi_tekst}** med **{risiko_map.get(flammer, 'moderat risiko')}**."

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
    gemte_fokus = _hent_gemte_fokus_ligaer()
    har_gemt_fokus = len(gemte_fokus) > 0
    st.markdown(f"### 🏆 Vælg ligaer med flueben ({len(ligaer)} aktive i {timer}T):")
    husk_val = st.checkbox("📌 Husk mine valgte fokus-ligaer fast", value=har_gemt_fokus, key="man_husk_favorit", on_change=_opdater_fokus_hukommelse, args=(ligaer,))
    if husk_val and gemte_fokus:
        st.caption(f"📌 Fastgjorte fokus-ligaer aktive ({len(gemte_fokus)} stk.) – øvrige ligaer er klar til flueben nedenfor.")
    for liga in ligaer:
        l_key = f"man_liga_chk_{liga}"
        if l_key not in st.session_state:
            st.session_state[l_key] = (liga in gemte_fokus) if har_gemt_fokus else False
    v_ligaer = []
    cols = st.columns(3)
    for idx, liga in enumerate(ligaer):
        l_key = f"man_liga_chk_{liga}"
        label = f"📌 {liga}" if (husk_val and liga in gemte_fokus) else liga
        with cols[idx % 3]:
            if st.checkbox(label, key=l_key, on_change=_opdater_fokus_hukommelse, args=(ligaer,)):
                v_ligaer.append(liga)
    pulje = [k for k in aktive if k["liga"] in v_ligaer]
    alle_klubber = sorted({k["hj"] for k in pulje} | {k["ud"] for k in pulje})
    valgte_klubber = st.multiselect("🔎 Søg eller vælg klubnavne i rullemenuen (lad feltet stå tomt for alle klubber i valgte ligaer):", options=alle_klubber, default=[], placeholder="Skriv eller vælg klubnavn...", key="man_klub_rullemenu")
    kandidater = []
    for k in pulje:
        if valgte_klubber:
            if k["hj"] in valgte_klubber or k["ud"] in valgte_klubber:
                kopi = dict(k)
                if k["hj"] in valgte_klubber and k["ud"] not in valgte_klubber:
                    kopi["valgt_hold"] = k["hj"]
