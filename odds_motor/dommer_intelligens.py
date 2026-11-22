import datetime
import re
import urllib.parse
import xml.etree.ElementTree as ET
import requests

HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,da;q=0.8",
}
_DOMMER_CACHE = {}
_FORBUDT = {"Stadion", "Stadium", "Runde", "Match", "League", "Live", "Score", "Stats", "Odds", "Preview", "Var", "Assistant", "Fourth", "Official", "Kickoff", "Result"}


def _ren_hold(navn):
    stop = {"fc", "cf", "ac", "sc", "bk", "if", "fk", "sk", "cd", "ud", "rcd", "afc", "club", "real", "rovers", "united", "city"}
    dele = [re.sub(r"[^a-zA-ZæøåÆØÅ0-9]", "", w).lower() for w in str(navn or "").split()]
    kerne = [w for w in dele if len(w) >= 4 and w not in stop]
    return next(iter(kerne), next((w for w in dele if len(w) >= 3), ""))


def _udtraek_navn(tekst, hj="", ud=""):
    ren = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(tekst or "")))
    hold_ord = set(re.findall(r"[A-Za-zÀ-ž]{3,}", f"{hj} {ud}"))
    for pat in (
        r"(?:Referee|Dommer|Schiedsrichter|Árbitro|Arbitro|Main\s+referee)[:\.\s\-]+([A-ZÀ-Ž][a-zà-ž]+(?:\s+[A-ZÀ-Ž][a-zà-ž\.\-']+){1,2})",
        r"([A-ZÀ-Ž][a-zà-ž]+(?:\s+[A-ZÀ-Ž][a-zà-ž\.\-']+){1,2})\s+(?:to referee|will referee|is the referee|named referee|appointed referee|er dommer|dømmer|skal dømme|arbitrerà)",
    ):
        for m in re.finditer(pat, ren):
            kand = m.group(1).strip().rstrip(".,;:|")
            ord_liste = kand.split()
            if 5 <= len(kand) <= 32 and 2 <= len(ord_liste) <= 3:
                if not any(w in _FORBUDT or w in hold_ord for w in ord_liste):
                    return kand
    return ""


def _hent_web_dommer(hj, ud):
    hk, uk = _ren_hold(hj), _ren_hold(ud)
    if not hk or not uk:
        return ""
    for q in (f'"{hk}" "{uk}" referee', f"{hk} vs {uk} referee"):
        try:
            u = f"https://duckduckgo.com{urllib.parse.quote(q)}"
            html = requests.get(u, headers=HDR, timeout=4).text
            for blok in re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html, re.S)[:6]:
                if navn := _udtraek_navn(blok, hj, ud):
                    return navn
        except Exception:
            pass
    try:
        u = f"https://google.com{urllib.parse.quote(f'{hk} {uk} referee')}&hl=en&gl=US&ceid=US:en"
        root = ET.fromstring(requests.get(u, headers=HDR, timeout=4).text)
        for item in root.findall(".//item")[:6]:
            samlet = f"{item.findtext('title') or ''} {item.findtext('description') or ''}"
            if (hk in samlet.lower() or uk in samlet.lower()):
                if navn := _udtraek_navn(samlet, hj, ud):
                    return navn
    except Exception:
        pass
    return ""


def _hent_espn_dommer(hj, ud, ev_id="", slug=""):
    try:
        hk, uk = _ren_hold(hj), _ren_hold(ud)
        if ev_id and slug and slug != "all":
            sm = requests.get(f"https://espn.com{slug}/summary", params={"event": ev_id}, headers=HDR, timeout=3).json()
            for off in ((sm.get("gameInfo") or {}).get("officials") or []):
                if n := str(off.get("displayName") or off.get("fullName") or "").strip():
                    return n
        nu = datetime.date.today()
        dato_sp = f"{(nu - datetime.timedelta(days=1)).strftime('%Y%m%d')}-{(nu + datetime.timedelta(days=2)).strftime('%Y%m%d')}"
        for s_try in list(dict.fromkeys([s for s in (slug, "ita.1", "eng.1", "eng.2", "esp.1", "ger.1", "fra.1", "den.1") if s and s != "all"]))[:5]:
            sb = requests.get(f"https://espn.com{s_try}/scoreboard", params={"dates": dato_sp}, headers=HDR, timeout=3).json()
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


def hent_dommer(hj, ud, ev_id="", slug="all", dt_iso="", liga=""):
    key = f"{_ren_hold(hj)}|{_ren_hold(ud)}"
    if key in _DOMMER_CACHE:
        return _DOMMER_CACHE[key]
    fundet = _hent_espn_dommer(hj, ud, ev_id, slug) or _hent_web_dommer(hj, ud)
    if fundet:
        _DOMMER_CACHE[key] = fundet
    return fundet


def dommer_effekt(dommer, liga="", hj="", ud=""):
    dele = []
    eff = 0.0
    if dommer and "ikke" not in str(dommer).lower():
        eff = 1.0
        try:
            from udvidelser.historik_statistik import hent_dommer_profil
            p = hent_dommer_profil(dommer)
            eff = float(p.get("effekt", 1.0))
            dele.append(f"Dommer {dommer} ({p.get('kort_snit', 4.0)} kort/kamp)")
        except Exception:
            dele.append(f"Dommer {dommer} bekræftet")
    if hj and ud:
        try:
            from udvidelser.historik_statistik import hent_h2h_profil
            h2h = hent_h2h_profil(hj, ud)
            if h2h.get("tekst"):
                dele.append(h2h["tekst"])
        except Exception:
            pass
    return eff, " | ".join(dele)
