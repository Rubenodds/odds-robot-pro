import streamlit as st
from odds_motor import autopilot_scanner as ap
from odds_motor import byg_kupon, liga_favoritter
from historik import gem_data

def vis_manuel_scanner():
    st.subheader("⚽ 2. Manuel Hold Scanner (Flueben pr. Hold)")
    favs = list(liga_favoritter.hent_favorit_ligaer())

    c1, c2 = st.columns(2)
    timer = c1.slider("⏱️ Tidsramme frem (timer):", 1, 72, 48, key="man_timer")
    min_o, max_o = c2.slider("🎯 Ønsket odds-lag:", 2.0, 200.0, (10.0, 40.0), key="man_odds")

    alle = ap._hent_kampe_v9(tuple(favs))
    aktive = [k for k in alle if 0 < k["timer"] <= timer]
    ligaer = sorted({k["liga"] for k in aktive})

    if not ligaer:
        st.info(f"Ingen aktive ligaer inden for {timer} timer.")
        return

    v_ligaer = st.multiselect(f"🏆 Vælg ligaer ({len(ligaer)} aktive i {timer}T):", ligaer, default=ligaer, key="man_ligaer")
    pulje = [k for k in aktive if k["liga"] in v_ligaer]

    st.markdown("### ✅ Sæt flueben ved de hold, du vil have spillet på:")
    valgte_kampe_data = []
    for k in pulje:
        kid = str(k.get("id", f"{k['hj']}_{k['ud']}"))
        hj_key, ud_key = f"mhj_{kid}", f"mud_{kid}"
        hj_val = st.session_state.get(hj_key, False)
        ud_val = st.session_state.get(ud_key, False)

        col1, col2, col3 = st.columns([2, 2, 2])
        if not ud_val:
            hj_val = col1.checkbox(f"🏠 {k['hj']}", value=hj_val, key=hj_key)
        if not hj_val:
            ud_val = col2.checkbox(f"✈️ {k['ud']}", value=ud_val, key=ud_key)
        col3.caption(f"{k['liga'].split(' - ')[-1]} | {k['start'][-5:]}")

        if hj_val or ud_val:
            valgt_hold = k["hj"] if hj_val else k["ud"]
            kopi = dict(k)
            kopi["valgt_hold"] = valgt_hold
            valgte_kampe_data.append(kopi)

    markeder = st.multiselect("📊 Specialmarkeder:", ap.MARKEDER, default=ap.MARKEDER[:2], key="man_mark")

    if st.button(f"🔍 BEREGN KUPON ({len(valgte_kampe_data)} hold valgt)", type="primary", key="btn_man_scan"):
        if not valgte_kampe_data:
            st.warning("Sæt flueben ved mindst ét hold ovenfor.")
        else:
            maal = round((min_o + max_o) / 2.0, 2)
            kupon = byg_kupon.byg_kombineret_kupon(valgte_kampe_data, markeder or ap.MARKEDER[:1], maal)
            for k_obj, u_obj in zip(kupon["kampe"], valgte_kampe_data):
                k_obj["ctx"] = u_obj.get("ctx", {})
                k_obj["valgt_hold"] = u_obj["valgt_hold"]
            st.session_state["man_kupon"] = kupon

    if kupon := st.session_state.get("man_kupon"):
        st.markdown("### 🎫 Din Kupon:")
        valgte_kampe = []
        for i, k in enumerate(kupon["kampe"]):
            fok = f" [{k['valgt_hold']}]" if k.get("valgt_hold") else ""
            titel = f"{i+1}. {k['hj']} vs {k['ud']}{fok} — {', '.join(k['kombinationer'])} (Odds: {k['b365']} | {k['vinderchance_pct']}%)"
            if st.checkbox(titel, value=True, key=f"man_k_chk_{i}_{k['hj']}"):
                valgte_kampe.append(k)
        if valgte_kampe:
            side, samlet_o, uni_o, odd_o, samlet_pct, stjerner, flammer = ap._vurder_kupon(valgte_kampe)
            st.info(f"📊 **{len(valgte_kampe)}/{len(kupon['kampe'])} valg** | Odds: **{samlet_o}** ({side}) | Chance: **{samlet_pct}%** | Værdi: {'⭐' * stjerner} | Risiko: {'🔥' * flammer}")
            indsats = st.number_input("Indsats (kr.):", min_value=1.0, value=100.0, step=10.0, key="man_kr")
            if st.button("🚀 SPILLET (Gem i Supabase)", type="primary", key="btn_man_spillet"):
                if gem_data.gem_kupon_i_historik(list({k["liga"] for k in valgte_kampe}), [f"{k['hj']} - {k['ud']} ({', '.join(k['kombinationer'])})" for k in valgte_kampe], samlet_o, uni_o, odd_o, side, stjerner, indsats):
                    st.success("Manuel kupon gemt i Supabase!")
