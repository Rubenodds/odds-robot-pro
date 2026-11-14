import io, re
from PIL import Image, ImageOps
try:
    import pytesseract
except Exception:
    pytesseract = None

STOJ = (
    "session", "ansvarsfuldt", "genbrug", "del", "luk væddemål",
    "luk vaddemal", "indsats", "gevinst", "fuldtid", "total antal",
    "byg væddemål", "byg vaddemal", "indskiftning", "kr.", "triple",
    "double", "single", "kupon"
)

def _rens_tekst(linje):
    t = re.sub(r"\b(man|tir|ons|tor|fre|lør|lor|søn|son)\s+\d{1,2}\s+[a-zæøå]{3,4}\b", "", linje, flags=re.I)
    t = re.sub(r"\b\d{1,2}:\d{2}\b", "", t)
    t = re.sub(r"^[o0•\-FijHIl\|\[\]\(\)\s]{1,4}(?=[A-ZÆØÅ])", "", t)
    t = re.sub(r"^[^a-zA-ZæøåÆØÅ0-9]+", "", t).strip()
    return re.sub(r"\s{2,}", " ", t).strip()

def _er_stoj(linje):
    lav = linje.lower().strip()
    if len(lav) < 3:
        return True
    return any(s in lav for s in STOJ)

def udtraek_kupon_fra_billede(billede_bytes):
    if pytesseract is None:
        return [], 100.0, 0.0
    img = Image.open(io.BytesIO(billede_bytes))
    img = ImageOps.grayscale(img)
    w, h = img.size
    if w < 1000:
        img = img.resize((w * 2, h * 2))
    tekst = pytesseract.image_to_string(img, lang="dan+eng")
    return parse_kupon_tekst(tekst)

def parse_kupon_tekst(tekst):
    linjer = [l.strip() for l in tekst.splitlines() if l.strip()]
    indsats, kupon_odds = 100.0, 0.0
    for i, l in enumerate(linjer):
        lav = l.lower()
        if "indsats" in lav and i + 1 < len(linjer):
            m = re.search(r"(\d+[.,]\d{2})", linjer[i + 1])
            if m and float(m.group(1).replace(",", ".")) > 1.0:
                indsats = float(m.group(1).replace(",", "."))
        if "gevinst" in lav and i + 1 < len(linjer):
            m = re.search(r"(\d+[.,]\d{2})", linjer[i + 1])
            if m:
                kupon_odds = float(m.group(1).replace(",", "."))

    kampe, blok = [], []
    for l in linjer:
        if any(x in l.lower() for x in ("indsats", "luk væddemål", "luk vaddemal")):
            break
        blok.append(l)
        if re.search(r"\b\d{1,2}:\d{2}\b", l) and len(blok) >= 2:
            k = _tolk_kampblok(blok)
            if k:
                kampe.append(k)
            blok = []

    if kampe and kupon_odds <= 1.0:
        p = 1.0
        for k in kampe:
            p *= k["odds"]
        kupon_odds = round(p, 2)
    return kampe, indsats, round(kupon_odds, 2)

def _tolk_kampblok(blok):
    odds = 0.0
    for l in blok:
        if any(x in l.lower() for x in ("resultat:", "over ", "under ", "begge hold")):
            continue
        m = re.search(r"\b(\d{1,2}[.,]\d{2})\b", l)
        if m:
            val = float(m.group(1).replace(",", "."))
            if 1.05 <= val <= 50.0:
                odds = val
                break
    if odds <= 1.01:
        return None
    spil_dele = []
    for l in blok:
        if any(x in l.lower() for x in ("resultat:", "over ", "under ", "begge hold", "hjørne", "kort", "skud")):
            ren = re.sub(r"^[o0•\-F\s]{1,4}", "", l).strip()
            ren = re.sub(r"\s+\d{1,2}[.,]\d{2}$", "", ren).strip()
            if ren and ren not in spil_dele:
                spil_dele.append(ren)
    kandidater = []
    for l in blok:
        if _er_stoj(l) or re.search(r"\b\d{1,2}[.,]\d{2}\b", l):
            continue
        if any(x in l.lower() for x in ("resultat:", "over ", "under ", "begge hold", "hjørne", "kort", "skud")):
            continue
        ren = _rens_tekst(l)
        if len(ren) >= 3 and ren not in kandidater:
            kandidater.append(ren)
    if len(kandidater) < 2:
        return None
    hjemme, ude = kandidater[-2], kandidater[-1]
    spil = " + ".join(spil_dele) if spil_dele else "Kampresultat"
    return {"kamp": f"{hjemme} - {ude}", "hjemme": hjemme, "ude": ude, "spil": spil, "odds": odds}
