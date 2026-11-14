import os, json, sqlite3, urllib.request
from datetime import datetime, timedelta
import streamlit as st

DB_STI = os.path.join("historik", "kuponer.db")
TABEL = "kuponer"

def _dansk_tid_str():
    return (datetime.utcnow() + timedelta(hours=1)).strftime("%d-%m-%Y %H:%M")

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

@st.cache_data(ttl=15, show_spinner=False)
def hent_alle_kuponer():
    url, key = _supabase_cfg()
    if url and key:
        try:
            req = urllib.request.Request(
                f"{url}/rest/v1/{TABEL}?select=*&order=id.desc",
                headers={"apikey": key, "Authorization": f"Bearer {key}"})
            with urllib.request.urlopen(req, timeout=2) as res:
                return json.loads(res.read().decode("utf-8"))
        except Exception:
            pass
    _init_sqlite()
    con = sqlite3.connect(DB_STI)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(f"SELECT * FROM {TABEL} ORDER BY id DESC").fetchall()]
    con.close()
    return rows

def gem_kupon_i_historik(*args, **kwargs):
    st.cache_data.clear()
    kampe = kwargs.get("kampe") or kwargs.get("kampe_liste") or (args[0] if len(args) > 0 else [])
    odds = kwargs.get("total_odds") or kwargs.get("samlet_odds") or (args[1] if len(args) > 1 and isinstance(args[1], (int, float)) else 1.0)
    indsats = kwargs.get("indsats", 100.0)
    gevinst = kwargs.get("mulig_gevinst") or round(float(odds) * float(indsats), 2)
    post = {
        "dato": _dansk_tid_str(),
        "kampe": json.dumps(kampe, ensure_ascii=False) if not isinstance(kampe, str) else kampe,
        "total_odds": round(float(odds), 2),
        "indsats": float(indsats),
        "mulig_gevinst": round(float(gevinst), 2),
        "status": "[AFVENTER]"
    }
    url, key = _supabase_cfg()
    if url and key:
        try:
            req = urllib.request.Request(
                f"{url}/rest/v1/{TABEL}", data=json.dumps(post).encode("utf-8"),
                headers={"apikey": key, "Authorization": f"Bearer {key}",
                         "Content-Type": "application/json", "Prefer": "return=representation"},
                method="POST")
            with urllib.request.urlopen(req, timeout=3) as res:
                if res.status in (200, 201):
                    return True, "✅ Kupon gemt i Supabase Cloud!"
        except Exception:
            pass
    _init_sqlite()
    con = sqlite3.connect(DB_STI)
    con.execute(f"INSERT INTO {TABEL} (dato,kampe,total_odds,indsats,mulig_gevinst,status) VALUES (?,?,?,?,?,?)",
                (post["dato"], post["kampe"], post["total_odds"], post["indsats"], post["mulig_gevinst"], post["status"]))
    con.commit()
    con.close()
    return True, "✅ Kupon gemt i lokal SQLite-hukommelse!"

gem_kupon = gem_kupon_i_historik
gem_spil = gem_kupon_i_historik
hent_spil = hent_alle_kuponer
