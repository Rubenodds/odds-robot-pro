import io
import re
import requests
from PIL import Image, ImageOps, ImageStat
from odds_motor import kamp_intelligens

def _h(*parts):
    return ".".join(parts)

OCR_URL = f"https://{_h('api', 'ocr', 'space')}/parse/image"

def klargoer_billede(b_data):
    img = Image.open(io.BytesIO(b_data)).convert("L")
    if ImageStat.Stat(img).mean[0] < 128:
        img = ImageOps.invert(img)
    if img.width > 1000:
        img = img.resize((1000, int(img.height * (1000 / float(img.width)))))
    img = ImageOps.autocontrast(img)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def aflaes_via_cloud_ocr(ren_bytes):
    try:
        r = requests.post(OCR_URL, files={"file": ("kupon.png", ren_bytes, "image/png")}, data={"apikey": "helloworld", "language": "eng", "OCREngine": "2"}, timeout=15).json()
        parsed = r.get("ParsedResults") or []
        txt = "\n".join(p.get("ParsedText", "") for p in parsed)
        linjer = [l.strip() for l in txt.splitlines() if l.strip()]
        return (linjer, "") if linjer else ([], str(r.get("ErrorMessage") or "Ingen tekst fundet"))
    except Exception as e:
        return [], str(e)

def udtraek_kupon_liste(linjer):
    kampe, odds_liste, indsats = [], [], 100.0
    kamp_re = re.compile(r"([A-Za-zÆØÅæøå0-9\.\-\s]{2,28})\s+(?:-|–|vs\.?|v)\s+([A-Za-zÆØÅæøå0-9\.\-\s]{2,28})", re.I)
    odds_re = re.compile(r"\b(\d{1,3}[.,]\d{2})\b")
    dato_re = re.compile(r"^(?:man|tir|ons|tor|fre|lør|søn|mon|tue|wed|thu|fri|sat|sun|\d{1,2}[:.]\d{2}|\d{1,2}\s+[a-zæøå]{3})", re.I)
    spil_ord = ("over", "under", "mål", "hjørne", "skud", "kort", "resultat", "begge hold", "handicap", "dobbelt", "1x", "x2", "12")
    stop = ("indsats", "gevinst", "udbetaling", "total", "samlet", "kupon", "odds", "tidlig", "byg væddemål", "sport", "live", "væddemål", "casino", "share", "kr.", "udehold", "hjemmehold", "antal")
    hold, spil_linjer = [], []

    for i, l in enumerate(linjer):
        low = l.lower()
        if "indsats" in low and i + 1 < len(linjer):
            m_next = re.search(r"(\d+(?:[.,]\d{1,2})?)", linjer[i + 1])
            if m_next: indsats = float(m_next.group(1).replace(",", "."))
        if "kr" not in low:
            for m_o in odds_re.findall(l):
                t = float(m_o.replace(",", "."))
                if 1.05 <= t <= 250.0: odds_liste.append(t)
        if any(w in low for w in spil_ord) and not any(s in low for s in ("fuldtid - resultat", "total antal")):
            spil_linjer.append(l)
        elif kamp_re.search(l) and not any(w in low for w in stop) and not low.startswith("f -"):
            m_k = kamp_re.search(l)
            kampe.append({"kamp": f"{m_k.group(1).strip()} - {m_k.group(2).strip()}", "spil": "1X2 / Resultat", "odds": 1.85})
        elif 3 <= len(l) <= 28 and not dato_re.match(l) and not any(w in low for w in stop) and not re.match(r"^[\d.,\s]+$", l) and ":" not in l:
            if l not in hold: hold.append(l)

    if not kampe and len(hold) >= 2:
        for i in range(0, len(hold) - 1, 2):
            kampe.append({"kamp": f"{hold[i]} - {hold[i+1]}", "spil": "1X2 / Resultat", "odds": 1.85})
    for idx, k in enumerate(kampe):
        if idx < len(spil_linjer): k["spil"] = spil_linjer[idx]
        if idx < len(odds_liste): k["odds"] = odds_liste[idx]
    samlet = round(eval("*".join(str(k["odds"]) for k in kampe)), 2) if kampe else 2.00
    return kampe, samlet, indsats

def analyser_enkelt_kamp(kamp_str, spil_str, odds_val):
    dele = re.split(r"\s+(?:-|–|vs\.?|v)\s+", kamp_str, maxsplit=1, flags=re.I)
    hj, ud = dele[0].strip(), (dele[1].strip() if len(dele) > 1 else "")
    beriget = kamp_intelligens.berig_valgte_kampe([{"hj": hj, "ud": ud, "ctx": {"by": hj}}])
    ctx = (beriget[0].get("ctx") or {}) if beriget else {}
    just = ctx.get("justering_pct", 0.0)
    pct = round(max(8.0, min(92.0, (100.0 / max(1.01, odds_val)) * 0.94 - (just * 0.6))), 1)
    stj = max(1, min(5, int(round((pct * odds_val) / 21.0))))
    flm = max(1, min(5, int(round((100.0 - pct) / 17.0))))
    v = ctx.get("vejr")
    v_txt = f"{v['temp']}°C, {v['vind']} m/s ({v['effekt']})" if v else "Vejr afventer"
    analyse = f"Spil: {spil_str} | Dommer: {ctx.get('dommer', 'Ukendt')} | Vejr: {v_txt}. " + ("Høj risiko på denne linje – lavere linje anbefales." if flm >= 4 else "God matematisk balance i denne kamp.")
    forslag = f"{kamp_str} (Sikker linje: Dobbeltchance 1X / Over 1.5 mål)" if flm >= 4 or stj <= 2 else f"{kamp_str} (Hold fast i: {spil_str})"
    return {"pct": pct, "stj": stj, "flm": flm, "analyse": analyse, "forslag": forslag}
