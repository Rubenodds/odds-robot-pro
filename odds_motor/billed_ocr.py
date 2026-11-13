import io, re
import numpy as np
from PIL import Image, ImageOps, ImageStat

try:
    from rapidocr_onnxruntime import RapidOCR
    _RAPID = RapidOCR()
except Exception:
    _RAPID = None

try:
    import pytesseract
    _TESS = True
except Exception:
    _TESS = False

def klargoer_billede(b_data):
    img = Image.open(io.BytesIO(b_data)).convert("L")
    try:
        if next(iter(ImageStat.Stat(img).mean), 255) < 128:
            img = ImageOps.invert(img)
    except Exception:
        pass
    if img.width > 1200:
        img = img.resize((1200, int(img.height * (1200 / float(img.width)))))
    return ImageOps.autocontrast(img)

def laes_tekst_lokalt(b_data):
    orig_img = Image.open(io.BytesIO(b_data)).convert("RGB")
    kontrast_img = klargoer_billede(b_data).convert("RGB")
    if _RAPID is not None:
        for im in (orig_img, kontrast_img):
            try:
                res, _ = _RAPID(np.array(im))
                linjer = [str(p[1]).strip() for p in (res or []) if isinstance(p, (list, tuple)) and len(p) >= 2 and str(p[1]).strip()]
                if linjer:
                    return linjer, ""
            except Exception:
                pass
    if _TESS:
        for im in (kontrast_img, orig_img):
            try:
                txt = pytesseract.image_to_string(im)
                linjer = [l.strip() for l in txt.splitlines() if l.strip()]
                if linjer:
                    return linjer, ""
            except Exception:
                pass
    return [], "Lokal OCR ikke klar endnu"

def udtraek_kupon_liste(linjer):
    kampe, indsats = [], 100.0
    kamp_re = re.compile(r"^([A-Za-zÆØÅæøå0-9\.\s]{2,26})\s+(?:-|–|vs\.?|v)\s+([A-Za-zÆØÅæøå0-9\.\s]{2,26})$", re.I)
    dato_re = re.compile(r"^(?:man|tir|ons|tor|fre|lør|lor|søn|son|mon|tue|wed|thu|fri|sat|sun)\s+\d{1,2}", re.I)
    live_re = re.compile(r"^\d{1,3}[:.]\d{2}$")
    stop = ("indsats", "gevinst", "udbetaling", "fuldtid", "resultat", "tidlig", "byg", "vaddemal", "væddemål", "begge hold", "sport", "live", "casino", "share", "kr.", "angreb", "farligt", "placer", "samlede", "unibet", "luk", "indskiftning", "spil", "hjørne", "hjornespark", "skud", "kort", "over", "under")
    spil_buf, odds_buf, alle_odds, hold_buf, alle_hold = [], [], [], [], []

    def _ren(t):
        t = re.sub(r"^[^A-Za-zÆØÅæøå]+", "", t).strip()
        if len(t) < 2 or len(t) > 26 or re.search(r"[\d:+]", t):
            return ""
        return "" if any(w in t.lower() for w in stop) else t

    for i, l in enumerate(linjer):
        low = l.lower()
        if "indsats" in low and i + 1 < len(linjer):
            m = re.search(r"(\d+(?:[.,]\d{2}))", linjer[i + 1])
            if m: indsats = float(m.group(1).replace(",", "."))
        if "kr" not in low:
            for mo in re.findall(r"\b(\d{1,3}[.,]\d{2})\b", l):
                t = float(mo.replace(",", "."))
                if 1.05 <= t <= 99.0: odds_buf.append(t); alle_odds.append(t)
        if any(w in low for w in ("over ", "under ", "begge hold", "f - resultat", "hjørne", "hjornespark", "skud", "kort", "handicap", "målscorer")) and "fuldtid - resultat" not in low:
            spil_buf.append(re.sub(r"^[o°•\-\s]+", "", l).strip())
        elif kamp_re.match(l) and not any(w in low for w in stop):
            m1 = kamp_re.match(l)
            kampe.append({"kamp": f"{m1.group(1).strip()} - {m1.group(2).strip()}", "spil": " + ".join(dict.fromkeys(spil_buf)) or "1X2 / Resultat", "odds": odds_buf[-1] if odds_buf else 2.00})
            spil_buf, odds_buf, hold_buf = [], [], []
        elif (dato_re.match(l) or live_re.match(l)) and len(hold_buf) >= 2:
            kampe.append({"kamp": f"{hold_buf[-2]} - {hold_buf[-1]}", "spil": " + ".join(dict.fromkeys(spil_buf)) or "1X2 / Resultat", "odds": odds_buf[-1] if odds_buf else 2.00})
            spil_buf, odds_buf, hold_buf = [], [], []
        elif not dato_re.match(l) and not live_re.match(l):
            h = _ren(l)
            if h: hold_buf.append(h); alle_hold.append(h)

    if not kampe and len(alle_hold) >= 2:
        for idx in range(0, len(alle_hold) - 1, 2):
            kampe.append({"kamp": f"{alle_hold[idx]} - {alle_hold[idx+1]}", "spil": "1X2 / Resultat", "odds": alle_odds[idx//2] if idx//2 < len(alle_odds) else 2.00})
    return kampe, indsats
