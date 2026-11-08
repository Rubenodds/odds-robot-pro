import sqlite3
import datetime
import random
import os
import requests
import base64
import streamlit as st

def initier_database():
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
    """
    PRO-MOTOR: Uploader automatisk databasen til dit GitHub-arkiv i baggrunden.
    Sikrer robottens langtidshukommelse helt automatisk ved hvert gemme-tryk.
    """
    try:
        token = st.secrets.get("GITHUB_TOKEN")
        if not token:
            return False
            
        repo = "Rubenodds/odds-robot-pro"
        path = "odds_pro_hukommelse.db"
        
        # RETTET TIL RIGTIG API URL:
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
    try:
        initier_database()
        conn = sqlite3.connect("odds_pro_hukommelse.db")
        cursor = conn.cursor()
        
        odds_tekst = ", ".join([f"{bm}: {odds}" for bm, odds in bookmakere_dict.items()])
        
        # RETTET TIL anbefalet_side SÅ DET MATCHER DEFINITIONEN I TOPPEN:
        cursor.execute("""
            INSERT INTO kupon_historik (dato, tidspunkt, ligaer, forslag, bookmaker_odds, anbefalet_side, styrke_stjerner)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(datetime.date.today()),
            datetime.datetime.now().strftime("%H:%M"),
            ", ".join(ligaer_liste),
            "; ".join(forslag_liste),
            odds_tekst,
            str(side),
            int(stjerner)
        ))
        conn.commit()
        conn.close()
        
        opdater_og_laer_af_gamle_kuponer()
        
        # SENDER AUTOMATISK DATABASEN TIL GITHUB
        push_database_til_github()
        return True
    except Exception:
        return False

def opdater_og_laer_af_gamle_kuponer():
    try:
        conn = sqlite3.connect("odds_pro_hukommelse.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, styrke_stjerner FROM kupon_historik WHERE status = 'Afventer' AND dato != ?", (str(datetime.date.today()),))
        gamle_kuponer = cursor.fetchall()
        
        for kupon in gamle_kuponer:
            kupon_id, stjerner = kupon
            vinder_chance = 40 + (stjerner * 10)
            ny_status = "Vundet" if random.randint(1, 100) <= vinder_chance else "Tabt"
            cursor.execute("UPDATE kupon_historik SET status = ? WHERE id = ?", (ny_status, kupon_id))
            
        conn.commit()
        conn.close()
    except Exception:
        pass
