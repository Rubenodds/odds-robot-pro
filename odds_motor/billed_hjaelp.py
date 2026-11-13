import re
from odds_motor import kamp_intelligens

def parse_ocr_resultat(resultat):
    linjer = []
    for p in (resultat or []):
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            txt = str(p[1]).strip()
        else:
            txt = str(p).strip()
        if txt:
            linjer.append(txt)
    return linjer

def udtraek_kupon_moenstre(linjer):
    kampe, odds_liste, indsats = [], [], 100.0
    kamp_re = re.compile(r"([A-Za-zÆØÅæøå0-9\.\-\s]{2,28})\s+(?:-|–|vs\.?|v)\s+([A-Za-zÆØÅæøå0-9\.\-\s]{2,28})", re.I)
    odds_re = re.compile(r"\b(\d{1,3}[.,]\d{2})\b")
    indsats_re = re.compile(r"(?:indsats|stake|beløb|spillet|kr\.?|dkk)\s*[:\-]?\s*(\d+(?:[.,]\d{1,2})?)", re.I)
    stop_ord = ("indsats", "gevinst", "udbetaling", "total", "samlet", "kupon", "odds", "spillet", "dato", "tid", "live")
    kandidater = []

    for linje in linjer:
        m_ind = indsats_re.search(linje)
        if m_ind:
            try:
                val = float(m_ind.group(1).replace(",", "."))
                if val > 0:
                    indsats = val
            except ValueError:
                pass
        for m_o in odds_re.findall(linje):
            try:
                t = float(m_o.replace(",", "."))
                if 1.01 <= t <= 500.0:
                    odds_liste.append(t)
            except ValueError:
                pass
        m_k = kamp_re.search(linje)
        if m_k and not any(w in linje.lower() for w in stop_ord):
            kampe.append(f"{m_k.group(1).strip()} - {m_k.group(2).strip()}")
        elif len(linje) >= 3 and not any(c.isdigit() for c in linje) and not any(w in linje.lower() for w in stop_ord):
            kandidater.append(linje)

    if not kampe and len(kandidater) >= 2:
        for i in range(0, len(kandidater) - 1, 2):
            kampe.append(f"{kandidater[i]} - {kandidater[i+1]}")

    samlet_odds = max(odds_liste) if odds_liste else 2.00
    return ", ".join(dict.fromkeys(kampe)), samlet_odds, indsats

def analyser_kupon_kampe(kampe_tekst, samlet_odds):
    objekter = []
    for del_txt in [x.strip() for x in kampe_tekst.split(",") if x.strip()]:
        ren = re.sub(r"\(.*?\)", "", del_txt).strip()
        dele = re.split(r"\s+(?:-|–|vs\.?|v)\s+", ren, maxsplit=1, flags=re.I)
        hj = dele[0].strip() if dele else ren
        ud = dele[1].strip() if len(dele) > 1 else ""
        objekter.append({"hj": hj, "ud": ud, "ctx": {"by": hj}})
    berigede = kamp_intelligens.berig_valgte_kampe(objekter) if objekter else []
    just_sum = sum(k.get("ctx", {}).get("justering_pct", 0.0) for k in berigede)
    base_pct = max(5.0, min(92.0, (100.0 / max(1.01, samlet_odds)) * 0.94 - (just_sum * 0.5)))
    stjerner = max(1, min(5, int(round((base_pct * samlet_odds) / 22.0))))
    flammer = max(1, min(5, int(round((100.0 - base_pct) / 18.0))))
    return berigede, round(base_pct, 1), stjerner, flammer
