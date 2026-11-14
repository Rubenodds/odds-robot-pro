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

def _sb_req(sti, metode="GET", data=None):
    url, key = _supabase_cfg()
    if not url or not key:
        return None
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if metode == "POST":
        headers["Prefer"] = "return=representation"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(f"{url}/rest/v1/{sti}", data=body, headers=headers, method=metode)
    with urllib.request.urlopen(req, timeout=3) as res:
        txt = res.read().decode("utf-8")
        return json.loads(txt) if txt else True

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
    try:
        res = _sb_req(f"{TABEL}?select=*&order=id.desc")
        if isinstance(res, list):
            return res
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
    kilde, kampe, tal = "Scanner", [], []
    for a in args:
        if isinstance(a, (list, tuple)) and a and any(":" in str(x) or "vs" in str(x) or "-" in str(x) for x in a):
            kampe = list(a)
        elif isinstance(a, (int, float)):
            tal.append(float(a))
        elif isinstance(a, str):
            kilde = a
    kampe = kwargs.get("kampe") or kampe
    odds = round(float(kwargs.get("odds") or kwargs.get("total_odds") or next(iter(tal), 1.0)), 2)
    indsats = float(kwargs.get("indsats") or (tal[-1] if len(tal) >= 4 else 100.0))
    dato = _dansk_tid_str()
    post = {
        "dato": dato, "kilde": kilde, "kampe": f"{len(kampe)} kampe ({dato})",
        "detaljer": json.dumps(kampe, ensure_ascii=False), "odds": odds,
        "indsats": indsats, "mulig_gevinst": round(odds * indsats, 2), "status": "[AFVENTER]"
    }
    try:
        ok = bool(_sb_req(TABEL, "POST", post))
    except Exception:
        ok = False
    if not ok:
        _init_sqlite()
        con = sqlite3.connect(DB_STI)
        con.execute(f"INSERT INTO {TABEL} (dato,kilde,kampe,detaljer,odds,indsats,mulig_gevinst,status) VALUES (?,?,?,?,?,?,?,?)",
                    (post["dato"], post["kilde"], post["kampe"], post["detaljer"], post["odds"], post["indsats"], post["mulig_gevinst"], post["status"]))
        con.commit()
        con.close()
    st.toast("OK – tilføjet til historikken")
    return True

gem_kupon = gem_kupon_i_historik
gem_spil = gem_kupon_i_historik
hent_spil = hent_alle_kuponer
