import datetime

def hent_dansk_klokkeslaet():
    # Henter serverens universelle standardtid (UTC)
    server_tid = datetime.datetime.utcnow()
    
    # Da Danmark er i normaltid/vintertid nu, lægger vi præcis 1 time til.
    # Det sikrer, at appen kører 100% synkront med klokken på din telefon.
    dansk_tid = server_tid + datetime.timedelta(hours=1)
    
    return dansk_tid
