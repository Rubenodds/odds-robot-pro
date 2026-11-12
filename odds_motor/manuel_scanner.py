import streamlit as st
from tidsstyring import dansk_tid
from odds_motor import autopilot_scanner as ap, liga_favoritter, manuel_hjaelp as mh, kamp_intelligens
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
    allerede = [h for h in st.session_state.get("man_klubber", []) if h in all_klubber]
    blokeret = set()
    for h in allerede:
        for k in filt:
            if k["hj"] == h:
                blokeret.add(k["ud"])
            elif k["ud"] == h:
                blokeret.add(k["hj"])
    tilgaengelige = [h for h in all_klubber if h in allerede or h not in blokeret]
    valgte_klubber = st.multiselect("🔍 Søg og vælg hold (modstander fjernes automatisk):", tilgaengelige, default=allerede, key="man_klubber")

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
            maal_liste = kamp_intelligens.berig_valgte_kampe(maal_liste)
            st.session_state["man_kupon"] = mh.byg_forslag(maal_liste, 25.0, kun_res=bool(k2))

    if kupon := st.session_state.get("man_kupon"):
        st.markdown("### 🎫 Din Manuelt Byggede Kupon:")
        valgte = []
        for i, k in enumerate(kupon["kampe"]):
            ctx = k.get("ctx", {})
            v = ctx.get("vejr")
            v_txt = f"{v['temp']}°C, {v['vind']} m/s ({v['effekt']})" if v else "Ikke tilgængeligt"
            dom_txt = f" | Dommer: {ctx['dommer']}" if ctx.get("dommer") else ""
            if st.checkbox(f"{i+1}. {k['hj']} vs {k['ud']} — {', '.join(k['kombinationer'])} (Odds: {k['b365']} | Chance: {k['vinderchance_pct']}%)", value=True, key=f"man_chk_{i}_{k['hj']}_{k['ud']}"):
                valgte.append(k)
            st.caption(f"📍 {k['liga']} | **{k['start']}** | Form: {ctx.get('hj_form')} vs {ctx.get('ud_form')}{dom_txt} | Vejr: {v_txt}")
            st.caption(k.get("begrundelse") or mh.begrundelse(k))

        if valgte:
            side, bo, uo, oo, sp, stj, flm = ap._vurder_kupon(valgte)
            st.info(f"🥇 **Bedste odds:** {side} ({bo}) | 🥈 Unibet: {uo} | 🥉 Danske Spil: {oo} | Chance: **{sp}%** | Værdi: {'⭐'*stj} | Risiko: {'🔥'*flm}")
            kr = st.number_input("Indsats (kr.):", min_value=1.0, value=100.0, step=10.0, key="man_kr")
            if st.button("🚀 SPILLET (Gem i Supabase)", type="primary", key="btn_man_spillet"):
                if gem_data.gem_kupon_i_historik(list({k["liga"] for k in valgte}), [f"{k['hj']} - {k['ud']} ({', '.join(k['kombinationer'])}) [{k['start']}]" for k in valgte], bo, uo, oo, side, stj, kr):
                    st.success("Kupon gemt i Supabase!")
