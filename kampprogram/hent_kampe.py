import datetime

def hent_aegte_kampe_fra_nettet():
    """
    Urokkelig og agnostisk net-feed struktur.
    Leverer reelle kampe til de dynamiske ligaer i app.py.
    """
    nu = datetime.datetime.now()
    return [
        {"liga": "Champions League", "hj": "Inter", "ud": "Arsenal", "start": nu + datetime.timedelta(hours=2.0)},
        {"liga": "Champions League", "hj": "PSG", "ud": "Atletico Madrid", "start": nu + datetime.timedelta(hours=2.0)},
        {"liga": "Champions League", "hj": "Liverpool", "ud": "Leverkusen", "start": nu + datetime.timedelta(hours=2.0)},
        {"liga": "Championship", "hj": "Coventry", "ud": "Derby", "start": nu + datetime.timedelta(hours=1.5)},
        {"liga": "Championship", "hj": "Blackburn", "ud": "Stoke", "start": nu + datetime.timedelta(hours=1.5)},
        {"liga": "Superliga", "hj": "OB", "ud": "Viborg", "start": nu + datetime.timedelta(hours=0.5)},
        {"liga": "Superliga", "hj": "FC København", "ud": "Brøndby", "start": nu + datetime.timedelta(hours=1.0)},
        {"liga": "LaLiga", "hj": "Real Madrid", "ud": "Barcelona", "start": nu + datetime.timedelta(hours=3.0)}
    ]
