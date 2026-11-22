import datetime
import re
import urllib.parse
import xml.etree.ElementTree as ET
import requests

def _h(*p):
    return ".".join(p)

HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0 Safari/537.36"}
ESPN_H = _h("site", "api", "espn", "com")
SDB_H = _h("www", "thesportsdb", "com")
BING_H = _h("www", "bing", "com")
GNEWS_H = _h("news", "google", "com")
_DOMMER_CACHE = {}
_FORBUDT = {"Stadion", "Stadium", "Runde", "Match", "League", "Live", "Score", "Stats", "Odds", "Preview", "Var", "Assistant", "Fourth", "Official", "Kickoff", "Result", "Highlights"}


def _ren(navn):
    stop = {"fc", "cf", "ac", "sc", "bk", "if", "fk", "sk", "cd", "ud", "rcd", "afc", "club", "real", "rovers", "united", "city", "fortuna"}
    dele = [re.sub(r"[^a-zA-ZæøåÆØÅ0-9]", "", w).lower() for w in str(navn or "").split()]
    kerne = [w for w in dele if len(w) >= 4 and w not in stop]
    return next(iter(kerne), next((w for w in dele if len(w) >= 3), ""))


def _find_navn(tekst, hj="", ud=""):
    ren = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(tekst or "")))
    hold_ord = set(re.findall(r"[A-Za-zÀ-ž]{3,}", f"{hj} {ud}"))
    for pat in (
        r"(?:Referee|Dommer|Schiedsrichter|Árbitro|Arbitro|Main\s+referee)[:\.\s\-]+([A-ZÀ-Ž][a-zà-ž]+(?:\s+[A-ZÀ-Ž][a-zà-ž\.\-']+){1,2})",
        r"([A-ZÀ-Ž][a-zà-ž]+(?:\s+[A-ZÀ-Ž][a-zà-ž\.\-']+){1,2})\s*(?:\((?:Referee|Dommer|Arbitro)\)|to referee|will referee|is the referee|named referee|appointed referee|er dommer|dømmer|skal dømme)",
    ):
        for m in re.finditer(pat, ren):
            kand = m.group(1).strip().rstrip(".,;:|")
            ord_l = kand.split()
            if 5 <= len(kand) <= 32 and 2 <= len(ord_l) <= 3:
                if not any(w in _FORBUDT or w in hold_ord for w in ord_l):
                    return kand
    return ""


def _espn_dommer(hj, ud, ev_id="", slug=""):
    try:
        hk, uk = _ren(hj), _ren(ud)
        if ev_id:
            s_use = slug if (slug and slug != "all") else "all"
            sm = requests.get(f"https://{ESPN_H}/apis/site/v2/sports/soccer/{s_use}/summary", params={"event": ev_id}, headers=HDR, timeout=3).json()
            for off in ((sm.get("gameInfo") or {}).get("officials") or []):
                if n := str(off.get("displayName") or off.get("fullName") or "").strip():
                    return n
        nu = datetime.date.today()
        d_sp = f"{(nu - datetime.timedelta(days=1)).strftime('%Y%m%d')}-{(nu + datetime.timedelta(days=1)).strftime('%Y%m%d')}"
        for s_try in list(dict.fromkeys([s for s in (slug, "esp.2", "nor.1", "den.1", "swe.1", "eng.1", "eng.2", "ita.1", "esp.1", "ger.1", "fra.1") if s and s != "all"]))[:6]:
            sb = requests.get(f"https://{ESPN_H}/apis/site/v2/sports/soccer/{s_try}/scoreboard", params={"dates": d_sp}, headers=HDR, timeout=2.5).json()
            for ev in (sb.get("events") or []):
                for comp in (ev.get("competitions") or []):
                    navne = [str((t.get("team") or {}).get("displayName") or "").lower() for t in (comp.get("competitors") or [])]
                    if any(hk in n for n in navne) and any(uk in n for n in navne):
                        for off in (comp.get("officials") or []):
                            if n := str(off.get("displayName") or off.get("fullName") or "").strip():
                                return n
    except Exception:
        pass
    return ""


def _web_dommer(hj, ud):
    hk, uk = _ren(hj), _ren(ud)
    if not hk or not uk:
        return ""
    for q in (f"{hk}_vs_{uk}", f"{hj}_vs_{ud}".replace(" ", "_")):
        try:
            r = requests.get(f"https://{SDB_H}/api/v1/json/3/searchevents.php?e={urllib.parse.quote(q)}", headers=HDR, timeout=2.5).json()
            for ev in (r.get("event") or [])[:5]:
                ref = str(ev.get("strReferee") or "").strip()
                if len(ref) >= 5 and " " in ref:
                    return ref
        except Exception:
            pass
    for u in (
        f"https://{BING_H}/search?q={urllib.parse.quote(f'{hk} {uk} referee')}&format=rss",
        f"https://{GNEWS_H}/rss/search?q={urllib.parse.quote(f'{hk} {uk} referee')}&hl=en&gl=US&ceid=US:en",
    ):
        try:
            root = ET.fromstring(requests.get(u, headers=HDR, timeout=3).text)
            for item in root.findall(".//item")[:8]:
                txt = f"{item.findtext('title') or ''} {item.findtext('description') or ''}"
                if hk in txt.lower() or uk in txt.lower():
                    if navn := _find_navn(txt, hj, ud):
                        return navn
        except Exception:
            pass
    return ""


def hent_dommer(hj, ud, ev_id="", slug="all", dt_iso="", liga=""):
    key = f"{_ren(hj)}|{_ren(ud)}"
    if key in _DOMMER_CACHE:
        return _DOMMER_CACHE[key]
    fundet = _espn_dommer(hj, ud, ev_id, slug) or _web_dommer(hj, ud)
    if fundet:
        try:
            from udvidelser.historik_statistik import hent_dommer_profil
            p = hent_dommer_profil(fundet)
            if p and p.get("kort_snit"):
                fundet = f"{fundet} ({p['kort_snit']} kort/kamp)"
        except Exception:
            pass
        _DOMMER_CACHE[key] = fundet
    return fundet


def dommer_effekt(dommer, liga="", hj="", ud=""):
    if not dommer or "ikke" in str(dommer).lower():
        return 0.0, ""
    return 1.0, f"Dommer {dommer} bekræftet"
