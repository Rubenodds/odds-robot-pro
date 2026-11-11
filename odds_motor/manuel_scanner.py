import streamlit as st
from odds_motor import autopilot_scanner as ap
from odds_motor import liga_favoritter, manuel_hjaelp as mh
from historik import gem_data

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
            st.session_state["man_kupon"] = mh.byg_forslag(udv, maal, k_res)
    if kupon := st.session_state.get("man_kupon"):
        st.markdown("### 🎫 Din Kupon (Accepter / fjern forslag med flueben):")
        valgte = []
        for i, k in enumerate(kupon["kampe"]):
            fok = f" [{k['valgt_hold']}]" if k.get("valgt_hold") else ""
            if st.checkbox(f"{i+1}. {k['hj']} vs {k['ud']}{fok} — {', '.join(k['kombinationer'])} (Odds: {k['b365']} | {k['vinderchance_pct']}%)", value=True, key=f"man_k_chk_{i}_{k['hj']}"):
                valgte.append(k)
            st.caption(k.get("begrundelse", mh.begrundelse(k)))
        if valgte:
            side, s_o, u_o, o_o, s_pct, stj, flm = ap._vurder_kupon(valgte)
            imp = round(100.0 / max(s_o, 1.01), 1)
            val_p = round(s_pct - imp, 1)
            v1, v2, v3 = st.columns(3)
            v1.metric("🎯 Chance", f"{s_pct:.1f}%", f"Marked: {imp:.1f}%")
            v2.metric("⭐ Værdi", "⭐" * stj, f"{val_p:+.1f}% edge")
            v3.metric("🔥 Risiko", "🔥" * flm, f"{len(valgte)}/{len(kupon['kampe'])} valg")
            st.info(f"Kuponen har **{len(valgte)} spil** til samlet odds **{s_o:.2f}** ({side}). Vurderet chance er **{s_pct:.1f}%** ({val_p:+.1f}% edge).")
            top3 = sorted([("Bet365", float(s_o)), ("Unibet", float(u_o)), ("Danske Spil", float(o_o))], key=lambda item: item[1], reverse=True)
            (g_n, g_o), (s_n, s_o2), (b_n, b_o) = top3
            t1, t2, t3 = st.columns(3)
            t1.metric(f"🥇 Guld: {g_n}", f"{g_o:.2f}x")
            t2.metric(f"🥈 Sølv: {s_n}", f"{s_o2:.2f}x")
            t3.metric(f"🥉 Bronze: {b_n}", f"{b_o:.2f}x")
            indsats = st.number_input("Indsats (kr.):", min_value=1.0, value=100.0, step=10.0, key="man_kr")
            if st.button("🚀 SPILLET (Gem i Supabase)", type="primary", use_container_width=True, key="btn_man_spillet"):
                try:
                    res = gem_data.gem_kupon_i_historik(list({k["liga"] for k in valgte}), [f"{k['hj']} - {k['ud']} ({', '.join(k['kombinationer'])})" for k in valgte], s_o, u_o, o_o, side, stj, indsats)
                    st.success(f"✅ Kupon på {indsats:.0f} kr. gemt i Supabase!") if res is not False else st.error("⚠️ Supabase fejl ved lagring.")
                except Exception as e:
                    st.error(f"⚠️ Fejl ved lagring: {e}")
