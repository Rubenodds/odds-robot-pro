import streamlit as st
from udvidelser.special_api import hent_kamp_tilbud, hent_startopstilling, oversaet_da

MARKED_NAVN = {
    "h2h": "Kampvinder (1X2)", "totals": "Over/Under Mål", "spreads": "Handicap",
    "btts": "Begge hold scorer", "draw_no_bet": "Uafgjort intet væddemål",
    "double_chance": "Dobbeltchance", "h2h_h1": "1. halvleg vinder",
    "totals_h1": "1. halvleg Over/Under Mål", "player_goal_scorer_anytime": "Målscorer i kampen",
    "player_shots_on_target": "Spillerskud på mål", "player_shots": "Spillerskud i alt",
    "player_assists": "Spiller-assist"
}

def udtraek_alle_tilbud(kamp_json, startere):
    tilbud = {}
    for bm in kamp_json.get("bookmakers", []):
        bm_navn = bm.get("title", "Bookmaker")
        for m in bm.get("markets", []):
            m_key = m.get("key", "")
            m_label = MARKED_NAVN.get(m_key, oversaet_da(m_key.replace("_", " ").title()))
            for o in m.get("outcomes", []):
                spiller = o.get("description", "")
                if "player_" in m_key and startere and spiller and spiller not in startere:
                    continue
                punkt = f" {o['point']}" if "point" in o else ""
                navn_da = oversaet_da(o.get("name", ""))
                valg = f"{spiller} {navn_da}{punkt}".strip()
                tilbud.setdefault(m_label, {}).setdefault(valg, {})[bm_navn] = o.get("price", 0)
    return tilbud

def vis_special_panel(kampe):
    st.subheader("🎯 Alle Kampens Bookmaker-tilbud (Dansk)")
    aktiv_key = st.text_input("Valgfri egen Odds-API nøgle", type="password").strip() or st.secrets.get("ODDS_API_KEY", "")
    if not kampe:
        st.info("Vælg eller scan kampe først for at hente bookmakernes tilbud.")
        return
    kamp_labels = [f"{k.get('hjemme')} - {k.get('ude')}" for k in kampe]
    idx = st.selectbox("Vælg kamp", range(len(kamp_labels)), format_func=lambda i: kamp_labels[i])
    kamp = kampe[idx]
    liga = kamp.get("liga_kode", "eng.1")
    data, rest, kilde = hent_kamp_tilbud(liga, kamp.get("odds_api_id", ""), aktiv_key)
    st.caption(f"Kilde: **{kilde}** | API-kreditter tilbage: **{rest if rest is not None else 'Gratis'}**")
    startere = hent_startopstilling(kamp.get("id"), liga)
    if not data:
        st.warning("Ingen live bookmaker-tilbud fundet endnu for denne liga.")
        return
    tilbud = udtraek_alle_tilbud(data, startere)
    alle_kategorier = ["🤖 Alle udbudte markeder (Top værdi)"] + sorted(tilbud.keys())
    kat = st.selectbox("Filtrer i kampens faktiske markeder", alle_kategorier)
    valgte_kat = list(tilbud.keys()) if kat.startswith("🤖") else [kat]
    for k_navn in valgte_kat:
        for valg, priser in list(tilbud[k_navn].items())[:5]:
            sorteret = sorted(priser.items(), key=lambda x: x[1], reverse=True)
            b365_odds = priser.get("Bet365", sorteret[0][1])
            st.markdown(f"**[{k_navn}] {valg}** ({round(100 / b365_odds)}%)")
            st.caption(f"🥇 Bet365: {b365_odds} | 🥈 {sorteret[0][0]}: {sorteret[0][1]}")

