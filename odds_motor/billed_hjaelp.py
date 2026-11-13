import re
from odds_motor import kamp_intelligens, billed_ocr

def udtraek_kupon_liste(linjer):
    return billed_ocr.udtraek_kupon_liste(linjer)

def analyser_kamp_med_maalzone(kamp_str, spil_str, odds_val, faktor=1.0):
    dele = re.split(r"\s+(?:-|–|vs\.?|v)\s+", kamp_str, maxsplit=1, flags=re.I)
    hj = dele[0].strip() if dele else kamp_str
    ud = dele[1].strip() if len(dele) > 1 else ""
    beriget = kamp_intelligens.berig_valgte_kampe([{"hj": hj, "ud": ud, "ctx": {"by": hj}}])
    ctx = (beriget[0].get("ctx") or {}) if beriget else {}
    v, dom = ctx.get("vejr"), ctx.get("dommer", "")
    pct = round(max(10.0, min(90.0, (100.0 / max(1.01, odds_val)) * 0.93)), 1)
    stj = max(1, min(5, int(round((pct * odds_val) / 21.0))))
    flm = max(1, min(5, int(round((100.0 - pct) / 17.0))))
    vurdering = "Tæt opgør med høj varians – dobbeltchance eller mållinje sikrer kuponen." if odds_val >= 2.20 else "Favoritprofil med stabil sandsynlighed."
    meta = ([f"Dommer: {dom}"] if dom and "ukendt" not in dom.lower() and "ikke udpeget" not in dom.lower() else []) + ([f"Vejr: {v['temp']}°C, {v['vind']} m/s ({v['effekt']})"] if v else [])
    analyse = f"**Spil:** {spil_str} | **Analyse:** {vurdering}" + (f" ({', '.join(meta)})" if meta else "")

    o_dc = round(min(1.68, max(1.22, 1.15 + (odds_val * 0.14))), 2)
    o_ov = round(min(1.85, max(1.28, 1.20 + (odds_val * 0.18))), 2)
    o_vl = round(min(4.50, max(1.65, odds_val * 1.12 * faktor)), 2)
    forslag = []
    for lbl, o_ny in [("Sikker Dobbeltchance (1X / X2)", o_dc), ("Mål-linje (Over 1.5 mål i kampen)", o_ov), ("Value-linje (Sejr + Over 1.5 mål)", o_vl)]:
        p_ny = round(max(12.0, min(91.0, (100.0 / o_ny) * 0.93)), 1)
        forslag.append({"txt": f"{kamp_str} — {lbl}", "odds": o_ny, "pct": p_ny})

    svaer_match = (odds_val >= 4.50 or flm == 5)
    return {"pct": pct, "stj": stj, "flm": flm, "tekst": analyse, "forslag": forslag, "svaer_match": svaer_match}
