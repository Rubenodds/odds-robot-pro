import re
from datetime import datetime, timedelta
import requests
from udvidelser.holdnavne_oversaetter import samme_hold

ESPN_LIGAER = [
    "eng.1", "esp.1", "ita.1", "ger.1", "fra.1",
    "den.1", "uefa.champions", "uefa.europa", "fifa.world"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

def _dato_interval():
    nu = datetime.utcnow()
    start = (nu - timedelta(days=1)).strftime("%Y%m%d")
    slut = (nu + timedelta(days=5)).strftime("%Y%m%d")
    return f"{start}-{slut}"

def _hent_dommer_espn(hjemme, ude):
    datoer = _dato_interval()
    for liga in ESPN_LIGAER:
        try:
            url = f"https://espn.com{liga}/scoreboard?dates={datoer}"
            r = requests.get(url, headers=HEADERS, timeout=5).json()
            for ev in r.get("events", []):
                comp = ev.get("competitions", [{}])
                hold = [c.get("team", {}).get("displayName", "") for c in comp.get("competitors", [])]
                if len(hold) == 2 and (
                    (samme_hold(hjemme, hold) and samme_hold(ude, hold)) or
                    (samme_hold(hjemme, hold) and samme_hold(ude, hold))
                ):
                    ev_id = ev.get("id")
                    sum_url = f"https://espn.com{liga}/summary?event={ev_id}"
                    s_data = requests.get(sum_url, headers=HEADERS, timeout=5).json()
                    officials = s_data.get("gameInfo", {}).get("officials", [])
                    if officials:
                        return officials.get("displayName", "").strip()
        except Exception:
            continue
    return ""

def _hent_dommer_web(hjemme, ude):
    try:
        q = requests.utils.quote(f'"{hjemme}" "{ude}" referee')
        r = requests.get(f"https://duckduckgo.com{q}", headers=HEADERS, timeout=6)
        tekst = re.sub(r"<[^>]+>", " ", r.text)
        m = re.search(r"(?:Referee|Arbitro|Dommer)[:\s-]+([A-ZÀ-ÿ][a-zà-ÿ'-]+(?:\s+[A-ZÀ-ÿ][a-zà-ÿ'-]+){1,2})", tekst)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return ""

def hent_dommer(hjemme, ude):
    espn_navn = _hent_dommer_espn(hjemme, ude)
    web_navn = "" if espn_navn else _hent_dommer_web(hjemme, ude)
    return {
        "espn": espn_navn,
        "web": web_navn,
        "samlet": espn_navn or web_navn
    }

def dommer_effekt(dommer_navn):
    if not dommer_navn:
        return "Dommer ikke offentliggjort endnu (neutral vurdering)."
    return f"Dommer: {dommer_navn} – tjek kort-profil før linjespil."
