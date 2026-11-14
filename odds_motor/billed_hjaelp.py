import math, re
try:
    from odds_motor import kamp_intelligens as ki
except Exception:
    ki = None
try:
    from odds_motor import dommer_intelligens as di
except Exception:
    di = None

def _rens_holdnavn(navn):
    t = re.sub(r"^[^a-zA-ZæøåÆØÅ]+", "", str(navn)).strip()
    t = re.sub(r"^(ap|fc|cf)\s+", "", t, flags=re.I).strip()
    return t or "Hold"

def _match_live_kamp(k):
    h, u = k.get("hjemme", "").lower(), k.get("ude", "").lower()
    obj = {"kamp": k.get("kamp", ""), "hjemme": k.get("hjemme", ""), "ude": k.get("ude", "")}
    if ki:
        try:
            for timer in (48, 120):
                if hasattr(ki, "_hent_kampe_v9"):
                    alle = ki._hent_kampe_v9(timer) or []
                    for m in alle:
                        mk = str(m.get("kamp", "")).lower()
                        if (len(h) >= 4 and h[:5] in mk) or (len(u) >= 4 and u[:5] in mk):
                            obj.update(m)
                            break
                if obj.get("event_id") or obj.get("id"):
                    break
            if hasattr(ki, "berig_valgte_kampe"):
                res = ki.berig_valgte_kampe([obj])
                if res and isinstance(res, list) and len(res) > 0:
                    obj.update(res[0])
        except Exception:
            pass
    if di:
        for fn in ("hent_dommer_info", "hent_kort_profil"):
            if hasattr(di, fn):
                try:
                    obj.update(getattr(di, fn)(obj) or {})
                except Exception:
                    pass
    return obj

def analyser_kupon_kamp(k):
    odds = float(k.get("odds", 1.80))
    spil = re.sub(r"^[\-\s]+", "", k.get("spil", "")).strip()
    hjemme = _rens_holdnavn(k.get("hjemme", "Hjemmehold"))
    ude = _rens_holdnavn(k.get("ude", "Udehold"))
    kamp = f"{hjemme} - {ude}"
    ctx = _match_live_kamp({"kamp": kamp, "hjemme": hjemme, "ude": ude})

    vejr = ctx.get("vejr") or ctx.get("vejr_tekst") or ctx.get("vejr_info")
    vejr_txt = f"🌤️ {vejr}" if vejr else f"🌤️ Stadionvejr ({hjemme}): Afventer live kickoff-data"

    d_navn = ctx.get("dommer_navn") or ctx.get("dommer") or ""
    gule = ctx.get("gule_snit") or ctx.get("kort_snit")
    roede = ctx.get("roede_snit")
    h2h_kort = ctx.get("h2h_kort") or ctx.get("hold_kort_snit") or ctx.get("kort_tekst")

    d_del = ""
    if d_navn:
        r_del = f" / {roede} røde" if roede is not None else ""
        k_del = f" (snitter {gule} gule{r_del}/kamp)" if gule else ""
        d_del = f"Dommer: <b>{d_navn}</b>{k_del}"
    h2h_del = (
        f"Indbyrdes & holdkort: {h2h_kort}" if h2h_kort
        else f"Indbyrdes & holdkort ({hjemme} vs. {ude}): Hentes fra H2H/liga-kortdata"
    )
    kort_txt = f"🟨 {d_del} | {h2h_del}" if d_del else f"🟨 {h2h_del}"

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
    meta = f"{vejr_txt}<br>{kort_txt}"
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
