import datetime

def hent_dansk_klokkeslaet():
    server_tid = datetime.datetime.utcnow()
    # Tilføjer præcis 1 time, så uret passer med dansk vintertid på din telefon
    return server_tid + datetime.timedelta(hours=1)
