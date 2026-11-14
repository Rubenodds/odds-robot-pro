import os, json, sqlite3, urllib.request
import pandas as pd
import streamlit as st
from historik.gem_data import DB_STI, TABEL, _supabase_cfg, _init_sqlite

def _hent_alle():
    url, key = _supabase_cfg()
    if url and key:
        try:
            req = urllib.request.Request(
                f"{url}/rest/v1/{TABEL}?select=*&order=id.desc",
                headers={"apikey": key, "Authorization": f"Bearer {key}"})
            with urllib.request.urlopen(req, timeout=8) as res:
                return json.loads(res.read().decode("utf-8")), "Supabase"
        except Exception:
            pass
    _init_sqlite()
    con = sqlite3.connect(DB_STI)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(f"SELECT * FROM {TABEL} ORDER BY id DESC").fetchall()]
    con.close()
    return rows, "Lokal SQLite"

def _opdater_status(kid, ny_status, kilde):
    url, key = _supabase_cfg()
    if kilde == "Supabase" and url and key:
        try:
            req = urllib.request.Request(
                f"{url}/rest/v1/{TABEL}?id=eq.{kid}",
                data=json.dumps({"status": ny_status}).encode("utf-8"),
                headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                method="PATCH")
            urllib.request.urlopen(req, timeout=8)
            return
        except Exception:
            pass
    con = sqlite3.connect(DB_STI)
    con.execute(f"UPDATE {TABEL} SET status=? WHERE id=?", (ny_status, kid))
    con.commit()
    con.close()

def vis_regnskab():
    rækker, kilde = _hent_alle()
    st.caption(f"📡 Datakilde aktiv: **{kilde}**")
    if not rækker:
        st.info("Ingen gemte kuponer endnu. Tryk på 🚀 SPILLET for at gemme din første kupon.")
        return

    df = pd.DataFrame(rækker)
    df["aar"] = df["dato"].astype(str).str.slice(6, 10)
    afgjorte = df[df["status"].isin(["VUNDET", "TABT"])]
    vundne = df[df["status"] == "VUNDET"]
    oms = afgjorte["indsats"].sum() if not afgjorte.empty else 0.0
    udb = vundne["mulig_gevinst"].sum() if not vundne.empty else 0.0
    netto = round(udb - oms, 2)
    hit = round((len(vundne) / len(afgjorte) * 100), 1) if len(afgjorte) else 0.0
    roi = round((udb / oms * 100), 1) if oms > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 TOTAL SUM", f"{netto:+.2f} kr.")
    c2.metric("🎯 Hitrate", f"{hit}%")
    c3.metric("📈 Tilbagebetaling", f"{roi}%")
    c4.metric("🎟️ Kuponer", len(df))

    for r in rækker:
        st_txt = r.get("status", "[AFVENTER]")
        with st.container(border=True):
            st.markdown(f"**🎟️ Kupon #{r['id']}** | 📅 {r['dato']} | Odds: **{r['total_odds']}** | Gevinst: **{r['mulig_gevinst']} kr.** | Status: **{st_txt}**")
            kampe = json.loads(r["kampe"]) if isinstance(r["kampe"], str) else r["kampe"]
            for k in (kampe or []):
                st.write(f"• {k}")
            b1, b2, b3 = st.columns(3)
            if b1.button("✅ Vundet", key=f"v_{r['id']}"):
                _opdater_status(r["id"], "VUNDET", kilde); st.rerun()
            if b2.button("❌ Tabt", key=f"t_{r['id']}"):
                _opdater_status(r["id"], "TABT", kilde); st.rerun()
            if b3.button("⏳ Afventer", key=f"a_{r['id']}"):
                _opdater_status(r["id"], "[AFVENTER]", kilde); st.rerun()
