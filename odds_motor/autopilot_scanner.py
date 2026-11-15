import streamlit as st
from tidsstyring import dansk_tid
from odds_motor import liga_favoritter, byg_kupon, kamp_intelligens, manuel_hjaelp as mh, autopilot_hjaelp as ah, autopilot_kamp_feed as kf
from historik import gem_data

MARKEDER = ["Standard (Mål / Kampvinder)", "Hjørnespark (Over/Under & Flest)", "Spillerskud & Skud på mål", "Tacklinger & Målmandsredninger", "Kort-sandsynlighed (Gule/Røde)", "Målscorer (Anytime/Første)", "Offsides"]

def _hent_kampe_v9(ligaer_tuple, timer_maks=24):
    return kf.hent_kampe_v9(ligaer_tuple, timer_maks)

def _vurder_kupon(valgte):
    top3, sp, _, stj, flm = ah.vurder_top3(valgte)
    return top3[0][0], top3[0][1], top3[1][1], top3[2][1], sp, stj, flm

def vis_autopilot_scanner():
    st.subheader("🌐 1. Autopilot Scanner (Form, H2H, Dommer & Vejr)")
    if msg := st.session_state.pop("sidste_gem_ok", None):
        st.success(msg)
    favs = list(liga_favoritter.hent_favorit_ligaer())
    timer = dansk_tid.vaelg_tidsramme("auto", standard=12)
    c1, c2, c3 = st.columns(3)
    min_o = c1.number_input("🎯 Min. odds:", min_value=1.2, value=10.0, step=1.0, key="auto_min_o")
    max_o = c2.number_input("🎯 Maks. odds:", min_value=1.5, value=50.0, step=5.0, key="auto_max_o")
    max_kampe = c3.number_input("🎫 Maks. kampe:", min_value=1, max_value=20, value=4, step=1, key="auto_max_kampe")

    alle = _hent_kampe_v9(tuple(favs), timer)
    aktive = [k for k in alle if 0 < k["timer"] <= timer]
    senere = [k for k in alle if k["timer"] > timer]
    ligaer = sorted({k["liga"] for k in aktive})

    if ligaer:
        v_ligaer = st.multiselect(f"🏆 Aktive turneringer ({len(ligaer)} i {timer}T | {len(aktive)} kampe):", ligaer, default=ligaer, key=f"auto_ligaer_{timer}")
        filt = [k for k in aktive if k["liga"] in v_ligaer]
        valg_mode = st.radio("🎯 Kampvalg:", [f"Alle kampe i valgte ligaer ({len(filt)} stk.)", "Håndpluk bestemte kampe"], horizontal=True, key="auto_mode")
        kandidater = [k for k in filt if k["label"] in st.multiselect("⚽ Søg kampe:", [k["label"] for k in filt], key=f"auto_kv_{timer}")] if valg_mode == "Håndpluk bestemte kampe" else filt
        if senere:
            n1 = next(iter(senere))
            st.caption(f"⏭️ Næste kamp efter {timer}T: **{n1['hj']} vs {n1['ud']}** ({n1['liga']} | {n1['start']} — om **{n1['timer']}T**)")
    else:
        kandidater = []
        f1 = next(iter(alle), None)
        st.info(f"📭 Ingen kampe inden for **{timer} timer**." + (f" Næste: **{f1['hj']} vs {f1['ud']}** ({f1['start']} — om **{f1['timer']}T**)." if f1 else ""))

    markeder = st.multiselect("📊 Specialmarkeder:", MARKEDER, default=MARKEDER[:3], key="auto_mark")
    b1, b2 = st.columns(2)
    if b1.button("🔍 FIND NYE SPILFORSLAG", type="primary", key="btn_scan") or b2.button("⚡ SCAN ALLE VALGTE KAMPE", key="btn_scan_alle"):
        if not kandidater or not markeder:
            st.warning("⚠️ Vælg både kampe og specialmarkeder.")
        else:
            runde = st.session_state.get("auto_scan_runde", 0)
            st.session_state["auto_scan_runde"] = runde + 1
            maal = round((min_o + max(min_o, max_o)) / 2.0, 2)
            udv = kandidater if st.session_state.get("btn_scan_alle") else ah.udvaelg_kandidater(kandidater, int(max_kampe), maal, runde)
            udv = kamp_intelligens.berig_valgte_kampe(udv)
            kupon = byg_kupon.byg_kombineret_kupon(udv, markeder, maal, runde, min_o=min_o, max_o=max_o)
            for idx, (ko, uo) in enumerate(zip(kupon["kampe"], udv)):
                ko["ctx"] = uo["ctx"]
                kupon["kampe"][idx] = ah.rens_kamp_valg(ko, runde)
            st.session_state["auto_kupon"] = kupon

    if kupon := st.session_state.get("auto_kupon"):
        st.markdown("### 🎫 Vælg hvilke forslag der skal med på kuponen:")
        valgte = []
        for i, k in enumerate(kupon["kampe"]):
            ctx = k.get("ctx", {})
            v = ctx.get("vejr")
            v_txt = f"{v['temp']}°C, {v['vind']} m/s ({v['effekt']})" if v else "Ikke tilgængeligt"
            dom_txt = f" | Dommer: {ctx['dommer']}" if ctx.get("dommer") else ""
            if st.checkbox(f"{i+1}. {k['hj']} vs {k['ud']} — {', '.join(k['kombinationer'])} (Odds: {k['b365']} | Chance: {k['vinderchance_pct']}%)", value=True, key=f"kupon_chk_{i}_{k['hj']}_{k['ud']}"):
                valgte.append(k)
            st.caption(f"📍 {k['liga']} | **{k['start']}** | Form: {ctx.get('hj_form')} vs {ctx.get('ud_form')}{dom_txt} | Vejr: {v_txt}")
            st.caption(mh.begrundelse(k))
        if valgte:
            top3, sp, vp, stj, flm = ah.vurder_top3(valgte)
            s_txt = f"🥇 **{top3[0][0]}:** {top3[0][1]} | 🥈 **{top3[1][0]}:** {top3[1][1]} | 🥉 **{top3[2][0]}:** {top3[2][1]}"
            st.info(f"{s_txt}\n\n📊 **{len(valgte)}/{len(kupon['kampe'])} valg** | Chance: **{sp}%** | Værdi: {'⭐'*stj} ({vp:+.1f}%) | Risiko: {'🔥'*flm}")
            kr = st.number_input("Indsats (kr.):", min_value=1.0, value=100.0, step=10.0, key="auto_kr")
            if st.button("🚀 SPILLET (Gem valgte i Historik)", type="primary", key="btn_auto_spillet"):
                if gem_data.gem_kupon_i_historik(kilde="Autopilot Scanner", kampe=[f"{k['hj']} - {k['ud']} ({', '.join(k['kombinationer'])}) [{k['start']}]" for k in valgte], odds=top3[0][1], indsats=kr):
                    st.rerun()
