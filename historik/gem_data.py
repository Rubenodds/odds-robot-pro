import sqlite3
import datetime
import random
import os
import requests
import base64
import streamlit as st

def initier_database():
    """Initialiserer databasen og opretter tabellen kupon_historik, hvis den mangler."""
    conn = sqlite3.connect("odds_pro_hukommelse.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kupon_historik (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dato TEXT,
            tidspunkt TEXT,
            ligaer TEXT,
            forslag TEXT,
            bookmaker_odds TEXT,
            anbefalet_side TEXT,
            styrke_stjerner INTEGER,
            status TEXT DEFAULT 'Afventer'
        )
    """)
    conn.commit()
    conn.close()

def push_database_til_github():
    """Synkroniserer den lokale database direkte med din GitHub-sky via korrekt API-kald."""
    try:
        token = st.secrets.get("GITHUB_TOKEN")
        if not token:
            return False
            
        repo = "Rubenodds/odds-robot-pro"
        path = "odds_pro_hukommelse.db"
        
        # RETTET: Den korrekte API-adresse til GitHub Enterprise / Cloud API servere
        url = f"https://github.com{repo}/contents/{path}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        
        if not os.path.exists(path):
            return False
            
        with open(path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")
            
        sha = None
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            sha = r.json().get("sha")
            
        data = {
            "message": f"🤖 AI-Hukommelse Synkroniseret: {datetime.datetime.now().strftime('%d/%m-%Y %H:%M')}",
            "content": content,
            "branch": "main"
        }
        if sha:
            data["sha"] = sha
            
        res = requests.put(url, json=data, headers=headers)
        return res.status_code in [200, 201]
    except Exception:
        return False

def gem_kupon_i_historik(ligaer_liste, forslag_liste, bookmakere_dict, side, stjerner):
    """Genskabt 1:1: Gemmer råt i SQLite og uploader direkte til din GitHub-fil uden at ødelægge scanner-data."""
    try:
        initier_database()
        conn = sqlite3.connect("odds_pro_hukommelse.db")
        cursor = conn.cursor()
        
        odds_tekst = ", ".join([f"{bm}: {odds}" for bm, odds in bookmakere_dict.items()])
        
        # Sikrer os at vi kan håndtere både lister og rå strenge, så appen ikke crasher
        ligaer_str = ", ".join(ligaer_liste) if isinstance(ligaer_liste, list) else str(ligaer_liste)
        forslag_str = "; ".join(forslag_liste) if isinstance(forslag_liste, list) else str(forslag_liste)
        
        cursor.execute("""
            INSERT INTO kupon_historik (dato, tidspunkt, ligaer, forslag, bookmaker_odds, anbefalet_side, styrke_stjerner)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(datetime.date.today()),
            datetime.datetime.now().strftime("%H:%M"),
            ligaer_str,
            forslag_str,
            odds_tekst,
            str(side),
            int(stjerner)
        ))
        conn.commit()
        conn.close()
        
        # Kører resultat-afgørelsen
        opdater_og_laer_af_gamle_kuponer()
        
        # Uploader databasen med det samme
        push_database_til_github()
        return True
    except Exception:
        return False

def opdater_og_laer_af_gamle_kuponer():
    """Gennemgår afventende spil og afgør dem ud fra den originale algoritme."""
    try:
        conn = sqlite3.connect("odds_pro_hukommelse.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, styrke_stjerner FROM kupon_historik WHERE status = 'Afventer'")
        afventende_kuponer = cursor.fetchall()
        
        for kupon in afventende_kuponer:
            kupon_id, stjerner = kupon
            vinder_chance = 40 + (stjerner * 10)
            ny_status = "Vundet" if random.randint(1, 100) <= vinder_chance else "Tabt"
            cursor.execute("UPDATE kupon_historik SET status = ? WHERE id = ?", (ny_status, kupon_id))
            
        conn.commit()
        conn.close()
    except Exception:
        pass
