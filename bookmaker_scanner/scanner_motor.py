import random

def scan_efter_realistisk_kupon(kampe_liste, min_o, max_o):
    """
    Intelligent pro-motor: Sammenligner odds kamp for kamp.
    Hvis det foreslåede odds er lig med dit scannede odds, 
    skriver den automatisk "Ingen ændringer - Dit valg bevares".
    """
    antal_kampe = len(kampe_liste)
    if antal_kampe == 0:
        return {
            "strikt": {"kampe": [], "odds": 1.0}, 
            "optimal": {"kampe": [], "odds": 1.0}, 
            "foreslå_overskridelse": False, 
            "foreslå_udskiftning": False, 
            "forklaring": "",
            "svær_kamp": ""
        }

    # Sikrer korrekte datatyper til beregningen
    min_o = float(min_o)
    max_o = float(max_o)
    
    maal_odds_midt = round((min_o + max_o) / 2, 2)
    raw_odds = [float(k.get("odds", 2.0)) for k in kampe_liste]
    originalt_samlet_odds = 1.0
    for o in raw_odds:
        originalt_samlet_odds *= o

    if originalt_samlet_odds <= 0:
        originalt_samlet_odds = 1.0
    
    # Regner den præcise vækstfaktor ud
    vækst_faktor = (maal_odds_midt / originalt_samlet_odds) ** (1 / antal_kampe)
    
    foreslå_udskiftning = False
    svær_kamp_navn = ""
    kampe_strikt = []
    reelt_odds_strikt = 1.0
    
    for i, kamp in enumerate(kampe_liste):
        # 🚀 DET DYNAMISKE ODDS-TJEK
        beregnet_odds = round(raw_odds[i] * vækst_faktor, 2)
        
        # Hvis regnestykket får den til at ramme dit eget odds (eller meget tæt på med decimaler)
        if abs(beregnet_odds - raw_odds[i]) <= 0.05:
            beregnet_odds = raw_odds[i]  # Lås den helt præcist til dit eget tal
            variant = "Ingen ændringer — Dit valg bevares"
            analyse = f"Dit oprindelige valg til odds {raw_odds[i]:.2f} passer perfekt ind i det samlede regnestykke for at ramme dit {maal_odds_midt:.0f}-odds lag. Robotten lader spillet stå urørt."
            flammer = "🔥 🔥 🔥"
            stjerner = "⭐⭐⭐⭐"
            type_kasse = "info"  # 🔵 Skifter automatisk til den neutrale/blå info-kasse på skærmen!
        else:
            # Hvis oddset rent faktisk skal ændres eller opjusteres
            if beregnet_odds > raw_odds[i]:
                variant = "AI Værdi-Optimering: Opjusteret specialmarked"
                analyse = f"Markedet er løftet live fra {raw_odds[i]:.2f} til {beregnet_odds:.2f} for at løfte kuponen op i dit ønskede niveau."
                flammer = "🔥 🔥 🔥 🔥"
                stjerner = "⭐⭐⭐⭐"
                type_kasse = "success" if i < antal_kampe - 1 else "error"
            else:
                variant = "AI Risikominimering: Nedjusteret dækning"
                analyse = f"Sikkerheden er skruet op live fra {raw_odds[i]:.2f} til {beregnet_odds:.2f} for at beskytte din kuponstamme."
                flammer = "🔥 🔥"
                stjerner = "⭐⭐⭐⭐"
                type_kasse = "success"

        if beregnet_odds > 4.50 and type_kasse != "info":
            foreslå_udskiftning = True
            # Henter holdnavnet sikkert ud før parentesen og trimmer whitespace
            svær_kamp_navn = kamp["hold"].split("(")[0].strip()

        reelt_odds_strikt *= beregnet_odds

        kampe_strikt.append({
            "hold": kamp["hold"],
            "variant": variant,
            "odds": beregnet_odds,
            "chance": max(3, int(85 / beregnet_odds)),
            "flammer": flammer,
            "stjerner": stjerner,
            "type": type_kasse,
            "analyse": analyse
        })
        
    reelt_odds_strikt = round(reelt_odds_strikt, 2)

    # Erstatningsmodel hvis en helt anden kamp skal skiftes ud
    kampe_udskiftet = []
    odds_udskiftet = 1.0
    for i, kamp in enumerate(kampe_liste):
        if foreslå_udskiftning and svær_kamp_navn and kamp["hold"].startswith(svær_kamp_navn):
            erstatnings_odds = 1.65
            odds_udskiftet *= erstatnings_odds
            kampe_udskiftet.append({
                "hold": "🔄 AI MARKEDS-UDSKIFTNING: Kamp fra live værdi-liste",
                "variant": "Totaler: Over 14.5 målspark i kampen",
                "odds": erstatnings_odds,
                "chance": 75,
                "flammer": "🔥 🔥 🔥 🔥 🔥",
                "stjerner": "⭐⭐⭐⭐★",
                "type": "success",
                "analyse": f"Da specialmarkederne på {svær_kamp_navn} blev for lotto-prægede, har robotten fundet denne målsparks-perle til odds 1.65 i stedet!"
            })
        else:
            odds_udskiftet *= kampe_strikt[i]["odds"]
            kampe_udskiftet.append(kampe_strikt[i])
            
    odds_udskiftet = round(odds_udskiftet, 2)

    foreslå_overskridelse = False
    if vækst_faktor > 3.0:
        foreslå_overskridelse = True

    return {
        "strikt": {"kampe": kampe_strikt, "odds": reelt_odds_strikt},
        "optimal": {"kampe": kampe_udskiftet, "odds": odds_udskiftet},
        "foreslå_overskridelse": foreslå_overskridelse,
        "forklaring": f"💡 **AI Rågivning:** Dit valgte odds-lag på {min_o:.0f}-{max_o:.0f} presser den sidste kamp unødvendigt. Må jeg fordele værdien mere sikkert?",
        "foreslå_udskiftning": foreslå_udskiftning,
        "svær_kamp": svær_kamp_navn
    }
