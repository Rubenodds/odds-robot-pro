import datetime
import requests
from bs4 import BeautifulSoup

def hent_aegte_kampe_fra_nettet():
    kampe = []
    
    try:
        # Vi kobler os direkte på en åben live-xml sportstjeneste
        url = "https://scorespro.com"
        svar = requests.get(url, timeout=5)
        soup = BeautifulSoup(svar.content, "xml")
        items = soup.find_all("item")
        
        # Ordbog til at fange og oversætte dine 24 favoritligaer fra det internationale feed
        liga_map = {
            "ENGLAND PREMIER LEAGUE": "Premier League",
            "DENMARK SUPERLIGAEN": "Superligaen",
            "SPAIN LALIGA": "LaLiga",
            "ITALY SERIE A": "Serie A (Italien)",
            "GERMANY BUNDESLIGA": "Bundesliga",
            "ENGLAND CHAMPIONSHIP": "Championship",
            "CHAMPIONS LEAGUE": "Champions League",
            "EUROPA LEAGUE": "Europa League",
            "DENMARK LANDSPOKALEN": "Betano Pokalen",
            "ENGLAND LEAGUE ONE": "League One",
            "ENGLAND LEAGUE TWO": "League Two",
            "ENGLAND FA CUP": "FA Cup",
            "ENGLAND EFL CUP": "EFL Cup",
            "DENMARK 1. DIVISION": "Betinia LIGA (1.div)",
            "DENMARK 2. DIVISION": "CampoBet 2. Div",
            "SPAIN SEGUNDA DIVISION": "LaLiga2",
            "SPAIN COPA DEL REY": "Copa del Rey",
            "SWEDEN ALLSVENSKAN": "Allsvenskan",
            "NORWAY ELITESERIEN": "Eliteserien (Norge)",
            "FRANCE LIGUE 1": "Ligue 1 (Frankrig)",
            "ITALY SERIE B": "Serie B (Italien)",
            "PORTUGAL PRIMEIRA LIGA": "Liga Portugal",
            "NETHERLANDS EREDIVISIE": "Æresdivisionen",
            "USA MLS": "MLS (USA)",
            "JAPAN J2 LEAGUE": "J2 League (Japan)"
        }
        
        for item in items:
            title = item.title.text  # Format: "Hold A vs Hold B"
            descr = item.description.text  # Indeholder liga-info
            
            fundet_liga = None
            for k, v in liga_map.items():
                if k in title.upper() or k in descr.upper():
                    fundet_liga = v
                    break
            
            # Hvis kampen tilhører en af dine ligaer, tager vi den med
            if fundet_liga and " vs " in title:
                hold = title.split(" vs ")
                hj = hold[0].strip()
                ud = hold[1].strip()
                
                # Da feedet opdateres live, sætter vi tidsstemplet
                kampe.append({
                    "liga": fundet_liga,
                    "hj": hj,
                    "ud": ud,
                    "start": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
                })
    except Exception:
        pass
        
    return kampe
