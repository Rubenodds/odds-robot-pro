import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

def _get_headers():
    url = st.secrets["SUPABASE_URL"].rstrip("/")
    key = st.secrets["SUPABASE_KEY"]
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    return url, headers

def _til_float(vaerdi, standard=0.0):
    try:
        if vaerdi is None or vaerdi == "":
            return standard
        return float(str(vaerdi).replace(",", "."))
    except (ValueError, TypeError):
        return standard

def gem_kupon_i_historik(ligaer, forslag, b365_odds, unibet_odds, oddset_odds, bedste_side, styrke, indsats=100.0):
    try:
        url, headers = _get_headers()
        final_indsats = _til_float(indsats, 100.0)
        if final_indsats <= 0:
            final_indsats = 100.0

        dansk_tid = datetime.now(ZoneInfo("Europe/Copenhagen")).isoformat()

        payload = {
            "kampe": ", ".join(forslag) if isinstance(forslag, list) else str(forslag),
            "strategi": ", ".join(ligaer) if isinstance(ligaer, list) else str(ligaer),
            "odds": _til_float(b365_odds, 1.0),
            "indsats": final_indsats,
            "vaerdi_manuel": _til_float(unibet_odds, 0.0),
            "bookmaker_type": str(bedste_side),
            "rating_stjerner": int(_til_float(styrke, 5)),
            "timestamp": dansk_tid
        }
        res = requests.post(f"{url}/rest/v1/historik", headers=headers, json=payload, timeout=10)
        return res.status_code in (200, 201)
    except Exception as e:
        print(f"[Supabase Gem-Fejl]: {e}")
        return False

def hent_alle_kuponer():
    try:
        url, headers = _get_headers()
        res = requests.get(f"{url}/rest/v1/historik?select=*&order=id.desc", headers=headers, timeout=10)
        return res.json() if res.status_code == 200 else []
    except Exception as e:
        print(f"[Supabase Hent-Fejl]: {e}")
        return []
