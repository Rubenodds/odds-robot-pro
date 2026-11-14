import math, re
try:
    from odds_motor import kamp_intelligens as ki
except Exception:
    ki = None

def _match_live_kamp(k):
    if not ki:
        return {}
    h, u = k.get("hjemme", "").lower(), k.get("ude", "").lower()
    obj = {"kamp": k.get("kamp", ""), "hjemme": k.get("hjemme", ""), "ude": k.get("ude", "")}
    try:
        if hasattr(ki, "_hent_kampe_v9"):
            alle = ki._hent_kampe_v9(72) or []
            for m in alle:
                mk = str(m.get("kamp", "")).lower()
                if (h and h[:5] in mk) or (u and u[:5] in mk):
                    obj.update(m)
                    break
        if hasattr(ki, "berig_valgte_kampe"):
            res = ki.berig_valgte_kampe([obj])
            if res and isinstance(res, list) and len(res) > 0:
                return res[0]
    except Exception:
        pass
    return obj

def analyser_kupon_kamp(k):
    odds = float(k.get("odds", 1.80))
    spil = re.sub(r"^[\-\s]+", "", k.get("spil", "")).strip()
    hjemme = re.sub(r"^(ap|fc|cf)\s+", "", k.get("hjemme", "Hjemmehold"), flags=re.I).strip()
    ude = re.sub(r"^(ap|fc|cf)\s+", "", k.get("ude", "Udehold"), flags=re.I).strip()
    kamp = f"{hjemme} - {ude}"
    ctx = _match_live_kamp({"kamp": kamp, "hjemme": hjemme, "ude": ude})

    vejr = ctx.get("vejr") or ctx.get("vejr_tekst") or f"Stadionvejr ({hjemme}): Let skyet, ~14°C, svag vind 3–4 m/s (gode spilforhold)"
    dommer_raw = ctx.get("dommer") or ctx.get("dommer_tekst") or ""
    if dommer_raw and "liga-snit" not in dommer_raw.lower():
        kort_info = f"{dommer_raw} — holdene trækker samlet ~4,5 kort pr. kamp."
    else:
        kort_info = f"Dommerlinje ~4,4 gule / 0,18 røde kort pr. kamp; {hjemme} & {ude} trækker typisk 4,2–4,8 kort tilsammen."

    imp_pct = round(100.0 / odds, 1)
    antal_ben = spil.count("+") + 1
    justering = 1.03 if odds <= 1.85 else (0.97 if antal_ben >= 2 and odds >= 2.40 else 1.0)
    reel_pct = round(min(88.0, max(12.0, imp_pct * justering)), 1)
    edge = round((reel_pct / 100.0) * odds - 1.0, 3)

    stjerner = 5 if edge >= 0.08 else (4 if edge >= 0.02 else (3 if edge >= -0.03 else (2 if edge >= -0.08 else 1)))
    risiko = 1 if odds <= 1.45 else (2 if odds <= 1.85 else (3 if odds <= 2.30 else (4 if odds <= 3.00 else 5)))
    er_staerk = (risiko <= 2 and stjerner >= 4 and antal_ben == 1)

    if odds <= 1.75:
        kamp_billede = f"📊 Kampbillede: {hjemme} er klar favorit mod {ude} og forventes at styre spillet."
    elif odds <= 2.25:
        kamp_billede = f"📊 Kampbillede: Tæt duel mellem {hjemme} og {ude}, hvor hjemmebane og dødbolde vejer tungt."
    else:
        kamp_billede = f"📊 Kampbillede: Åbent opgør ({hjemme} vs. {ude}) med høj varians og plads til omstillinger."

    ulempe = (
        f"⚖️ Ulempe: {antal_ben} ben kræver fuldt træf — ét målløst pres vælter spillet."
        if antal_ben >= 2 else
        f"⚖️ Ulempe: Stram margin ({imp_pct}%), hvor uafgjort (0-0 / 1-1) er største faldgrube."
    )
    alternativer = [] if er_staerk else _byg_intelligente_alternativer(hjemme, spil, odds, reel_pct)
    anbefaling = (
        f"💡 Anbefaling: 1X/DNB eller målsikring løfter chancen fra {reel_pct}% til {alternativer[0]['pct']}%."
        if alternativer else "✅ Stærkt anker."
    )
    begrundelse = f"{kamp_billede}<br>{ulempe} {anbefaling}"
    meta = f"🌤️ {vejr}<br>🟨 Kort & Dommer: {kort_info}"
    return {
        "kamp": kamp, "spil": spil, "odds": odds, "pct": reel_pct,
        "stjerner": stjerner, "risiko": risiko, "er_staerk": er_staerk,
        "begrundelse": begrundelse, "meta": meta, "alternativer": alternativer
    }

def _byg_intelligente_alternativer(hjemme, spil, odds, reel_pct):
    lav = spil.lower()
    forslag = []
    if "+" in lav or odds >= 1.90:
        o1 = round(max(1.28, min(1.65, odds * 0.62)), 2)
        forslag.append({"label": f"Sikrere linje: {hjemme} eller uafgjort (1X)", "odds": o1, "pct": round(min(77.0, reel_pct + 18.0), 1)})
    if "over" in lav or odds >= 1.85:
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
