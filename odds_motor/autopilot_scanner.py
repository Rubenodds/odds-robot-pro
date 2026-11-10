import requests
import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from odds_motor import liga_favoritter, byg_kupon, kamp_intelligens
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


def _udtraek_bedste_markedsodds(comp):
    try:
        odds_liste = comp.get("odds", [])
        if odds_liste:
            hjemme_ml = odds_liste.get("homeTeamOdds", {}).get("moneyLine")
            ude_ml = odds_liste.get("awayTeamOdds", {}).get("moneyLine")
            kandidater = []
            for ml in (hjemme_ml, ude_ml):
                if isinstance(ml, (int, float)) and ml != 0:
                    dec = (100.0 / abs(ml) + 1.0) if ml < 0 else (ml / 100.0 + 1.0)
                    if dec > 1.01:
                        kandidater.append(round(dec, 2))
            if kandidater:
                return min(kandidater)
    except Exception:
        pass
    return 1.85


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
            for event in res.json().get("events", []):
                if event.get("status", {}).get("type", {}).get("state") != "pre":
                    continue
                raw_date = event.get("date")
                if not raw_date:
                    continue
                dk_dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).astimezone(dk_tz)
                diff_timer = (dk_dt - nu_dk).total_seconds() / 3600.0
                if diff_timer <= 0:
                    continue

                comp = event.get("competitions", [{}])
                competitors = comp.get("competitors", [])
                hj = next((c["team"]["displayName"] for c in competitors if c.get("homeAway") == "home"), None)
                ud = next((c["team"]["displayName"] for c in competitors if c.get("homeAway") == "away"), None)
                if hj and ud:
                    laveste_odds = _udtraek_bedste_markedsodds(comp)
                    kontekst = kamp_intelligens.analyser_kamp_kontekst(comp, hj, ud)
                    basal_pct = byg_kupon.beregn_sandsynlighed_fra_odds(laveste_odds)
                    justeret_pct = round(max(35.0, min(95.0, basal_pct + kontekst["justering_pct"])), 1)
                    alle_kampe.append({
                        "liga": liga_navn,
                        "hj": hj,
                        "ud": ud,
                        "dk_dt": dk_dt,
                        "start": dk_dt.strftime("%d-%m-%Y kl. %H:%M"),
                        "timer_frem": round(diff_timer, 2),
                        "markedsodds": laveste_odds,
                        "sandsynlighed": justeret_pct,
                        "kontekst": kontekst,
                    })
        except Exception as e:
            print(f"[Live-Feed Advarsel for {liga_navn}]: {e}")

    alle_kampe.sort(key=lambda x: x["dk_dt"])
    return alle_kampe


