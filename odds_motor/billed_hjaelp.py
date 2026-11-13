import io, re, requests
from PIL import Image, ImageOps, ImageStat
from odds_motor import kamp_intelligens

def _h(*p): return ".".join(p)
OCR_URL = f"https://{_h('api', 'ocr', 'space')}/parse/image"

def klargoer_billede(b_data):
    img = Image.open(io.BytesIO(b_data)).convert("L")
    if ImageStat.Stat(img).mean[0] < 128: img = ImageOps.invert(img)
    if img.width > 1000: img = img.resize((1000, int(img.height * (1000 / float(img.width)))))
    buf = io.BytesIO()
    ImageOps.autocontrast(img).save(buf, format="PNG")
    return buf.getvalue()

def aflaes_via_cloud_ocr(ren_bytes):
    try:
        r = requests.post(OCR_URL, files={"file": ("kupon.png", ren_bytes, "image/png")}, data={"apikey": "helloworld", "language": "eng", "OCREngine": "2"}, timeout=15).json()
        txt = "\n".join(p.get("ParsedText", "") for p in (r.get("ParsedResults") or []))
        linjer = [l.strip() for l in txt.splitlines() if l.strip()]
        return (linjer, "") if linjer else ([], str(r.get("ErrorMessage") or "Ingen tekst"))
    except Exception as e:
        return [], str(e)

def udtraek_kupon_liste(linjer):
    kampe, indsats = [], 100.0
    kamp_re = re.compile(r"^([A-Za-zÆØÅæøå0-9\.\s]{3,26})\s+(?:-|–|vs\.?|v)\s+([A-Za-zÆØÅæøå0-9\.\s]{3,26})$", re.I)
    dato_re = re.compile(r"^(?:man|tir|ons|tor|fre|lør|søn|mon|tue|wed|thu|fri|sat|sun)\s+\d{1,2}", re.I)
    live_re = re.compile(r"^\d{1,3}[:.]\d{2}$")
    stop = ("indsats", "gevinst", "udbetaling", "fuldtid", "resultat", "tidlig", "byg væddemål", "sport", "live", "væddemål", "casino", "share", "kr.", "angreb", "farligt")
    spil_buf, odds_buf = [], []

    for i, l in enumerate(linjer):
        low = l.lower()
        if "indsats" in low and i + 1 < len(linjer):
            m = re.search(r"(\d+(?:[.,]\d{1,2})?)", linjer[i + 1])
            if m: indsats = float(m.group(1).replace(",", "."))
        if "kr" not in low:
            for mo in re.findall(r"\b(\d{1,2}[.,]\d{2})\b", l):
                t = float(mo.replace(",", "."))
                if 1.05 <= t <= 99.0: odds_buf.append(t)
        if any(w in low for w in ("over ", "under ", "begge hold", "f - resultat", "hjørne", "skud", "kort", "handicap", "målscorer", "byg væddemål")) and "fuldtid - resultat" not in low:
            spil_buf.append(re.sub(r"^[o°•\-\s]+", "", l).strip())
        m_1linje = kamp_re.match(l)
        if m_1linje and not any(w in low for w in stop):
            kampe.append({"kamp": f"{m_1linje.group(1).strip()} - {m_1linje.group(2).strip()}", "spil": " + ".join(dict.fromkeys(spil_buf)) or "1X2 / Resultat", "odds": odds_buf[-1] if odds_buf else 2.00})
            spil_buf, odds_buf = [], []
        elif dato_re.match(l) and i >= 1 and i + 1 < len(linjer):
            hj, ud = re.sub(r"^[^A-Za-zÆØÅæøå]+", "", linjer[i - 1]).strip(), re.sub(r"^[^A-Za-zÆØÅæøå]+", "", linjer[i + 1]).strip()
            if len(hj) >= 3 and len(ud) >= 3 and not any(w in hj.lower() + ud.lower() for w in stop):
                kampe.append({"kamp": f"{hj} - {ud}", "spil": " + ".join(dict.fromkeys(spil_buf)) or "1X2 / Resultat", "odds": odds_buf[-1] if odds_buf else 2.00})
                spil_buf, odds_buf = [], []
        elif live_re.match(l) and i >= 2 and ":" not in linjer[i - 1] and ":" not in linjer[i - 2]:
            hj, ud = re.sub(r"^[^A-Za-zÆØÅæøå]+", "", linjer[i - 2]).strip(), re.sub(r"^[^A-Za-zÆØÅæøå]+", "", linjer[i - 1]).strip()
            if len(hj) >= 3 and len(ud) >= 3 and not any(w in hj.lower() + ud.lower() for w in stop):
                kampe.append({"kamp": f"{hj} - {ud}", "spil": "Live 1X2 / Resultat", "odds": odds_buf[-1] if odds_buf else 2.00})
                spil_buf, odds_buf = [], []
    return kampe, indsats

def analyser_kamp_med_maalzone(kamp_str, spil_str, odds_val, faktor=1.0):
    dele = re.split(r"\s+(?:-|–|vs\.?|v)\s+", kamp_str, maxsplit=1, flags=re.I)
    hj, ud = dele[0].strip(), (dele[1].strip() if len(dele) > 1 else "")
    beriget = kamp_intelligens.berig_valgte_kampe([{"hj": hj, "ud": ud, "ctx": {"by": hj}}])
    ctx = (beriget[0].get("ctx") or {}) if beriget else {}
    v, dom = ctx.get("vejr"), ctx.get("dommer", "")
    ekstra = ([f"Dommer: {dom}"] if dom and "ukendt" not in dom.lower() and "ikke udpeget" not in dom.lower() else []) + ([f"Vejr: {v['temp']}°C, {v['vind']} m/s ({v['effekt']})"] if v else [])
    pct = round(max(10.0, min(90.0, (100.0 / max(1.01, odds_val)) * 0.93)), 1)
    stj, flm = max(1, min(5, int(round((pct * odds_val) / 21.0)))), max(1, min(5, int(round((100.0 - pct) / 17.0))))
    forslag = [
        {"txt": f"{kamp_str} — Sikker Dobbeltchance (1X / X2)", "odds": max(1.18, round(odds_val * 0.72 * faktor, 2))},
        {"txt": f"{kamp_str} — Mål/Hjørne-linje (Over 1.5 mål / Over 8.5 hjørner)", "odds": max(1.30, round(odds_val * 0.88 * faktor, 2))},
        {"txt": f"{kamp_str} — Value-linje (Sejr + Over 1.5 mål)", "odds": max(1.50, round(odds_val * 1.15 * faktor, 2))},
    ]
    tekst = f"**Spil:** {spil_str}" + (f" | {' | '.join(ekstra)}" if ekstra else "")
    return {"pct": pct, "stj": stj, "flm": flm, "tekst": tekst, "forslag": forslag, "erstat_raad": (flm == 5 or odds_val >= 6.5)}
