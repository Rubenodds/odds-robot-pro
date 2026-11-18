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
    "double", "single", "kupon", "dobbeltchance", "tillægstid", "tillaegstid"
)
SPIL_ORD = ("resultat:", "over ", "under ", "begge hold", "hjørne", "kort", "skud", "eller uafgjort", "uafgjort eller")

def _rens_tekst(linje):
    t = re.sub(r"\b(man|tir|ons|tor|fre|lør|lor|søn|son)\s+\d{1,2}\s+[a-zæøå]{3,4}\b", "", linje, flags=re.I)
    t = re.sub(r"\b\d{1,2}:\d{2}\b", "", t)
    t = re.sub(r"^[o0•\-FijHIl\|\[\]\(\)\s]{1,4}(?=[A-ZÆØÅ])", "", t)
    t = re.sub(r"^[^a-zA-ZæøåÆØÅ0-9]+", "", t).strip()
    return re.sub(r"\s{2,}", " ", t).strip()

def _er_stoj(linje):
    lav = linje.lower().strip()
    return len(lav) < 3 or any(s in lav for s in STOJ)

def udtraek_kupon_fra_billede(billede_bytes):
    if pytesseract is None:
        return [], 100.0, 0.0
    img = ImageOps.grayscale(Image.open(io.BytesIO(billede_bytes)))
    w, h = img.size
    if w < 1600:
        skala = 2 if w >= 800 else 3
        img = img.resize((w * skala, h * skala))
    tekst = pytesseract.image_to_string(img, lang="dan+eng", config="--psm 6")
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
        lav = l.lower()
        if any(x in lav for x in ("indsats", "luk væddemål", "luk vaddemal")):
            break
        if ("byg væddemål" in lav or "byg vaddemal" in lav) and len(blok) >= 3:
            if k := _tolk_kampblok(blok):
                kampe.append(k)
            blok = []
        blok.append(l)
        if re.search(r"\b\d{1,2}:\d{2}\b", l) and len(blok) >= 3:
            if k := _tolk_kampblok(blok):
                kampe.append(k)
            blok = []
    if len(blok) >= 3:
        if k := _tolk_kampblok(blok):
            kampe.append(k)

    if kampe and kupon_odds <= 1.0:
        p = 1.0
        for k in kampe:
            p *= k["odds"]
        kupon_odds = round(p, 2)
    return kampe, indsats, round(kupon_odds, 2)

def _tolk_kampblok(blok):
    odds = 0.0
    for l in blok:
        ren_l = re.sub(r"\b(over|under)\s+\d+([.,]\d+)?\b", "", l, flags=re.I)
        m = re.search(r"\b(\d{1,2}[.,]\d{2})\b", ren_l)
        if m and 1.05 <= float(m.group(1).replace(",", ".")) <= 50.0:
            odds = float(m.group(1).replace(",", "."))
            break
    if odds <= 1.01:
        return None
    spil_dele, kandidater = [], []
    for l in blok:
        lav = l.lower()
        if any(x in lav for x in SPIL_ORD):
            ren = re.sub(r"^[o0•\-F\s]{1,4}", "", l).strip()
            ren = re.sub(r"\s+\d{1,2}[.,]\d{2}$", "", ren).strip()
            if ren and ren not in spil_dele:
                spil_dele.append(ren)
        elif not _er_stoj(l) and not re.search(r"\b\d{1,2}[.,]\d{2}\b", l):
            ren = _rens_tekst(l)
            if len(ren) >= 3 and ren not in kandidater:
                kandidater.append(ren)
    if len(kandidater) < 2:
        return None
    hjemme, ude = kandidater[-2], kandidater[-1]
    return {"kamp": f"{hjemme} - {ude}", "hjemme": hjemme, "ude": ude, "spil": " + ".join(spil_dele) if spil_dele else "Kampresultat", "odds": odds}
