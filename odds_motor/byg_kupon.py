import random
import datetime

def byg_kombineret_kupon(valgte_kampe, valgte_markeder, maal_odds):
    if not valgte_kampe:
        return None
        
    kupon_data = []
    samlet_b365, samlet_unibet, samlet_oddset = 1.0, 1.0, 1.0
    odds_per_kamp_basal = maal_odds ** (1 / len(valgte_kampe))
    
    for k in valgte_kampe:
        # ULTIMATIV DATATRANSFORMATOR: Håndterer både ordbøger (dicts) og rå SQLite-rækker (tuples/lists)
        liga, hj, ud, start = "Ukendt Liga", "Hjemmehold", "Udehold", None
        
        if isinstance(k, dict):
            # Prøver både små og store bogstaver for at være 100% sikker
            liga = k.get("liga") or k.get("Liga") or k.get("turnering") or "Ukendt Liga"
            hj = k.get("hj") or k.get("Hj") or k.get("hjemmehold") or k.get("home") or "Hjemmehold"
            ud = k.get("ud") or k.get("Ud") or k.get("udehold") or k.get("away") or "Udehold"
            start = k.get("start") or k.get("Start") or k.get("tidspunkt")
        elif isinstance(k, (tuple, list)) and len(k) >= 4:
            # Hvis det er en rå databaserække fra SQLite, mapper vi efter typisk kolonne-rækkefølge
            liga = str(k[0])
            hj = str(k[1])
            ud = str(k[2])
            start = k[3]
        elif isinstance(k, (tuple, list)) and len(k) > 0:
            # Faldbane for kortere tupler
            liga = str(k[0])
            hj = str(k[1]) if len(k) > 1 else "Hjemmehold"
            ud = str(k[2]) if len(k) > 2 else "Udehold"
            start = k[3] if len(k) > 3 else None

        if not start:
            start = datetime.datetime.now()

        kombier = []
        
        # Alle forslag bruger nu de reelle, transformerede hold-navne sikkert uden KeyError
        pool_standard = [f"Resultat: {hj} vinder", f"Halvleg/Fuldtid: {hj}/{hj}", "Begge hold scorer: JA"]
        pool_hjoerne = [f"Over 9.5 hjørnespark i kampen", f"Flest hjørnespark til {hj}", f"{hj} over 4.5 hjørnespark"]
        pool_skud = [f"{hj} over 4.5 skud på mål", f"{ud} over 3.5 skud på mål", "Over 8.5 skud på mål samlet"]
        pool_tack = [f"{hj} over 12.5 tacklinger", f"{ud} over 13.5 tacklinger", "Over 25.5 tacklinger samlet"]
        pool_kort = ["Over 4.5 gule kort i kampen", f"{hj} over 1.5 kort", f"{ud} over 1.5 kort"]
        pool_scorer = ["Over 2.5 mål i kampen", "Over 1.5 mål i 2. halvleg", f"{hj} over 1.5 mål"]
        
        if "Standard (Mål / Kampvinder)" in valgte_markeder: kombier.append(random.choice(pool_standard))
        if "Hjørnespark (Over/Under & Flest)" in valgte_markeder: kombier.append(random.choice(pool_hjoerne))
        if "Spillerskud & Skud på mål" in valgte_markeder: kombier.append(random.choice(pool_skud))
        if "Tacklinger & Målmandsredninger" in valgte_markeder: kombier.append(random.choice(pool_tack))
        if "Kort-sandsynlighed (Gule/Røde)" in valgte_markeder: kombier.append(random.choice(pool_kort))
        if "Målscorer (Anytime/Første)" in valgte_markeder: kombier.append(random.choice(pool_scorer))
        
        vis_kombier = random.sample(kombier, min(random.randint(2, 4), len(kombier))) if len(kombier) > 2 else kombier
        kombi_b365 = round(odds_per_kamp_basal * random.uniform(0.98, 1.02), 2)
        kombi_uni = round(kombi_b365 * random.uniform(0.93, 1.03), 2)
        kombi_odd = round(kombi_b365 * random.uniform(0.88, 0.98), 2)
        
        samlet_b365 *= kombi_b365
        samlet_unibet *= kombi_uni
        samlet_oddset *= kombi_odd
        
        kupon_data.append({
            "liga": liga, "hj": hj, "ud": ud, "start": start,
            "kombinationer": vis_kombier, "b365": kombi_b365, "uni": kombi_uni, "oddset": kombi_odd
        })
        
    sider_odds = {"Bet365": samlet_b365, "Unibet": samlet_unibet, "Danske Spil (Oddset)": samlet_oddset}
    bedste_side = max(sider_odds, key=sider_odds.get)
    
    return {
        "kampe": kupon_data, "samlet_b365": round(samlet_b365, 2), "samlet_unibet": round(samlet_unibet, 2),
        "samlet_oddset": round(samlet_oddset, 2), "bedste_side": bedste_side, "bedste_odds": round(sider_odds[bedste_side], 2),
        "styrke": random.randint(3, 5)
    }