def vis_autopilot_scanner():
    st.subheader("🌐 1. Autopilot Scanner (Form, H2H, Dommer & Vejr-Intelligens)")

    alle_favoritter = liga_favoritter.hent_favorit_ligaer()

    col_t, col_o = st.columns(2)
    with col_t:
        timer = st.slider("⏱️ Tidsramme frem (timer fra nu):", 1, 72, 12, key="auto_timer")
    with col_o:
        min_o, max_o = st.slider("🎯 Ønsket samlet odds-lag:", 2.0, 200.0, (20.0, 50.0), key="auto_odds_interval")

    alle_kommende = _hent_aegte_kampe_fra_net(tuple(alle_favoritter))
    kampe_i_tidsramme = [k for k in alle_kommende if 0 < k["timer_frem"] <= timer]
    ligaer_med_kampe = sorted(list({k["liga"] for k in kampe_i_tidsramme}))

    if ligaer_med_kampe:
        valgte_ligaer = st.multiselect(
            f"🏆 Favoritligaer med kampe inden for {timer} timer ({len(ligaer_med_kampe)} aktive):",
            options=ligaer_med_kampe,
            default=ligaer_med_kampe,
            key="auto_valgte_ligaer",
        )
    else:
        valgte_ligaer = []
        if alle_kommende:
            naeste = alle_kommende
            st.info(
                f"📭 Ingen af dine {len(alle_favoritter)} favoritligaer har kampe inden for de næste **{timer} timer**. "
                f"Næste kamp er **{naeste['hj']} vs {naeste['ud']}** ({naeste['liga']}) d. **{naeste['start']}**."
            )
        else:
            st.info(f"📭 Ingen af dine {len(alle_favoritter)} favoritligaer har kampe de næste 72 timer.")

    with st.expander(f"⚙️ Administrer dine {len(alle_favoritter)} faste favoritligaer (Tilføj / Fjern)"):
        c1, c2 = st.columns(2)
        with c1:
            ny_liga = st.text_input("➕ Tilføj ny favoritliga:", placeholder="F.eks. Brasilien - Serie A", key="auto_ny_liga")
            if st.button("Gem favorit", key="auto_btn_tilfoej"):
                if liga_favoritter.tilfoej_ny_favorit_liga(ny_liga):
                    st.success(f"Tilføjet: {ny_liga}")
                    st.rerun()
        with c2:
            fjern_valg = st.selectbox("🗑️ Fjern liga permanent fra favoritter:", alle_favoritter, key="auto_fjern_valg")
            if st.button("Fjern liga", key="auto_btn_fjern"):
                if liga_favoritter.fjern_favorit_liga(fjern_valg):
                    st.warning(f"Fjernet: {fjern_valg}")
                    st.rerun()

    valgte_markeder = st.multiselect(
        "📊 Vælg tilladte specialmarkeder:",
        options=SPECIAL_MARKEDER,
        default=["Standard (Mål / Kampvinder)", "Hjørnespark (Over/Under & Flest)", "Spillerskud & Skud på mål"],
        key="auto_markeder",
    )

    if st.button("🔍 SCAN MARKEDET NU (Inkl. Form, H2H, Dommer & Vejr)", type="primary", key="btn_start_auto_scan"):
        if not valgte_ligaer or not valgte_markeder:
            st.warning("Der er ingen valgte ligaer med kampe i denne tidsramme (eller intet marked valgt).")
        else:
            kandidat_kampe = sorted(
                [k for k in kampe_i_tidsramme if k["liga"] in valgte_ligaer],
                key=lambda x: x["sandsynlighed"],
                reverse=True,
            )
            antal_kampe = min(len(kandidat_kampe), 5 if max_o >= 25 else 3)
            udvalgte = kandidat_kampe[:antal_kampe]
            maal_odds = round((min_o + max_o) / 2.0, 2)
            kupon = byg_kupon.byg_kombineret_kupon(udvalgte, valgte_markeder, maal_odds)
            for idx, k_obj in enumerate(kupon["kampe"]):
                k_obj["kontekst"] = udvalgte[idx].get("kontekst", {})
            st.session_state["auto_scannet_kupon"] = kupon
            st.session_state["auto_scannede_kampe_liste"] = kandidat_kampe
            st.session_state["auto_scannet_timer"] = timer

    if st.session_state.get("auto_scannet_kupon"):
        kupon = st.session_state["auto_scannet_kupon"]
        alle_fundne = st.session_state.get("auto_scannede_kampe_liste", [])
        brugt_timer = st.session_state.get("auto_scannet_timer", timer)

        st.success(f"✓ Scanning gennemført! Udvalgte de mest sandsynlige kampe ud af {len(alle_fundne)} aktive kampe ({brugt_timer}T).")

        st.markdown("### 🎫 Anbefalet Autopilot-Kupon (Afventer din SPILLET-godkendelse)")
        for idx, kamp in enumerate(kupon["kampe"], start=1):
            ctx = kamp.get("kontekst", {})
            vejr = ctx.get("vejr")
            vejr_txt = f"{vejr['temp']}°C, {vejr['vind']} m/s ({vejr['effekt']})" if vejr else "Vejrdata afventer"
            st.markdown(
