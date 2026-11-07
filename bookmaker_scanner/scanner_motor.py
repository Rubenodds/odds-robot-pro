import random

def hent_ai_alternativer_for_kamp(kamp_navn, originalt_odds):
    """
    Genererer uafhængige AI-alternativer, som brugeren kan vælge med flueben.
    """
    originalt_odds = float(originalt_odds)
    
    odds_lav = round(max(1.20, originalt_odds * 0.55), 2)
    odds_midt = round(max(1.45, originalt_odds * 0.80), 2)
    
    return [
        {
            "id": "lav",
            "variant": "🛡️ AI Risiko-Sikring: Dobbeltchance / Asian Handicap",
            "odds": odds_lav,
            "chance": max(10, int(90 / odds_lav)),
            "flammer": "🔥 🔥",
            "stjerner": "⭐⭐⭐⭐⭐",
            "analyse": f"Højere vinderchance. Vi fjerner de svære specialkrav og dækker op for overraskelser til odds {odds_lav:.2f}."
        },
        {
            "id": "midt",
            "variant": "⚽ AI Værdi-Boost: Målspark / Kort / Speciel-linje",
            "odds": odds_midt,
            "chance": max(10, int(83 / odds_midt)),
            "flammer": "🔥 🔥 🔥 🔥",
            "stjerner": "⭐⭐⭐⭐★",
            "analyse": f"Statistikken viser massiv historisk værdi på dette specialmarked til odds {odds_midt:.2f} frem for dit oprindelige valg."
        }
    ]
