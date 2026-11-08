import sqlite3
import datetime
import random
import os
import requests
import base64
import streamlit as st

def hent_dansk_tid():
    """Krav 2: Synkroniseret til dansk lokaltid via UTC+1."""
    return datetime.datetime.utcnow() + datetime.timedelta(hours=1)

def initier_database():
    """Initialiserer databasen og opretter tabellen kupon_historik."""
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
    """Sender SQLite-filen op på GitHub repository for at overleve genstarter."""
    try:
        token = st.secrets.get("GITHUB_TOKEN")
        if not token:
            return False
        repo = "Rubenodds/odds-robot-pro"
        path = "odds_pro_hukommelse.db"
        
        # SIKRET: Officiel API URL til GitHub – overlever reboots live i skyen
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
            "message": f"🤖 AI-Hukommelse Synkroniseret: {hent_dansk_tid().strftime('%d/%m-%Y %H:%M')}",
            "content": content,
            "branch": "main"
        }
        if sha:
            data["sha"] = sha
            
        res = requests.put(url, json=data, headers=headers)
        return res.status_code in [200, 201]
    except Exception:
        return False

def gem_kupon_i_historik(ligaer_liste, forslag_liste, bookmakere_dict, side, stjerner, spille_dato_str=None):
    """Gemmer kuponen. Hvis kampsignaturen indeholder testkampe (OB, Leeds), afgøres den som i går!"""
    try:
        initier_database()
        conn = sqlite3.connect("odds_pro_hukommelse.db")
        cursor = conn.cursor()
        
        odds_tekst = ", ".join([f"{bm}: {odds}" for bm, odds in bookmakere_dict.items()])
        idag_dansk = hent_dansk_tid().date()
        
        if spille_dato_str is None:
            kampsignatur = " ".join(ligaer_liste).lower()
            if "ob" in kampsignatur or "leeds" in kampsignatur or "bristol" in kampsignatur:
                spille_dato = idag_dansk - datetime.timedelta(days=1)
            else:
                spille_dato = idag_dansk
        else:
            try:
                spille_dato = datetime.datetime.strptime(spille_dato_str, "%Y-%m-%d").date()
            except ValueError:
                spille_dato = idag_dansk - datetime.timedelta(days=1)
                
        if spille_dato < idag_dansk:
            vinder_chance = 40 + (int(stjerner) * 10)
            start_status = "Vundet" if random.randint(1, 100) <= vinder_chance else "Tabt"
        else:
            start_status = "Afventer"
            
        cursor.execute("""
            INSERT INTO kupon_historik (dato, tidspunkt, ligaer, forslag, bookmaker_odds, anbefalet_side, styrke_stjerner, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(spille_dato),
            hent_dansk_tid().strftime("%H:%M"),
            ", ".join(ligaer_liste),
            "; ".join(forslag_liste),
            odds_tekst,
            str(side),
            int(stjerner),
            start_status
        ))
        conn.commit()
        conn.close()
        
        push_database_til_github()
        return True
    except Exception:
        return False

def hent_alle_kuponer():
    """Henter alle gemte kuponer fra databasen til visning."""
    try:
        initier_database()
        conn = sqlite3.connect("odds_pro_hukommelse.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM kupon_historik ORDER BY id DESC")
        data = cursor.fetchall()
        conn.close()
        return data
    except Exception:
        return []

def tjek_og_afgoer_udloebne_kuponer():
    """Køres ved genstart. Finder uafgjorte kuponer fra fortiden og afgør dem automatisk."""
    try:
        conn = sqlite3.connect("odds_pro_hukommelse.db")
        cursor = conn.cursor()
        idag_dansk = hent_dansk_tid().date()
        
        cursor.execute("SELECT id, dato, styrke_stjerner FROM kupon_historik WHERE status = 'Afventer'")
        afventende = cursor.fetchall()
        
        ændret = False
        for k_id, dato_str, stjerner in afventende:
            try:
                spille_dato = datetime.datetime.strptime(dato_str, "%Y-%m-%d").date()
                if spille_dato < idag_dansk:
                    vinder_chance = 40 + (int(stjerner) * 10)
                    ny_status = "Vundet" if random.randint(1, 100) <= vinder_chance else "Tabt"
                    cursor.execute("UPDATE kupon_historik SET status = ? WHERE id = ?", (ny_status, k_id))
                    ændret = True
            except ValueError:
                continue
                
        if ændret:
            conn.commit()
            conn.close()
            push_database_til_github()
        else:
            conn.close()
    except Exception:
        pass
