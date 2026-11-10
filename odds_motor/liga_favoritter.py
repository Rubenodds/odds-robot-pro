import streamlit as st
import requests

STANDARD_24_LIGAER = [
    "Danmark - Superliga", "Danmark - Betinia LIGA (1. Division)",
    "Danmark - CampoBet 2. Division", "Danmark - Betano Pokalen",
    "England - Premier League", "England - Championship",
    "England - League One", "England - FA Cup",
    "Spanien - La Liga", "Spanien - Copa del Rey",
    "Italien - Serie A", "Italien - Serie B", "Italien - Coppa Italia",
    "Tyskland - Bundesliga", "Tyskland - 2. Bundesliga", "Tyskland - DFB Pokal",
    "Frankrig - Ligue 1", "Frankrig - Ligue 2", "Frankrig - National (Ligue 3)",
    "Norge - Eliteserien", "Norge - OBOS-ligaen", "Sverige - Allsvenskan",
    "Holland - Eredivisie", "Portugal - Liga Portugal",
    "Japan - J1 League", "Japan - J2 League",
    "UEFA - Champions League", "UEFA - Europa League", "Landskampe - FIFA / UEFA",
]

# Hjælper til at rette stavefejl som "copa del ray" -> "Spanien - Copa del Rey"
ALIAS_OPSLAG = {
    "copa del ray": "Spanien - Copa del Rey",
    "copa del rey": "Spanien - Copa del Rey",
    "fa cup": "England - FA Cup",
    "coppa italia": "Italien - Coppa Italia",
    "dfb pokal": "Tyskland - DFB Pokal",
    "superliga": "Danmark - Superliga",
    "premier league": "England - Premier League",
    "champions league": "UEFA - Champions League",
    "europa league": "UEFA - Europa League",
    "landskampe": "Landskampe - FIFA / UEFA",
}

def normaliser_liga_navn(tekst):
    ren = tekst.strip()
    lav = ren.lower()
    if lav in ALIAS_OPSLAG:
        return ALIAS_OPSLAG[lav]
    for std in STANDARD_24_LIGAER:
        if lav in std.lower():
            return std
    return ren

def _send_favorit_event(handling, liga_navn):
    try:
        url = st.secrets["SUPABASE_URL"].rstrip("/")
        key = st.secrets["SUPABASE_KEY"]
        headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "kampe": f"Favorit {handling}: {liga_navn}",
            "strategi": f"{handling}:{liga_navn}",
            "odds": 1.0, "indsats": 0.0, "vaerdi_manuel": 0.0,
            "bookmaker_type": "System-Favorit", "rating_stjerner": 5,
        }
        requests.post(f"{url}/rest/v1/historik", headers=headers, json=payload, timeout=5)
    except Exception:
        pass

def hent_favorit_ligaer():
    if "favorit_synkroniseret" not in st.session_state:
        st.session_state["ekstra_ligaer"] = []
        st.session_state["fjernede_ligaer"] = []
        try:
            url = st.secrets["SUPABASE_URL"].rstrip("/")
            key = st.secrets["SUPABASE_KEY"]
            headers = {"apikey": key, "Authorization": f"Bearer {key}"}
            res = requests.get(f"{url}/rest/v1/historik?select=strategi&bookmaker_type=eq.System-Favorit&order=id.asc&limit=500", headers=headers, timeout=5)
            if res.status_code == 200:
                for row in res.json():
                    strat = str(row.get("strategi", ""))
                    if strat.startswith("TILFOEJ_LIGA:"):
                        navn = normaliser_liga_navn(strat.replace("TILFOEJ_LIGA:", ""))
                        if navn in st.session_state["fjernede_ligaer"]:
                            st.session_state["fjernede_ligaer"].remove(navn)
                        if navn not in STANDARD_24_LIGAER and navn not in st.session_state["ekstra_ligaer"]:
                            st.session_state["ekstra_ligaer"].append(navn)
                    elif strat.startswith("FJERN_LIGA:"):
                        navn = normaliser_liga_navn(strat.replace("FJERN_LIGA:", ""))
                        if navn not in st.session_state["fjernede_ligaer"]:
                            st.session_state["fjernede_ligaer"].append(navn)
                        if navn in st.session_state["ekstra_ligaer"]:
                            st.session_state["ekstra_ligaer"].remove(navn)
        except Exception:
            pass
        st.session_state["favorit_synkroniseret"] = True

    samlet = [l for l in STANDARD_24_LIGAER if l not in st.session_state["fjernede_ligaer"]]
    for ekstra in st.session_state["ekstra_ligaer"]:
        if ekstra not in samlet and ekstra not in st.session_state["fjernede_ligaer"]:
            samlet.append(ekstra)
    return samlet if samlet else ["Ingen aktive ligaer (Tilføj nedenfor)"]

def tilfoej_ny_favorit_liga(ny_liga):
    if not ny_liga or not ny_liga.strip():
        return False
    ren = normaliser_liga_navn(ny_liga)
    hent_favorit_ligaer()
    if ren in st.session_state["fjernede_ligaer"]:
        st.session_state["fjernede_ligaer"].remove(ren)
    if ren not in STANDARD_24_LIGAER and ren not in st.session_state["ekstra_ligaer"]:
        st.session_state["ekstra_ligaer"].append(ren)
    _send_favorit_event("TILFOEJ_LIGA", ren)
    return True

def fjern_favorit_liga(liga_navn):
    ren = liga_navn.strip()
    if not ren or ren.startswith("Ingen aktive"):
        return False
    hent_favorit_ligaer()
    if ren not in st.session_state["fjernede_ligaer"]:
        st.session_state["fjernede_ligaer"].append(ren)
    if ren in st.session_state["ekstra_ligaer"]:
        st.session_state["ekstra_ligaer"].remove(ren)
    _send_favorit_event("FJERN_LIGA", ren)
    return True
