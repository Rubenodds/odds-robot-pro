import io
import re
from PIL import Image, ImageOps

try:
    import pytesseract
except Exception:
    pytesseract = None

STOP_ORD = (
    "indsats", "gevinst", "luk væddemål", "luk vaddemal",
    "casino", "væddemål", "vaddemal",
)
STOJ_ORD = (
    "session", "ansvarsfuldt", "genbrug", "del", "fuldtid", "total antal",
    "byg væddemål", "byg vaddemal", "indskiftning", "triple",
    "double", "single", "kupon", "dobbeltchance", "tillægstid", "tillaegstid",
    "halvleg", "slut", "live", "sport", "hjem", "fog", "ned", "bod",
)
SPIL_ORD = (
    "resultat:", "over ", "under ", "begge hold", "hjørne",
    "kort", "skud", "eller uafgjort", "uafgjort eller",
)


def _rens_holdnavn(linje: str) -> str:
    t = re.sub(r"\b(man|tir|ons|tor|fre|lør|lor|søn|son)\s+\d{1,2}\s+[a-zæøå]{3,4}\b", "", linje, flags=re.I)
    t = re.sub(r"\b\d{1,2}[:.]\d{2}\b", "", t)
    t = re.sub(r"\b\d+\.\s*halvleg.*$", "", t, flags=re.I)
    t = re.sub(r"\b(slut|live|pause)\b", "", t, flags=re.I)
    t = re.sub(r"\s+\d{1,2}$", "", t)
    t = re.sub(r"\s+(fog|ned|bod|og|ppt|fal)\b.*$", "", t, flags=re.I)
    t = re.sub(r"^[a-zæøå]\s+", "", t, flags=re.I)
    t = re.sub(r"^[^a-zA-ZæøåÆØÅ]+", "", t)
    t = re.sub(r"[^a-zA-ZæøåÆØÅ0-9\s\-\.]+$", "", t)
    return re.sub(r"\s{2,}", " ", t).strip()


def _er_stoj(linje: str) -> bool:
    lav = linje.lower().strip()
    if len(lav) < 4:
        return True
    if any(s in lav for s in STOJ_ORD):
        return True
    bogstaver = sum(1 for c in lav if c.isalpha())
    return bogstaver < 4


def udtraek_kupon_fra_billede(billede_bytes: bytes):
    if pytesseract is None:
        return [], 100.0, 0.0
    img = ImageOps.grayscale(Image.open(io.BytesIO(billede_bytes)))
    w, h = img.size
    # Beskær top-statusbar (øverste 8%) og bund-navigationsbar (nederste 9%)
    img = img.crop((0, int(h * 0.08), w, int(h * 0.91)))
    w, h = img.size
    if w < 1600:
        skala = 2 if w >= 800 else 3
        img = img.resize((w * skala, h * skala))
    tekst = pytesseract.image_to_string(img, lang="dan+eng", config="--psm 6")
    return parse_kupon_tekst(tekst)


def _find_blok_odds(linje: str) -> float:
    ren = re.sub(r"\b(over|under)\s+\d+([.,]\d+)?\b", "", str(linje), flags=re.I)
    m = re.search(r"\b(\d{1,2}[.,]\d{2})\b", ren)
    if m:
        val = float(m.group(1).replace(",", "."))
        if 1.05 <= val <= 50.0:
            return val
    return 0.0


def parse_kupon_tekst(tekst: str):
    linjer = [l.strip() for l in tekst.splitlines() if l.strip()]
    indsats = 100.0
    for idx, l in enumerate(linjer):
        if "indsats" in l.lower():
            for tjek in linjer[idx : idx + 3]:
                m = re.search(r"\b(\d{1,5})[.,]\d{2}\b", tjek)
                if m:
                    indsats = float(m.group(1))
                    break

    blokke, aktuel_blok = [], []
    for l in linjer:
        lav = l.lower()
        if any(s in lav for s in STOP_ORD):
            break
        if _find_blok_odds(l) > 1.01 and not any(sp in lav for sp in SPIL_ORD):
            if aktuel_blok:
                blokke.append(aktuel_blok)
            aktuel_blok = [l]
        elif aktuel_blok:
            aktuel_blok.append(l)
    if aktuel_blok:
        blokke.append(aktuel_blok)

    kampe = []
    for blok in blokke:
        k = _tolk_kampblok(blok)
        if k:
            kampe.append(k)

    total_odds = 1.0
    for k in kampe:
        total_odds *= k["odds"]
    return kampe, indsats, round(total_odds, 2) if kampe else 0.0


def _tolk_kampblok(blok: list):
    if not blok:
        return None
    odds = _find_blok_odds(blok[0])
    if odds <= 1.01:
        return None

    spil_dele, hold_kandidater = [], []
    for l in blok[1:]:
        lav = l.lower()
        if any(sp in lav for sp in SPIL_ORD):
            ren = re.sub(r"^[o0•\-F\s]{1,4}", "", l).strip()
            ren = re.sub(r"\s+\d{1,2}[.,]\d{2}$", "", ren).strip()
            if ren and ren not in spil_dele:
                spil_dele.append(ren)
        elif not _er_stoj(l) and not re.search(r"\b\d{1,2}[.,]\d{2}\b", l):
            navn = _rens_holdnavn(l)
            if len(navn) >= 4 and navn not in hold_kandidater:
                hold_kandidater.append(navn)

    if len(hold_kandidater) < 2:
        return None

    hjemme, ude = hold_kandidater[-2], hold_kandidater[-1]
    spil = " + ".join(spil_dele) if spil_dele else "Kampresultat"
    return {
        "kamp": f"{hjemme} - {ude}",
        "hjemme": hjemme,
        "ude": ude,
        "spil": spil,
        "odds": odds,
    }
