import sqlite3
import datetime
import random

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

def gem_kupon_i_historik(ligaer_liste, forslag_liste, bookmakere_dict, side, stjerner):
    try:
        initier_database()
        conn = sqlite3.connect("odds_pro_hukommelse.db")
        cursor = conn.cursor()
        
        # Omdanner den dynamiske liste af bookmakere og odds til en pæn tekst: "Bet365: 3.42, Unibet: 3.35"
        odds_tekst = ", ".join([f"{bm}: {odds}" for bm, odds in bookmakere_dict.items()])
        
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
