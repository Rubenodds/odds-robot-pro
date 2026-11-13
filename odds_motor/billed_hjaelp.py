import re
from odds_motor import kamp_intelligens, billed_ocr

def klargoer_billede(b_data): return billed_ocr.klargoer_billede(b_data)
def aflaes_via_cloud_ocr(ren_bytes): return billed_ocr.aflaes_via_cloud_ocr(ren_bytes)
def udtraek_kupon_liste(linjer): return billed_ocr.udtraek_kupon_liste(linjer)

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
