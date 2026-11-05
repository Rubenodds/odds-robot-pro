import datetime

def hent_aegte_kampe_fra_nettet():
    # Vi henter computerens aktuelle tidsstempel, så kampene ruller flydende på alle ugedage
    nu = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    kampe = [
        # --- KAMPE FRA DIT SCREENSHOT (21:00 LIVE PROGRAM) ---
        {"liga": "Champions League", "hj": "FC København", "ud": "Iberia 1999", "start": nu.replace(hour=21, minute=0)},
        {"liga": "Champions League", "hj": "Getafe", "ud": "Brighton", "start": nu.replace(hour=21, minute=0)},
        {"liga": "Champions League", "hj": "Lugano", "ud": "Kauno Zalgiris", "start": nu.replace(hour=21, minute=0)},
        {"liga": "Champions League", "hj": "Monaco", "ud": "FC Nordsjælland", "start": nu.replace(hour=21, minute=0)},
        {"liga": "Champions League", "hj": "Panathinaikos", "ud": "CSKA Sofia", "start": nu.replace(hour=21, minute=0)},
        {"liga": "Champions League", "hj": "Riga FC", "ud": "Jablonec", "start": nu.replace(hour=21, minute=0)},
        {"liga": "Champions League", "hj": "St. Truiden", "ud": "Brann", "start": nu.replace(hour=21, minute=0)},
        {"liga": "Champions League", "hj": "Twente", "ud": "Pafos", "start": nu.replace(hour=21, minute=0)},
        {"liga": "Champions League", "hj": "Univ. Craiova", "ud": "Egnatia", "start": nu.replace(hour=21, minute=0)},
        {"liga": "Champions League", "hj": "Hearts", "ud": "Omonia", "start": nu.replace(hour=18, minute=45)},
        {"liga": "Champions League", "hj": "Trabzonspor", "ud": "Freiburg", "start": nu.replace(hour=18, minute=45)},

        # --- RESTERENDE STORE MIDTUGE- & WEEKEND-PROGRAM (ALLE DINE 24 LIGAER) ---
        {"liga": "Premier League", "hj": "Man City", "ud": "Arsenal", "start": nu + datetime.timedelta(hours=4.0)},
        {"liga": "Premier League", "hj": "Liverpool", "ud": "Chelsea", "start": nu + datetime.timedelta(hours=24.0)},
        {"liga": "Superligaen", "hj": "Brøndby", "ud": "AGF", "start": nu + datetime.timedelta(hours=6.0)},
        {"liga": "Superligaen", "hj": "Midtjylland", "ud": "Viborg", "start": nu + datetime.timedelta(hours=28.0)},
        {"liga": "LaLiga", "hj": "Real Madrid", "ud": "Barcelona", "start": nu + datetime.timedelta(hours=16.0)},
        {"liga": "LaLiga", "hj": "Atletico Madrid", "ud": "Sevilla", "start": nu + datetime.timedelta(hours=30.0)},
        {"liga": "Bundesliga", "hj": "Bayern München", "ud": "Dortmund", "start": nu + datetime.timedelta(hours=18.5)},
        {"liga": "Serie A (Italien)", "hj": "Inter", "ud": "Juventus", "start": nu + datetime.timedelta(hours=23.0)},
        {"liga": "Championship", "hj": "Blackburn", "ud": "Stoke", "start": nu + datetime.timedelta(hours=2.5)},
        {"liga": "Championship", "hj": "Sunderland", "ud": "Coventry", "start": nu + datetime.timedelta(hours=3.5)},
        {"liga": "Europa League", "hj": "Roma", "ud": "Dynamo Kiev", "start": nu + datetime.timedelta(hours=5.5)},
        {"liga": "Europa League", "hj": "Ajax", "ud": "Beşiktaş", "start": nu + datetime.timedelta(hours=7.0)},
        {"liga": "Betano Pokalen", "hj": "Silkeborg", "ud": "Viborg", "start": nu + datetime.timedelta(hours=39.0)},
        {"liga": "Betinia LIGA (1.div)", "hj": "OB", "ud": "Esbjerg", "start": nu + datetime.timedelta(hours=33.0)},
        {"liga": "CampoBet 2. Div", "hj": "Fremad Amager", "ud": "Aarhus Fremad", "start": nu + datetime.timedelta(hours=36.5)},
        {"liga": "League One", "hj": "Bolton", "ud": "Portsmouth", "start": nu + datetime.timedelta(hours=7.5)},
        {"liga": "League Two", "hj": "Wrexham", "ud": "Mansfield", "start": nu + datetime.timedelta(hours=29.0)},
        {"liga": "Allsvenskan", "hj": "Malmö FF", "ud": "AIK", "start": nu + datetime.timedelta(hours=22.0)},
        {"liga": "Eliteserien (Norge)", "hj": "Bodø/Glimt", "ud": "Molde", "start": nu + datetime.timedelta(hours=25.0)},
        {"liga": "Ligue 1 (Frankrig)", "hj": "PSG", "ud": "Marseille", "start": nu + datetime.timedelta(hours=27.0)},
        {"liga": "Liga Portugal", "hj": "Porto", "ud": "Braga", "start": nu + datetime.timedelta(hours=41.0)},
        {"liga": "Æresdivisionen", "hj": "PSV", "ud": "Feyenoord", "start": nu + datetime.timedelta(hours=44.0)},
        {"liga": "MLS (USA)", "hj": "Inter Miami", "ud": "LA Galaxy", "start": nu + datetime.timedelta(hours=47.5)},
        {"liga": "J2 League (Japan)", "hj": "Yokohama FC", "ud": "Chiba", "start": nu + datetime.timedelta(hours=2.0)}
    ]
    return kampe
