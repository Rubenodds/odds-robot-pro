import json, sqlite3
from collections import defaultdict
import pandas as pd
import streamlit as st
from historik.gem_data import DB_STI, TABEL, hent_alle_kuponer, _sb_req

def _handling(kid, valg):
    st.cache_data.clear()
    ny = {"✅ Vundet": "VUNDET", "❌ Tabt": "TABT", "⏳ Afventer": "[AFVENTER]"}.get(valg)
    try:
        if valg == "🗑️ Slet" and _sb_req(f"{TABEL}?id=eq.{kid}", "DELETE"):
            return
        if ny and _sb_req(f"{TABEL}?id=eq.{kid}", "PATCH", {"status": ny}):
            return
    except Exception:
        pass
    con = sqlite3.connect(DB_STI)
    if valg == "🗑️ Slet":
        con.execute(f"DELETE FROM {TABEL} WHERE id=?", (kid,))
    elif ny:
        con.execute(f"UPDATE {TABEL} SET status=? WHERE id=?", (ny, kid))
    con.commit()
    con.close()

def _tegn_kuponer(liste_r):
    if not liste_r:
        st.info("Ingen kuponer i denne kategori.")
        return
    maaneder = defaultdict(list)
    for r in liste_r:
        d = str(r.get("dato", "00-00-0000"))
        maaneder[f"{d[3:5]}-{d[6:10]}"].append(r)
    for mdr, kuponer in maaneder.items():
        with st.expander(f"📅 Måned {mdr}  ({len(kuponer)} kuponer)", expanded=(len(maaneder) == 1)):
            for r in kuponer:
                with st.container(border=True):
                    st.markdown(f"**🎟️ #{r['id']}** | {str(r.get('dato',''))[:10]} | Odds **{r.get('odds')}** | Gevinst **{r.get('mulig_gevinst')} kr.** | **{r.get('status')}**")
                    raw = r.get("detaljer") or r.get("kampe")
                    try:
                        kampe = json.loads(raw) if isinstance(raw, str) and raw.startswith("[") else [raw]
                    except Exception:
                        kampe = [raw]
                    for k in kampe:
                        st.caption(f"• {k}")
                    c1, c2 = st.columns([3, 1])
                    valg = c1.selectbox("Handling", ["✅ Vundet", "❌ Tabt", "⏳ Afventer", "🗑️ Slet"], key=f"sel_{r['id']}", label_visibility="collapsed")
                    if c2.button("OK", key=f"ok_{r['id']}"):
                        _handling(r["id"], valg); st.rerun()

def vis_regnskab():
    rækker = hent_alle_kuponer()
    if not rækker:
        st.info("Ingen gemte kuponer endnu.")
        return
    df = pd.DataFrame(rækker)
    afg = df[df["status"].isin(["VUNDET", "TABT"])]
    vun = df[df["status"] == "VUNDET"]
    oms = afg["indsats"].sum() if not afg.empty else 0.0
    udb = vun["mulig_gevinst"].sum() if not vun.empty else 0.0
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 TOTAL SUM", f"{udb - oms:+.2f} kr.")
    c2.metric("🎯 Hitrate", f"{(len(vun)/len(afg)*100 if len(afg) else 0):.1f}%")
    c3.metric("📈 ROI", f"{(udb/oms*100 if oms else 0):.1f}%")

    f1, f2, f3 = st.tabs(["⏳ Afventer", "✅ Afgjorte", "🗂️ Alle"])
    with f1:
        _tegn_kuponer([r for r in rækker if r.get("status") == "[AFVENTER]"])
    with f2:
        _tegn_kuponer([r for r in rækker if r.get("status") in ("VUNDET", "TABT")])
    with f3:
        _tegn_kuponer(rækker)
