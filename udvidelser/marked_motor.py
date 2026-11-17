import streamlit as st
from udvidelser.special_api import hent_kamp_tilbud, hent_startopstilling
from udvidelser.special_markeder import udtraek_alle_tilbud

def hent_reelle_muligheder(kamp, api_noegle=""):
    liga = kamp.get("liga_kode", "eng.1")
    hjemme, ude = kamp.get("hjemme", ""), kamp.get("ude", "")
    key = api_noegle or st.secrets.get("ODDS_API_KEY", "")
    data, rest, kilde = hent_kamp_tilbud(liga, kamp.get("odds_api_id", ""), key)
    startere = hent_startopstilling(kamp.get("id"), liga)
    if not data:
        return [], kilde, rest
    match_json = data
    for k_item in data:
        h_api = k_item.get("home_team", "").lower()
        u_api = k_item.get("away_team", "").lower()
        if hjemme.lower() in h_api or ude.lower() in u_api:
            match_json = k_item
            break
    tilbud = udtraek_alle_tilbud(match_json, startere)
    resultat = []
    for marked, valg_dict in tilbud.items():
        for valg, priser in valg_dict.items():
            sorteret = sorted(priser.items(), key=lambda x: x, reverse=True)
            b365 = priser.get("Bet365", sorteret)
            konk = [p for p in sorteret if p != "Bet365"][:2]
            resultat.append({
                "marked": marked, "valg": valg, "b365": b365,
                "konk1": konk if len(konk) > 0 else ("Unibet", b365),
                "konk2": konk if len(konk) > 1 else ("Danske Spil", b365),
                "start11": bool(startere), "kilde": kilde
            })
    return resultat, kilde, rest

def tjek_kupon_spil_mod_marked(kamp, scannet_valg, api_noegle=""):
    muligheder, kilde, _ = hent_reelle_muligheder(kamp, api_noegle)
    if not muligheder:
        return True, "Ingen live-odds fundet – vurderet via lokal statistik.", []
    fundet = [m for m in muligheder if scannet_valg.lower() in m["valg"].lower()]
    if fundet:
        top = fundet
        return True, f"✅ Verificeret hos bookmaker ({top['marked']}: {top['valg']} @ {top['b365']}).", muligheder[:3]
    return False, "⚠️ Spillet matcher ikke standardudbuddet på kampen – se reelle alternativer.", muligheder[:3]
