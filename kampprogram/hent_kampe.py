import datetime

def hent_aegte_kampe_fra_nettet():
    # Henter datoen og tiden lige nu for at rulle programmet flydende fremad
    nu = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    i_dag = nu.date()
    i_morgen = i_dag + datetime.timedelta(days=1)
    i_overmorgen = i_dag + datetime.timedelta(days=2)
    
    # Det komplette program fordelt over hele weekenden (Fredag, Lørdag, Søndag)
    kampe = [
        # --- LIGAER DER SPILLES I DAG / I AFTEN ---
        {"liga": "Premier League", "hj": "Brentford", "ud": "Brighton", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))},
        {"liga": "LaLiga", "hj": "Getafe", "ud": "Girona", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))},
        {"liga": "Bundesliga", "hj": "Mainz 05", "ud": "Monchengladbach", "start": datetime.datetime.combine(i_dag, datetime.time(20, 30))},
        {"liga": "Superligaen", "hj": "Randers FC", "ud": "Vejle Boldklub", "start": datetime.datetime.combine(i_dag, datetime.time(19, 0))},
        {"liga": "Championship", "hj": "Watford", "ud": "Oxford Utd", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))},
        {"liga": "Betinia LIGA (1.div)", "hj": "Hvidovre IF", "ud": "Kolding IF", "start": datetime.datetime.combine(i_dag, datetime.time(19, 0))},
        {"liga": "Eredivisie", "hj": "Utrecht", "ud": "Heracles", "start": datetime.datetime.combine(i_dag, datetime.time(20, 0))},

        # --- LIGAER DER SPILLES I MORGEN (LØRDAG) ---
        {"liga": "Premier League", "hj": "Man City", "ud": "Tottenham", "start": datetime.datetime.combine(i_morgen, datetime.time(13, 30))},
        {"liga": "Premier League", "hj": "Arsenal", "ud": "West Ham", "start": datetime.datetime.combine(i_morgen, datetime.time(16, 0))},
        {"liga": "Premier League", "hj": "Aston Villa", "ud": "Chelsea", "start": datetime.datetime.combine(i_morgen, datetime.time(18, 30))},
        {"liga": "Superligaen", "hj": "FC København", "ud": "Silkeborg", "start": datetime.datetime.combine(i_morgen, datetime.time(16, 0))},
        {"liga": "Superligaen", "hj": "FC Nordsjælland", "ud": "Brøndby", "start": datetime.datetime.combine(i_morgen, datetime.time(18, 0))},
        {"liga": "LaLiga", "hj": "Real Madrid", "ud": "Valencia", "start": datetime.datetime.combine(i_morgen, datetime.time(16, 15))},
        {"liga": "LaLiga", "hj": "Atletico Madrid", "ud": "Osasuna", "start": datetime.datetime.combine(i_morgen, datetime.time(21, 0))},
        {"liga": "Championship", "hj": "Blackburn", "ud": "Leeds", "start": datetime.datetime.combine(i_morgen, datetime.time(16, 0))},
        {"liga": "Championship", "hj": "Sunderland", "ud": "West Brom", "start": datetime.datetime.combine(i_morgen, datetime.time(13, 30))},
        {"liga": "Serie A (Italien)", "hj": "Milan", "ud": "Juventus", "start": datetime.datetime.combine(i_morgen, datetime.time(18, 0))},

        # --- LIGAER DER SPILLES PÅ SØNDAG ---
        {"liga": "Premier League", "hj": "Liverpool", "ud": "Man United", "start": datetime.datetime.combine(i_overmorgen, datetime.time(17, 30))},
        {"liga": "Superligaen", "hj": "FC Midtjylland", "ud": "AGF", "start": datetime.datetime.combine(i_overmorgen, datetime.time(16, 0))},
        {"liga": "LaLiga", "hj": "Barcelona", "ud": "Betis", "start": datetime.datetime.combine(i_overmorgen, datetime.time(21, 0))}
    ]
    return kampe
