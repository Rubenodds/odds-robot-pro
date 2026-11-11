import streamlit as st
from odds_motor import liga_favoritter, byg_kupon
from historik import gem_data

# Importer din Mappe 1-motor (ret stien hvis din Mappe 1-fil ligger i en anden mappe)
from mappe_1 import autopilot_scanner as ap


def _generer_spilbare_forslag(kampe_liste):
    """
    Beriger hver kamp med konkrete, spilbare forslag på tværs af ALLE markeder
    (mål, hjørnespark, skud, kort, målscorere osv.), så de indgår i udvælgelsen.
    """
    spilbare = []
    for k in kampe_liste:
        kamp_kopi = dict(k)
        try:
            # Kalder din eksisterende kupon-/markedsbygger med alle markeder
            forslag = byg_kupon.byg_spilbare_forslag(kamp_kopi, ap.MARKEDER)
            if isinstance(forslag, dict) and forslag.get("kombinationer"):
                kamp_kopi.update(forslag)
                spilbare.append(kamp_kopi)
                continue
        except Exception:
            pass

        # Fallback: Genererer spilbare kombinationer ud fra kampens kontekst og procent
        ctx = kamp_kopi.get("ctx") or {}
        pct = float(kamp_kopi.get("pct", 55.0))
        kombis = []

        if pct >= 62.0:
            kamp_kopi["valgt_hold"] = kamp_kopi["hj"]
            kombis.append(f"1X2: {kamp_kopi['hj']} vinder")
        elif pct <= 44.0:
            kamp_kopi["valgt_hold"] = kamp_kopi["ud"]
            kombis.append(f"1X2: {kamp_kopi['ud']} vinder")
        else:
            kombis.append("Standard: Over 1.5 mål i kampen")

        if ctx.get("justering_pct", 0.0) >= 2.0:
            kombis.append("Hjørnespark: Over 8.5 total")
        if ctx.get("dommer") and ctx.get("dommer") != "Afventer":
            kombis.append("Kort-sandsynlighed: Over 3.5 kort")

        kamp_kopi["kombinationer"] = kombis
        kamp_kopi.setdefault("b365", round(max(1.35, min(3.40, 100.0 / max(pct, 30.0))), 2))
        kamp_kopi.setdefault("vinderchance_pct", pct)
        spilbare.append(kamp_kopi)

    return spilbare


