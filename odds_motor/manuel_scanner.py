import streamlit as st
from odds_motor import autopilot_scanner as ap
from odds_motor import byg_kupon, liga_favoritter
from historik import gem_data


def _byg_spilbare_forslag(udvalgte, maal_odds):
    try:
        kupon = byg_kupon.byg_kombineret_kupon(udvalgte, ap.MARKEDER, maal_odds)
        if isinstance(kupon, dict) and kupon.get("kampe"):
            for k_obj, u_obj in zip(kupon["kampe"], udvalgte):
                k_obj["ctx"] = u_obj.get("ctx", {})
                if u_obj.get("valgt_hold"):
                    k_obj["valgt_hold"] = u_obj["valgt_hold"]
            return kupon
    except Exception:
        pass

    kampe_resultat = []
    for u in udvalgte:
        kopi = dict(u)
        pct = float(kopi.get("pct", 55.0))
        ctx = kopi.get("ctx") or {}
        fokus = kopi.get("valgt_hold")

        forslag = []
        if fokus:
            forslag.append(f"Kampvinder / DNB: {fokus}")
        elif pct >= 60.0:
            forslag.append(f"Kampvinder: {kopi['hj']}")
        elif pct <= 44.0:
            forslag.append(f"Kampvinder: {kopi['ud']}")
        else:
            forslag.append("Standard: Over 1.5 mål i kampen")

        if ctx.get("justering_pct", 0.0) >= 1.5:
            forslag.append("Hjørnespark: Over 8.5 total")
        if ctx.get("dommer") and ctx.get("dommer") != "Afventer":
            forslag.append("Kort-sandsynlighed: Over 3.5 kort")

        kopi["kombinationer"] = forslag
        kopi.setdefault("b365", round(max(1.35, min(3.40, 100.0 / max(pct, 30.0))), 2))
        kopi.setdefault("vinderchance_pct", pct)
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
    husk_aktiv = st.session_state.get("man_husk_favorit", False)
    if husk_aktiv:
        valgte_nu = [l for l in aktive_ligaer if st.session_state.get(f"man_liga_chk_{l}", False)]
        tidligere = [l for l in _hent_gemte_fokus_ligaer() if l not in aktive_ligaer]
        samlet = sorted(set(valgte_nu + tidligere))
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

    gemte_fokus = _hent_gemte_fokus_ligaer()
    har_gemt_fokus = len(gemte_fokus) > 0

    st.markdown(f"### 🏆 Vælg ligaer med flueben ({len(ligaer)} aktive i {timer}T):")

    # Favorit-hukommelsesknap til mobil og PC
    husk_val = st.checkbox(
        "⭐ Husk mine valgte fokus-ligaer fast",
        value=har_gemt_fokus,
        key="man_husk_favorit",
        on_change=_opdater_fokus_hukommelse,
        args=(ligaer,),
    )

    if husk_val and gemte_fokus:
        st.caption(f"📌 Gemte fokus-ligaer aktive ({len(gemte_fokus)} stk.) – øvrige ligaer er klar til flueben nedenfor.")

    # Initialiser flueben ud fra gemte fokus-ligaer (eller alle, hvis ingen fokus-ligaer er gemt)
    for liga in ligaer:
        l_key = f"man_liga_chk_{liga}"
        if l_key not in st.session_state:
            st.session_state[l_key] = (liga in gemte_fokus) if har_gemt_fokus else True

    v_ligaer = []
    cols = st.columns(3)
    for idx, liga in enumerate(ligaer):
        l_key = f"man_liga_chk_{liga}"
        label = f"⭐ {liga}" if (husk_val and liga in gemte_fokus) else liga
        with cols[idx % 3]:
            if st.checkbox(
                label,
                key=l_key,
                on_change=_opdater_fokus_hukommelse,
                args=(ligaer,),
            ):
                v_ligaer.append(liga)

    pulje = [k for k in aktive if k["liga"] in v_ligaer]

    # Søgbar rullemenu til klubnavne
    alle_klubber = sorted({k["hj"] for k in pulje} | {k["ud"] for k in pulje})
    valgte_klubber = st.multiselect(
        "🔎 Søg eller vælg klubnavne i rullemenuen (lad feltet stå tomt for alle klubber i valgte ligaer):",
        options=alle_klubber,
        default=[],
        placeholder="Skriv eller vælg klubnavn...",
        key="man_klub_rullemenu",
    )

    kandidater = []
    for k in pulje:
        if valgte_klubber:
            if k["hj"] in valgte_klubber or k["ud"] in valgte_klubber:
                kopi = dict(k)
                if k["hj"] in valgte_klubber and k["ud"] not in valgte_klubber:
                    kopi["valgt_hold"] = k["hj"]
                elif k["ud"] in valgte_klubber and k["hj"] not in valgte_klubber:
                    kopi["valgt_hold"] = k["ud"]
                kandidater.append(kopi)
        else:
            kandidater.append(dict(k))

    st.caption(f"📊 **{len(kandidater)} kampe** i spil – alle spilmarkeder analyseres automatisk.")

    if st.button(f"🔍 BEREGN KUPON ({len(kandidater)} kampe i spil)", type="primary", use_container_width=True, key="btn_man_scan"):
        if not kandidater:
            st.warning("⚠️ Sæt flueben ved mindst én liga (eller ryd klubfilteret).")
        else:
            if len(kandidater) > max_kampe and not valgte_klubber:
                udvalgte, maal = ap._vaelg_bedste_kombination(kandidater, min_o, max_o, max_kampe)
            else:
                udvalgte = kandidater[:max_kampe]
                maal = round((min_o + max_o) / 2.0, 2)

            st.session_state["man_kupon"] = _byg_spilbare_forslag(udvalgte, maal)

    if kupon := st.session_state.get("man_kupon"):
        st.markdown("### 🎫 Din Kupon (Accepter / fjern forslag med flueben):")
        valgte_kampe = []
        for i, k in enumerate(kupon["kampe"]):
            fok = f" [{k['valgt_hold']}]" if k.get("valgt_hold") else ""
            titel = f"{i+1}. {k['hj']} vs {k['ud']}{fok} — {', '.join(k['kombinationer'])} (Odds: {k['b365']} | {k['vinderchance_pct']}%)"
            if st.checkbox(titel, value=True, key=f"man_k_chk_{i}_{k['hj']}"):
                valgte_kampe.append(k)

        if valgte_kampe:
            side, samlet_o, uni_o, odd_o, samlet_pct, stjerner, flammer = ap._vurder_kupon(valgte_kampe)

            st.markdown("#### 🏆 Top 3 Bedste Bets (Live-beregnet på dine valgte forslag):")
            top3 = sorted(
                [("Bet365", samlet_o), ("Unibet", uni_o), ("Danske Spil", odd_o)],
                key=lambda x: x[1],
                reverse=True,
            )
            t1, t2, t3 = st.columns(3)
            t1.metric(f"🥇 #1 {top3[0][0]}", f"{top3[0][1]:.2f}x", f"Chance: {samlet_pct}%")
            t2.metric(f"🥈 #2 {top3[1][0]}", f"{top3[1][1]:.2f}x", f"{'⭐' * stjerner}")
            t3.metric(f"🥉 #3 {top3[2][0]}", f"{top3[2][1]:.2f}x", f"{'🔥' * flammer}")

            indsats = st.number_input("Indsats (kr.):", min_value=1.0, value=100.0, step=10.0, key="man_kr")
            if st.button("🚀 SPILLET (Gem i Supabase)", type="primary", key="btn_man_spillet"):
                if gem_data.gem_kupon_i_historik(
                    list({k["liga"] for k in valgte_kampe}),
                    [f"{k['hj']} - {k['ud']} ({', '.join(k['kombinationer'])})" for k in valgte_kampe],
                    samlet_o,
                    uni_o,
                    odd_o,
                    side,
                    stjerner,
                    indsats,
                ):
                    st.success("✅ Kupon gemt i Supabase!")
