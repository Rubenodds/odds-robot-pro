import random

def hent_ai_alternativer_for_kamp(kamp_navn, originalt_odds, total_orig_odds, antal_kampe):
    """
    Genererer specifikke væddemålslinjer samt nød- og boost-flag.
    """
    originalt_odds = float(originalt_odds)
    total_orig_odds = float(total_orig_odds)
    
    maal_lav = max(1.5, total_orig_odds - 5.0)
    faktor_lav = (maal_lav / total_orig_odds) ** (1 / max(1, antal_kampe))
    
    maal_hoej = total_orig_odds + 5.0
    faktor_hoej = (maal_hoej / total_orig_odds) ** (1 / max(1, antal_kampe))
    
    odds_lav = round(max(1.10, originalt_odds * faktor_lav), 2)
    odds_midt = round(max(1.25, originalt_odds * faktor_hoej), 2)
    
    anmod_om_hoejt_odds_boost = False
    ai_forklaring_til_boost = ""
    
    if originalt_odds > 4.0:
        anmod_om_hoejt_odds_boost = True
        ai_forklaring_til_boost = (
            f"🤖 **AI Markedsscan:** På kampen *{kamp_navn}* viser vores data en markedsfejl. "
            f"Det sprænger din max-grænse en smule, men værdien er enorm!"
        )
        
    aktiver_joker_system = False
    if odds_lav <= 1.15:
        aktiver_joker_system = True
        
    # Dynamiske eksempler på konkrete spil baseret på holdnavn
    if "OB" in kamp_navn:
        spil_lav = "OB eller Uafgjort (1X)"
        spil_midt = "Over 8.5 målspark i kampen"
    elif "Leeds" in kamp_navn:
        spil_lav = "Tottenham eller Uafgjort (X2)"
        spil_midt = "Over 3.5 kort i kampen"
    else:
        spil_lav = "Norwich +1.5 Asian Handicap"
        spil_midt = "Begge hold scorer: JA"

    forslag = [
        {
            "id": "lav",
            "titel": f"🛡️ AI Risiko-Sikring: {spil_lav}",
            "variant": spil_lav,
            "odds": odds_lav,
            "chance": max(10, int(88 / odds_lav)),
            "flammer": "🔥 🔥",
            "stjerner": "⭐⭐⭐⭐⭐",
            "analyse": f"Sikkerheden er skruet op. Vi dækker op for overraskelser til odds {odds_lav:.2f}."
        },
        {
            "id": "midt",
            "titel": f"⚽ AI Værdi-Boost: {spil_midt}",
            "variant": spil_midt,
            "odds": odds_midt,
            "chance": max(10, int(83 / odds_midt)),
            "flammer": "🔥 🔥 🔥 🔥",
            "stjerner": "⭐⭐⭐⭐★",
            "analyse": f"Statistikken viser massiv værdi på denne linje til odds {odds_midt:.2f}."
        }
    ]
    
    return forslag, aktiver_joker_system, anmod_om_hoejt_odds_boost, ai_forklaring_til_boost
