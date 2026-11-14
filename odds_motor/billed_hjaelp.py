import datetime, math, re, requests

BY_MAP = {"mallorca": "Palma", "sheff wed": "Sheffield", "sheff utd": "Sheffield", "man utd": "Manchester", "man city": "Manchester", "wolves": "Wolverhampton", "west ham": "London", "arsenal": "London", "chelsea": "London", "tottenham": "London", "real oviedo": "Oviedo", "real madrid": "Madrid", "atletico": "Madrid", "betis": "Sevilla"}
LIGAER = ["esp.1", "esp.2", "eng.1", "eng.2", "eng.3", "ger.1", "ger.2", "ita.1", "ita.2", "fra.1", "den.1", "uefa.champions"]

def _rens_holdnavn(navn):
    t = re.sub(r"^[^a-zA-ZæøåÆØÅ]+", "", str(navn)).strip()
    t = re.sub(r"^(ap|fc|cf)\s+", "", t, flags=re.I).strip()
    return t or "Hold"

def _hent_live_vejr(klub):
    by = BY_MAP.get(klub.lower(), klub)
    try:
        g = requests.get(f"https://open-meteo.com{by}&count=1&language=da", timeout=3).json()
        res = g.get("results") or []
        if res:
            lat, lon = res["latitude"], res["longitude"]
            w = requests.get(f"https://open-meteo.com{lat}&longitude={lon}&current=temperature_2m,wind_speed_10m&wind_speed_unit=ms", timeout=3).json()
            cur = w.get("current") or {}
            if cur.get("temperature_2m") is not None:
                return f"Stadionvejr ({by}): {cur['temperature_2m']}°C, vind {cur['wind_speed_10m']} m/s"
    except Exception:
        pass
    return ""

def _hent_historik_kort_og_dommer(hjemme, ude):
    nu = datetime.date.today()
    dato_sp = f"{(nu - datetime.timedelta(days=14)).strftime('%Y%m%d')}-{(nu + datetime.timedelta(days=3)).strftime('%Y%m%d')}"
    h_kort, u_kort, dommer = [], [], ""
    for lg in LIGAER:
        try:
            url = f"https://espn.com{lg}/scoreboard?dates={dato_sp}"
            for ev in (requests.get(url, timeout=3).json().get("events") or []):
                comps = ev.get("competitions") or []
                if not comps:
                    continue
                comp = comps
                teams = comp.get("competitors") or []
                navne = [t.get("team", {}).get("displayName", "").lower() for t in teams]
                if any(hjemme.lower()[:5] in n for n in navne) and any(ude.lower()[:5] in n for n in navne):
                    offs = comp.get("officials") or []
                    if offs:
                        dommer = offs.get("displayName", "")
                for t in teams:
                    tn = t.get("team", {}).get("displayName", "").lower()
                    stats = {s.get("name"): s.get("displayValue") for s in (t.get("statistics") or [])}
                    if stats.get("yellowCards") is not None:
                        val = float(stats["yellowCards"]) + float(stats.get("redCards") or 0)
                        if hjemme.lower()[:5] in tn:
                            h_kort.append(val)
                        elif ude.lower()[:5] in tn:
                            u_kort.append(val)
        except Exception:
            continue
    h_snit = round(sum(h_kort) / len(h_kort), 1) if h_kort else None
    u_snit = round(sum(u_kort) / len(u_kort), 1) if u_kort else None
    return h_snit, u_snit, dommer

def analyser_kupon_kamp(k):
    odds = float(k.get("odds", 1.80))
    spil = re.sub(r"^[\-\s]+", "", k.get("spil", "")).strip()
    hjemme = _rens_holdnavn(k.get("hjemme", "Hjemmehold"))
    ude = _rens_holdnavn(k.get("ude", "Udehold"))
    kamp = f"{hjemme} - {ude}"

    vejr = _hent_live_vejr(hjemme)
    vejr_txt = f"🌤️ {vejr}" if vejr else f"🌤️ Stadionvejr ({hjemme}): Ikke tilgængeligt for lokation"

    h_snit, u_snit, dommer = _hent_historik_kort_og_dommer(hjemme, ude)
    d_del = f"Dommer: <b>{dommer}</b> | " if dommer else "Dommer: Ikke offentliggjort | "
    if h_snit is not None or u_snit is not None:
        tot = f" (samlet ~{round((h_snit or 0) + (u_snit or 0), 1)}/kamp)" if (h_snit is not None and u_snit is not None) else ""
        kort_txt = f"🟨 {d_del}Historisk kortsnit: {hjemme} {h_snit if h_snit is not None else '?'}/kamp & {ude} {u_snit if u_snit is not None else '?'}/kamp{tot}"
    else:
        kort_txt = f"🟨 {d_del}Ingen nylig kort-historik fundet i ESPN for {hjemme} / {ude}"

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
        f"💡 Anbefaling: 1X/DNB eller målsikring løfter chancen fra {reel_pct}% til {alternativer['pct']}%."
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
