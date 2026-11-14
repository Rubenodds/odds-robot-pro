import math
try:
    from odds_motor import kamp_intelligens as ki
except Exception:
    ki = None

def _hent_kontekst(kamp_navn):
    if ki and hasattr(ki, "analyser_enkelt_kamp"):
        try:
            return ki.analyser_enkelt_kamp(kamp_navn) or {}
        except Exception:
            pass
    return {}

def analyser_kupon_kamp(k):
    odds = float(k.get("odds", 1.80))
    spil = k.get("spil", "")
    kamp = k.get("kamp", "")
    ctx = _hent_kontekst(kamp)
    vejr = ctx.get("vejr", "")
    dommer = ctx.get("dommer", "")
    form_tekst = ctx.get("analyse", "")

    imp_pct = round(100.0 / odds, 1)
    antal_ben = spil.count("+") + 1
    justering = 1.03 if odds <= 1.85 else (0.97 if antal_ben >= 2 and odds >= 2.40 else 1.0)
    reel_pct = round(min(88.0, max(12.0, imp_pct * justering)), 1)
    edge = round((reel_pct / 100.0) * odds - 1.0, 3)

    stjerner = 5 if edge >= 0.08 else (4 if edge >= 0.02 else (3 if edge >= -0.03 else (2 if edge >= -0.08 else 1)))
    risiko = 1 if odds <= 1.45 else (2 if odds <= 1.85 else (3 if odds <= 2.30 else (4 if odds <= 3.00 else 5)))

    er_staerk = (risiko <= 3 and stjerner >= 3 and antal_ben <= 2)
    if er_staerk:
        begrundelse = (
            f"Stærkt og velafbalanceret valg på {kamp} (@ {odds:.2f}). "
            f"Implikation på {imp_pct}% matcher markedets sandsynlighed ({reel_pct}%)"
            + (f" — {form_tekst}" if form_tekst else ".")
        )
        alternativer = []
    else:
        aarsag = "flere kombinerede ben øger variansen" if antal_ben >= 2 else "højt odds giver stram træfsikkerhed"
        begrundelse = (
            f"Sårbarhed på {kamp} (@ {odds:.2f}): {aarsag} "
            f"(reel chance ca. {reel_pct}%). Overvej sikkerhed eller enklere linje."
        )
        alternativer = _byg_intelligente_alternativer(k, odds, reel_pct)

    meta = " | ".join([x for x in [vejr, dommer] if x])
    return {
        "kamp": kamp, "spil": spil, "odds": odds, "pct": reel_pct,
        "stjerner": stjerner, "risiko": risiko, "er_staerk": er_staerk,
        "begrundelse": begrundelse, "meta": meta, "alternativer": alternativer
    }

def _byg_intelligente_alternativer(k, odds, reel_pct):
    hjemme = k.get("hjemme", "Hjemmehold")
    spil = k.get("spil", "").lower()
    forslag = []
    if "+" in spil or odds >= 2.25:
        o1 = round(max(1.32, min(1.68, odds * 0.62)), 2)
        forslag.append({"label": f"Sikrere linje: {hjemme} eller uafgjort (1X)", "odds": o1, "pct": round(min(76.0, reel_pct + 18.0), 1)})
    if "over" in spil or odds >= 2.00:
        o2 = round(max(1.28, min(1.58, odds * 0.58)), 2)
        forslag.append({"label": "Målsikring: Over 1.5 mål i kampen", "odds": o2, "pct": round(min(79.0, reel_pct + 21.0), 1)})
    if odds >= 2.50:
        o3 = round(max(1.65, min(2.15, odds * 0.80)), 2)
        forslag.append({"label": f"Ren favorit: {hjemme} DNB (indsats retur ved X)", "odds": o3, "pct": round(min(65.0, reel_pct + 10.0), 1)})
    return forslag[:3]

def samlet_kupon_analyse(analyser, indsats):
    if not analyser:
        return {}
    samlet_odds = math.prod(a["odds"] for a in analyser)
    samlet_pct = round(math.prod(a["pct"] / 100.0 for a in analyser) * 100.0, 1)
    svageste = min(analyser, key=lambda x: x["pct"])
    staerkeste = max(analyser, key=lambda x: x["pct"])
    gevinst = round(indsats * samlet_odds, 2)
    dom = (
        f"Kuponen samler {len(analyser)} kampe til totalodds {samlet_odds:.2f} "
        f"(potentiel udbetaling {gevinst:.2f} kr. ved {indsats:.0f} kr. indsats). "
        f"Samlet matematisk træfsikkerhed er {samlet_pct}%. "
        f"Stærkeste anker er {staerkeste['kamp']} ({staerkeste['pct']}%), mens "
        f"{svageste['kamp']} (@ {svageste['odds']:.2f}) er kuponens største flaskehals."
    )
    return {"odds": round(samlet_odds, 2), "pct": samlet_pct, "gevinst": gevinst, "dom": dom, "svageste": svageste["kamp"]}
