import streamlit as st
import requests
from datetime import datetime

def _get_headers():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    return url, headers

def gem_kupon_i_historik(ligaer, forslag, b365_odds, unibet_odds, oddset_odds, bedste_side, styrke, indsats=100.0):
    try:
        url, headers = _get_headers()
        final_indsats = float(indsats) if indsats else 100.0
        payload = {
            "kampe": ", ".join(forslag) if isinstance(forslag, list) else str(forslag),
            "strategi": ", ".join(ligaer) if isinstance(ligaer, list) else str(ligaer),
            "odds": float(b365_odds),
            "indsats": final_indsats,
            "vaerdi_manuel": float(unibet_odds) if unibet_odds else 0.0,
            "bookmaker_type": str(bedste_side),
            "rating_stjerner": int(styrke) if styrke else 5,
            "timestamp": str(datetime.now())
        }
        res = requests.post(f"{url}/rest/v1/historik", headers=headers, json=payload)
        return res.status_code in
    except Exception:
        return False

def hent_alle_kuponer():
    try:
        url, headers = _get_headers()
        res = requests.get(f"{url}/rest/v1/historik?select=*&order=id.desc", headers=headers)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []
