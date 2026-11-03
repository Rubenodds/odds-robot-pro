import sqlite3
import random
import datetime

def init_database():
    conn = sqlite3.connect("odds_pro_hukommelse.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historik_pro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dato TEXT,
            tidspunkt TEXT,
            liga TEXT,
            hjemmehold TEXT,
            udehold TEXT,
            marked TEXT,
            spilforslag TEXT,
            odds REAL,
            status TEXT DEFAULT 'Afventer'
        )
    """)
    conn.commit()
    conn.close()

def hent_pro_kampe(valgte_ligaer, tidsfilter_timer):
    # Komplet database af simulerede live-kampe med præcise starttider
    nu = datetime.datetime.now()
    
    alle_kampe = [
        {"liga": "Premier League", "hj": "Man City", "ud": "Arsenal", "start": nu + datetime.timedelta(hours=2)},
        {"liga": "Premier League", "hj": "Liverpool", "ud": "Chelsea", "start": nu + datetime.timedelta(hours=5)},
        {"liga": "Superligaen", "hj": "FCK", "ud": "Brøndby", "start": nu + datetime.timedelta(hours=1.5)},
        {"liga": "Superligaen", "hj": "FC Midtjylland", "ud": "AGF", "start": nu + datetime.timedelta(hours=24)},
        {"liga": "LaLiga", "hj": "Real Madrid", "ud": "Barcelona", "start": nu + datetime.timedelta(hours=28)},
        {"liga": "Serie A (Italien)", "hj": "Inter", "ud": "Juventus", "start": nu + datetime.timedelta(hours=4)},
        {"liga": "Bundesliga (Tyskland)", "hj": "Bayern München", "ud": "Dortmund", "start": nu + datetime.timedelta(hours=42)},
        {"liga": "Champions League", "hj": "Real Madrid", "ud": "Man City", "start": nu + datetime.timedelta(hours=12)},
        {"liga": "Championship (England)", "hj": "Leeds", "ud": "Burnley", "start": nu + datetime.timedelta(hours=3)},
        {"liga": "Betano Pokalen", "hj": "Silkeborg", "ud": "Viborg", "start": nu + datetime.timedelta(hours=2.5)}
    ]
    
    filtrerede_kampe = []
    for k in alle_kampe:
        # Tjek om ligaen er valgt af brugeren
        if k["liga"] in valgte_ligaer:
            # Tjek om kampen starter inden for tidsfristen (f.eks. 3 eller 48 timer)
            timer_til_start = (k["start"] - nu).total_seconds() / 3600
            if timer_til_start <= tidsfilter_timer:
                filtrerede_kampe.append(k)
                
    return filtrerede_kampe

def generer_pro_forslag(kamp, marked):
    hj = kamp["hj"]
    ud = kamp["ud"]
    
    # Avancerede statistiske markeder
    if marked == "Hjørnespark":
        valg = [f"Over 8.5 hjørnespark i kampen", f"Over 4.5 hjørnespark til {hj}", f"Flest hjørnespark: {hj}"]
        odds = [1.55, 1.72, 1.60]
    elif marked == "Spillerskud / Skud på mål":
        valg = [f"Byg spil: Topscorer skyder 1+ skud på mål", f"Byg spil: Hjemmehold over 4.5 skud på mål", f"Udehold over 3.5 skud på mål"]
        odds = [1.45, 1.80, 1.65]
    elif marked == "Tacklinger / Redninger":
        valg = [f"Byg spil: Midtbanegeneral laver 2+ tacklinger", f"Målmand ({ud}) laver over 3.5 redninger", f"Over 22.5 tacklinger i kampen"]
        odds = [1.68, 1.85, 1.70]
    elif marked == "Kort sandsynlighed":
        valg = [f"Over 3.5 kort i kampen", f"Byg spil: Kampens forsvarsspiller får kort", f"Flest kort i kampen: {ud}"]
        odds = [1.60, 2.95, 2.10]
    elif marked == "Målscorer":
        valg = [f"Hjemmeholdets angriber scorer i kampen", f"Første målscorer: Spiller fra {hj}", f"Begge hold scorer (Ja)"]
        odds = [2.20, 1.95, 1.65]
    else: # Standard / Kombination
        valg = [f"Byg Væddemål: {hj} vinder + Over 2.5 mål", f"Dobbeltchance: {hj} eller Uafgjort", f"Over 1.5 mål i 1. halvleg"]
        odds = [2.40, 1.30, 2.15]
        
    idx = random.randint(0, 2)
    return valg[idx], odds[idx]

def byg_pro_kupon(maal_odds, antal_kampe, valgte_ligaer, tidsfilter_timer, markeder):
    kampe_pulje = hent_pro_kampe(valgte_ligaer, tidsfilter_timer)
    
    if not kampe_pulje or not markeder:
        return [], 1.0
        
    antal = min(antal_kampe, len(kampe_pulje))
    valgte_kampe = random.sample(kampe_pulje, antal)
    
    kupon = []
    samlet_odds = 1.0
    
    for k in valgte_kampe:
        marked = random.choice(markeder)
        spil, o = generer_pro_forslag(k, marked)
        
        # Dynamisk AI-justering for at ramme odds-målet
        justering = (maal_odds / 20.0) ** (1 / antal)
        if justering < 0.8: justering = 0.8
        if justering > 2.2: justering = 2.2
        
        nyt_odds = round(o * justering, 2)
        if nyt_odds < 1.15: nyt_odds = 1.15
        
        kupon.append({
            "liga": k["liga"], "hjemme": k["hj"], "ude": k["ud"],
            "marked": marked, "spil": spil, "odds": nyt_odds
        })
        samlet_odds *= nyt_odds
        
    return kupon, round(samlet_odds, 2)

def gem_pro_kupon(dato, tid, liga, hj, ud, marked, spil, o, status):
    conn = sqlite3.connect("odds_pro_hukommelse.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO historik_pro (dato, tidspunkt, liga, hjemmehold, udehold, marked, spilforslag, odds, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (dato, tid, liga, hj, ud, marked, spil, o, status))
    conn.commit()
    conn.close()
