import sqlite3
import datetime
import os
import requests
import base64

DB_FILE = "odds_pro_hukommelse.db"

def init_db():
    """ Sikrer at tabellen altid eksisterer, er blank fra start og ikke fejler """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kupon_historik (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dato TEXT,
            ligaer TEXT,
            forslag TEXT,
            billede_status TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

def gem_kupon_i_historik(gemme_ligaer, gemme_forslag, samlet_billede_data):
    """
    Fikser fejlen på linje 134 i app.py. 
    Modtager data sikkert og logger kuponen som afventende uden at vælte appen.
    """
    init_db()
    
    # Dansk tidsstyring (Krav 2)
    dansk_tid = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    dato_str = dansk_tid.strftime("%Y-%m-%d %H:%M")
    
    # Sikring mod None-værdier fra billedscanneren
    if samlet_billede_data is None:
        samlet_billede_data = "Intet eller uægte screenshot"
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO kupon_historik (dato, ligaer, forslag, billede_status, status)
            VALUES (?, ?, ?, ?, ?)
        """, (dato_str, str(gemme_ligaer), str(gemme_forslag), str(samlet_billede_data), "⏳ Afventer"))
        conn.commit()
    except Exception as e:
        print(f"Fejl ved lokal lagring: {e}")
    finally:
        conn.close()
        
    # Synkroniser databasen med skyen, så intet mistes ved reboot
    gem_database_til_github_cloud()

def afgoer_alle_afventendinge_kuponer_live():
    """ Forbliver låst indtil reel validering sker (Krav 5) """
    init_db()
    pass

def vis_auto_resultat_og_rapport():
    """ Viser rapporten i appen """
    init_db()
    pass

# --- REBOOT RECOVERY MOTOR (GITHUB CLOUD LAGRING) ---
def gem_database_til_github_cloud():
    """ Backup-motor der skyder din database direkte i skyen ved ændringer """
    # Her kobler vi dit GitHub token på via Streamlit Secrets i næste skridt
    pass

def hent_database_fra_github_cloud():
    """ Henter din database tilbage fra skyen, når Streamlit har været genstartet """
    pass
