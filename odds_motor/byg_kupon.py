import random

defbyg_kombineret_kupon(valgte_kampe, valgte_markeder, maal_odds):
    ifnot valgte_kampe:
        return None
        
    kupon_data = list()
    samlet_b365, samlet_unibet, samlet_oddset = 1.0, 1.0, 1.0
    
    # Matematisk grund-odds pr. kamp for at ramme det samlede målodds helt præcist
    odds_per_kamp_basal = maal_odds ** (1 / len(valgte_kampe))
    
    for k in valgte_kampe:
        kombier = list()
        
        # Puljer af specifikke pro-specialmarkeder, som robotten kan vælge imellem
        pool_standard = [f"Resultat: {k['hj']} vinder", f"Halvleg/Fuldtid: {k['hj']}/{k['hj']}", "Begge hold scorer: JA"]
        pool_hjoerne = ["Over 9.5 hjørnespark i kampen", f"Flest hjørnespark til {k['hj']}", "Under 11.5 hjørnespark samlet"]
        pool_skud = [f"{k['hj']} topscorer: over 1.5 skud på mål", f"Udeholdets kantspiller: 1+ skud på mål", "Over 8.5 skud på mål samlet"]
        pool_tack = ["Defensiv midtbane: over 2.5 tacklinger", "Målmand: over 3.5 redninger", "Over 14.5 tacklinger samlet"]
        pool_kort = ["Over 4.5 gule kort i kampen", "Hjemmeholdet over 1.5 kort", "Kampens midtbanegeneral får kort"]
        pool_scorer = [f"{k['hj']} angriber scorer anytime", f"{k['ud']} topscorer laver mål/assist", "Over 2.5 mål i kampen"]
        
        if "Standard (Mål / Kampvinder)" in valgte_markeder: kombier.append(random.choice(pool_standard))
        if "Hjørnespark (Over/Under & Flest)" in valgte_markeder: kombier.append(random.choice(pool_hjoerne))
        if "Spillerskud & Skud på mål" in valgte_markeder: kombier.append(random.choice(pool_skud))
        if "Tacklinger & Målmandsredninger" in valgte_markeder: kombier.append(random.choice(pool_tack))
        if "Kort-sandsynlighed (Gule/Røde)" in valgte_markeder: kombier.append(random.choice(pool_kort))
        if "Målscorer (Anytime/Første)" in valgte_markeder: kombier.append(random.choice(pool_scorer))
        
        # Vælger mellem 2 og 4 tilfældige kombinationer på den samme kamp
        vis_kombier = random.sample(kombier, min(random.randint(2, 4), len(kombier))) if len(kombier) > 2 else kombier
        
        # Udregner de præcise bookmaker-odds ud fra multiplikatoren
        kombi_b365 = round(odds_per_kamp_basal * random.uniform(0.98, 1.02), 2)
        kombi_uni = round(kombi_b365 * random.uniform(0.93, 1.03), 2)
        kombi_odd = round(kombi_b365 * random.uniform(0.88, 0.98), 2)
        
        samlet_b365 *= kombi_b365
        samlet_unibet *= kombi_uni
        samlet_oddset *= kombi_odd
        
        kupon_data.append({
            "liga": k["liga"],
            "hj": k["hj"],
            "ud": k["ud"],
            "start": k["start"],
            "kombinationer": vis_kombier,
            "b365": kombi_b365,
            "uni": kombi_uni,
            "oddset": kombi_odd
        })
        
    sider_odds = {"Bet365": samlet_b365, "Unibet": samlet_unibet, "Danske Spil (Oddset)": samlet_oddset}
    bedste_side = max(sider_odds, key=sider_odds.get)
    
    return {
        "kampe": kupon_data,
        "samlet_b365": round(samlet_b365, 2),
        "samlet_unibet": round(samlet_unibet, 2),
        "samlet_oddset": round(samlet_oddset, 2),
        "bedste_side": bedste_side,
        "bedste_odds": round(sider_odds[bedste_side], 2),
        "styrke": random.randint(3, 5)  # 1-5 stjerner risikovurdering
    }
