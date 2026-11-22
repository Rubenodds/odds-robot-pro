import re

_ALIAS = {
    "man utd": "manchester united",
    "man united": "manchester united",
    "man city": "manchester city",
    "sheff wed": "sheffield wednesday",
    "sheff utd": "sheffield united",
    "nottm forest": "nottingham forest",
    "wolves": "wolverhampton wanderers",
    "spurs": "tottenham hotspur",
    "newcastle": "newcastle united",
    "west ham": "west ham united",
    "brighton": "brighton and hove albion",
    "leicester": "leicester city",
    "leeds": "leeds united",
    "blackburn": "blackburn rovers",
    "qpr": "queens park rangers",
    "preston": "preston north end",
    "west brom": "west bromwich albion",
    "inter": "internazionale",
    "inter milan": "internazionale",
    "ac milan": "milan",
    "juve": "juventus",
    "roma": "as roma",
    "lazio": "ss lazio",
    "napoli": "ssc napoli",
    "atletico": "atletico madrid",
    "atletico de madrid": "atletico madrid",
    "ath bilbao": "athletic club",
    "real sociedad": "real sociedad",
    "betis": "real betis",
    "bayern": "bayern munich",
    "dortmund": "borussia dortmund",
    "leverkusen": "bayer leverkusen",
    "rb leipzig": "rb leipzig",
    "gladbach": "borussia monchengladbach",
    "psg": "paris saint germain",
    "marseille": "olympique marseille",
    "lyon": "olympique lyonnais",
    "fck": "fc copenhagen",
    "fc københavn": "fc copenhagen",
    "bif": "brondby if",
    "brøndby": "brondby if",
    "fcm": "fc midtjylland",
    "agf": "agf aarhus",
    "aab": "aalborg bk",
    "ob": "odense boldklub",
    "rfc": "randers fc",
    "sif": "silkeborg if",
    "vff": "viborg ff",
    "fcn": "fc nordsjaelland",
}


def normaliser_hold(navn):
    txt = str(navn or "").strip().lower()
    txt = txt.replace("ø", "o").replace("æ", "ae").replace("å", "aa").replace("é", "e").replace("ü", "u")
    txt = re.sub(r"[^a-z0-9\s]", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    if txt in _ALIAS:
        return _ALIAS[txt]
    ren = re.sub(r"\b(fc|cf|ac|sc|bk|if|fk|sk|cd|ud|rcd|afc|ssc|as|ss)\b", "", txt)
    ren = re.sub(r"\s+", " ", ren).strip()
    return _ALIAS.get(ren, ren or txt)


def samme_hold(h1, h2):
    a, b = normaliser_hold(h1), normaliser_hold(h2)
    if not a or not b:
        return False
    return a == b or a in b or b in a
