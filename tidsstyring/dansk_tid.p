import datetime

def hent_dansk_klokkeslaet():
    # Henter serverens standardtid (Greenwich Mean Time)
    server_tid = datetime.datetime.utcnow()
    
    # Da Danmark er i vintertid nu (UTC+1), lægger vi præcis 1 time til, 
    # så uret i appen passer 100% med uret øverst på din telefon.
    dansk_tid = server_tid + datetime.timedelta(hours=1)
    
    return dansk_tid
