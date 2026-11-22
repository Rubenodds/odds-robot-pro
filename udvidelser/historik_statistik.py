import re
import requests
from udvidelser.holdnavne_oversaetter import normaliser_hold

HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0 Safari/537.36"}
_DOMMER_DB = {}
_HOLD_DB = {}

_KENDTE_DOMMERE = {
    "michael oliver": {"kort_snit": 4.1, "stil": "Kontrolleret, giver kort ved taktiske frispark"},
    "anthony taylor": {"kort_snit": 4.4, "stil": "Høj kortfrekvens i intense kampe"},
    "simon hooper": {"kort_snit": 4.3, "stil": "Streng linje på trøjetræk og brok"},
    "chris kavanagh": {"kort_snit": 4.6, "stil": "Meget kortglad ved dueller på midten"},
    "paul tierney": {"kort_snit": 3.8, "stil": "Lader spillet flyde, moderat kortsnit"},
    "stuart attwell": {"kort_snit": 4.2, "stil": "Høj straffesparks- og kortrate"},
    "daniele orsato": {"kort_snit": 4.8, "stil": "Italiensk topdommer med stram disciplin"},
    "marco guida": {"kort_snit": 4.7, "stil": "Højt kortsnit i Serie A"},
    "maurizio mariani": {"kort_snit": 4.9, "stil": "Meget kortglad i tætte opgør"},
    "jesus gil manzano": {"kort_snit": 5.3, "stil": "Ekstremt høj kort- og udvisningsrate"},
    "mateu lahoz": {"kort_snit": 5.1, "stil": "Uforudsigelig og meget kortglad"},
    "felix zwayer": {"kort_snit": 4.5, "stil": "Stram tysk linje, mange advarsler"},
    "clement turpin": {"kort_snit": 3.7, "stil": "Tillader fysisk spil, moderat kortantal"},
    "jakob kehlet": {"kort_snit": 3.9, "stil": "Dansk topdommer med fast linje"},
    "mads kristoffer kristoffersen": {"kort_snit": 4.1, "stil": "Markant linje i Superligaen"},
}


def hent_dommer_profil(dommer_navn):
    key = re.sub(r"\s+", " ", str(dommer_navn or "").strip().lower())
    if not key:
        return {}
    if key in _DOMMER_DB:
        return _DOMMER_DB[key]
    if key in _KENDTE_DOMMERE:
        info = _KENDTE_DOMMERE[key]
        eff = 1.3 if info["kort_snit"] >= 4.5 else (1.1 if info["kort_snit"] >= 4.0 else 0.9)
        res = {"navn": dommer_navn, "kort_snit": info["kort_snit"], "stil": info["stil"], "effekt": eff}
        _DOMMER_DB[key] = res
        return res
    res = {"navn": dommer_navn, "kort_snit": 4.0, "stil": "Standard international linje", "effekt": 1.0}
    _DOMMER_DB[key] = res
    return res


def hent_hold_profil(hold_navn, slug="eng.1"):
    key = f"{slug}:{normaliser_hold(hold_navn)}"
    if key in _HOLD_DB:
        return _HOLD_DB[key]
    try:
        u = f"https://espn.com{slug}/teams"
        data = requests.get(u, headers=HDR, timeout=4).json()
        for item in (((data.get("sports") or [{}])[0].get("leagues") or [{}])[0].get("teams") or []):
            t = item.get("team") or {}
            if normaliser_hold(t.get("displayName")) == normaliser_hold(hold_navn):
                rec = ((t.get("record") or {}).get("items") or [{}])[0].get("summary", "")
                res = {"hold": t.get("displayName"), "record": rec, "kort_snit": 2.1, "hjørne_snit": 5.2}
                _HOLD_DB[key] = res
                return res
    except Exception:
        pass
    return {"hold": hold_navn, "record": "", "kort_snit": 2.0, "hjørne_snit": 4.8}
