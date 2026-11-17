import math, streamlit as st
from tidsstyring import dansk_tid
from odds_motor import liga_favoritter, byg_kupon, kamp_intelligens, manuel_hjaelp as mh, autopilot_hjaelp as ah, autopilot_kamp_feed as kf
from historik import gem_data

ALLE_MARKEDER = ["Standard (Mål / Kampvinder)", "Hjørnespark (Over/Under & Flest)", "Spillerskud & Skud på mål", "Tacklinger & Målmandsredninger", "Kort-sandsynlighed (Gule/Røde)", "Målscorer (Anytime/Første)", "Offsides"]

def _hent_kampe_v9(ligaer_tuple, timer_maks=24):
    return kf.hent_kampe_v9(ligaer_tuple, timer_maks)

def vis_autopilot_scanner():
    st.subheader("🌐 1. Autopilot Scanner (Form, H2H, Dommer & Vejr)")
    favs = list(liga_favoritter.hent_favorit_ligaer())
    timer = dansk_tid.vaelg_tidsramme("auto", standard=12)
    c1, c2, c3 = st.columns(3)
    min_o = c1.number_input("🎯 Min. odds:", min_value=1.2, value=10.0, step=1.0, key="auto_min_o")
    max_o = c2.number_input("🎯 Maks. odds:", min_value=1.5, value=50.0, step=5.0, key="auto_max_o")
    max_kampe = c3.number_input("🎫 Maks. kampe:", min_value=1, max_value=20, value=6, step=1, key="auto_max_kampe")

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
        kandidater, f1 = [], next(iter(alle), None)
        st.info(f"📭 Ingen kampe inden for **{timer} timer**." + (f" Næste: **{f1['hj']} vs {f1['ud']}** ({f1['start']} — om **{f1['timer']}T**)." if f1 else ""))

    st.caption("🤖 Scanner automatisk blandt alle udbudte bookmaker-markeder (±5 odds-tolerance).")
    b1, b2 = st.columns(2)
    if b1.button("🔍 FIND NYE SPILFORSLAG", type="primary", key="btn_scan") or b2.button("⚡ SCAN ALLE VALGTE KAMPE", key="btn_scan_alle"):
        if not kandidater:
            st.warning("⚠️ Ingen kampe valgt inden for tidsrammen.")
        else:
            st.session_state.pop("auto_gemt_msg", None)
            with st.spinner("⏳ Robotten analyserer kampe, vejr, dommere og live bookmaker-odds..."):
                runde = st.session_state.get("auto_scan_runde", 0)
                st.session_state["auto_scan_runde"] = runde + 1
                maal = round((max(1.2, min_o - 5.0) + max_o + 5.0) / 2.0, 2)
                udv = kandidater if st.session_state.get("btn_scan_alle") else ah.udvaelg_kandidater(kandidater, int(max_kampe), maal, runde)
                udv = kamp_intelligens.berig_valgte_kampe(udv)
                maks_ben = round(max(1.35, min(3.30, (max_o + 5.0) ** (1.0 / max(1, len(udv))))), 2)
                kupon = byg_kupon.byg_kombineret_kupon(udv, ALLE_MARKEDER, maal, runde, min_o=max(1.2, min_o - 5.0), max_o=max_o + 5.0)
                for idx, (ko, uo) in enumerate(zip(kupon["kampe"], udv)):
                    ko["ctx"] = uo["ctx"]
                    kupon["kampe"][idx] = ah.rens_kamp_valg(ko, runde, maks_ben)
                while len(kupon["kampe"]) > 1 and math.prod(x["b365"] for x in kupon["kampe"]) > (max_o + 5.0):
                    kupon["kampe"].pop()
                st.session_state["auto_kupon"] = kupon

    if kupon := st.session_state.get("auto_kupon"):
        st.markdown("### 🎫 Vælg hvilke forslag der skal med på kuponen:")
        valgte = []
        for i, k in enumerate(kupon["kampe"]):
            ctx = k.get("ctx", {})
            v = ctx.get("vejr")
            v_txt = f"{v['temp']}°C, {v['vind']} m/s ({v['effekt']})" if v else "Ikke tilgængeligt"
            col_chk, col_ny = st.columns([0.85, 0.15])
            if col_chk.checkbox(f"{i+1}. {k['hj']} vs {k['ud']} — {', '.join(k['kombinationer'])} (Odds: {k['b365']} | Chance: {k['vinderchance_pct']}%)", value=True, key=f"kupon_chk_{i}_{k['hj']}"):
                valgte.append(k)
            if col_ny.button("🔄", key=f"ny_valg_{i}_{k['hj']}", help="Skift spil og odds"):
                ny_r = k.get("kamp_runde", 0) + 1
                ny_k = ah.rens_kamp_valg(k, ny_r, 3.20)
                ny_k["kamp_runde"] = ny_r
                kupon["kampe"][i] = ny_k
                st.rerun()
            st.caption(f"📍 {k['liga']} | **{k['start']}** | Form: {ctx.get('hj_form')} vs {ctx.get('ud_form')} | Vejr: {v_txt}")
            st.caption(mh.begrundelse(k))
        if valgte:
            top3, sp, vp, stj, flm = ah.vurder_top3(valgte)
            anker = max(valgte, key=lambda x: float(x.get("vinderchance_pct", 50)))
            risiko_k = min(valgte, key=lambda x: float(x.get("vinderchance_pct", 50)))
            analyse_txt = f"🧠 **Samlet analyse:** Stærkeste anker er **{anker['hj']} - {anker['ud']}** ({anker['vinderchance_pct']}%), mens **{risiko_k['hj']} - {risiko_k['ud']}** (@ {risiko_k['b365']}) er kuponens flaskehals."
            st.info(f"🥇 **{top3[0][0]}:** {top3[0][1]} | 🥈 **{top3[1][0]}:** {top3[1][1]} | 🥉 **{top3[2][0]}:** {top3[2][1]}\n\n📊 **{len(valgte)}/{len(kupon['kampe'])} valg** | Chance: **{sp}%** | Værdi: {'⭐'*stj} ({vp:+.1f}%) | Risiko: {'🔥'*flm}\n\n{analyse_txt}")
            kr = st.number_input("Indsats (kr.):", min_value=1.0, value=100.0, step=10.0, key="auto_kr")
            if st.button("🚀 SPILLET", type="primary", key="btn_auto_spillet"):
                gem_data.gem_kupon({"kilde": "Autopilot", "kampe": valgte, "odds": top3[0][1], "indsats": kr, "chance_pct": sp})
                st.session_state["auto_gemt_msg"] = f"✅ OK — Kupon med {len(valgte)} kampe (odds {top3[0][1]}) er lagt i historikken!"
            if gemt_msg := st.session_state.get("auto_gemt_msg"):
                st.success(gemt_msg)
