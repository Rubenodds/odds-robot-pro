import re
from odds_motor import kamp_intelligens

def parse_ocr_resultat(resultat):
    linjer = []
    for p in (resultat or []):
        txt = str(p[1] if isinstance(p, (list, tuple)) and len(p) >= 2 else p).strip()
        if txt:
            linjer.append(txt)
    return linjer

def udtraek_kupon_liste(linjer):
    kampe, odds_liste, indsats = [], [], 100.0
    kamp_re = re.compile(r"([A-Za-zÆØÅæøå0-9\.\-\s]{2,28})\s+(?:-|–|vs\.?|v)\s+([A-Za-zÆØÅæøå0-9\.\-\s]{2,28})", re.I)
    odds_re = re.compile(r"\b(\d{1,3}[.,]\d{2})\b")
    indsats_re = re.compile(r"(?:indsats|stake|beløb|spillet|kr\.?|dkk)\s*[:\-]?\s*(\d+(?:[.,]\d{1,2})?)", re.I)
    stop = ("indsats", "gevinst", "udbetaling", "total", "samlet", "kupon", "odds", "spillet", "dato", "tid", "live")
    kandidater = []

    for l in linjer:
        m_i = indsats_re.search(l)
        if m_i:
            try:
                v = float(m_i.group(1).replace(",", "."))
                if v > 0:
                    indsats = v
            except ValueError:
                pass
        for m_o in odds_re.findall(l):
            try:
                t = float(m_o.replace(",", "."))
                if 1.01 <= t <= 500.0:
                    odds_liste.append(t)
            except ValueError:
                pass
        m_k = kamp_re.search(l)
        if m_k and not any(w in l.lower() for w in stop):
            kampe.append({"kamp": f"{m_k.group(1).strip()} - {m_k.group(2).strip()}", "spil": "1X2 / Aflæst udfald", "odds": 1.85})
        elif len(l) >= 3 and not any(c.isdigit() for c in l) and not any(w in l.lower() for w in stop):
            kandidater.append(l)

    if not kampe and len(kandidater) >= 2:
        for i in range(0, len(kandidater) - 1, 2):
            kampe.append({"kamp": f"{kandidater[i]} - {kandidater[i+1]}", "spil": "1X2 / Aflæst udfald", "odds": 1.85})

    if kampe and odds_liste:
        enkelt = [o for o in odds_liste if o < max(odds_liste)] or odds_liste
        for idx, k in enumerate(kampe):
            if idx < len(enkelt):
                k["odds"] = enkelt[idx]
    return kampe, (max(odds_liste) if odds_liste else 2.00), indsats

def analyser_enkelt_kamp(kamp_str, spil_str, odds_val):
    dele = re.split(r"\s+(?:-|–|vs\.?|v)\s+", kamp_str, maxsplit=1, flags=re.I)
    hj = dele[0].strip() if dele else kamp_str
    ud = dele[1].strip() if len(dele) > 1 else ""
    beriget = kamp_intelligens.berig_valgte_kampe([{"hj": hj, "ud": ud, "ctx": {"by": hj}}])
    ctx = (beriget[0].get("ctx") or {}) if beriget else {}
    just = ctx.get("justering_pct", 0.0)
    pct = round(max(8.0, min(92.0, (100.0 / max(1.01, odds_val)) * 0.94 - (just * 0.6))), 1)
    stj = max(1, min(5, int(round((pct * odds_val) / 21.0))))
    flm = max(1, min(5, int(round((100.0 - pct) / 17.0))))
    v = ctx.get("vejr")
    v_txt = f"{v['temp']}°C, {v['vind']} m/s ({v['effekt']})" if v else "Vejr afventer"
    analyse = f"Dommer: {ctx.get('dommer', 'Ukendt')} | Vejr: {v_txt}. " + ("Høj risiko ved dette odds – lavere linje anbefales." if flm >= 4 else "Solid matematisk balance ud fra kampkontekst.")
    forslag = f"{kamp_str} (Dobbeltchance 1X / Over 1.5 mål)" if flm >= 4 or stj <= 2 else ""
    return {"pct": pct, "stj": stj, "flm": flm, "analyse": analyse, "forslag": forslag}
