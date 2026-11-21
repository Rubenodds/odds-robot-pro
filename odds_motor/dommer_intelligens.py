import datetime
import re
import urllib.parse
import xml.etree.ElementTree as ET
import requests

def _h(*parts):
    return ".".join(parts)

HDR = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "da-DK,da;q=0.9,en-US;q=0.8,en;q=0.7",
}
GNEWS_HOST = _h("news", "google", "com")
SITE_HOST = _h("site", "api", "espn", "com")

_DOMMER_CACHE = {}


def _ren_hold(navn):
    stop = {"fc", "cf", "ac", "sc", "bk", "if", "fk", "sk", "cd", "ud", "rcd", "afc", "club", "real", "rovers", "united", "city"}
    dele = [re.sub(r"[^a-zA-ZæøåÆØÅ0-9]", "", w).lower() for w in str(navn or "").split()]
    kerne = [w for w in dele if len(w) >= 4 and w not in stop]
    return next(iter(kerne), next((w for w in dele if len(w) >= 3), ""))


def _udtraek_navn(tekst):
    ren = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(tekst or "")))
    for pat in (
        r"([A-ZÀ-Ž][a-zà-ž]+(?:\s+[A-ZÀ-Ž][a-zà-ž\.]+){1,2})\s+(?:to referee|will referee|is the referee|named referee|appointed referee|er dommer|dømmer|skal dømme)",
        r"(?:Dommer|Referee|Schiedsrichter|Árbitro|Arbitro)[:\.\s\-]+([A-ZÀ-Ž][a-zà-ž]+(?:\s+[A-ZÀ-Ž][a-zà-ž\.]+){1,2})",
    ):
        m = re.search(pat, ren)
        if m:
            kand = m.group(1).strip().rstrip(".")
            forbudt = {"Stadion", "Stadium", "Runde", "Match", "League", "Live", "Score", "Stats", "Odds", "Preview", "Juventus", "Venezia", "Burnley", "Blackburn", "Horsens", "Silkeborg"}
            if 5 <= len(kand) <= 34 and not any(w in kand for w in forbudt):
                return kand
    return ""


def _hent_google_news_dommer(hj, ud):
    hk, uk = _ren_hold(hj), _ren_hold(ud)
    if not hk or not uk:
        return ""
    for q in (f"{hk} {uk} referee", f"{hk} {uk} dommer"):
        try:
            u = f"https://{GNEWS_HOST}/rss/search?q={urllib.parse.quote(q)}&hl=en&gl=US&ceid=US:en"
            xml_txt = requests.get(u, headers=HDR, timeout=4).text
            root = ET.fromstring(xml_txt)
            for item in root.findall(".//item")[:8]:
                titel = item.findtext("title") or ""
                besk = item.findtext("description") or ""
                samlet = f"{titel} {besk}"
                if hk in samlet.lower() or uk in samlet.lower():
                    if navn := _udtraek_navn(samlet):
                        return navn
        except Exception:
            continue
    return ""


def _hent_espn_dommer(hj, ud, ev_id="", slug=""):
    try:
        hk, uk = _ren_hold(hj), _ren_hold(ud)
        if ev_id and slug and slug != "all":
            sm = requests.get(f"https://{SITE_HOST}/apis/site/v2/sports/soccer/{slug}/summary", params={"event": ev_id}, headers=HDR, timeout=3).json()
            for off in ((sm.get("gameInfo") or {}).get("officials") or []):
                n = str(off.get("displayName") or off.get("fullName") or "").strip()
                if n:
                    return n
        nu = datetime.date.today()
        dato_sp = f"{(nu - datetime.timedelta(days=1)).strftime('%Y%m%d')}-{(nu + datetime.timedelta(days=2)).strftime('%Y%m%d')}"
        for s_try in list(dict.fromkeys([s for s in (slug, "ita.1", "eng.1", "eng.2", "eng.3", "esp.1", "ger.1", "fra.1", "den.1") if s and s != "all"]))[:5]:
            sb = requests.get(f"https://{SITE_HOST}/apis/site/v2/sports/soccer/{s_try}/scoreboard", params={"dates": dato_sp}, headers=HDR, timeout=3).json()
            for ev in (sb.get("events") or []):
                for comp in (ev.get("competitions") or []):
                    teams = comp.get("competitors") or []
                    navne = [str((t.get("team") or {}).get("displayName") or "").lower() for t in teams]
                    if any(hk in n for n in navne) and any(uk in n for n in navne):
                        for off in (comp.get("officials") or []):
                            n = str(off.get("displayName") or off.get("fullName") or "").strip()
                            if n:
                                return n
    except Exception:
        pass
    return ""


def hent_dommer(hj, ud, ev_id="", slug="all", dt_iso="", liga=""):
    key = f"{_ren_hold(hj)}|{_ren_hold(ud)}"
    if key in _DOMMER_CACHE:
        return _DOMMER_CACHE[key]
    fundet = _hent_google_news_dommer(hj, ud) or _hent_espn_dommer(hj, ud, ev_id, slug)
    if fundet:
        _DOMMER_CACHE[key] = fundet
        return fundet
    return ""


def dommer_effekt(dommer, liga=""):
    if not dommer or "ikke" in str(dommer).lower():
        return 0.0, ""
    return 1.0, f"Dommer {dommer} bekræftet"
