import io, re, requests
from PIL import Image, ImageOps, ImageStat
from odds_motor import kamp_intelligens

def _h(*p): return ".".join(p)
OCR_URL = f"https://{_h('api', 'ocr', 'space')}/parse/image"

def klargoer_billede(b_data):
    img = Image.open(io.BytesIO(b_data)).convert("L")
    try:
        if next(iter(ImageStat.Stat(img).mean), 255) < 128: img = ImageOps.invert(img)
    except Exception:
        pass
    if img.width > 1200: img = img.resize((1200, int(img.height * (1200 / float(img.width)))))
    buf = io.BytesIO()
    ImageOps.autocontrast(img).save(buf, format="PNG")
    return buf.getvalue()

def aflaes_via_cloud_ocr(ren_bytes):
    try:
        r = requests.post(OCR_URL, files={"file": ("k.png", ren_bytes, "image/png")}, data={"apikey": "helloworld", "language": "eng", "OCREngine": "2"}, timeout=15).json()
        txt = "\n".join(p.get("ParsedText", "") for p in (r.get("ParsedResults") or []))
        linjer = [l.strip() for l in txt.splitlines() if l.strip()]
        return (linjer, "") if linjer else ([], "Ingen tekst")
    except Exception as e:
        return [], str(e)

def udtraek_kupon_liste(linjer):
    kampe, indsats = [], 100.0
    kamp_re = re.compile(r"^([A-Za-zÆØÅæøå0-9\.\s]{2,26})\s+(?:-|–|vs\.?|v)\s+([A-Za-zÆØÅæøå0-9\.\s]{2,26})$", re.I)
    dato_re = re.compile(r"^(?:man|tir|ons|tor|fre|lør|søn|mon|tue|wed|thu|fri|sat|sun)\s+\d{1,2}", re.I)
    live_re = re.compile(r"^\d{1,3}[:.]\d{2}$")
    stop = ("indsats", "gevinst", "udbetaling", "fuldtid", "resultat", "tidlig", "byg væddemål", "sport", "live", "væddemål", "casino", "share", "kr.", "angreb", "farligt", "placer", "samlede", "unibet", "luk")
    spil_buf, odds_buf, hold_buf = [], [], []

    def _ren_hold(t):
        t = re.sub(r"^[^A-Za-zÆØÅæøå]+", "", t).strip()
        return t if 2 <= len(t) <= 26 and not any(w in t.lower() for w in stop) and not re.search(r"\d", t) else ""

    for i, l in enumerate(linjer):
        low = l.lower()
        if "indsats" in low and i + 1 < len(linjer):
            m = re.search(r"(\d+(?:[.,]\d{2}))", linjer[i + 1])
            if m: indsats = float(m.group(1).replace(",", "."))
        if "kr" not in low:
            for mo in re.findall(r"\b(\d{1,3}[.,]\d{2})\b", l):
                t = float(mo.replace(",", "."))
                if 1.05 <= t <= 99.0: odds_buf.append(t)
        if any(w in low for w in ("over ", "under ", "begge hold", "f - resultat", "hjørne", "skud", "kort", "handicap", "målscorer", "byg væddemål")) and "fuldtid - resultat" not in low:
            spil_buf.append(re.sub(r"^[o°•\-\s]+", "", l).strip())
        elif kamp_re.match(l) and not any(w in low for w in stop):
            m1 = kamp_re.match(l)
            kampe.append({"kamp": f"{m1.group(1).strip()} - {m1.group(2).strip()}", "spil": " + ".join(dict.fromkeys(spil_buf)) or "1X2 / Resultat", "odds": odds_buf[-1] if odds_buf else 2.00})
            spil_buf, odds_buf, hold_buf = [], [], []
        elif (dato_re.match(l) or live_re.match(l)) and len(hold_buf) >= 2:
            kampe.append({"kamp": f"{hold_buf[-2]} - {hold_buf[-1]}", "spil": " + ".join(dict.fromkeys(spil_buf)) or "1X2 / Resultat", "odds": odds_buf[-1] if odds_buf else 2.00})
            spil_buf, odds_buf, hold_buf = [], [], []
        elif not dato_re.match(l) and not live_re.match(l):
            h = _ren_hold(l)
            if h: hold_buf.append(h)
    return kampe, indsats

def analyser_kamp_med_maalzone(kamp_str, spil_str, odds_val, faktor=1.0):
    dele = re.split(r"\s+(?:-|–|vs\.?|v)\s+", kamp_str, maxsplit=1, flags=re.I)
    hj = dele[0].strip() if dele else kamp_str
    ud = dele[1].strip() if len(dele) > 1 else ""
    beriget = kamp_intelligens.berig_valgte_kampe([{"hj": hj, "ud": ud, "ctx": {"by": hj}}])
    ctx = (beriget[0].get("ctx") or {}) if beriget else {}
    v, dom = ctx.get("vejr"), ctx.get("dommer", "")
    pct = round(max(10.0, min(90.0, (100.0 / max(1.01, odds_val)) * 0.93)), 1)
    stj, flm = max(1, min(5, int(round((pct * odds_val) / 21.0)))), max(1, min(5, int(round((100.0 - pct) / 17.0))))
    vurdering = "Tæt opgør med høj varians – dobbeltchance eller mållinje sikrer kuponen." if odds_val >= 2.20 else "Favoritprofil med stabil sandsynlighed."
    meta = ([f"Dommer: {dom}"] if dom and "ukendt" not in dom.lower() and "ikke udpeget" not in dom.lower() else []) + ([f"Vejr: {v['temp']}°C, {v['vind']} m/s ({v['effekt']})"] if v else [])
    analyse = f"**Spil:** {spil_str} | **Analyse:** {vurdering}" + (f" ({', '.join(meta)})" if meta else "")
    forslag = []
    for lbl, mult in [("Sikker Dobbeltchance (1X / X2)", 0.72), ("Mål-linje (Over 1.5 mål i kampen)", 0.88), ("Value-linje (Sejr + Over 1.5 mål)", 1.15)]:
        o_ny = max(1.18, round(odds_val * mult * faktor, 2))
        p_ny = round(max(12.0, min(91.0, (100.0 / o_ny) * 0.93)), 1)
        forslag.append({"txt": f"{kamp_str} — {lbl}", "odds": o_ny, "pct": p_ny})
    return {"pct": pct, "stj": stj, "flm": flm, "tekst": analyse, "forslag": forslag, "erstat_raad": (flm == 5 or odds_val >= 6.5)}
