import os, json, sqlite3, urllib.request, urllib.error
import streamlit as st
from tidsstyring.dansk_tid import dansk_nu

DB_STI = os.path.join("historik", "kuponer.db")
TABEL = "kuponer"

def _supabase_cfg():
    try:
        url = st.secrets.get("SUPABASE_URL", "").strip().rstrip("/")
        key = st.secrets.get("SUPABASE_KEY", "").strip()
        if url and key:
            return url, key
    except Exception:
        pass
    return None, None

def _init_sqlite():
    os.makedirs("historik", exist_ok=True)
    con = sqlite3.connect(DB_STI)
    con.execute(f"""CREATE TABLE IF NOT EXISTS {TABEL} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dato TEXT, kampe TEXT, total_odds REAL,
        indsats REAL, mulig_gevinst REAL, status TEXT)""")
    con.commit()
    con.close()

def gem_kupon(kampe_liste, total_odds, indsats=100.0):
    dato_str = dansk_nu().strftime("%d-%m-%Y %H:%M")
    kampe_json = json.dumps(kampe_liste, ensure_ascii=False)
    gevinst = round(float(total_odds) * float(indsats), 2)
    post = {
        "dato": dato_str, "kampe": kampe_json,
        "total_odds": round(float(total_odds), 2),
        "indsats": float(indsats), "mulig_gevinst": gevinst,
        "status": "[AFVENTER]"
    }
    url, key = _supabase_cfg()
    if url and key:
        try:
            req = urllib.request.Request(
                f"{url}/rest/v1/{TABEL}",
                data=json.dumps(post).encode("utf-8"),
                headers={
                    "apikey": key, "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation"
                }, method="POST")
            with urllib.request.urlopen(req, timeout=8) as res:
                if res.status in (200, 201):
                    return True, "✅ Kupon gemt i Supabase Cloud!"
        except urllib.error.HTTPError as e:
            st.warning(f"Supabase HTTP {e.code}: {e.read().decode('utf-8','ignore')} – gemmer lokalt.")
        except Exception as e:
            st.warning(f"Supabase utilgængelig ({e}) – gemmer lokalt.")

    _init_sqlite()
    con = sqlite3.connect(DB_STI)
    con.execute(f"INSERT INTO {TABEL} (dato,kampe,total_odds,indsats,mulig_gevinst,status) VALUES (?,?,?,?,?,?)",
                (post["dato"], post["kampe"], post["total_odds"], post["indsats"], post["mulig_gevinst"], post["status"]))
    con.commit()
    con.close()
    return True, "✅ Kupon gemt i lokal SQLite-hukommelse!"
