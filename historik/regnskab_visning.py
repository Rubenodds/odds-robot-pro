import json, sqlite3
from collections import defaultdict
import pandas as pd
import streamlit as st
from historik.gem_data import DB_STI, TABEL, hent_alle_kuponer, _sb_req

def _opdater_status(kid, ny_status):
    st.cache_data.clear()
    try:
        if _sb_req(f"{TABEL}?id=eq.{kid}", "PATCH", {"status": ny_status}):
            return
    except Exception:
        pass
    con = sqlite3.connect(DB_STI)
    con.execute(f"UPDATE {TABEL} SET status=? WHERE id=?", (ny_status, kid))
    con.commit()
    con.close()

def _slet_kupon(kid):
    st.cache_data.clear()
    try:
        if _sb_req(f"{TABEL}?id=eq.{kid}", "DELETE"):
            return
    except Exception:
        pass
    con = sqlite3.connect(DB_STI)
    con.execute(f"DELETE FROM {TABEL} WHERE id=?", (kid,))
    con.commit()
    con.close()

def vis_regnskab():
    rækker = hent_alle_kuponer()
    if not rækker:
        st.info("Ingen gemte kuponer endnu. Tryk på 🚀 SPILLET for at gemme din første kupon.")
        return

    df = pd.DataFrame(rækker)
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
    c3.metric("📈 ROI", f"{roi}%")
    c4.metric("🎟️ Kuponer", len(df))

    mapper = defaultdict(list)
    for r in rækker:
        dag = str(r.get("dato", "Ukendt dato"))[:10]
        mapper[dag].append(r)

    for dag, kuponer in mapper.items():
        with st.expander(f"📁 {dag}  —  {len(kuponer)} kupon(er)", expanded=False):
            for r in kuponer:
                with st.container(border=True):
                    st.markdown(f"**🎟️ Kupon #{r['id']}** ({r.get('kilde','Scanner')}) | Odds: **{r.get('odds')}** | Mulig gevinst: **{r.get('mulig_gevinst')} kr.** | Status: **{r.get('status')}**")
                    raw = r.get("detaljer") or r.get("kampe")
                    try:
                        liste = json.loads(raw) if isinstance(raw, str) and raw.startswith("[") else [raw]
                    except Exception:
                        liste = [raw]
                    for k in liste:
                        st.write(f"• {k}")
                    b1, b2, b3, b4 = st.columns(4)
                    if b1.button("✅ Vundet", key=f"v_{r['id']}"):
                        _opdater_status(r["id"], "VUNDET"); st.rerun()
                    if b2.button("❌ Tabt", key=f"t_{r['id']}"):
                        _opdater_status(r["id"], "TABT"); st.rerun()
                    if b3.button("⏳ Afventer", key=f"a_{r['id']}"):
                        _opdater_status(r["id"], "[AFVENTER]"); st.rerun()
                    if b4.button("🗑️ Slet", key=f"s_{r['id']}"):
                        _slet_kupon(r["id"]); st.rerun()
