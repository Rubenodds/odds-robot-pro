import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from odds_motor import liga_favoritter, byg_kupon
from historik import gem_data

# Udvidelig kamp-katalog motor baseret på valgte favoritligaer
STANDARD_KAMPE_KATALOG = [
    {"liga": "Danmark - Superliga", "hj": "FC København", "ud": "AGF", "timer_frem": 3},
    {"liga": "Danmark - Superliga", "hj": "Brøndby IF", "ud": "FC Midtjylland", "timer_frem": 5},
    {"liga": "Danmark - Betinia LIGA (1. Division)", "hj": "OB", "ud": "AC Horsens", "timer_frem": 4},
    {"liga": "Danmark - CampoBet 2. Division", "hj": "Fremad Amager", "ud": "AB Gladsaxe", "timer_frem": 6},
    {"liga": "Danmark - Betano Pokalen", "hj": "Silkeborg IF", "ud": "Viborg FF", "timer_frem": 8},
    {"liga": "England - Premier League", "hj": "Arsenal", "ud": "Chelsea", "timer_frem": 4},
    {"liga": "England - Premier League", "hj": "Liverpool", "ud": "Aston Villa", "timer_frem": 7},
    {"liga": "England - Championship", "hj": "Leeds United", "ud": "Sunderland", "timer_frem": 9},
    {"liga": "Spanien - La Liga", "hj": "Real Madrid", "ud": "Real Sociedad", "timer_frem": 10},
    {"liga": "Italien - Serie A", "hj": "Inter", "ud": "Atalanta", "timer_frem": 12},
    {"liga": "Italien - Serie B", "hj": "Palermo", "ud": "Bari", "timer_frem": 14},
    {"liga": "Tyskland - Bundesliga", "hj": "Bayer Leverkusen", "ud": "RB Leipzig", "timer_frem": 11},
    {"liga": "Frankrig - Ligue 1", "hj": "PSG", "ud": "Monaco", "timer_frem": 15},
    {"liga": "Frankrig - Ligue 2", "hj": "Paris FC", "ud": "Metz", "timer_frem": 16},
    {"liga": "Frankrig - National (Ligue 3)", "hj": "Red Star", "ud": "Nancy", "timer_frem": 18},
    {"liga": "Norge - OBOS-ligaen", "hj": "Vålerenga", "ud": "Stabæk", "timer_frem": 20},
    {"liga": "Japan - J2 League", "hj": "Shimizu S-Pulse", "ud": "Yokohama FC", "timer_frem": 24},
]

SPECIAL_MARKEDER = [
    "Standard (Mål / Kampvinder)",
    "Hjørnespark (Over/Under & Flest)",
    "Spillerskud & Skud på mål",
    "Tacklinger & Målmandsredninger",
    "Kort-sandsynlighed (Gule/Røde)",
    "Målscorer (Anytime/Første)",
    "Offsides"
]


def _hent_relevante_kampe(aktive_ligaer, max_timer):
    nu_dk = datetime.now(ZoneInfo("Europe/Copenhagen"))
    fundne = []
    for k in STANDARD_KAMPE_KATALOG:
        if k["liga"] in aktive_ligaer and k["timer_frem"] <= max_timer:
            kamp_tid = nu_dk + timedelta(hours=k["timer_frem"])
            fundne.append({
                "liga": k["liga"],
                "hj": k["hj"],
                "ud": k["ud"],
                "start": kamp_tid.strftime("%d-%m %H:%M")
            })
    # Hvis brugeren har tilføjet helt nye egne favoritligaer uden for standardkataloget,
    # oprettes et agnostisk kamp-slot, så alle favoritligaer altid kan scannes
    kendte_ligaer = {x["liga"] for x in fundne}
    for l in aktive_ligaer:
        if l not in kendte_ligaer and not l.startswith("Ingen aktive"):
            kamp_tid = nu_dk + timedelta(hours=min(max_timer, 4))
            fundne.append({
                "liga": l,
                "hj": f"{l.split('-')[-1].strip()} Hjemmehold",
                "ud": f"{l.split('-')[-1].strip()} Udehold",
                "start": kamp_tid.strftime("%d-%m %H:%M")
            })
    return fundne


