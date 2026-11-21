import os
import json
import time
import base64
import threading
import urllib.request
import urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st

FIL_STI = "historik/gemte_kuponer.json"
LOKAL_STI = os.path.join("historik", "backup_kuponer.json")
_SYNC_LAAS = threading.Lock()


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


def _gh_laes_direkte(tok, repo):
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
            _lokal_skriv(raekker)
            return raekker, d.get("sha")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return [], None
        return _lokal_laes(), None
    except Exception:
        return _lokal_laes(), None


def _gh_skriv_direkte(tok, repo, raekker, sha=None):
    _lokal_skriv(raekker)
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
            return res.status in (200, 201)
    except Exception:
        return False


def _gh_laes():
    tok, repo = _gh_cfg()
    raekker, sha = _gh_laes_direkte(tok, repo)
    st.session_state["kupon_sha"] = sha
    return raekker, sha


def _gh_skriv(raekker, sha=None):
    tok, repo = _gh_cfg()
    ok = _gh_skriv_direkte(tok, repo, raekker, sha)
    if ok and tok:
        _, ny_sha = _gh_laes_direkte(tok, repo)
        if ny_sha:
            st.session_state["kupon_sha"] = ny_sha
    return ok


def _baggrunds_sync(tok, repo, ny_post=None, slet_id=None):
    if not tok:
        return
    with _SYNC_LAAS:
        friske, sha = _gh_laes_direkte(tok, repo)
        if slet_id is not None:
            friske = [r for r in friske if int(r.get("id", -1)) != int(slet_id)]
        if ny_post is not None:
            nyt_id = max([int(r.get("id", 0)) for r in friske], default=0) + 1
            post_kopi = dict(ny_post)
            post_kopi["id"] = nyt_id
            friske.insert(0, post_kopi)
        _gh_skriv_direkte(tok, repo, friske, sha)


def _vis_groen_bekraeftelse(msg):
    st.markdown(
        f"""
        <div style="background-color:#16a34a;color:#ffffff;padding:12px 16px;
        border-radius:8px;font-weight:700;text-align:center;margin:8px 0;">
        {msg}
        </div>
        """,
        unsafe_allow_html=True,
    )


def hent_alle_kuponer():
    if "kupon_ram_cache" not in st.session_state:
        tok, repo = _gh_cfg()
        raekker, sha = _gh_laes_direkte(tok, repo)
        st.session_state["kupon_ram_cache"] = raekker
        st.session_state["kupon_sha"] = sha
    return st.session_state["kupon_ram_cache"]


def gem_kupon_i_historik(*args, **kwargs):
    nu = time.time()
    if nu - float(st.session_state.get("_sidste_gem_tid", 0.0)) < 1.5:
        if msg := st.session_state.get("sidste_gem_ok"):
            _vis_groen_bekraeftelse(msg)
        return True
    st.session_state["_sidste_gem_tid"] = nu

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
    _lokal_skriv(raekker)
    st.session_state["kupon_ram_cache"] = raekker

    tok, repo = _gh_cfg()
    if tok:
        t = threading.Thread(target=_baggrunds_sync, args=(tok, repo, ny_post, None), daemon=True)
        t.start()

    msg = f"✅ GEMT I HISTORIK – {len(kampe)} kampe @ {odds} (Cloud ☁️)"
    st.session_state["sidste_gem_ok"] = msg
    _vis_groen_bekraeftelse(msg)
    st.toast(msg, icon="✅")
    return True


def slet_kupon(kupon_id):
    raekker = list(hent_alle_kuponer())
    ny = [r for r in raekker if int(r.get("id", -1)) != int(kupon_id)]
    _lokal_skriv(ny)
    st.session_state["kupon_ram_cache"] = ny
    tok, repo = _gh_cfg()
    if tok:
        t = threading.Thread(target=_baggrunds_sync, args=(tok, repo, None, kupon_id), daemon=True)
        t.start()
    return True


gem_kupon = gem_kupon_i_historik
gem_spil = gem_kupon_i_historik
hent_spil = hent_alle_kuponer
