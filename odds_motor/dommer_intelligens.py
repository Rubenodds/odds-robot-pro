import re
from datetime import datetime, timedelta
import requests
from udvidelser.holdnavne_oversaetter import samme_hold

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

def _dato_interval():
    nu = datetime.utcnow()
    start = (nu - timedelta(days=1)).strftime("%Y%m%d")
    slut = (nu + timedelta(days=5)).strftime("%Y%m%d")
    return f"{start}-{slut}"

def _espn_dommer(hjemme, ude):
    """Søger på tværs af ALLE fodboldligaer globalt på ESPN."""
    datoer = _dato_interval()
    url = f"https://espn.com{datoer}&limit=500"
    try:
        r = requests.get(url, headers=HEADERS, timeout=7).json()
        for ev in r.get("events", []):
            comps = ev.get("competitions") or []
            if not comps:
                continue
            hold = [c.get("team", {}).get("displayName", "") for c in comps[0].get("competitors", [])]
            if len(hold) == 2 and (
                (samme_hold(hjemme, hold[0]) and samme_hold(ude, hold[1])) or
                (samme_hold(hjemme, hold[1]) and samme_hold(ude, hold[0]))
            ):
                ev_id = ev.get("id")
                liga_slug = ev.get("league", {}).get("slug", "all")
                sum_url = f"https://espn.com{liga_slug}/summary?event={ev_id}"
                s_data = requests.get(sum_url, headers=HEADERS, timeout=5).json()
                officials = s_data.get("gameInfo", {}).get("officials") or []
                if officials:
                    return officials[0].get("displayName", "").strip()
    except Exception:
        pass
    return ""

def _web_dommer(hjemme, ude):
    """Bred flersproget websøgning for alle ligaer."""
    try:
        q = requests.utils.quote(f'"{hjemme}" "{ude}" referee OR arbitro OR dommer')
        r = requests.get(f"https://duckduckgo.com{q}", headers=HEADERS, timeout=6)
        tekst = re.sub(r"<[^>]+>", " ", r.text)
        m = re.search(
            r"(?:Referee|Arbitro|Árbitro|Schiedsrichter|Dommer)[:\s-]+([A-ZÀ-ÿ][a-zà-ÿ'-]+(?:\s+[A-ZÀ-ÿ][a-zà-ÿ'-]+){1,2})",
            tekst
        )
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return ""

def hent_dommer(hjemme, ude):
    espn_navn = _espn_dommer(hjemme, ude)
    web_navn = "" if espn_navn else _web_dommer(hjemme, ude)
    return {
        "espn": espn_navn,
        "web": web_navn,
        "samlet": espn_navn or web_navn
    }

def dommer_effekt(dommer_navn):
    if not dommer_navn:
        return "Dommer ikke offentliggjort endnu (neutral vurdering)."
    return f"Dommer: {dommer_navn} – tjek kort-profil før linjespil."
