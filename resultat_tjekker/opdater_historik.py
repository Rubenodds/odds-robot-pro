import sqlite3
import datetime
import os
import requests
import base64
import streamlit as st

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

def hent_github_config():
    """ Henter dine krypterede data sikkert fra Streamlit Secrets """
    try:
        return (
            st.secrets["github"]["token"],
            st.secrets["github"]["username"],
            st.secrets["github"]["repo"]
        )
    except Exception:
        return None, None, None

def gem_database_til_github_cloud():
    """ Backup-motor der skyder din database direkte op på GitHub ved ændringer """
    token, username, repo = hent_github_config()
    if not token or not os.path.exists(DB_FILE):
        return

    # RETTET URL-ADRESSE TIL OFFICIAL API
    url = f"https://api.github.com/repos/{username}/{repo}/contents/{DB_FILE}"
    headers = {"Authorization": f"token {token}", "Accept": "application/json"}

    try:
        with open(DB_FILE, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")

        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None

        data = {
            "message": f"🤖 Odds-Robot-Pro: Automatisk database-backup [{datetime.datetime.utcnow() + datetime.timedelta(hours=1)}]",
            "content": content,
        }
        if sha:
            data["sha"] = sha

        requests.put(url, headers=headers, json=data)
    except Exception as e:
        print(f"Cloud backup fejlede: {e}")

def hent_database_fra_github_cloud():
    """ Gendannelses-motor: Henter din database tilbage, hvis Streamlit har været genstartet """
    token, username, repo = hent_github_config()
    if not token:
        return

    # RETTET URL-ADRESSE TIL OFFICIAL API
    url = f"https://api.github.com/repos/{username}/{repo}/contents/{DB_FILE}"
    headers = {"Authorization": f"token {token}", "Accept": "application/json"}

    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            file_data = res.json()
            content = base64.b64decode(file_data["content"])
            with open(DB_FILE, "wb") as f:
                f.write(content)
    except Exception as e:
        print(f"Kunne ikke hente cloud-database ved opstart: {e}")

def gem_kupon_i_historik(gemme_ligaer, gemme_forslag, samlet_billede_data):
    """ Fikser fejlen på linje 134 i app.py og logger kuponen """
    if not os.path.exists(DB_FILE):
        hent_database_fra_github_cloud()
        
    init_db()
    
    dansk_tid = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    dato_str = dansk_tid.strftime("%Y-%m-%d %H:%M")
    
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
        
    gem_database_til_github_cloud()

def afgoer_alle_afventende_kuponer_live():
    if not os.path.exists(DB_FILE):
        hent_database_fra_github_cloud()
    init_db()

def vis_auto_resultat_og_rapport():
    if not os.path.exists(DB_FILE):
        hent_database_fra_github_cloud()
    init_db()
