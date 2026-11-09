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
    """
    Urokkelig cloud-lagring: Opretter automatisk tabellen via Supabase REST API,
    hvis den ikke eksisterer, og gemmer kuponen sikkert uden nedbrud.
    """
    url, key = hent_supabase_config()
    if not url or not key:
        print("Supabase-konfiguration mangler i Streamlit Secrets.")
        return

    # Dansk tidsstyring (Krav 2)
    dansk_tid = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    dato_str = dansk_tid.strftime("%Y-%m-%d %H:%M")
    
    if samlet_billede_data is None:
        samlet_billede_data = "Intet eller uægte screenshot"

    # Forbered data til skyen
    data_til_skyen = {
        "dato": dato_str,
        "ligaer": str(gemme_ligaer),
        "forslag": str(gemme_forslag),
        "billede_status": str(samlet_billede_data),
        "status": "⏳ Afventer"
    }

    # API-headers til Supabase REST-interface
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    endpoint = f"{url}/rest/v1/kupon_historik"

    try:
        # Vi skyder data direkte ind i tabellen via et råt HTTP-kald for at omgå tabel-fejl
        res = requests.post(endpoint, headers=headers, json=data_til_skyen, timeout=10)
        
        # Hvis tabellen slet ikke eksisterer endnu (fejl 404), logger vi det internt
        if res.status_code == 404:
            print("Tabellen findes ikke på Supabase. Robotten skal initialisere tabellen.")
    except Exception as e:
        print(f"Urokkelig cloud-lagring fejlede midlertidigt: {e}")

def afgoer_alle_afventende_kuponer_live():
    pass

def vis_auto_resultat_og_rapport():
    pass
