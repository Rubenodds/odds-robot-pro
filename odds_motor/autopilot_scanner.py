import requests
import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from odds_motor import liga_favoritter, byg_kupon
from historik import gem_data

LIGA_FEED_ENDPOINTS = {
    "Danmark - Superliga": "https://espn.com",
    "England - Premier League": "https://espn.com",
    "England - Championship": "https://espn.com",
    "England - League One": "https://espn.com",
    "Spanien - La Liga": "https://espn.com",
    "Italien - Serie A": "https://espn.com",
    "Italien - Serie B": "https://espn.com",
    "Tyskland - Bundesliga": "https://espn.com",
    "Tyskland - 2. Bundesliga": "https://espn.com",
    "Frankrig - Ligue 1": "https://espn.com",
    "Frankrig - Ligue 2": "https://espn.com",
    "Norge - Eliteserien": "https://espn.com",
    "Sverige - Allsvenskan": "https://espn.com",
    "Holland - Eredivisie": "https://espn.com",
    "Portugal - Liga Portugal": "https://espn.com",
    "Japan - J1 League": "https://espn.com",
    "UEFA - Champions League": "https://espn.com",
    "UEFA - Europa League": "https://espn.com",
}

SPECIAL_MARKEDER = [
    "Standard (Mål / Kampvinder)",
    "Hjørnespark (Over/Under & Flest)",
    "Spillerskud & Skud på mål",
    "Tacklinger & Målmandsredninger",
    "Kort-sandsynlighed (Gule/Røde)",
    "Målscorer (Anytime/Første)",
    "Offsides",
]


@st.cache_data(ttl=300, show_spinner=False)
def _hent_aegte_kampe_fra_net(aktive_ligaer_tuple):
    dk_tz = ZoneInfo("Europe/Copenhagen")
    nu_dk = datetime.now(dk_tz)
    dato_streng = f"{nu_dk.strftime('%Y%m%d')}-{(nu_dk + timedelta(days=3)).strftime('%Y%m%d')}"

    alle_kampe = []
    for liga_navn in aktive_ligaer_tuple:
        url = LIGA_FEED_ENDPOINTS.get(liga_navn)
        if not url:
            continue
        try:
            res = requests.get(f"{url}?dates={dato_streng}", timeout=6)
            if res.status_code != 200:
                continue
            data = res.json()
            for event in data.get("events", []):
                status_type = event.get("status", {}).get("type", {}).get("state", "")
                if status_type != "pre":
                    continue

                raw_date = event.get("date")
                if not raw_date:
                    continue

                utc_dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                dk_dt = utc_dt.astimezone(dk_tz)

                diff_timer = (dk_dt - nu_dk).total_seconds() / 3600.0
                if diff_timer <= 0:
                    continue

                competitions = event.get("competitions", [])
                competitors = competitions[0].get("competitors", []) if competitions else []
                hj = next((c["team"]["displayName"] for c in competitors if c.get("homeAway") == "home"), None)
                ud = next((c["team"]["displayName"] for c in competitors if c.get("homeAway") == "away"), None)

                if hj and ud:
                    alle_kampe.append({
                        "liga": liga_navn,
                        "hj": hj,
                        "ud": ud,
                        "dk_dt": dk_dt,
                        "start": dk_dt.strftime("%d-%m-%Y kl. %H:%M"),
                        "timer_frem": round(diff_timer, 2),
                    })
        except Exception as e:
            print(f"[Live-Feed Advarsel for {liga_navn}]: {e}")

    alle_kampe.sort(key=lambda x: x["dk_dt"])
    return alle_kampe


