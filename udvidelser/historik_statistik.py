import json
import os
import re
import urllib.parse
import requests
from udvidelser.holdnavne_oversaetter import normaliser_hold, samme_hold

HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0 Safari/537.36"}
_DOMMER_DB = {}
_HOLD_DB = {}
_H2H_DB = {}

_KENDTE_DOMMERE = {
    "michael oliver": {"kort_snit": 4.1, "stil": "Kontrolleret"},
    "anthony taylor": {"kort_snit": 4.4, "stil": "Høj kortfrekvens"},
    "simon hooper": {"kort_snit": 4.3, "stil": "Streng linje"},
    "chris kavanagh": {"kort_snit": 4.6, "stil": "Meget kortglad"},
    "paul tierney": {"kort_snit": 3.8, "stil": "Moderat kortsnit"},
    "stuart attwell": {"kort_snit": 4.2, "stil": "Høj kortrate"},
    "daniele orsato": {"kort_snit": 4.8, "stil": "Stram disciplin"},
    "marco guida": {"kort_snit": 4.7, "stil": "Højt kortsnit"},
    "maurizio mariani": {"kort_snit": 4.9, "stil": "Meget kortglad"},
    "jesus gil manzano": {"kort_snit": 5.3, "stil": "Ekstrem kortrate"},
    "felix zwayer": {"kort_snit": 4.5, "stil": "Stram tysk linje"},
    "clement turpin": {"kort_snit": 3.7, "stil": "Tillader fysisk spil"},
    "jakob kehlet": {"kort_snit": 3.9, "stil": "Dansk topdommer"},
    "mads kristoffer kristoffersen": {"kort_snit": 4.1, "stil": "Markant linje"},
}


def hent_dommer_profil(dommer_navn):
    key = re.sub(r"\s+", " ", str(dommer_navn or "").strip().lower())
    if not key:
        return {}
    if key in _DOMMER_DB:
        return _DOMMER_DB[key]
    info = _KENDTE_DOMMERE.get(key, {"kort_snit": 4.0, "stil": "Standard linje"})
    eff = 1.3 if info["kort_snit"] >= 4.5 else (1.1 if info["kort_snit"] >= 4.0 else 0.9)
    res = {"navn": dommer_navn, "kort_snit": info["kort_snit"], "stil": info["stil"], "effekt": eff}
    _DOMMER_DB[key] = res
    return res


def hent_h2h_profil(hj, ud):
    key = f"{normaliser_hold(hj)}|{normaliser_hold(ud)}"
    if key in _H2H_DB:
        return _H2H_DB[key]
    maal_liste = []
    try:
        q = urllib.parse.quote(f'"{hj}" "{ud}" head to head results')
        html = requests.get(f"https://duckduckgo.com{q}", headers=HDR, timeout=4).text
        for m in re.finditer(r"\b([0-6])\s*[-–:]\s*([0-6])\b", re.sub(r"<[^>]+>", " ", html)):
            maal_liste.append(int(m.group(1)) + int(m.group(2)))
            if len(maal_liste) >= 5:
                break
    except Exception:
        pass
    if maal_liste:
        snit = round(sum(maal_liste) / len(maal_liste), 1)
        o15 = sum(1 for x in maal_liste if x >= 2)
        res = {"kampe": len(maal_liste), "maal_snit": snit, "tekst": f"H2H: {snit} mål/kamp ({o15}/{len(maal_liste)} O1.5)"}
    else:
        res = {"kampe": 0, "maal_snit": 0.0, "tekst": ""}
    _H2H_DB[key] = res
    return res


def hent_hold_profil(hold_navn, slug="eng.1"):
    key = f"{slug}:{normaliser_hold(hold_navn)}"
    if key in _HOLD_DB:
        return _HOLD_DB[key]
    try:
        u = f"https://espn.com{slug}/teams"
        data = requests.get(u, headers=HDR, timeout=4).json()
        for item in (((data.get("sports") or [{}])[0].get("leagues") or [{}]).get("teams") or []):
            t = item.get("team") or {}
            if samme_hold(t.get("displayName"), hold_navn):
                rec = ((t.get("record") or {}).get("items") or [{}])[0].get("summary", "")
                res = {"hold": t.get("displayName"), "record": rec, "kort_snit": 2.1, "hjørne_snit": 5.2}
                _HOLD_DB[key] = res
                return res
    except Exception:
        pass
    return {"hold": hold_navn, "record": "", "kort_snit": 2.0, "hjørne_snit": 4.8}
