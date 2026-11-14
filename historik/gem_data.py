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
        id INTEGER PRIMARY KEY AUTOINCREMENT, dato TEXT, kilde TEXT,
        kampe TEXT, detaljer TEXT, odds REAL, indsats REAL,
        mulig_gevinst REAL, status TEXT)""")
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
    kilde = kwargs.get("kilde", "Scanner")
    kampe = kwargs.get("kampe") or kwargs.get("kampe_liste") or []
    odds = kwargs.get("odds") or kwargs.get("total_odds") or kwargs.get("samlet_odds")
    for a in args:
        if isinstance(a, str) and not kampe:
            kilde = a
        elif isinstance(a, (list, tuple)) and not kampe:
            kampe = list(a)
        elif isinstance(a, (int, float)) and odds is None:
            odds = float(a)
    odds = round(float(odds or 1.0), 2)
    indsats = float(kwargs.get("indsats", 100.0))
    gevinst = round(odds * indsats, 2)
    antal = len(kampe) if isinstance(kampe, (list, tuple)) else 1
    dato = _dansk_tid_str()
    kort_titel = f"{antal} kampe ({dato})"
    detaljer_json = json.dumps(kampe, ensure_ascii=False)
    post = {
        "dato": dato, "kilde": kilde, "kampe": kort_titel,
        "detaljer": detaljer_json, "odds": odds, "indsats": indsats,
        "mulig_gevinst": gevinst, "status": "[AFVENTER]"
    }
    _init_sqlite()
    con = sqlite3.connect(DB_STI)
    con.execute(f"INSERT INTO {TABEL} (dato,kilde,kampe,detaljer,odds,indsats,mulig_gevinst,status) VALUES (?,?,?,?,?,?,?,?)",
                (post["dato"], post["kilde"], post["kampe"], post["detaljer"], post["odds"], post["indsats"], post["mulig_gevinst"], post["status"]))
    con.commit()
    con.close()
    return True, "✅ Kupon gemt!"

gem_kupon = gem_kupon_i_historik
gem_spil = gem_kupon_i_historik
hent_spil = hent_alle_kuponer
