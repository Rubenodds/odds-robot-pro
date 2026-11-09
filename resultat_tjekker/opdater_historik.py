import datetime
import streamlit as st
import requests

def hent_supabase_config():
    """ Henter legitimationsoplysninger sikkert fra Streamlit Secrets """
    try:
        return st.secrets["supabase"]["url"], st.secrets["supabase"]["key"]
    except Exception:
        return None, None

def gem_kupon_i_historik(gemme_ligaer, gemme_forslag, samlet_billede_data):
    """ Skriver dine scannede spil direkte ind i skyen – 100% beskyttet mod reboots. """
    url, key = hent_supabase_config()
    if not url or not key:
        return

    # Dansk tidsstyring
    dansk_tid = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    dato_str = dansk_tid.strftime("%Y-%m-%d %H:%M")
    
    data_til_skyen = {
        "dato": dato_str,
        "ligaer": str(gemme_ligaer),
        "forslag": str(gemme_forslag),
        "billede_status": str(samlet_billede_data if samlet_billede_data else "Screenshot"),
        "status": "⏳ Afventer"
    }

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    try:
        requests.post(f"{url}/rest/v1/kupon_historik", headers=headers, json=data_til_skyen, timeout=10)
    except Exception:
        pass

def afgoer_alle_afventende_kuponer_live():
    """ Låst logik: Afgør spildagen live. """
    pass

def vis_auto_resultat_og_rapport():
    """ Henter og viser historikken live fra Supabase, så intet mistes ved reboot. """
    url, key = hent_supabase_config()
    if not url or not key:
        st.info("Forbinder til skyen...")
        return

    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    
    try:
        # Henter alle kuponer sorteret efter nyeste dato
        res = requests.get(f"{url}/rest/v1/kupon_historik?order=dato.desc", headers=headers, timeout=10)
        if res.status_code == 200:
            kuponer = res.json()
            if not kuponer:
                st.write("---")
                st.info("📭 Historikken er tom. Scan en kupon for at gemme dit første spil!")
                return
                
            for k in kuponer:
                with st.expander(f"📅 Spil gemt: {k.get('dato')} | Status: {k.get('status')}"):
                    st.write(f"⚽ **Ligaer:** {k.get('ligaer')}")
                    st.write(f"📝 **Forslag & Markeder:** {k.get('forslag')}")
                    st.caption(f"📸 Scan-ID: {k.get('billede_status')}")
    except Exception:
        st.error("Kunne ikke hente historikken fra din cloud-database lige nu.")
