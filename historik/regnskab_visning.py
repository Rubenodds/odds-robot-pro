import json
from collections import defaultdict
import pandas as pd
import streamlit as st
from historik.gem_data import hent_alle_kuponer, _gh_laes, _gh_skriv, _gh_cfg

def _handling(kid, valg):
    raekker = list(hent_alle_kuponer())
    ny = {"✅ Vundet": "VUNDET", "❌ Tabt": "TABT", "⏳ Afventer": "[AFVENTER]"}.get(valg)
    if valg == "🗑️ Slet":
        raekker = [r for r in raekker if int(r.get("id", -1)) != int(kid)]
    elif ny:
        for r in raekker:
            if int(r.get("id", -1)) == int(kid):
                r["status"] = ny
    st.session_state["kupon_ram_cache"] = raekker
    sha = st.session_state.get("kupon_sha")
    if not sha:
        _, sha = _gh_laes()
    if not _gh_skriv(raekker, sha):
        _, ny_sha = _gh_laes()
        if ny_sha:
            _gh_skriv(raekker, ny_sha)

def _tegn_kuponer(liste_r, fane_prefix):
    if not liste_r:
        st.caption("Ingen kuponer her endnu.")
        return
    dage = defaultdict(list)
    for r in liste_r:
        dage[str(r.get("dato", "Ukendt"))[:10]].append(r)
    valgm = ["✅ Vundet", "❌ Tabt", "⏳ Afventer"]
    idx_map = {"VUNDET": 0, "TABT": 1, "[AFVENTER]": 2}
    for dag, kuponer in dage.items():
        with st.expander(f"📁 {dag}  ({len(kuponer)} kupon{'er' if len(kuponer)!=1 else ''})", expanded=False):
            for r in kuponer:
                kid = r["id"]
                st_ikon = {"VUNDET": "✅", "TABT": "❌"}.get(r.get("status"), "⏳")
                st.markdown(f"**{st_ikon} Kupon #{kid}** • Odds **{r.get('odds')}** • Mulig gevinst **{r.get('mulig_gevinst')} kr.**")
                raw = r.get("detaljer") or r.get("kampe")
                try:
                    kampe = json.loads(raw) if isinstance(raw, str) and raw.startswith("[") else [raw]
                except Exception:
                    kampe = [raw]
                for k in kampe:
                    st.caption(f"• {k}")
                c1, c2, c3 = st.columns((2, 1, 1))
                valg = c1.selectbox("Status", valgm, index=idx_map.get(r.get("status"), 2), key=f"s_{fane_prefix}_{kid}", label_visibility="collapsed")
                if c2.button("Gem", key=f"b_{fane_prefix}_{kid}", use_container_width=True):
                    _handling(kid, valg); st.rerun()
                if c3.button("🗑️ Slet", key=f"del_{fane_prefix}_{kid}", use_container_width=True):
                    _handling(kid, "🗑️ Slet"); st.rerun()
                st.divider()

def vis_regnskab():
    tok, _ = _gh_cfg()
    fejl = st.session_state.get("gh_fejl")
    c_top1, c_top2 = st.columns((3, 1))
    if tok and not fejl:
        c_top1.caption("☁️ **Cloud-lagring aktiv** — alle kuponer gemmes permanent på GitHub ved reboot.")
    else:
        c_top1.warning(f"⚠️ Cloud-status: {fejl or 'Mangler GitHub-token i Secrets'}")
    if c_top2.button("🔄 Synk Cloud", key="btn_synk_cloud", use_container_width=True):
        st.session_state.pop("kupon_ram_cache", None)
        st.rerun()

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
        _tegn_kuponer([r for r in rækker if r.get("status") == "[AFVENTER]"], "afv")
    with f2:
        _tegn_kuponer([r for r in rækker if r.get("status") in ("VUNDET", "TABT")], "afg")
    with f3:
        _tegn_kuponer(rækker, "all")
