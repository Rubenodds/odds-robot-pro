import json
from collections import defaultdict
import pandas as pd
import streamlit as st
from historik.gem_data import hent_alle_kuponer, _gh_laes, _gh_skriv

def _handling(kid, valg):
    raekker, sha = _gh_laes()
    ny = {"✅ Vundet": "VUNDET", "❌ Tabt": "TABT", "⏳ Afventer": "[AFVENTER]"}.get(valg)
    if valg == "🗑️ Slet":
        raekker = [r for r in raekker if r.get("id") != kid]
    elif ny:
        for r in raekker:
            if r.get("id") == kid:
                r["status"] = ny
    if _gh_skriv(raekker, sha):
        st.session_state["kupon_ram_cache"] = raekker

def _tegn_kuponer(liste_r):
    if not liste_r:
        st.caption("Ingen kuponer her endnu.")
        return
    dage = defaultdict(list)
    for r in liste_r:
        dage[str(r.get("dato", "Ukendt"))[:10]].append(r)
    for dag, kuponer in dage.items():
        with st.expander(f"📁 {dag}  ({len(kuponer)} kupon{'er' if len(kuponer)!=1 else ''})", expanded=False):
            for r in kuponer:
                st_ikon = {"VUNDET": "✅", "TABT": "❌"}.get(r.get("status"), "⏳")
                st.markdown(f"**{st_ikon} Kupon #{r['id']}** • Odds **{r.get('odds')}** • Mulig gevinst **{r.get('mulig_gevinst')} kr.**")
                raw = r.get("detaljer") or r.get("kampe")
                try:
                    kampe = json.loads(raw) if isinstance(raw, str) and raw.startswith("[") else [raw]
                except Exception:
                    kampe = [raw]
                for k in kampe:
                    st.caption(f"• {k}")
                c1, c2 = st.columns([3, 1])
                valg = c1.selectbox("Status", ["✅ Vundet", "❌ Tabt", "⏳ Afventer", "🗑️ Slet"], key=f"s_{r['id']}", label_visibility="collapsed")
                if c2.button("Gem", key=f"b_{r['id']}", use_container_width=True):
                    _handling(r["id"], valg); st.rerun()
                st.divider()

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
    netto = udb - oms
    hit = (len(vun) / len(afg) * 100) if len(afg) else 0.0
    roi = (udb / oms * 100) if oms else 0.0

    st.info(f"💰 **TOTAL SUM:** {netto:+.2f} kr.  |  🎯 **Hitrate:** {hit:.1f}%  |  📈 **ROI:** {roi:.1f}%")
    f1, f2, f3 = st.tabs(["⏳ Afventer", "✅ Afgjorte", "🗂️ Alle"])
    with f1:
        _tegn_kuponer([r for r in rækker if r.get("status") == "[AFVENTER]"])
    with f2:
        _tegn_kuponer([r for r in rækker if r.get("status") in ("VUNDET", "TABT")])
    with f3:
        _tegn_kuponer(rækker)
