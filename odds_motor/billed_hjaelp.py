import io, re, requests
from PIL import Image, ImageOps, ImageStat
from odds_motor import kamp_intelligens

def _h(*p): return ".".join(p)
OCR_URL = f"https://{_h('api', 'ocr', 'space')}/parse/image"

def klargoer_billede(b_data):
    img = Image.open(io.BytesIO(b_data)).convert("L")
    if ImageStat.Stat(img).mean < 128: img = ImageOps.invert(img)
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
    kampe, odds_l, indsats = [], [], 100.0
    dato_re = re.compile(r"^(?:man|tir|ons|tor|fre|lør|søn|mon|tue|wed|thu|fri|sat|sun)\s+\d{1,2}", re.I)
    odds_re = re.compile(r"\b(\d{1,2}[.,]\d{2})\b")
    stop = ("indsats", "gevinst", "udbetaling", "fuldtid", "resultat", "tidlig", "byg væddemål", "total antal", "udehold", "hjemmehold", "sport", "live", "væddemål", "casino", "share", "kr.")
    aktuelle_spil, brugt_idx = [], set()

    for i, l in enumerate(linjer):
        low = l.lower()
        if "indsats" in low and i + 1 < len(linjer):
            m = re.search(r"(\d+(?:[.,]\d{1,2})?)", linjer[i + 1])
            if m: indsats = float(m.group(1).replace(",", "."))
        if "kr" not in low:
            for mo in odds_re.findall(l):
                t = float(mo.replace(",", "."))
                if 1.05 <= t <= 99.0: odds_l.append(t)
        if any(w in low for w in ("over ", "under ", "begge hold", "f - resultat", "hjørne", "skud", "kort", "handicap")) and not any(s in low for s in ("fuldtid - resultat", "total antal", "antal hjørne")):
            aktuelle_spil.append(re.sub(r"^[o°•\-\s]+", "", l).strip())
        if dato_re.match(l) and i >= 1 and i + 1 < len(linjer):
            hj = re.sub(r"^[^A-Za-zÆØÅæøå]+", "", linjer[i - 1]).strip()
            ud = re.sub(r"^[^A-Za-zÆØÅæøå]+", "", linjer[i + 1]).strip()
            if len(hj) >= 3 and len(ud) >= 3 and not any(w in hj.lower() + ud.lower() for w in stop):
                o_val = odds_l[-1] if odds_l else 1.85
                spil_txt = " + ".join(dict.fromkeys(aktuelle_spil)) if aktuelle_spil else "1X2 / Resultat"
                kampe.append({"kamp": f"{hj} - {ud}", "spil": spil_txt, "odds": o_val})
                aktuelle_spil, brugt_idx = [], brugt_idx | {i - 1, i, i + 1}

    if not kampe:
        ren_hold = [re.sub(r"^[^A-Za-zÆØÅæøå]+", "", l).strip() for idx, l in enumerate(linjer) if idx not in brugt_idx and 3 <= len(l) <= 26 and not any(w in l.lower() for w in stop) and not re.search(r"\d", l)]
        for i in range(0, len(ren_hold) - 1, 2):
            kampe.append({"kamp": f"{ren_hold[i]} - {ren_hold[i+1]}", "spil": "1X2 / Resultat", "odds": odds_l[i//2] if i//2 < len(odds_l) else 1.85})
    samlet = round(eval("*".join(str(k["odds"]) for k in kampe)), 2) if kampe else 2.00
    return kampe, samlet, indsats

def analyser_enkelt_kamp(kamp_str, spil_str, odds_val):
    dele = re.split(r"\s+(?:-|–|vs\.?|v)\s+", kamp_str, maxsplit=1, flags=re.I)
    hj, ud = dele.strip(), (dele.strip() if len(dele) > 1 else "")
    beriget = kamp_intelligens.berig_valgte_kampe([{"hj": hj, "ud": ud, "ctx": {"by": hj}}])
    ctx = (beriget.get("ctx") or {}) if beriget else {}
    v = ctx.get("vejr")
    dom = ctx.get("dommer", "")
    info_dele = [f"Valgt spil: **{spil_str}**"]
    if dom and "ukendt" not in dom.lower() and "ikke udpeget" not in dom.lower(): info_dele.append(f"Dommer: {dom}")
    if v: info_dele.append(f"Vejr: {v['temp']}°C, {v['vind']} m/s ({v['effekt']})")
    pct = round(max(10.0, min(90.0, (100.0 / max(1.01, odds_val)) * 0.93)), 1)
    stj = max(1, min(5, int(round((pct * odds_val) / 21.0))))
    flm = max(1, min(5, int(round((100.0 - pct) / 17.0))))
    vurd = "Høj risiko på kombineret linje – overvej at skære den svageste del fra." if flm >= 4 else "Fin balance mellem sandsynlighed og odds."
    forslag = [
        f"{kamp_str} (Sikker: Dobbeltchance 1X / X2)",
        f"{kamp_str} (Mål-fokus: Over 1.5 mål i kampen)",
        f"{kamp_str} (Hjørne/Tempo: Over 8.5 hjørnespark)" if "hjørne" in spil_str.lower() else f"{kamp_str} (Reduceret linje: Fjern højrisiko-ben)"
    ]
    return {"pct": pct, "stj": stj, "flm": flm, "analyse": " | ".join(info_dele) + f". {vurd}", "forslag": forslag}