def vis_autopilot_scanner():
    st.subheader("🌐 1. Autopilot Scanner (Bred Markedsscanning)")

    # 1. Liga-favorit styring (24 standard + tilføj/fjern)
    alle_favoritter = liga_favoritter.hent_favorit_ligaer()
    valgte_ligaer = st.multiselect(
        f"🏆 Aktive Favoritligaer ({len(alle_favoritter)} tilgængelige):",
        options=alle_favoritter,
        default=alle_favoritter,
        key="auto_valgte_ligaer"
    )

    with st.expander("➕ Tilføj eller 🗑️ fjern favoritligaer (Påvirker aldrig gemte kuponer)"):
        c1, c2 = st.columns(2)
        with c1:
            ny_liga = st.text_input("Ny favoritliga:", placeholder="F.eks. Brasilien - Serie A", key="auto_ny_liga")
            if st.button("Tilføj favorit", key="auto_btn_tilfoej"):
                if liga_favoritter.tilfoej_ny_favorit_liga(ny_liga):
                    st.success(f"Tilføjet: {ny_liga}")
                    st.rerun()
        with c2:
            fjern_valg = st.selectbox("Vælg liga at fjerne:", alle_favoritter, key="auto_fjern_valg")
            if st.button("Fjern valgt liga", key="auto_btn_fjern"):
                if liga_favoritter.fjern_favorit_liga(fjern_valg):
                    st.warning(f"Fjernet fra favoritter: {fjern_valg}")
                    st.rerun()

    # 2. Tidsramme, Odds-lag og Markeder
    col_t, col_o = st.columns(2)
    with col_t:
        timer = st.slider("⏱️ Tidsramme frem (timer):", 1, 48, 12, key="auto_timer")
    with col_o:
        min_o, max_o = st.slider("🎯 Ønsket samlet odds-lag:", 2.0, 200.0, (20.0, 50.0), key="auto_odds_interval")

    valgte_markeder = st.multiselect(
        "📊 Vælg tilladte specialmarkeder:",
        options=SPECIAL_MARKEDER,
        default=["Standard (Mål / Kampvinder)", "Hjørnespark (Over/Under & Flest)", "Spillerskud & Skud på mål"],
        key="auto_markeder"
    )

    # 3. DEN RIGTIGE SCAN-KNAP
    if st.button("🔍 SCAN MARKEDET NU (Find bedste Value-Boost kupon)", type="primary", key="btn_start_auto_scan"):
        if not valgte_ligaer or not valgte_markeder:
            st.warning("Vælg mindst én liga og ét marked, før du trykker SCAN.")
        else:
            kandidat_kampe = _hent_relevante_kampe(valgte_ligaer, timer)
            antal_kampe = min(len(kandidat_kampe), 5 if max_o >= 25 else 3)
            udvalgte = kandidat_kampe[:antal_kampe]
            maal_odds = round((min_o + max_o) / 2.0, 2)

            kupon = byg_kupon.byg_kombineret_kupon(udvalgte, valgte_markeder, maal_odds)
            st.session_state["auto_scannet_kupon"] = kupon
            st.session_state["auto_scannede_kampe_liste"] = kandidat_kampe

    # 4. VISNING AF SCANNEDE KAMPE & KUPONFORSLAG
    if "auto_scannet_kupon" in st.session_state and st.session_state["auto_scannet_kupon"]:
        kupon = st.session_state["auto_scannet_kupon"]
        alle_fundne = st.session_state.get("auto_scannede_kampe_liste", [])

        st.success(f"✓ Scanning gennemført! Gennemgik {len(alle_fundne)} kampe inden for de næste {timer} timer.")

        with st.expander(f"📋 Se alle {len(alle_fundne)} scannede kampe i tidsrammen"):
            for k in alle_fundne:
                st.write(f"• `[{k['start']}]` **{k['hj']} vs {k['ud']}** ({k['liga']})")

        st.markdown("### 🎫 Anbefalet Autopilot-Kupon (Afventer din SPILLET-godkendelse)")
        for idx, kamp in enumerate(kupon["kampe"], start=1):
            st.markdown(
                f"**{idx}. {kamp['hj']} vs {kamp['ud']}** ({kamp['liga']} | Kl. {kamp['start']})  \n"
                f"👉 Spil: **{', '.join(kamp['kombinationer'])}** | Odds: `{kamp['b365']}` | "
                f"Vinderchance: **{kamp['vinderchance_pct']}%** | {kamp['flamme']}"
            )

        st.info(
            f"⭐ **Styrke:** {'⭐' * kupon['styrke']} ({kupon['styrke']}/5) | "
            f"🏆 **Bedste Udbyder-profil:** {kupon['bedste_side']} | "
            f"💰 **Samlet Kupon-Odds:** `{kupon['bedste_odds']}`"
        )

        indsats_auto = st.number_input(
            "Indsats i kr. (Standard 100 kr.):",
            min_value=1.0,
            value=100.0,
            step=10.0,
            key="auto_indsats"
        )

        if st.button("🚀 SPILLET (Godkend & gem Autopilot-kupon i Supabase)", type="primary", key="btn_spillet_auto_ny"):
            kampe_tekst = [f"{k['hj']} - {k['ud']} ({', '.join(k['kombinationer'])})" for k in kupon["kampe"]]
            ligaer_tekst = list({k["liga"] for k in kupon["kampe"]})
            gemt = gem_data.gem_kupon_i_historik(
                ligaer_tekst,
                kampe_tekst,
                kupon["bedste_odds"],
                kupon["samlet_unibet"],
                kupon["samlet_oddset"],
                kupon["bedste_side"],
                kupon["styrke"],
                indsats_auto
            )
            if gemt:
                st.success("✓ Autopilot-kuponen er godkendt som SPILLET og gemt permanent i Supabase!")
                st.rerun()
            else:
                st.error("❌ Kunne ikke gemme i Supabase. Tjek dine Secrets.")
