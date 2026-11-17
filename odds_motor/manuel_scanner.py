import streamlit as st
from tidsstyring import dansk_tid
from odds_motor import autopilot_scanner as ap, liga_favoritter, manuel_hjaelp as mh, autopilot_hjaelp as ah, kamp_intelligens
from historik import gem_data

def vis_manuel_scanner():
    st.subheader("🎯 2. Manuel Kamp-Vælger & Kuponbygger")
    favs = list(liga_favoritter.hent_favorit_ligaer())
    timer = dansk_tid.vaelg_tidsramme("man", standard=12)
    alle = ap._hent_kampe_v9(tuple(favs), timer)
    aktive = [k for k in alle if 0 < k["timer"] <= timer]
    ligaer = sorted({k["liga"] for k in aktive})
    if not ligaer:
        f1 = next(iter(alle), None)
        st.info(f"📭 Ingen aktive kampe inden for **{timer} timer**." + (f" Næste: **{f1['hj']} vs {f1['ud']}** ({f1['start']})." if f1 else ""))
        return

    st.session_state.setdefault("man_pins", [])
    pins = [l for l in st.session_state["man_pins"] if l in ligaer]
    c_l1, c_l2 = st.columns([3, 1])
    v_ligaer = c_l1.multiselect(f"🏆 Vælg ligaer ({len(ligaer)} aktive i {timer}T):", ligaer, default=pins, key="man_ligaer")
    if c_l2.button("📌 Fastgør valgte", key="btn_man_pin"):
        st.session_state["man_pins"] = list(v_ligaer)
        st.rerun()

    filt = [k for k in aktive if k["liga"] in v_ligaer]
    if not filt:
        st.caption("👆 Sæt flueben ved én eller flere ligaer ovenfor for at se kampe og klubber.")
        return

    all_klubber = sorted({k["hj"] for k in filt} | {k["ud"] for k in filt})
    st.session_state["man_klubber"] = [h for h in st.session_state.get("man_klubber", []) if h in all_klubber]
    blokeret = {k["ud"] if k["hj"] == h else k["hj"] for h in st.session_state["man_klubber"] for k in filt if h in (k["hj"], k["ud"])}
    tilgaengelige = [h for h in all_klubber if h in st.session_state["man_klubber"] or h not in blokeret]

    c_k1, c_k2 = st.columns([2, 1])
    valgte_klubber = c_k1.multiselect("🔍 Søg og vælg hold (modstander fjernes automatisk):", tilgaengelige, key="man_klubber")
    maal_odds = c_k2.number_input("🎯 Ønsket mål-odds:", min_value=1.10, max_value=5000.0, value=10.0, step=1.0, key="man_maal_odds")

    udvalgte, sete_kampe = [], set()
    for hold in valgte_klubber:
        k = next((x for x in filt if (x["hj"] == hold or x["ud"] == hold) and x["id"] not in sete_kampe), None)
        if k:
            sete_kampe.add(k["id"])
            ko = dict(k)
            ko["valgt_hold"] = hold
            udvalgte.append(ko)

    b1, b2, b3 = st.columns(3)
    k1 = b1.button("🧮 Beregn Kupon (Valgte hold)", type="primary", key="btn_man_beregn")
    k2 = b2.button("🎯 Kun Resultatspil (1X2 / Ciffer)", key="btn_man_res")
    k3 = b3.button("⚡ TILFØJ ALLE KAMPE I LIGAER", key="btn_man_alle")
    if k1 or k2 or k3:
        maal_liste = [dict(x) for x in filt] if k3 else udvalgte
        if not maal_liste:
            st.warning("⚠️ Vælg mindst ét hold i rullemenuen først.")
        else:
            st.session_state.pop("man_gemt_ok", None)
            with st.spinner("⏳ Beregner rigtige bookmaker-markeder..."):
                st.session_state["man_kupon"] = mh.byg_forslag(kamp_intelligens.berig_valgte_kampe(maal_liste), float(maal_odds), kun_res=bool(k2))

    if kupon := st.session_state.get("man_kupon"):
        st.markdown("### 🎫 Din Manuelt Byggede Kupon:")
        valgte = []
        for i, k in enumerate(kupon["kampe"]):
            ctx = k.get("ctx", {})
            v = ctx.get("vejr")
            v_txt = f"{v['temp']}°C, {v['vind']} m/s ({v['effekt']})" if v else "Ikke tilgængeligt"
            if st.checkbox(f"{i+1}. {k['hj']} vs {k['ud']} (@ {k['b365']} | {k['vinderchance_pct']}%)", value=True, key=f"man_chk_{i}_{k['hj']}_{k['ud']}"):
                valgte.append(k)
            st.markdown(f"🎯 **{', '.join(k['kombinationer'])}**")
            st.caption(f"📍 {k['liga']} | **{k['start']}** | Form: {ctx.get('hj_form')} vs {ctx.get('ud_form')} | Vejr: {v_txt}")
            st.caption(mh.begrundelse(k))

        if valgte:
            top3, sp, vp, stj, flm = ah.vurder_top3(valgte)
            bo = float(top3[0][1])
            kr = st.number_input("Indsats (kr.):", min_value=1.0, value=100.0, step=10.0, key="man_kr")
            sort_k = sorted(valgte, key=lambda x: float(x.get("vinderchance_pct", 50)), reverse=True)
            anker, flaske = sort_k[0], sort_k[-1]
            f_txt = f", mens **{flaske['hj']} - {flaske['ud']}** (@ {flaske['b365']}) er flaskehalsen" if len(sort_k) > 1 else ""
            analyse_txt = f"🧠 **Samlet kuponanalyse:** Kuponen giver **{round(kr * bo, 2):.2f} kr.** ved {kr:.0f} kr. indsats. Stærkeste anker er **{anker['hj']} - {anker['ud']}** ({anker['vinderchance_pct']}%){f_txt}."
            st.info(f"🥇 **{top3[0][0]}:** {top3[0][1]} | 🥈 **{top3[1][0]}:** {top3[1][1]} | 🥉 **{top3[2][0]}:** {top3[2][1]}\n\n📊 **{len(valgte)} valg** | Chance: **{sp}%** | Værdi: {'⭐'*stj} ({vp:+.1f}%) | Risiko: {'🔥'*flm}\n\n{analyse_txt}")
            if ok_msg := st.session_state.get("man_gemt_ok"):
                st.success(ok_msg)
            elif st.button("🚀 SPILLET (Gem i Historik)", type="primary", key="btn_man_spillet"):
                with st.spinner("⏳ Gemmer kupon i Cloud-historik..."):
                    gem_data.gem_kupon_i_historik(kilde="Manuel Scanner", kampe=[f"{k['hj']} - {k['ud']} ({', '.join(k['kombinationer'])}) [{k['start']}]" for k in valgte], odds=bo, indsats=kr)
                    st.session_state["man_gemt_ok"] = f"✅ OK — Kupon ({len(valgte)} kampe @ {bo}) er gemt i historikken!"
                    st.rerun()