def vis_manuel_scanner():
    st.subheader("🎯 2. Manuel Liga- & Klub-Scanner (Alle Spilmarkeder)")
    favs = list(liga_favoritter.hent_favorit_ligaer())

    # 1. Kontrolpanel (isolerede keys med 'man_')
    c1, c2, c3 = st.columns(3)
    timer = c1.slider("⏱️ Tidsramme frem (timer):", 1, 72, 48, key="man_timer")
    min_o, max_o = c2.slider("🎯 Ønsket odds-lag:", 2.0, 200.0, (20.0, 50.0), key="man_odds")
    max_kampe = c3.slider("🎫 Maks. kampe på kupon:", 1, 12, 4, key="man_max_kampe")

    # 2. Hent alle kommende kampe via Mappe 1
    alle = ap._hent_kampe_v9(tuple(favs))
    aktive = [k for k in alle if 0 < k["timer"] <= timer]
    ligaer = sorted({k["liga"] for k in aktive})

    if ligaer:
        # 3. LIGAER MED FLUEBEN (kun ligaer – ingen flueben på spilmarkeder)
        st.markdown(f"### 🏆 Vælg ligaer med flueben ({len(ligaer)} aktive i {timer}T):")
        vaelg_alle = st.checkbox("Vælg / fravælg alle aktive ligaer", value=True, key="man_alle_ligaer")

        v_ligaer = []
        cols = st.columns(3)
        for idx, liga in enumerate(ligaer):
            with cols[idx % 3]:
                if st.checkbox(liga, value=vaelg_alle, key=f"man_liga_chk_{liga}"):
                    v_ligaer.append(liga)

        filt_liga = [k for k in aktive if k["liga"] in v_ligaer]

        # 4. SØGBAR RULLEMENU FOR KLUBNAVNE
        alle_klubber = sorted({k["hj"] for k in filt_liga} | {k["ud"] for k in filt_liga})
        valgte_klubber = st.multiselect(
            "🔎 Søg eller vælg klubnavne i rullemenuen (lad feltet stå tomt for alle klubber i valgte ligaer):",
            options=alle_klubber,
            default=[],
            placeholder="Skriv klubnavn (f.eks. FC København, Arsenal, Real Madrid)...",
            key="man_klub_rullemenu",
        )

        if valgte_klubber:
            kandidater = [
                k for k in filt_liga
                if k["hj"] in valgte_klubber or k["ud"] in valgte_klubber
            ]
        else:
            kandidater = filt_liga

        st.caption(f"📊 Antal kampe i spil: **{len(kandidater)} kampe** (analyseres på tværs af alle {len(ap.MARKEDER)} spilmarkeder).")
    else:
        kandidater = []
        foerste = next(iter(alle), None)
        naeste = f" Næste kamp: **{foerste['hj']} vs {foerste['ud']}** ({foerste['start']})." if foerste else ""
        st.info(f"📭 Ingen turneringer har kampe inden for **{timer} timer**.{naeste}")

    # 5. Administrer favoritter (identisk med Mappe 1)
    with st.expander(f"⚙️ Administrer favoritter ({len(favs)} aktive)"):
        ny = st.text_input("➕ Ny favoritliga:", key="man_ny")
        if st.button("Gem favorit", key="man_add") and liga_favoritter.tilfoej_ny_favorit_liga(ny):
            st.cache_data.clear()
            st.rerun()
        fjern = st.selectbox("🗑️ Fjern liga:", favs, key="man_del_sel")
        if st.button("Fjern valgt liga", key="man_del_btn") and liga_favoritter.fjern_favorit_liga(fjern):
            st.cache_data.clear()
            st.rerun()

    st.divider()

    # 6. Scan og byg spilbare forslag på tværs af alle markeder
    if st.button("🚀 Find spilbare forslag (Alle spilmarkeder)", type="primary", use_container_width=True, key="btn_man_scan"):
        if not kandidater:
            st.warning("⚠️ Ingen kampe matcher dine valgte ligaer/klubnavne i tidsrammen.")
            return

        # Hent spilbare forslag på tværs af markeder FØR endelig kupon-kombination vælges
        spilbare_kandidater = _generer_spilbare_forslag(kandidater)
        valgte_kampe, _ = ap._vaelg_bedste_kombination(spilbare_kandidater, min_o, max_o, max_kampe)
        st.session_state["man_seneste_kupon"] = valgte_kampe

    # 7. Vis kupon med spilbare forslag og gem i Supabase (100 kr. standardindsats)
    kupon_kampe = st.session_state.get("man_seneste_kupon", [])
    if kupon_kampe:
        bedste_side, samlet_odds, _, _, samlet_pct, stjerner, flammer = ap._vurder_kupon(kupon_kampe)

        st.success(
            f"🎫 **Spilbart forslag klar ({len(kupon_kampe)} valg)** | Odds: **{samlet_odds}** ({bedste_side}) | "
            f"Vinderchance: **{samlet_pct}%** | {'⭐' * stjerner} | {'🔥' * flammer}"
        )

        endelig_valgte = []
        for i, k in enumerate(kupon_kampe):
            fok = f" ({k['valgt_hold']})" if k.get("valgt_hold") else ""
            kombi_txt = ", ".join(k.get("kombinationer", []))
            label_chk = f"**{k['hj']} vs {k['ud']}**{fok} – {kombi_txt} *(Liga: {k['liga']} | {k['start']})*"
            if st.checkbox(label_chk, value=True, key=f"man_k_chk_{i}_{k['hj']}"):
                endelig_valgte.append(k)

        if endelig_valgte:
            b_side, s_odds, _, _, s_pct, _, _ = ap._vurder_kupon(endelig_valgte)
            indsats = st.number_input("💰 Indsats (kr.):", min_value=1.0, value=100.0, step=10.0, key="man_indsats")

            if st.button("💾 Gem & spil kupon i Supabase", type="primary", key="btn_man_spil"):
                gem_data.gem_kupon_historik(
                    kampe=endelig_valgte,
                    samlet_odds=s_odds,
                    indsats=indsats,
                    bookmaker=b_side,
                    vinderchance_pct=s_pct,
                    ligaer=list({k["liga"] for k in endelig_valgte}),
                    kilde="Mappe 2 - Manuel Liga- & Klub-Scanner",
                )
                st.toast("✅ Kupon gemt i Supabase!")
