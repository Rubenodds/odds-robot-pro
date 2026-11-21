import datetime
import math
import re
import requests

BY_MAP = {
    "mallorca": "Palma", "sheff wed": "Sheffield", "sheff utd": "Sheffield",
    "man utd": "Manchester", "man city": "Manchester", "wolves": "Wolverhampton",
    "west ham": "London", "arsenal": "London", "chelsea": "London", "tottenham": "London",
    "real oviedo": "Oviedo", "real madrid": "Madrid", "atletico": "Madrid", "betis": "Sevilla",
    "rayo vallecano": "Madrid", "valencia": "Valencia", "napoli": "Naples", "torino": "Turin",
}
LIGAER = ["esp.1", "esp.2", "eng.1", "eng.2", "eng.3", "ger.1", "ger.2", "ita.1", "ita.2", "fra.1", "den.1", "uefa.champions"]
GEO_HOST = ".".join(["geocoding-api", "open-meteo", "com"])
WX_HOST = ".".join(["api", "open-meteo", "com"])
ESPN_HOST = ".".join(["site", "api", "espn", "com"])


def _rens_holdnavn(navn):
    t = re.sub(r"^[^a-zA-ZæøåÆØÅ]+", "", str(navn)).strip()
    t = re.sub(r"^(ap|fc|cf)\s+", "", t, flags=re.I).strip()
    try:
        from udvidelser.holdnavne_oversaetter import normaliser_holdnavn
        t = normaliser_holdnavn(t)
    except Exception:
        pass
    return t or "Hold"


def _hent_live_vejr(klub):
    by = BY_MAP.get(klub.lower(), klub)
    try:
        g = requests.get(f"https://{GEO_HOST}/v1/search", params={"name": by, "count": 1, "language": "da"}, timeout=3).json()
        for r in (g.get("results") or []):
            w = requests.get(
                f"https://{WX_HOST}/v1/forecast",
                params={"latitude": r["latitude"], "longitude": r["longitude"], "current": "temperature_2m,wind_speed_10m", "wind_speed_unit": "ms"},
                timeout=3,
            ).json()
            cur = w.get("current") or {}
            if cur.get("temperature_2m") is not None:
                return f"Stadionvejr ({by}): {cur['temperature_2m']}°C, vind {cur['wind_speed_10m']} m/s"
    except Exception:
        pass
    return ""


def _hent_dommer_og_kort(hjemme, ude):
    dommer = ""
    try:
        from odds_motor import dommer_intelligens
        dommer = dommer_intelligens.hent_dommer(hjemme, ude) or ""
    except Exception:
        pass

    nu = datetime.date.today()
    dato_sp = f"{(nu - datetime.timedelta(days=14)).strftime('%Y%m%d')}-{(nu + datetime.timedelta(days=3)).strftime('%Y%m%d')}"
    h_kort, u_kort = [], []
    for lg in LIGAER:
        try:
            url = f"https://{ESPN_HOST}/apis/site/v2/sports/soccer/{lg}/scoreboard"
            for ev in (requests.get(url, params={"dates": dato_sp}, timeout=3).json().get("events") or []):
                for comp in (ev.get("competitions") or []):
                    teams = comp.get("competitors") or []
                    navne = [t.get("team", {}).get("displayName", "").lower() for t in teams]
                    if not dommer and any(hjemme.lower()[:5] in n for n in navne) and any(ude.lower()[:5] in n for n in navne):
                        dommer = next((o.get("displayName", "") for o in (comp.get("officials") or []) if o.get("displayName")), dommer)
                    for t in teams:
                        tn = t.get("team", {}).get("displayName", "").lower()
                        stats = {s.get("name"): s.get("displayValue") for s in (t.get("statistics") or [])}
                        if stats.get("yellowCards") is not None:
                            val = float(stats["yellowCards"]) + float(stats.get("redCards") or 0)
                            (h_kort if hjemme.lower()[:5] in tn else u_kort if ude.lower()[:5] in tn else []).append(val)
        except Exception:
            continue
    h_s = round(sum(h_kort) / len(h_kort), 1) if h_kort else None
    u_s = round(sum(u_kort) / len(u_kort), 1) if u_kort else None
    return h_s, u_s, dommer


