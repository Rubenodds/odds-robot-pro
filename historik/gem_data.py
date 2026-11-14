import os, json, base64, urllib.request
from datetime import datetime, timedelta
import streamlit as st

FIL_STI = "historik/gemte_kuponer.json"

def _dansk_tid():
    return (datetime.utcnow() + timedelta(hours=1)).strftime("%d-%m-%Y %H:%M")

def _gh_cfg():
    try:
        tok = (st.secrets.get("GITHUB_TOKEN") or st.secrets.get("GH_TOKEN") or st.secrets.get("TOKEN") or "").strip()
        repo = (st.secrets.get("GITHUB_REPO") or "Rubenodds/odds-robot-pro").strip()
        if tok:
            return tok, repo
    except Exception:
        pass
    return None, None

def _gh_laes():
    tok, repo = _gh_cfg()
    if not tok:
        return [], None
    req = urllib.request.Request(
        f"https://github.com{repo}/contents/{FIL_STI}",
        headers={"Authorization": f"token {tok}", "Accept": "application/vnd.github.v3+json", "User-Agent": "OddsRobotPro"})
    try:
        with urllib.request.urlopen(req, timeout=1.5) as res:
            d = json.loads(res.read().decode("utf-8"))
            raekker = json.loads(base64.b64decode(d["content"]).decode("utf-8"))
            return raekker, d["sha"]
    except Exception:
        return [], None

def _gh_skriv(raekker, sha=None):
    tok, repo = _gh_cfg()
    if not tok:
        return False
    body = {"message": "Opdaterer kuponer", "content": base64.b64encode(json.dumps(raekker, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8")}
    if sha:
        body["sha"] = sha
    req = urllib.request.Request(
        f"https://github.com{repo}/contents/{FIL_STI}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"token {tok}", "Accept": "application/vnd.github.v3+json", "User-Agent": "OddsRobotPro"},
        method="PUT")
    with urllib.request.urlopen(req, timeout=2.5) as res:
        return res.status in (200, 201)

def hent_alle_kuponer():
    if "kupon_ram_cache" not in st.session_state:
        raekker, _ = _gh_laes()
        st.session_state["kupon_ram_cache"] = raekker
    return st.session_state["kupon_ram_cache"]

def gem_kupon_i_historik(*args, **kwargs):
    kilde, kampe, tal = "Scanner", [], []
    for a in args:
        if isinstance(a, (list, tuple)) and a and any(":" in str(x) or "vs" in str(x) or "-" in str(x) for x in a):
            kampe = list(a)
        elif isinstance(a, (int, float)):
            tal.append(float(a))
        elif isinstance(a, str):
            kilde = a
    kampe = kwargs.get("kampe") or kampe
    odds = round(float(kwargs.get("odds") or kwargs.get("total_odds") or next(iter(tal), 1.0)), 2)
    indsats = float(kwargs.get("indsats") or (tal[-1] if len(tal) >= 4 else 100.0))
    dato = _dansk_tid()
    raekker, sha = _gh_laes()
    nyt_id = max([int(r.get("id", 0)) for r in raekker], default=0) + 1
    raekker.insert(0, {"id": nyt_id, "dato": dato, "kilde": kilde, "kampe": f"{len(kampe)} kampe ({dato})", "detaljer": json.dumps(kampe, ensure_ascii=False), "odds": odds, "indsats": indsats, "mulig_gevinst": round(odds * indsats, 2), "status": "[AFVENTER]"})
    _gh_skriv(raekker, sha)
    st.session_state["kupon_ram_cache"] = raekker
    st.toast("OK – tilføjet til historikken")
    return True

gem_kupon = gem_kupon_i_historik
gem_spil = gem_kupon_i_historik
hent_spil = hent_alle_kuponer
