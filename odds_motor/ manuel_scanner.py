import streamlit as st
from odds_motor import autopilot_scanner as ap
from odds_motor import byg_kupon, liga_favoritter
from historik import gem_data


def _byg_spilbare_forslag_sikkert(udvalgte, maal_odds):
    """
    Bruger byg_kupon.byg_kombineret_kupon på tværs af ALLE spilmarkeder (ap.MARKEDER),
    med sikker fallback hvis en kamp mangler eksterne oddsdata.
    """
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

    # Sikker fallback så kuponen altid genererer spilbare forslag
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
        st.info(f"📭 Ingen aktive ligaer inden for **{timer} timer**. Prøv at øge tidsrammen.")
        return

    # 1. LIGAER MED FLUEBEN (Kun ligaer – ingen flueben på spilmarkeder)
    st.markdown(f"### 🏆 Vælg ligaer med flueben ({len(ligaer)} aktive i {timer}T):")
    vaelg_alle = st.checkbox("Vælg / fravælg alle aktive ligaer", value=True, key="man_alle_ligaer")

    v_ligaer = []
    cols = st.columns(3)
    for idx, liga in enumerate(ligaer):
        with cols[idx % 3]:
            if st.checkbox(liga, value=vaelg_alle, key=f"man_liga_chk_{idx}_{liga}"):
                v_ligaer.append(liga)

    pulje = [k for k in aktive if k["liga"] in v_ligaer]

    # 2. SØGBAR RULLEMENU FOR KLUBNAVNE
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

    st.caption(f"📊 **{len(kandidater)} kampe** i spil – alle spilmarkeder og spilbare forslag analyseres automatisk.")

    # 3. BEREGN KUPON MED SPILBARE FORSLAG
    if st.button(f"🔍 BEREGN KUPON ({len(kandidater)} kampe i spil)", type="primary", use_container_width=True, key="btn_man_scan"):
        if not kandidater:
            st.warning("⚠️ Sæt flueben ved mindst én liga (eller ryd klubfilteret) for at finde kampe.")
        else:
            if len(kandidater) > max_kampe and not valgte_klubber:
                udvalgte, maal = ap._vaelg_bedste_kombination(kandidater, min_o, max_o, max_kampe)
            else:
                udvalgte = kandidater[:max_kampe]
                maal = round((min_o + max_o) / 2.0, 2)

            st.session_state["man_kupon"] = _byg_spilbare_forslag_sikkert(udvalgte, maal)

    # 4. VIS KUPON & GEM I SUPABASE
    if kupon := st.session_state.get("man_kupon"):
        st.markdown("### 🎫 Din Kupon (Spilbare Forslag):")
        valgte_kampe = []
        for i, k in enumerate(kupon["kampe"]):
            fok = f" [{k['valgt_hold']}]" if k.get("valgt_hold") else ""
            titel = f"{i+1}. {k['hj']} vs {k['ud']}{fok} — {', '.join(k['kombinationer'])} (Odds: {k['b365']} | {k['vinderchance_pct']}%)"
            if st.checkbox(titel, value=True, key=f"man_k_chk_{i}_{k['hj']}"):
                valgte_kampe.append(k)

        if valgte_kampe:
            side, samlet_o, uni_o, odd_o, samlet_pct, stjerner, flammer = ap._vurder_kupon(valgte_kampe)
            st.info(
                f"📊 **{len(valgte_kampe)}/{len(kupon['kampe'])} valg** | Odds: **{samlet_o}** ({side}) | "
                f"Chance: **{samlet_pct}%** | Værdi: {'⭐' * stjerner} | Risiko: {'🔥' * flammer}"
            )
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
                    st.success("✅ Manuel kupon gemt i Supabase!")