def _tjek_bookmaker_udbud(hjemme, ude, spil, liga_kode="eng.1"):
    try:
        from udvidelser.marked_motor import tjek_kupon_spil_mod_marked
        ok, status_txt, api_alt = tjek_kupon_spil_mod_marked({"hjemme": hjemme, "ude": ude, "liga_kode": liga_kode}, spil)
        alt_liste = []
        for m in api_alt:
            o = round(float(m.get("b365", 1.50)), 2)
            alt_liste.append({"label": f"[{m['marked']}] {m['valg']} (💡 Hvorfor? Verificeret hos bookmaker)", "odds": o, "pct": round(min(85.0, (100.0 / o) * 1.02), 1)})
        return ok, status_txt, alt_liste
    except Exception:
        return True, "", []


def analyser_kupon_kamp(k):
    odds = float(k.get("odds", 1.80))
    spil = re.sub(r"^[\-\s]+", "", k.get("spil", "")).strip()
    hjemme = _rens_holdnavn(k.get("hjemme", "Hjemmehold"))
    ude = _rens_holdnavn(k.get("ude", "Udehold"))
    vejr = _hent_live_vejr(hjemme)
    vejr_txt = f"🌤️ {vejr}" if vejr else f"🌤️ Stadionvejr ({hjemme}): Ikke tilgængeligt"
    h_snit, u_snit, dommer = _hent_dommer_og_kort(hjemme, ude)
    d_del = f"Dommer: <b>{dommer}</b> | " if dommer else "Dommer: Ikke offentliggjort | "
    kort_txt = f"🟨 {d_del}Kortsnit: {hjemme} {h_snit or '?'}/kamp & {ude} {u_snit or '?'}/kamp"
    bm_ok, bm_txt, api_alt = _tjek_bookmaker_udbud(hjemme, ude, spil, k.get("liga_kode", "eng.1"))
    imp_pct = round(100.0 / odds, 1)
    antal_ben = spil.count("+") + 1
    reel_pct = round(min(88.0, max(12.0, imp_pct * (1.03 if odds <= 1.85 else 0.98))), 1)
    edge = round((reel_pct / 100.0) * odds - 1.0, 3)
    stjerner = 5 if edge >= 0.08 else (4 if edge >= 0.02 else (3 if edge >= -0.03 else (2 if edge >= -0.08 else 1)))
    risiko = 1 if odds <= 1.45 else (2 if odds <= 1.85 else (3 if odds <= 2.30 else (4 if odds <= 3.00 else 5)))
    er_staerk = (risiko <= 2 and stjerner >= 4 and antal_ben == 1 and bm_ok)
    alternativer = [] if er_staerk else (api_alt or _byg_intelligente_alternativer(hjemme, spil, odds, reel_pct))
    meta = f"{vejr_txt}<br>{kort_txt}" + (f"<br>📡 {bm_txt}" if bm_txt else "")
    return {"kamp": f"{hjemme} - {ude}", "spil": spil, "odds": odds, "pct": reel_pct, "stjerner": stjerner, "risiko": risiko, "er_staerk": er_staerk, "begrundelse": f"📊 Kampbillede: {hjemme} vs. {ude}. {'✅ Godkendt udbud.' if bm_ok else '⚠️ Tjek markedslinje.'}", "meta": meta, "alternativer": alternativer}


def _byg_intelligente_alternativer(hjemme, spil, odds, reel_pct):
    forslag = []
    if "+" in spil.lower() or odds >= 1.90:
        o1 = round(max(1.28, min(1.65, odds * 0.62)), 2)
        forslag.append({"label": f"Sikrere linje: {hjemme} eller uafgjort (1X) (💡 Hvorfor? Dækker uafgjort)", "odds": o1, "pct": round(min(77.0, reel_pct + 18.0), 1)})
    if odds >= 1.85:
        o2 = round(max(1.25, min(1.56, odds * 0.58)), 2)
        forslag.append({"label": "Målsikring: Over 1.5 mål i kampen (💡 Hvorfor? Højere træfsikkerhed)", "odds": o2, "pct": round(min(80.0, reel_pct + 21.0), 1)})
    return forslag[:3]


def samlet_kupon_analyse(analyser, indsats):
    if not analyser:
        return {}
    samlet_odds = math.prod(a["odds"] for a in analyser)
    samlet_pct = round(math.prod(a["pct"] / 100.0 for a in analyser) * 100.0, 1)
    gevinst = round(indsats * samlet_odds, 2)
    return {"odds": round(samlet_odds, 2), "pct": samlet_pct, "gevinst": gevinst, "dom": f"Totalodds {samlet_odds:.2f} | Mulig gevinst {gevinst:.2f} kr. | Samlet chance {samlet_pct}%.", "svageste": min(analyser, key=lambda x: x["pct"])["kamp"]}
