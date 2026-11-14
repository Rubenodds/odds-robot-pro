import math, re, requests

def _rens_holdnavn(navn):
    t = re.sub(r"^[^a-zA-ZæøåÆØÅ]+", "", str(navn)).strip()
    t = re.sub(r"^(ap|fc|cf)\s+", "", t, flags=re.I).strip()
    return t or "Hold"

def _hent_live_vejr(by_navn):
    try:
        g = requests.get(f"https://open-meteo.com{by_navn}&count=1&language=da", timeout=4).json()
        res = g.get("results") or []
        if res:
            lat, lon = res[0]["latitude"], res[0]["longitude"]
            w = requests.get(f"https://open-meteo.com{lat}&longitude={lon}&current=temperature_2m,wind_speed_10m&wind_speed_unit=ms", timeout=4).json()
            cur = w.get("current") or {}
            temp, vind = cur.get("temperature_2m"), cur.get("wind_speed_10m")
            if temp is not None and vind is not None:
                return f"Stadionvejr ({by_navn}): {temp}°C, vind {vind} m/s"
    except Exception:
        pass
    return ""

def _hent_espn_kort_og_dommer(hjemme, ude):
    ligaer = ["esp.1", "esp.2", "eng.1", "eng.2", "eng.3", "ger.1", "ita.1", "fra.1", "den.1", "uefa.champions"]
    h_kort, u_kort, dommer = None, None, ""
    for lg in ligaer:
        try:
            url = f"https://espn.com{lg}/scoreboard"
            data = requests.get(url, timeout=3).json()
            for ev in data.get("events") or []:
                comps = ev.get("competitions") or []
                if not comps:
                    continue
                comp = comps[0]
                teams = comp.get("competitors") or []
                navne = [t.get("team", {}).get("displayName", "").lower() for t in teams]
                if any(hjemme.lower()[:5] in n for n in navne) or any(ude.lower()[:5] in n for n in navne):
                    offs = comp.get("officials") or []
                    if offs:
                        dommer = offs[0].get("displayName", "")
                    for t in teams:
                        t_navn = t.get("team", {}).get("displayName", "")
                        stats = {s.get("name"): s.get("displayValue") for s in (t.get("statistics") or [])}
                        yc = stats.get("yellowCards")
                        if yc and hjemme.lower()[:5] in t_navn.lower():
                            h_kort = yc
                        elif yc and ude.lower()[:5] in t_navn.lower():
                            u_kort = yc
                    if dommer or h_kort or u_kort:
                        return h_kort, u_kort, dommer
        except Exception:
            continue
    return h_kort, u_kort, dommer

def analyser_kupon_kamp(k):
    odds = float(k.get("odds", 1.80))
    spil = re.sub(r"^[\-\s]+", "", k.get("spil", "")).strip()
    hjemme = _rens_holdnavn(k.get("hjemme", "Hjemmehold"))
    ude = _rens_holdnavn(k.get("ude", "Udehold"))
    kamp = f"{hjemme} - {ude}"

    vejr = _hent_live_vejr(hjemme)
    vejr_txt = f"🌤️ {vejr}" if vejr else f"🌤️ Stadionvejr ({hjemme}): Ingen live-måling fundet for bynavn"

    h_kort, u_kort, dommer = _hent_espn_kort_og_dommer(hjemme, ude)
    d_del = f"Dommer: <b>{dommer}</b> | " if dommer else "Dommer: Afventer offentliggørelse | "
    if h_kort or u_kort:
        kort_txt = f"🟨 {d_del}Kort i seneste kampdata: {hjemme} ({h_kort or '?'}) & {ude} ({u_kort or '?'})"
    else:
        kort_txt = f"🟨 {d_del}Ingen offentliggjort kortstatistik i live-feed for {hjemme} vs. {ude} endnu"

    imp_pct = round(100.0 / odds, 1)
    antal_ben = spil.count("+") + 1
    justering = 1.03 if odds <= 1.85 else (0.97 if antal_ben >= 2 and odds >= 2.40 else 1.0)
    reel_pct = round(min(88.0, max(12.0, imp_pct * justering)), 1)
    edge = round((reel_pct / 100.0) * odds - 1.0, 3)

    stjerner = 5 if edge >= 0.08 else (4 if edge >= 0.02 else (3 if edge >= -0.03 else (2 if edge >= -0.08 else 1)))
    risiko = 1 if odds <= 1.45 else (2 if odds <= 1.85 else (3 if odds <= 2.30 else (4 if odds <= 3.00 else 5)))
    er_staerk = (risiko <= 2 and stjerner >= 4 and antal_ben == 1)

    kamp_billede = (
        f"📊 Kampbillede: {hjemme} er klar favorit mod {ude}." if odds <= 1.75 else
        f"📊 Kampbillede: Tæt duel mellem {hjemme} og {ude}, hvor hjemmebane og dødbolde vejer tungt." if odds <= 2.25 else
        f"📊 Kampbillede: Åbent opgør ({hjemme} vs. {ude}) med høj varians."
    )
    ulempe = (
        f"⚖️ Ulempe: {antal_ben} ben kræver fuldt træf — ét målløst pres vælter spillet." if antal_ben >= 2 else
        f"⚖️ Ulempe: Stram margin ({imp_pct}%), hvor uafgjort (0-0 / 1-1) er største faldgrube."
    )
    alternativer = [] if er_staerk else _byg_intelligente_alternativer(hjemme, spil, odds, reel_pct)
    anbefaling = (
        f"💡 Anbefaling: 1X/DNB eller målsikring løfter chancen fra {reel_pct}% til {alternativer[0]['pct']}%."
        if alternativer else "✅ Stærkt anker."
    )
    return {
        "kamp": kamp, "spil": spil, "odds": odds, "pct": reel_pct,
        "stjerner": stjerner, "risiko": risiko, "er_staerk": er_staerk,
        "begrundelse": f"{kamp_billede}<br>{ulempe} {anbefaling}",
        "meta": f"{vejr_txt}<br>{kort_txt}", "alternativer": alternativer
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
