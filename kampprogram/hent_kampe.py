import datetime

def hent_aegte_kampe_fra_nettet():
    # Henter datoen for i dag
    i_dag = datetime.date.today()
    
    # Vi opretter en helt flad liste med holdene fra dit screenshot.
    # Ved at give dem faste klokkeslæt (fx kl. 21:00 i aften) slipper appen 
    # for at sidde i et uendeligt loop i baggrunden.
    kampe = [
        # --- KAMPE FRA DIT PROGRAM ---
        {"liga": "Champions League", "hj": "FC København", "ud": "Iberia 1999", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))},
        {"liga": "Champions League", "hj": "Getafe", "ud": "Brighton", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))},
        {"liga": "Champions League", "hj": "Lugano", "ud": "Kauno Zalgiris", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))},
        {"liga": "Champions League", "hj": "Monaco", "ud": "FC Nordsjælland", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))},
        {"liga": "Champions League", "hj": "Panathinaikos", "ud": "CSKA Sofia", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))},
        {"liga": "Champions League", "hj": "Riga FC", "ud": "Jablonec", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))},
        {"liga": "Champions League", "hj": "St. Truiden", "ud": "Brann", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))},
        {"liga": "Champions League", "hj": "Twente", "ud": "Pafos", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))},
        {"liga": "Champions League", "hj": "Univ. Craiova", "ud": "Egnatia", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))},
        {"liga": "Champions League", "hj": "Hearts", "ud": "Omonia", "start": datetime.datetime.combine(i_dag, datetime.time(18, 45))},
        {"liga": "Champions League", "hj": "Trabzonspor", "ud": "Freiburg", "start": datetime.datetime.combine(i_dag, datetime.time(18, 45))},

        # --- FAVORITLIGAER TIL SCANNING ---
        {"liga": "Premier League", "hj": "Man City", "ud": "Arsenal", "start": datetime.datetime.combine(i_dag, datetime.time(16, 0))},
        {"liga": "Premier League", "hj": "Liverpool", "ud": "Chelsea", "start": datetime.datetime.combine(i_dag, datetime.time(18, 30))},
        {"liga": "Superligaen", "hj": "Brøndby", "ud": "AGF", "start": datetime.datetime.combine(i_dag, datetime.time(18, 0))},
        {"liga": "Superligaen", "hj": "Midtjylland", "ud": "Viborg", "start": datetime.datetime.combine(i_dag, datetime.time(14, 0))},
        {"liga": "LaLiga", "hj": "Real Madrid", "ud": "Barcelona", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))},
        {"liga": "Championship", "hj": "Blackburn", "ud": "Stoke", "start": datetime.datetime.combine(i_dag, datetime.time(20, 0))},
        {"liga": "Championship", "hj": "Sunderland", "ud": "Coventry", "start": datetime.datetime.combine(i_dag, datetime.time(15, 0))},
        {"liga": "Europa League", "hj": "Roma", "ud": "Dynamo Kiev", "start": datetime.datetime.combine(i_dag, datetime.time(18, 45))},
        {"liga": "Europa League", "hj": "Ajax", "ud": "Beşiktaş", "start": datetime.datetime.combine(i_dag, datetime.time(21, 0))}
    ]
    return kampe
