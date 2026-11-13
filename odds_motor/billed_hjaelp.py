import io
import re
from PIL import Image, ImageOps
from odds_motor import kamp_intelligens

def klargoer_billede(b_data):
    img = Image.open(io.BytesIO(b_data)).convert("L")
    if img.width > 1200:
        ratio = 1200 / float(img.width)
        img = img.resize((1200, int(img.height * ratio)))
    img = ImageOps.autocontrast(img)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), img

def parse_ocr_resultat(resultat):
    linjer = []
    for p in (resultat or []):
        txt = str(p if isinstance(p, (list, tuple)) and len(p) >= 2 else p).strip()
        if txt:
            linjer.append(txt)
    return linjer

def udtraek_kupon_liste(linjer):
    kampe, odds_liste, indsats = [], [], 100.0
    kamp_re = re.compile(r"([A-Za-zÆØÅæøå0-9\.\-\s]{2,28})\s+(?:-|–|vs\.?|v)\s+([A-Za-zÆØÅæøå0-9\.\-\s]{2,28})", re.I)
    odds_re = re.compile(r"\b(\d{1,3}[.,]\d{2})\b")
    dato_re = re.compile(r"^(?:man|tir|ons|tor|fre|lør|søn|mon|tue|wed|thu|fri|sat|sun|\d{1,2}[:.]\d{2}|\d{1,2}\s+[a-zæøå]{3})", re.I)
    stop = ("indsats", "gevinst", "udbetaling", "total", "samlet", "kupon", "odds", "fuldtid", "resultat", "tidlig", "byg væddemål", "begge hold", "sport", "live", "væddemål", "casino", "share", "kr.")
    hold_kandidater = []

    for i, l in enumerate(linjer):
        low = l.lower()
        if "indsats" in low and i + 1 < len(linjer):
            m_next = re.search(r"(\d+(?:[.,]\d{1,2})?)", linjer[i + 1])
            if m_next: indsats = float(m_next.group(1).replace(",", "."))
        if "kr" not in low:
            for m_o in odds_re.findall(l):
                t = float(m_o.replace(",", "."))
                if 1.05 <= t <= 250.0: odds_liste.append(t)
        m_k = kamp_re.search(l)
        if m_k and not any(w in low for w in stop):
            kampe.append({"kamp": f"{m_k.group(1).strip()} - {m_k.group(2).strip()}", "spil": "Aflæst udfald", "odds": 1.85})
        elif 3 <= len(l) <= 28 and not dato_re.match(l) and not any(w in low for w in stop) and not re.match(r"^[\d.,\s]+$", l):
            if ":" in l and len(l) > 6: l = l.split(":")[-1].strip()
            if len(l) >= 3 and l not in hold_kandidater: hold_kandidater.append(l)

    if not kampe and len(hold_kandidater) >= 2:
        for i in range(0, len(hold_kandidater) - 1, 2):
            kampe.append({"kamp": f"{hold_kandidater[i]} - {hold_kandidater[i+1]}", "spil": "Aflæst udfald", "odds": 1.85})

    for idx, k in enumerate(kampe):
        if idx < len(odds_liste): k["odds"] = odds_liste[idx]
    samlet = round(eval("*".join(str(k["odds"]) for k in kampe)), 2) if kampe else 2.00
    return kampe, samlet, indsats

def analyser_enkelt_kamp(kamp_str, spil_str, odds_val):
    dele = re.split(r"\s+(?:-|–|vs\.?|v)\s+", kamp_str, maxsplit=1, flags=re.I)
    hj, ud = dele.strip(), (dele.strip() if len(dele) > 1 else "")
    beriget = kamp_intelligens.berig_valgte_kampe([{"hj": hj, "ud": ud, "ctx": {"by": hj}}])
    ctx = (beriget.get("ctx") or {}) if beriget else {}
    just = ctx.get("justering_pct", 0.0)
    pct = round(max(8.0, min(92.0, (100.0 / max(1.01, odds_val)) * 0.94 - (just * 0.6))), 1)
    stj = max(1, min(5, int(round((pct * odds_val) / 21.0))))
    flm = max(1, min(5, int(round((100.0 - pct) / 17.0))))
    v = ctx.get("vejr")
    v_txt = f"{v['temp']}°C, {v['vind']} m/s ({v['effekt']})" if v else "Vejr afventer"
    analyse = f"Dommer: {ctx.get('dommer', 'Ukendt')} | Vejr: {v_txt}. " + ("Høj risiko ved dette odds – lavere linje anbefales." if flm >= 4 else "Solid matematisk balance ud fra kampkontekst.")
    forslag = f"{kamp_str} (Dobbeltchance 1X / Over 1.5 mål)" if flm >= 4 or stj <= 2 else ""
    return {"pct": pct, "stj": stj, "flm": flm, "analyse": analyse, "forslag": forslag}
