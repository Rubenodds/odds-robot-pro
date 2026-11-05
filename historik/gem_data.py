import sqlite3
import datetime

def initier_database():
    conn = sqlite3.connect("odds_pro_hukommelse.db")
    cursor = conn.cursor()
    # Opretter historiktabellen, hvis den ikke eksisterer i forvejen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kupon_historik (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dato TEXT,
            tidspunkt TEXT,
            ligaer TEXT,
            forslag TEXT,
            odds_b365 REAL,
            odds_unibet REAL,
            odds_oddset REAL,
            anbefalet_side TEXT,
            styrke_stjerner INTEGER,
            status TEXT DEFAULT 'Afventer'
        )
    """)
    conn.commit()
    conn.close()

def gem_kupon_i_historik(ligaer_liste, forslag_liste, o_b365, o_uni, o_odd, side, stjerner):
    try:
        initier_database()
        conn = sqlite3.connect("odds_pro_hukommelse.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO kupon_historik (dato, tidspunkt, ligaer, forslag, odds_b365, odds_unibet, odds_oddset, anbefalet_side, styrke_stjerner)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(datetime.date.today()),
            datetime.datetime.now().strftime("%H:%M"),
            ", ".join(ligaer_liste),
            "; ".join(forslag_liste),
            float(o_b365),
            float(o_uni),
            float(o_odd),
            str(side),
            int(stjerner)
        ))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False
