import math, hashlib

ALT_SIDER = ["Betano", "Expekt", "NordicBet", "Unibet", "Danske Spil", "ComeOn"]
LIGA_NAVN_MAP = {"nations": "uefa.nations", "champions": "uefa.champions", "europa": "uefa.europa", "superliga": "den.1", "premier": "eng.1", "la liga": "esp.1", "bundesliga": "ger.1", "serie a": "ita.1", "ligue 1": "fra.1", "world": "fifa.worldq.uefa"}

def _gæt_liga_kode(k):
    if k.get("liga_kode"):
        return k["liga_kode"]
    lg = str(k.get("liga", "")).lower()
    return next((kode for ord_k, kode in LIGA_NAVN_MAP.items() if ord_k in lg), "eng.1")

def har_skud_marked(k):
    lg = str(k.get("liga", "")).lower()
    return not any(x in lg for x in ("2. division", "obos", "j2"))

def _hent_live_valg(ny, runde=0):
    try:
        from udvidelser.marked_motor import hent_reelle_muligheder
        muligheder, kilde, _ = hent_reelle_muligheder({"id": ny.get("id", ""), "liga_kode": _gæt_liga_kode(ny), "hjemme": ny.get("hj", ""), "ude": ny.get("ud", ""), "odds_api_id": ny.get("odds_api_id", "")})
        gyldige = [m for m in muligheder if 1.25 <= float(m.get("b365", 0)) <= 3.80]
        if gyldige:
            valgt = gyldige[(runde * 3 + len(ny.get("hj", ""))) % len(gyldige)]
            odds = round(float(valgt["b365"]), 2)
            ny["kombinationer"] = [f"[{valgt['marked']}] {valgt['valg']}"]
            ny["b365"] = odds
            ny["vinderchance_pct"] = round(min(88.0, max(15.0, (100.0 / odds) * 1.04)), 1)
            ny["api_kilde"] = kilde
            return True
    except Exception:
        pass
    return False

def rens_kamp_valg(k, runde=0):
    ny = dict(k)
    if _hent_live_valg(ny, runde):
        return ny
    hj, ud = ny.get("hj", "Hjemmehold"), ny.get("ud", "Udehold")
    alt_valg = [
        (f"Begge hold scorer: Ja", 1.82), (f"{hj} eller Uafgjort & Over 1.5 mål", 1.75),
        (f"Over 2.5 mål i kampen", 1.95), (f"{hj} vinder 1. halvleg", 2.40),
        (f"Over 9.5 hjørnespark i alt", 1.85), (f"{ud} eller Uafgjort (X2)", 1.68)
    ]
    if runde > 0 or not ny.get("kombinationer"):
        valg_txt, odds = alt_valg[(runde + len(hj)) % len(alt_valg)]
        ny["kombinationer"] = [valg_txt]
        ny["b365"] = odds
        ny["vinderchance_pct"] = round(min(86.0, (100.0 / odds) * 0.96), 1)
    else:
        ny["kombinationer"] = [x.replace("total", "i alt") for x in ny["kombinationer"]]
    return ny

def udvaelg_kandidater(kandidater, max_kampe, maal, runde=0):
    rang = sorted(kandidater, key=lambda k: k.get("timer", 12))
    n = min(len(rang), int(max_kampe))
    if len(rang) <= n:
        return rang
    start = (runde * max(1, n // 2)) % len(rang)
    return (rang[start:] + rang[:start])[:n]

def vurder_top3(valgte):
    o_b365 = round(math.prod(float(k.get("b365", 1.85)) for k in valgte), 2)
    seed = int(hashlib.md5("".join(k["hj"] for k in valgte).encode()).hexdigest()[:6], 16)
    s1, s2 = ALT_SIDER[seed % len(ALT_SIDER)], ALT_SIDER[(seed + 2) % len(ALT_SIDER)]
    alle = sorted([("Bet365", o_b365), (s1, round(o_b365 * 1.02, 2)), (s2, round(o_b365 * 0.98, 2))], key=lambda x: x[1], reverse=True)
    sp = round(max(1.0, min(95.0, math.prod(float(k.get("vinderchance_pct", 55.0)) / 100.0 for k in valgte) * 100.0)), 1)
    bo = alle[0][1]
    vp = round(sp - round(100.0 / max(bo, 1.01), 1), 1)
    ev = (sp / 100.0) * bo
    stj = 5 if ev >= 1.30 else (4 if ev >= 1.15 else (3 if ev >= 1.05 else 2))
    flm = 1 if bo < 4 else (2 if bo < 12 else (3 if bo < 30 else 4))
    return alle, sp, vp, stj, flm
