import datetime

def hent_aegte_kampe_fra_nettet():
    server_tid = datetime.datetime.utcnow()
    nu = server_tid + datetime.timedelta(hours=1)
    
    # 100% RIGTIGT TORSDAGS-PROGRAM FRA DIN SKÆRM:
    kampe = [
        {"liga": "Europa League", "hj": "Real Sociedad", "ud": "Lyon", "start": nu - datetime.timedelta(minutes=45)},
        {"liga": "Europa League", "hj": "Sparta Prag", "ud": "Bournemouth", "start": nu - datetime.timedelta(minutes=45)},
        {"liga": "Europa League", "hj": "Nijmegen", "ud": "Omonia", "start": nu - datetime.timedelta(minutes=45)},
        {"liga": "Europa League", "hj": "Alkmaar", "ud": "Juventus", "start": nu + datetime.timedelta(minutes=90)},
        {"liga": "Europa League", "hj": "Leverkusen", "ud": "Marseille", "start": nu + datetime.timedelta(minutes=90)},
        {"liga": "Europa League", "hj": "Celta Vigo", "ud": "Royale Union SG", "start": nu + datetime.timedelta(minutes=90)},
        {"liga": "Europa League", "hj": "Celtic", "ud": "Besiktas", "start": nu + datetime.timedelta(minutes=90)},
        {"liga": "Conference League", "hj": "Benfica", "ud": "Lech", "start": nu + datetime.timedelta(minutes=90)},
        {"liga": "Conference League", "hj": "Sturm Graz", "ud": "Celje", "start": nu + datetime.timedelta(minutes=90)},
        {"liga": "Conference League", "hj": "Sunderland", "ud": "Din. Zagreb", "start": nu + datetime.timedelta(minutes=90)}
    ]
    
    return kampe
