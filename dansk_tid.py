import datetime

def hent_dansk_klokkeslaet():
    # Henter serverens standardtid (UTC)
    server_tid = datetime.datetime.utcnow()
    
    # Lægger præcis 1 time til, så det passer 100% med uret i Danmark (vintertid)
    dansk_tid = server_tid + datetime.timedelta(hours=1)
    
    return dansk_tid