def vis_autopilot_scanner():
    st.subheader("🌐 1. Autopilot Scanner (Ægte Dato- & Tidszone-Scanning)")

    alle_favoritter = liga_favoritter.hent_favorit_ligaer()
    valgte_ligaer = st.multiselect(
        f"🏆 Aktive Favoritligaer ({len(alle_favoritter)} tilgængelige):",
        options=alle_favoritter,
        default=alle_favoritter,
        key="auto_valgte_ligaer",
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

    col_t, col_o = st.columns(2)
    with col_t:
        timer = st.slider("⏱️ Tidsramme frem (timer fra nu):", 1, 72, 12, key="auto_timer")
    with col_o:
        min_o, max_o = st.slider("🎯 Ønsket samlet odds-lag:", 2.0, 200.0, (20.0, 50.0), key="auto_odds_interval")

    valgte_markeder = st.multiselect(
        "📊 Vælg tilladte specialmarkeder:",
        options=SPECIAL_MARKEDER,
        default=["Standard (Mål / Kampvinder)", "Hjørnespark (Over/Under & Flest)", "Spillerskud & Skud på mål"],
        key="auto_markeder",
    )

    if st.button("🔍 SCAN MARKEDET NU (Tjek ægte kampdatoer & Value-Boost)", type="primary", key="btn_start_auto_scan"):
        if not valgte_ligaer or not valgte_markeder:
            st.warning("Vælg mindst én liga og ét marked, før du trykker SCAN.")
        else:
            with st.spinner("Henter ægte kampprogram og tjekker datoer i dansk tid..."):
                alle_kommende = _hent_aegte_kampe_fra_net(tuple(valgte_ligaer))
                kandidat_kampe = [k for k in alle_kommende if 0 < k["timer_frem"] <= timer]

            if not kandidat_kampe:
                st.session_state["auto_scannet_kupon"] = None
                st.session_state["auto_scannede_kampe_liste"] = []
                if alle_kommende:
                    naeste = alle_kommende[0]
                    st.warning(
                        f"Ingen kampe i de valgte ligaer starter inden for de næste **{timer} timer**. "
                        f"Næste rigtige kamp er **{naeste['hj']} vs {naeste['ud']}** ({naeste['liga']}) "
                        f"d. **{naeste['start']}** (om ca. {naeste['timer_frem']:.1f} timer)."
                    )
                else:
                    st.warning(
                        "Ingen kommende kampe fundet i de valgte ligaer de næste 72 timer (f.eks. pga. landsholdspause). "
                        "Nul fiktive kampe oprettet."
                    )
            else:
                antal_kampe = min(len(kandidat_kampe), 5 if max_o >= 25 else 3)
                udvalgte = kandidat_kampe[:antal_kampe]
                maal_odds = round((min_o + max_o) / 2.0, 2)

                kupon = byg_kupon.byg_kombineret_kupon(udvalgte, valgte_markeder, maal_odds)
                st.session_state["auto_scannet_kupon"] = kupon
                st.session_state["auto_scannede_kampe_liste"] = kandidat_kampe
                st.session_state["auto_scannet_timer"] = timer

    if st.session_state.get("auto_scannet_kupon"):
        kupon = st.session_state["auto_scannet_kupon"]
        alle_fundne = st.session_state.get("auto_scannede_kampe_liste", [])
        brugt_timer = st.session_state.get("auto_scannet_timer", timer)

        st.success(f"✓ Scanning gennemført! Fandt {len(alle_fundne)} ægte kampe inden for de næste {brugt_timer} timer.")

        with st.expander(f"📋 Se alle {len(alle_fundne)} scannede kampe (Ægte datoer i dansk tid)"):
            for k in alle_fundne:
                st.write(f"• `[{k['start']}]` **{k['hj']} vs {k['ud']}** ({k['liga']})")

        st.markdown("### 🎫 Anbefalet Autopilot-Kupon (Afventer din SPILLET-godkendelse)")
        for idx, kamp in enumerate(kupon["kampe"], start=1):
            st.markdown(
                f"**{idx}. {kamp['hj']} vs {kamp['ud']}** ({kamp['liga']} | **{kamp['start']}**)  \n"
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
            key="auto_indsats",
        )

        if st.button("🚀 SPILLET (Godkend & gem Autopilot-kupon i Supabase)", type="primary", key="btn_spillet_auto_ny"):
            kampe_tekst = [f"{k['hj']} - {k['ud']} [{k['start']}] ({', '.join(k['kombinationer'])})" for k in kupon["kampe"]]
            ligaer_tekst = list({k["liga"] for k in kupon["kampe"]})
            gemt = gem_data.gem_kupon_i_historik(
