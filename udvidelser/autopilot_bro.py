from udvidelser.marked_motor import hent_reelle_muligheder
from udvidelser.holdnavne_oversaetter import normaliser_holdnavn

def hent_autopilot_valg_fra_api(kamp, min_odds=1.25, max_odds=3.50, brugte_valg=None):
    brugte_valg = brugte_valg or set()
    kamp_kopi = dict(kamp)
    kamp_kopi["hjemme"] = normaliser_holdnavn(kamp.get("hjemme", ""))
    kamp_kopi["ude"] = normaliser_holdnavn(kamp.get("ude", ""))
    muligheder, kilde, rest = hent_reelle_muligheder(kamp_kopi)
    kandidater = []
    for m in muligheder:
        odds = float(m.get("b365", 0))
        noegle = f"{kamp_kopi['hjemme']}_{m['marked']}_{m['valg']}"
        if not (min_odds <= odds <= max_odds) or noegle in brugte_valg:
            continue
        k1_navn, k1_odds = m["konk1"]
        k2_navn, k2_odds = m["konk2"]
        s11_txt = "✅ Bekræftet start-11. " if m.get("start11") else ""
        hvorfor = (
            f"{s11_txt}Faktisk udbudt linje under {m['marked']} ({kilde}). "
            f"Bet365 giver {odds}, mens {k1_navn} ligger på {k1_odds}."
        )
        kandidater.append({
            "kamp": f"{kamp_kopi['hjemme']} - {kamp_kopi['ude']}",
            "marked": m["marked"],
            "valg": m["valg"],
            "b365": odds,
            "konk1_navn": k1_navn, "konk1": k1_odds,
            "konk2_navn": k2_navn, "konk2": k2_odds,
            "chance_pct": round(100 / odds),
            "hvorfor": hvorfor,
            "kilde": kilde,
            "rest_kreditter": rest
        })
    return kandidater
