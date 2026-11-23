import re
from datetime import datetime, timedelta
import requests
from udvidelser.holdnavne_oversaetter import samme_hold

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept-Language": "da-DK,da;q=0.9,en;q=0.8"
}

BASIS_LIGAER = [
    "den.1", "eng.1", "eng.2", "esp.1", "ita.1", "ger.1",
    "fra.1", "ned.1", "por.1", "sco.1", "swe.1", "nor.1",
    "uefa.champions", "uefa.europa", "uefa.europa.conf", "fifa.world", "all"
]

def _alle_liga_slugs():
    """Kombinerer dine favoritligaer med brede ESPN-ligaer."""
    slugs = list(BASIS_LIGAER)
    try:
        import odds_motor.liga_favoritter as lf
        for v in vars(lf).values():
            if isinstance(v, (list, dict)):
                items = v.values() if isinstance(v, dict) else v
                for x in items:
                    if isinstance(x, str) and "." in x and x not in slugs:
                        slugs.insert(0, x)
    except Exception:
        pass
    return slugs

def _dato_interval():
    nu = datetime.utcnow()
    return f"{(nu - timedelta(days=1)).strftime('%Y%m%d')}-{(nu + timedelta(days=6)).strftime('%Y%m%d')}"

def _espn_dommer(hjemme, ude):
    datoer = _dato_interval()
    for liga in _alle_liga_slugs():
        try:
            url = f"https://espn.com{liga}/scoreboard?dates={datoer}&limit=300"
            r = requests.get(url, headers=HEADERS, timeout=5).json()
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
                    l_slug = ev.get("league", {}).get("slug", liga)
                    sum_url = f"https://espn.com{l_slug}/summary?event={ev_id}"
                    s_data = requests.get(sum_url, headers=HEADERS, timeout=5).json()
                    officials = s_data.get("gameInfo", {}).get("officials") or []
                    if officials:
                        return officials[0].get("displayName", "").strip()
        except Exception:
            continue
    return ""

def _web_dommer(hjemme, ude):
    try:
        q = requests.utils.quote(f'{hjemme} {ude} dommer OR referee OR arbitro')
        r = requests.get(f"https://duckduckgo.com{q}", headers=HEADERS, timeout=6)
        tekst = re.sub(r"<[^>]+>", " ", r.text)
        m = re.search(
            r"(?:Dommer|Referee|Arbitro|Árbitro|Schiedsrichter)[:\s-]+([A-ZÆØÅÀ-ÿ][a-zæøåà-ÿ'-]+(?:\s+[A-ZÆØÅÀ-ÿ][a-zæøåà-ÿ'-]+){1,2})",
            tekst
        )
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return ""

def hent_dommer(hjemme, ude):
    return _espn_dommer(hjemme, ude) or _web_dommer(hjemme, ude)

def dommer_effekt(dommer_navn):
    if not dommer_navn:
        return "Dommer ikke offentliggjort endnu (neutral vurdering)."
    return f"Dommer: {dommer_navn} – tjek kort-profil før linjespil."
