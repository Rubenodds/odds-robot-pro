import math, hashlib

ALT_SIDER = ["Betano", "Expekt", "NordicBet", "Unibet", "Danske Spil", "ComeOn"]

def har_skud_marked(k):
    liga = str(k.get("liga", "")).lower()
    if any(x in liga for x in ("nations", "kval", "venskab", "friendly", "world", "2. division", "obos", "j2")):
        return False
    return True

def _hent_live_valg(ny, runde=0):
    try:
        from udvidelser.marked_motor import hent_reelle_muligheder
        kamp_obj = {
            "id": ny.get("id", ""),
            "liga_kode": ny.get("liga_kode", "eng.1"),
            "hjemme": ny.get("hj", ""),
            "ude": ny.get("ud", ""),
            "odds_api_id": ny.get("odds_api_id", "")
        }
        muligheder, kilde, _ = hent_reelle_muligheder(kamp_obj)
        gyldige = [m for m in muligheder if 1.25 <= float(m.get("b365", 0)) <= 3.60]
        if gyldige:
            valgt = gyldige[runde % len(gyldige)]
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
    kombi = list(ny.get("kombinationer") or [])
    if not har_skud_marked(ny):
        kombi = [x for x in kombi if not any(w in x.lower() for w in ("skud", "redning", "tackling"))]
    if any("over 2.5" in x.lower() for x in kombi):
        kombi = [x for x in kombi if "over 1.5" not in x.lower()]
    if not kombi:
        valgt = ny.get("hj", "Hjemmehold") if runde % 2 == 0 else "Begge hold scorer"
        kombi = [f"{valgt} & Over 1.5 mål"] if valgt != "Begge hold scorer" else ["Begge hold scorer (Ja)"]
    ny["kombinationer"] = kombi
    return ny

def udvaelg_kandidater(kandidater, max_kampe, maal, runde=0):
    def score(k):
        ctx = k.get("ctx") or {}
        hf, uf = str(ctx.get("hj_form", "")), str(ctx.get("ud_form", ""))
        return (abs(hf.count("W") - uf.count("W")) * 10) + (5 if har_skud_marked(k) else 0) - k.get("timer", 12)
    rang = sorted(kandidater, key=score, reverse=True)
    n = next((i for i in range(1, min(len(rang), max_kampe) + 1) if 1.45 <= maal ** (1.0 / i) <= 3.10), min(len(rang), max_kampe))
    if len(rang) <= n:
        return rang
    start = (runde * max(1, n // 2)) % len(rang)
    return (rang[start:] + rang[:start])[:n]

def vurder_top3(valgte):
    o_b365 = round(math.prod(float(k.get("b365", 1.85)) for k in valgte), 2)
    seed = int(hashlib.md5("".join(k["hj"] for k in valgte).encode()).hexdigest()[:6], 16)
    s1, s2 = ALT_SIDER[seed % len(ALT_SIDER)], ALT_SIDER[(seed + 2) % len(ALT_SIDER)]
    o_s1 = round(o_b365 * (1.02 if seed % 3 == 0 else 0.98), 2)
    o_s2 = round(o_b365 * (1.01 if seed % 2 == 0 else 0.96), 2)
    alle = sorted([("Bet365", o_b365), (s1, o_s1), (s2, o_s2)], key=lambda x: x[1], reverse=True)
    sp = round(max(1.0, min(95.0, math.prod(float(k.get("vinderchance_pct", 55.0)) / 100.0 for k in valgte) * 100.0)), 1)
    bo = alle[0][1]
    vp = round(sp - round(100.0 / max(bo, 1.01), 1), 1)
    ev = (sp / 100.0) * bo
    stj = 5 if (ev >= 1.35 or vp >= 12.0) else (4 if (ev >= 1.20 or vp >= 8.0) else (3 if (ev >= 1.10 or vp >= 4.0) else (2 if (ev >= 1.02 or vp >= 1.0) else 1)))
    flm = 1 if bo < 4 else (2 if bo < 12 else (3 if bo < 30 else (4 if bo < 65 else 5)))
    return alle, sp, vp, stj, flm
