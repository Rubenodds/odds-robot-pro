import datetime
import zoneinfo

def hent_dansk_klokkeslaet():
    """ Henter den præcise danske lokaltid og håndterer automatisk sommertid/vintertid. """
    return datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Copenhagen"))
