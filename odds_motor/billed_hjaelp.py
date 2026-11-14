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
    hjemme = k.get("hjemme", "Hjemmehold")
    ude = k.get("ude", "Udehold")
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
    er_staerk = (risiko <= 2 and stjerner >= 4 and antal_ben == 1)

    if antal_ben >= 2:
        ulempe = f"Ulempe: Kombinationsspil ({antal_ben} ben) kræver at alt klapper — ét målløst halvlegspres eller 1-0 resultat vælter hele væddemålet."
    elif odds >= 2.35:
        ulempe = f"Ulempe: Højt odds ({odds:.2f}) giver kun {reel_pct}% teoretisk træfchance, og et tidligt føringsmål til {ude} gør spillet meget sårbart."
    elif odds >= 1.85:
        ulempe = f"Ulempe: Tæt opgør (markedet giver kun {imp_pct}%), hvor uafgjort (0-0 / 1-1) er den største faldgrube for {hjemme}."
    else:
        ulempe = f"Ulempe: Lav odds-margin ({odds:.2f}) giver begrænset betaling i forhold til risikoen ved rødt kort eller sene udsving."

    if er_staerk:
        begrundelse = f"{ulempe} ✅ Samlet vurdering: Alligevel et stærkt anker med god balance mellem risiko og betaling."
        alternativer = []
    else:
        alternativer = _byg_intelligente_alternativer(k, odds, reel_pct)
        anbefaling = (
            f"💡 Hvorfor alternativer: Ved at sikre mod uafgjort (1X/DNB) eller flytte fokus til kampens måltotal "
            f"løfter du træfsikkerheden fra {reel_pct}% til ca. {alternativer[0]['pct']}%."
            if alternativer else ""
        )
        extra = f" ({form_tekst})" if form_tekst else ""
        begrundelse = f"{ulempe}{extra} {anbefaling}".strip()

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
    if "+" in spil or odds >= 1.90:
        o1 = round(max(1.28, min(1.65, odds * 0.62)), 2)
        forslag.append({"label": f"Sikrere linje: {hjemme} eller uafgjort (1X)", "odds": o1, "pct": round(min(77.0, reel_pct + 18.0), 1)})
    if "over" in spil or odds >= 1.85:
        o2 = round(max(1.25, min(1.56, odds * 0.58)), 2)
        forslag.append({"label": "Målsikring: Over 1.5 mål i kampen", "odds": o2, "pct": round(min(80.0, reel_pct + 21.0), 1)})
    if odds >= 2.05:
        o3 = round(max(1.50, min(2.15, odds * 0.78)), 2)
        forslag.append({"label": f"DNB-sikring: {hjemme} (indsats retur ved X)", "odds": o3, "pct": round(min(68.0, reel_pct + 11.0), 1)})
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
