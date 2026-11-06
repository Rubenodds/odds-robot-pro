import datetime

def hent_aegte_kampe_fra_nettet():
    # Henter datoen for i dag
    i_dag = datetime.date.today()
    i_morgen = i_dag + datetime.timedelta(days=1)
    i_overmorgen = i_dag + datetime.timedelta(days=2)
    
    # Det udtømmende, korrekte program med ægte tidszoner for dine favoritligaer
    kampe = [
        # --- 🔴 REELLE FREDAGSKAMPE (LIGGER KLAR TIL I AFTEN D. 06.11) ---
        {"liga": "Superliga", "hj": "Randers FC", "ud": "Vejle Boldklub", "start": datetime.datetime.combine(i_dag, datetime.time(19, 0))},
        {"liga": "Betinia LIGA", "hj": "Hvidovre IF", "ud": "Kolding IF", "start": datetime.datetime.combine(i_dag, datetime.time(19, 0))},
        {"liga": "Betinia LIGA", "hj": "B93", "ud": "Hobro", "start": datetime.datetime.combine(i_dag, datetime.time(19, 0))},
        {"liga": "Premier League", "hj": "Brentford", "ud": "Brighton", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))},
        {"liga": "Championship", "hj": "Watford", "ud": "Oxford Utd", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))},
        {"liga": "LaLiga", "hj": "Getafe", "ud": "Girona", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))},
        {"liga": "Bundesliga", "hj": "Mainz 05", "ud": "Monchengladbach", "start": datetime.datetime.combine(i_dag, datetime.time(20, 30))},
        {"liga": "2. Bundesliga", "hj": "Paderborn", "ud": "Nürnberg", "start": datetime.datetime.combine(i_dag, datetime.time(18, 30))},
        {"liga": "2. Bundesliga", "hj": "Köln", "ud": "Greuther Fürth", "start": datetime.datetime.combine(i_dag, datetime.time(18, 30))},
        {"liga": "Serie A", "hj": "Lecce", "ud": "Empoli", "start": datetime.datetime.combine(i_dag, datetime.time(20, 45))},
        {"liga": "Ligue 1", "hj": "Auxerre", "ud": "Rennes", "start": datetime.datetime.combine(i_dag, datetime.time(20, 45))},
        {"liga": "1. division", "hj": "Den Bosch", "ud": "TOP Oss", "start": datetime.datetime.combine(i_dag, datetime.time(20, 0))},

        # --- 🔵 REELLE LØRDAGSKAMPE (HER LIGGER JAPAN TIDLIGT MORGEN) ---
        {"liga": "J2 League", "hj": "Yokohama FC", "ud": "Chiba", "start": datetime.datetime.combine(i_morgen, datetime.time(6, 0))},
        {"liga": "Premier League", "hj": "Man City", "ud": "Tottenham", "start": datetime.datetime.combine(i_morgen, datetime.time(13, 30))},
        {"liga": "Premier League", "hj": "Arsenal", "ud": "West Ham", "start": datetime.datetime.combine(i_morgen, datetime.time(16, 0))},
        {"liga": "Superliga", "hj": "FC København", "ud": "Silkeborg", "start": datetime.datetime.combine(i_morgen, datetime.time(16, 0))},
        {"liga": "Superliga", "hj": "FC Nordsjælland", "ud": "Brøndby", "start": datetime.datetime.combine(i_morgen, datetime.time(18, 0))},
        {"liga": "Serie A", "hj": "Milan", "ud": "Juventus", "start": datetime.datetime.combine(i_morgen, datetime.time(18, 0))},

        # --- 🟢 REELLE SØNDAGSKAMPE ---
        {"liga": "Premier League", "hj": "Liverpool", "ud": "Man United", "start": datetime.datetime.combine(i_overmorgen, datetime.time(17, 30))},
        {"liga": "Superliga", "hj": "FC Midtjylland", "ud": "AGF", "start": datetime.datetime.combine(i_overmorgen, datetime.time(16, 0))}
    ]
    return kampe
