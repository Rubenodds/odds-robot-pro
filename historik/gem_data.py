import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

def _get_headers():
    url = st.secrets["SUPABASE_URL"].rstrip("/")
    key = st.secrets["SUPABASE_KEY"]
    return url, {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

def _til_float(vaerdi, standard=0.0):
    try:
        return standard if (vaerdi is None or vaerdi == "") else float(str(vaerdi).replace(",", "."))
    except (ValueError, TypeError):
        return standard

def gem_kupon_i_historik(ligaer, forslag, b365_odds, unibet_odds, oddset_odds, bedste_side, styrke, indsats=100.0, kilde="Robot"):
    try:
        url, headers = _get_headers()
        final_indsats = max(1.0, _til_float(indsats, 100.0))
        dansk_tid = datetime.now(ZoneInfo("Europe/Copenhagen")).isoformat()
        strategi_txt = ", ".join(ligaer) if isinstance(ligaer, list) else str(ligaer)
        if kilde == "Mine Egne" and "[EGEN]" not in strategi_txt:
            strategi_txt = f"[EGEN] {strategi_txt}"
        payload = {
            "kampe": ", ".join(forslag) if isinstance(forslag, list) else str(forslag),
            "strategi": f"[AFVENTER] {strategi_txt}".strip(),
            "odds": _til_float(b365_odds, 1.0),
            "indsats": final_indsats,
            "vaerdi_manuel": _til_float(unibet_odds, 0.0),
            "bookmaker_type": str(bedste_side),
            "rating_stjerner": int(_til_float(styrke, 5)),
            "timestamp": dansk_tid,
        }
        res = requests.post(f"{url}/rest/v1/historik", headers=headers, json=payload, timeout=10)
        if res.status_code not in (200, 201):
            st.error(f"Supabase fejl ({res.status_code}): {res.text[:160]}")
            return False
        return True
    except Exception as e:
        st.error(f"Supabase forbindelsesfejl: {e}")
        return False

def opdater_kupon_status(kupon_id, ny_status):
    try:
        url, headers = _get_headers()
        r = requests.get(f"{url}/rest/v1/historik?id=eq.{kupon_id}&select=strategi", headers=headers, timeout=8)
        if r.status_code != 200 or not r.json():
            return False
        gl = str(r.json()[0].get("strategi") or "")
        for tag in ("[VUNDET]", "[TABT]", "[AFVENTER]"):
            gl = gl.replace(tag, "").strip()
        ny_strat = f"[{ny_status.upper()}] {gl}".strip()
        res = requests.patch(f"{url}/rest/v1/historik?id=eq.{kupon_id}", headers=headers, json={"strategi": ny_strat}, timeout=8)
        return res.status_code in (200, 204)
    except Exception:
        return False

def hent_alle_kuponer():
    try:
        url, headers = _get_headers()
        res = requests.get(f"{url}/rest/v1/historik?select=*&order=id.desc", headers=headers, timeout=10)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []
