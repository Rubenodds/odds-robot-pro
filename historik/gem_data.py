import os
import json
import base64
import urllib.request
import urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st

FIL_STI = "historik/gemte_kuponer.json"
LOKAL_STI = os.path.join("historik", "backup_kuponer.json")


def _dansk_tid():
    try:
        return datetime.now(ZoneInfo("Europe/Copenhagen")).strftime("%d-%m-%Y %H:%M")
    except Exception:
        return datetime.now().strftime("%d-%m-%Y %H:%M")


def _gh_cfg():
    try:
        gh = st.secrets.get("github") or {}
        tok = "".join(str(gh.get("token") or st.secrets.get("GITHUB_TOKEN") or "").split())
        user = "".join(str(gh.get("username") or "Rubenodds").split())
        repo_navn = "".join(str(gh.get("repo") or "odds-robot-pro").split())
        repo = repo_navn if "/" in repo_navn else f"{user}/{repo_navn}"
        if tok:
            return tok, repo
    except Exception:
        pass
    return None, None


def _gh_url(repo):
    host = ".".join(["api", "github", "com"])
    return f"https://{host}/repos/{repo}/contents/{FIL_STI}"


def _lokal_laes():
    if os.path.exists(LOKAL_STI):
        try:
            with open(LOKAL_STI, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _lokal_skriv(raekker):
    os.makedirs("historik", exist_ok=True)
    with open(LOKAL_STI, "w", encoding="utf-8") as f:
        json.dump(raekker, f, ensure_ascii=False, indent=2)


def _gh_laes():
    tok, repo = _gh_cfg()
    if not tok:
        return _lokal_laes(), None
    req = urllib.request.Request(
        _gh_url(repo),
        headers={
            "Authorization": f"Bearer {tok}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "OddsRobotPro",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=4) as res:
            d = json.loads(res.read().decode("utf-8"))
            raekker = json.loads(base64.b64decode(d["content"]).decode("utf-8"))
            st.session_state["kupon_sha"] = d.get("sha")
            st.session_state.pop("gh_fejl", None)
            _lokal_skriv(raekker)
            return raekker, d.get("sha")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            st.session_state.pop("gh_fejl", None)
            return [], None
        st.session_state["gh_fejl"] = f"HTTP {e.code} ({repo})"
        return _lokal_laes(), None
    except Exception as e:
        st.session_state["gh_fejl"] = f"{e} ({repo})"
        return _lokal_laes(), None


def _gh_skriv(raekker, sha=None):
    _lokal_skriv(raekker)
    tok, repo = _gh_cfg()
    if not tok:
        return False
    body = {
        "message": "Opdater kuponer",
        "content": base64.b64encode(json.dumps(raekker, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8"),
    }
    if sha:
        body["sha"] = sha
    req = urllib.request.Request(
        _gh_url(repo),
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {tok}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "OddsRobotPro",
        },
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            if res.status in (200, 201):
                ny_d = json.loads(res.read().decode("utf-8"))
                st.session_state["kupon_sha"] = (ny_d.get("content") or {}).get("sha")
                st.session_state.pop("gh_fejl", None)
                return True
    except urllib.error.HTTPError as e:
        st.session_state["gh_fejl"] = f"HTTP {e.code} ({repo})"
    except Exception as e:
        st.session_state["gh_fejl"] = f"{e} ({repo})"
    return False


def hent_alle_kuponer():
    if "kupon_ram_cache" not in st.session_state:
        raekker, _ = _gh_laes()
        st.session_state["kupon_ram_cache"] = raekker
    return st.session_state["kupon_ram_cache"]


def gem_kupon_i_historik(*args, **kwargs):
    kilde, kampe, tal = "Scanner", [], []
    for a in args:
        if isinstance(a, (list, tuple)) and a:
            kampe = list(a)
        elif isinstance(a, (int, float)):
            tal.append(float(a))
        elif isinstance(a, str) and a.strip():
            kilde = a.strip()
    kampe = kwargs.get("kampe") or kwargs.get("valg") or kampe
    odds = round(float(kwargs.get("odds") or kwargs.get("total_odds") or next(iter(tal), 1.0)), 2)
    indsats = float(kwargs.get("indsats") or (tal[-1] if len(tal) >= 2 and tal[-1] >= 10 else 100.0))
    dato = _dansk_tid()

    raekker = list(hent_alle_kuponer())
    sha = st.session_state.get("kupon_sha")
    if not sha:
        raekker, sha = _gh_laes()

    nyt_id = max([int(r.get("id", 0)) for r in raekker], default=0) + 1
    ny_post = {
        "id": nyt_id,
        "dato": dato,
        "kilde": kilde,
        "kampe": f"{len(kampe)} kampe ({dato})",
        "detaljer": json.dumps(kampe, ensure_ascii=False),
        "odds": odds,
        "indsats": indsats,
        "mulig_gevinst": round(odds * indsats, 2),
        "status": "[AFVENTER]",
    }
    raekker.insert(0, ny_post)

    cloud_ok = _gh_skriv(raekker, sha)
    if not cloud_ok:
        friske, ny_sha = _gh_laes()
        if ny_sha:
            nyt_id = max([int(r.get("id", 0)) for r in friske], default=0) + 1
            ny_post["id"] = nyt_id
            friske.insert(0, ny_post)
            raekker = friske
            cloud_ok = _gh_skriv(raekker, ny_sha)

    st.session_state["kupon_ram_cache"] = raekker
    fejl = st.session_state.get("gh_fejl")
    status_txt = " (Cloud ☁️)" if cloud_ok else f" (Kun lokal ⚠️ {fejl or ''})"
    msg = f"✅ OK – Kupon ({len(kampe)} kampe @ {odds}) er tilføjet til historikken!{status_txt}"
    st.session_state["sidste_gem_ok"] = msg
    st.success(msg)
    return True


def slet_kupon(kupon_id):
    raekker = list(hent_alle_kuponer())
    ny = [r for r in raekker if int(r.get("id", -1)) != int(kupon_id)]
    st.session_state["kupon_ram_cache"] = ny
    sha = st.session_state.get("kupon_sha")
    if not sha:
        _, sha = _gh_laes()
    if not _gh_skriv(ny, sha):
        _, ny_sha = _gh_laes()
        if ny_sha:
            _gh_skriv(ny, ny_sha)
    return True


gem_kupon = gem_kupon_i_historik
gem_spil = gem_kupon_i_historik
hent_spil = hent_alle_kuponer
