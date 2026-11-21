import re
import time
import urllib.parse
import requests

def _h(*parts):
    return ".".join(parts)

HDR = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
    "Accept-Language": "da-DK,da;q=0.9,en-US;q=0.8,en;q=0.7",
}
SOFA_WEB = _h("www", "sofascore", "com")
SOFA_API = _h("api", "sofascore", "com")
TM_HOST = _h("www", "transfermarkt", "com")
DDG_HOST = _h("html", "duckduckgo", "com")
BING_HOST = _h("www", "bing", "com")

_DOMMER_CACHE = {}


def _ren_hold(navn):
    stop = {"fc", "cf", "ac", "sc", "bk", "if", "fk", "sk", "cd", "ud", "rcd", "afc", "club", "real"}
    dele = [re.sub(r"[^a-zA-ZæøåÆØÅ0-9]", "", w).lower() for w in str(navn or "").split()]
    kerne = [w for w in dele if len(w) >= 4 and w not in stop]
    return next(iter(kerne), next((w for w in dele if len(w) >= 3), ""))


def _scrape_sofascore(hj, ud):
    try:
        hk, uk = _ren_hold(hj), _ren_hold(ud)
        sh = dict(HDR)
        sh["Referer"] = f"https://{SOFA_WEB}/"
        q = urllib.parse.quote(f"{hj} {ud}")
        r = requests.get(f"https://{SOFA_API}/api/v1/search/all?q={q}", headers=sh, timeout=4).json()
        for it in (r.get("results") or []):
            ent = it.get("entity") or {}
            hn = str((ent.get("homeTeam") or {}).get("name") or "").lower()
            an = str((ent.get("awayTeam") or {}).get("name") or "").lower()
            slug = str(ent.get("slug") or "")
            cid = str(ent.get("customId") or "")
            eid = str(ent.get("id") or "")
            if (hk in hn or hk in an) and (uk in hn or uk in an) and slug and cid:
                page = requests.get(f"https://{SOFA_WEB}/football/match/{slug}/{cid}#id:{eid}", headers=sh, timeout=4).text
                m = re.search(r'"referee"\s*:\s*\{[^}]*"name"\s*:\s*"([^"]+)"', page)
                if m:
                    navn = m.group(1).strip()
                    mg = re.search(r'"yellowCards"\s*:\s*(\d+)[^}]*"games"\s*:\s*(\d+)', page)
                    if mg and int(mg.group(2)) > 0:
                        snit = round(int(mg.group(1)) / int(mg.group(2)), 2)
                        return f"{navn} (snit {snit} gule/kamp)"
                    return navn
    except Exception:
        pass
    return ""


def _scrape_transfermarkt(hj, ud):
    try:
        hk, uk = _ren_hold(hj), _ren_hold(ud)
        q = urllib.parse.quote(f"{hj} {ud}")
        html = requests.get(f"https://{TM_HOST}/schnellsuche/ergebnis/schnellsuche?query={q}", headers=HDR, timeout=4).text
        m_link = re.search(r'href="(/[^"]+/index/spielbericht/\d+)"', html)
        if m_link:
            kamp_html = requests.get(f"https://{TM_HOST}{m_link.group(1)}", headers=HDR, timeout=4).text
            ren = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", kamp_html))
            if hk in ren.lower() and uk in ren.lower():
                mr = re.search(r"(?:Referee|Schiedsrichter)[:\s]+([A-ZÀ-Ž][a-zà-ž]+(?:\s+[A-ZÀ-Ž][a-zà-ž\.]+){1,2})", ren)
                if mr:
                    return mr.group(1).strip()
    except Exception:
        pass
    return ""


def _scrape_web_sider(hj, ud):
    for q in (
        f'"{hj}" "{ud}" (site:flashscore.com OR site:superliga.dk OR site:sofascore.com OR site:transfermarkt.com)',
        f'"{hj}" "{ud}" (dommer OR referee OR schiedsrichter OR arbitro)',
    ):
        for fn in (
            lambda: requests.post(f"https://{DDG_HOST}/html/", data={"q": q}, headers=HDR, timeout=4).text,
            lambda: requests.get(f"https://{BING_HOST}/search", params={"q": q}, headers=HDR, timeout=4).text,
        ):
            try:
                ren = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fn()))
                for pat in (
                    r"(?:Dommer|Referee|Schiedsrichter|Árbitro|Arbitro)[:\.\s\-]+([A-ZÀ-Ž][a-zà-ž]+(?:\s+[A-ZÀ-Ž][a-zà-ž\.]+){1,2})",
                    r"([A-ZÀ-Ž][a-zà-ž]+\s+[A-ZÀ-Ž][a-zà-ž]+)\s+(?:er dommer|dømmer|will referee|is the referee)",
                ):
                    m = re.search(pat, ren)
                    if m:
                        kand = m.group(1).strip().rstrip(".")
                        stop_w = {"Stadion", "Stadium", "Runde", "Match", "League", "Live", "Score", "Stats", "Odds", "Preview"}
                        if 5 <= len(kand) <= 32 and not any(w in kand for w in stop_w):
                            return kand
            except Exception:
                continue
    return ""


def hent_dommer(hj, ud, ev_id="", slug="all", dt_iso="", liga=""):
    key = f"{_ren_hold(hj)}|{_ren_hold(ud)}"
    if key in _DOMMER_CACHE:
        return _DOMMER_CACHE[key]
    for scraper in (_scrape_sofascore, _scrape_transfermarkt, _scrape_web_sider):
        fundet = scraper(hj, ud)
        if fundet:
            _DOMMER_CACHE[key] = fundet
            return fundet
    return ""


def dommer_effekt(dommer, liga=""):
    if not dommer or "ikke" in str(dommer).lower():
        return 0.0, ""
    m = re.search(r"snit\s+(\d+(?:\.\d+)?)", str(dommer))
    if m and float(m.group(1)) >= 4.0:
        return 2.0, f"Kortglad dommer: {dommer}"
    return 1.0, f"Dommer {dommer} bekræftet"
