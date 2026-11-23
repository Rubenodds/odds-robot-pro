import datetime
import re
import requests

def _h(*p):
    return ".".join(p)

HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0 Safari/537.36"}
ESPN_H = _h("site", "api", "espn", "com")
DDG_H = _h("html", "duckduckgo", "com")
_CACHE = {}
_STOP = {"Stadion", "Stadium", "Runde", "Match", "League", "Live", "Score", "Stats", "Odds", "Preview", "Var", "Assistant", "Fourth", "Official", "Kickoff", "Result", "Highlights", "Danmark", "Italy", "Spain", "Sweden"}


def _ren_tekst(t):
    s = str(t or "").lower()
    for a, b in (("ø", "o"), ("ö", "o"), ("æ", "ae"), ("ä", "a"), ("å", "aa"), ("é", "e"), ("í", "i"), ("á", "a"), ("ó", "o"), ("ú", "u"), ("ü", "u")):
        s = s.replace(a, b)
    return s


def _ren(navn):
    txt = _ren_tekst(navn)
    stop = {"fc", "cf", "ac", "sc", "bk", "if", "fk", "sk", "cd", "ud", "rcd", "afc", "club", "real", "rovers", "united", "city", "fortuna", "is", "ff", "ad"}
    dele = [re.sub(r"[^a-z0-9]", "", w) for w in txt.split()]
    kerne = [w for w in dele if len(w) >= 4 and w not in stop]
    return next(iter(kerne), next((w for w in dele if len(w) >= 3), ""))


def _find_navn(tekst, hj="", ud=""):
    ren = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(tekst or "")))
    hold_ord = set(re.findall(r"[A-Za-zÀ-ž]{3,}", f"{hj} {ud}"))
    for pat in (
        r"(?:Referee|Dommer|Domare|Schiedsrichter|Árbitro\s+principal|Árbitro|Arbitro|Main\s+referee|referee\s+for\s+the\s+match\s+is|referee\s+appointed\s+is)[:\.\s\-]*([A-ZÀ-Ž][a-zà-ž]+(?:\s+[A-ZÀ-Ž][a-zà-ž\.\-']+){1,2})",
        r"([A-ZÀ-Ž][a-zà-ž]+(?:\s+[A-ZÀ-Ž][a-zà-ž\.\-']+){1,2})\s*(?:\((?:Referee|Dommer|Domare|Arbitro)\)|to referee|will referee(?:\s+the\s+match)?|is the referee|named referee|appointed referee|er dommer|dømmer|skal dømme)",
    ):
        for m in re.finditer(pat, ren):
            kand = m.group(1).strip().rstrip(".,;:|")
            ord_l = kand.split()
            if 5 <= len(kand) <= 32 and 2 <= len(ord_l) <= 3 and not any(w in _STOP or w in hold_ord for w in ord_l):
                return kand
    return ""


def _espn_dommer(hj, ud, ev_id="", slug=""):
    try:
        hk, uk = _ren(hj), _ren(ud)
        if ev_id:
            for s_use in dict.fromkeys([s for s in (slug, "all") if s]):
                sm = requests.get(f"https://{ESPN_H}/apis/site/v2/sports/soccer/{s_use}/summary", params={"event": ev_id}, headers=HDR, timeout=3).json()
                for off in ((sm.get("gameInfo") or {}).get("officials") or []):
                    if n := str(off.get("displayName") or off.get("fullName") or "").strip():
                        return n
        nu = datetime.date.today()
        d_sp = f"{(nu - datetime.timedelta(days=1)).strftime('%Y%m%d')}-{(nu + datetime.timedelta(days=2)).strftime('%Y%m%d')}"
        for s_try in ([slug] if slug and slug != "all" else ["den.1", "ita.1", "esp.1", "esp.2", "swe.1", "eng.1", "ger.1", "fra.1"]):
            sb = requests.get(f"https://{ESPN_H}/apis/site/v2/sports/soccer/{s_try}/scoreboard", params={"dates": d_sp}, headers=HDR, timeout=2.5).json()
            for ev in (sb.get("events") or []):
                for comp in (ev.get("competitions") or []):
                    navne = [_ren((t.get("team") or {}).get("displayName") or "") for t in (comp.get("competitors") or [])]
                    if any(hk in n or n in hk for n in navne if n) and any(uk in n or n in uk for n in navne if n):
                        for off in (comp.get("officials") or []):
                            if n := str(off.get("displayName") or off.get("fullName") or "").strip():
                                return n
    except Exception:
        pass
    return ""


def _web_dommer(hj, ud):
    hk, uk = _ren(hj), _ren(ud)
    for q in (f"{hk} {uk} referee", f"{hk} {uk} arbitro", f"{hk} {uk} dommer domare") if (hk and uk) else ():
        try:
            txt = requests.post(f"https://{DDG_H}/html/", data={"q": q}, headers=HDR, timeout=3.5).text
            txt_ren = _ren_tekst(txt)
            if hk in txt_ren and uk in txt_ren and (navn := _find_navn(txt, hj, ud)):
                return navn
        except Exception:
            pass
    return ""


def hent_dommer(hj, ud, ev_id="", slug="all", dt_iso="", liga=""):
    key = f"{_ren(hj)}|{_ren(ud)}"
    if key in _CACHE:
        return _CACHE[key]
    fundet = _espn_dommer(hj, ud, ev_id, slug) or _web_dommer(hj, ud)
    if fundet:
        try:
            from udvidelser.historik_statistik import hent_dommer_profil
            p = hent_dommer_profil(fundet)
            if p and p.get("kort_snit"):
                fundet = f"{fundet} ({p['kort_snit']} kort/kamp)"
        except Exception:
            pass
        _CACHE[key] = fundet
    return fundet


def dommer_effekt(dommer, liga="", hj="", ud=""):
    if not dommer or "ikke" in str(dommer).lower():
        return 0.0, ""
    return 1.0, f"Dommer {dommer} bekræftet"
