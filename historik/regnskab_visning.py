import datetime
import json
import re
import time
from collections import defaultdict
import pandas as pd
import requests
import streamlit as st
from historik.gem_data import hent_alle_kuponer, _gh_laes, _gh_skriv, _gh_cfg

HOST = ".".join(["site", "api", "espn", "com"])
LIGAER = [
    "eng.1", "eng.2", "eng.3", "esp.1", "esp.2", "ger.1", "ger.2",
    "ita.1", "ita.2", "fra.1", "fra.2", "den.1", "den.2", "ned.1",
    "por.1", "bel.1", "nor.1", "swe.1", "uefa.champions", "uefa.europa",
]


def _hent_slutresultater():
    nu = datetime.date.today()
    d_sp = f"{(nu - datetime.timedelta(days=4)).strftime('%Y%m%d')}-{nu.strftime('%Y%m%d')}"
    res = []
    for lg in LIGAER:
        try:
            u = f"https://{HOST}/apis/site/v2/sports/soccer/{lg}/scoreboard"
            data = requests.get(u, params={"dates": d_sp}, timeout=3).json()
            for ev in (data.get("events") or []):
                if not (((ev.get("status") or {}).get("type")) or {}).get("completed"):
                    continue
                for comp in (ev.get("competitions") or []):
                    cs = list(comp.get("competitors") or [])
                    if len(cs) >= 2:
                        h = next((c for c in cs if c.get("homeAway") == "home"), cs.pop(0))
                        a = next((c for c in cs if c.get("homeAway") == "away"), cs.pop(0))
                        res.append({
                            "hj": str((h.get("team") or {}).get("displayName") or ""),
                            "ud": str((a.get("team") or {}).get("displayName") or ""),
                            "hs": int(float(h.get("score") or 0)),
                            "as": int(float(a.get("score") or 0)),
                        })
        except Exception:
            continue
    return res


def _vurd_ben(tekst, res_liste):
    t = str(tekst or "")
    m_hold = re.search(r"([A-Za-zÀ-ÿ0-9\s\.\-]+?)\s+-\s+([A-Za-zÀ-ÿ0-9\s\.\-]+?)(?:\s*\(|$)", t)
    if not m_hold:
        return None
    hj_q = m_hold.group(1).strip().lower()[:5]
    ud_q = m_hold.group(2).strip().lower()[:5]
    kamp = next((r for r in res_liste if hj_q in r["hj"].lower() and ud_q in r["ud"].lower()), None)
    if not kamp:
        return None
    hs, as_, tot = kamp["hs"], kamp["as"], kamp["hs"] + kamp["as"]
    m_sp = re.search(r"\(([^)]+)\)", t)
    spil = (m_sp.group(1) if m_sp else t).lower()
    for d in [p.strip() for p in spil.split("&")]:
        if "begge hold scorer" in d:
            if not ((hs > 0 and as_ > 0) if "nej" not in d else (hs == 0 or as_ == 0)):
                return False
        elif "over " in d and "mål" in d:
            m_tal = re.search(r"over\s+(\d+(?:\.\d+)?)", d)
            if m_tal and not (tot > float(m_tal.group(1))):
                return False
        elif "under " in d and "mål" in d:
            m_tal = re.search(r"under\s+(\d+(?:\.\d+)?)", d)
            if m_tal and not (tot < float(m_tal.group(1))):
                return False
        elif "el. uafgjort" in d or "1x" in d or "x2" in d:
            if (hj_q in d and not (hs >= as_)) or (ud_q in d and not (as_ >= hs)):
                return False
        elif "vinder" in d:
            if (hj_q in d and not (hs > as_)) or (ud_q in d and not (as_ > hs)):
                return False
    return True


def _auto_tjek_afventende(raekker, tvunget=False):
    nu = time.time()
    if not tvunget and (nu - float(st.session_state.get("_sidste_res_tjek", 0.0))) < 600:
        return raekker
    st.session_state["_sidste_res_tjek"] = nu
    if not any(r.get("status") == "[AFVENTER]" for r in raekker):
        return raekker
    res_liste = _hent_slutresultater()
    if not res_liste:
        return raekker
    opd = 0
    for r in raekker:
        if r.get("status") != "[AFVENTER]":
            continue
        raw = r.get("detaljer") or r.get("kampe")
        try:
            ben = json.loads(raw) if isinstance(raw, str) and raw.startswith("[") else [raw]
        except Exception:
            ben = [raw]
        udf = [_vurd_ben(b, res_liste) for b in ben]
        if any(u is False for u in udf):
            r["status"] = "TABT"
            opd += 1
        elif udf and all(u is True for u in udf):
            r["status"] = "VUNDET"
            opd += 1
    if opd > 0:
        st.session_state["kupon_ram_cache"] = raekker
        _, sha = _gh_laes()
        _gh_skriv(raekker, sha)
        st.toast(f"🏁 {opd} kupon(er) blev automatisk afgjort!", icon="✅")
    return raekker


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
        with st.expander(f"📁 {dag}  ({len(kuponer)} kupon{'er' if len(kuponer) != 1 else ''})", expanded=False):
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
                    _handling(kid, valg)
                    st.rerun()
                if c3.button("🗑️ Slet", key=f"del_{fane_prefix}_{kid}", use_container_width=True):
                    _handling(kid, "🗑️ Slet")
                    st.rerun()
                st.divider()


def vis_regnskab():
    tok, _ = _gh_cfg()
    fejl = st.session_state.get("gh_fejl")
    c_top1, c_top2 = st.columns((3, 1))
    if tok and not fejl:
        c_top1.caption("☁️ **Cloud & Auto-Resultat aktiv** — kuponer tjekkes automatisk og gemmes pr. år.")
    else:
        c_top1.warning(f"⚠️ Cloud-status: {fejl or 'Mangler GitHub-token i Secrets'}")
    if c_top2.button("🔄 Synk & Tjek", key="btn_synk_cloud", use_container_width=True):
        st.session_state.pop("kupon_ram_cache", None)
        st.session_state.pop("_sidste_res_tjek", None)
        st.rerun()

    raekker = _auto_tjek_afventende(list(hent_alle_kuponer()))
    if not raekker:
        st.info("Ingen gemte kuponer endnu.")
        return

    aar_liste = sorted({str(r.get("dato", ""))[6:10] for r in raekker if len(str(r.get("dato", ""))) >= 10}, reverse=True)
    aktuelt_aar = str(datetime.date.today().year)
    if aktuelt_aar not in aar_liste:
        aar_liste.insert(0, aktuelt_aar)
    valgt_aar = st.selectbox("📅 Regnskabsår:", aar_liste + ["Alle år (Total)"], index=0, key="regnskab_aar")

    filtreret = raekker if valgt_aar.startswith("Alle") else [r for r in raekker if str(r.get("dato", ""))[6:10] == valgt_aar]
    df = pd.DataFrame(filtreret) if filtreret else pd.DataFrame(columns=["status", "indsats", "mulig_gevinst"])
    afg = df[df["status"].isin(["VUNDET", "TABT"])]
    vun = df[df["status"] == "VUNDET"]
    oms = float(afg["indsats"].sum()) if not afg.empty else 0.0
    udb = float(vun["mulig_gevinst"].sum()) if not vun.empty else 0.0
    netto = udb - oms
    hit = (len(vun) / len(afg) * 100.0) if len(afg) else 0.0
    roi = (udb / oms * 100.0) if oms else 0.0

    st.info(f"💰 **{valgt_aar} Netto:** {netto:+.2f} kr.  |  🎯 **Hitrate:** {hit:.1f}% ({len(vun)}/{len(afg)})  |  📈 **Tilbagebetaling:** {roi:.1f}%")
    m1, m2, m3 = st.columns(3)
    m1.metric("Samlet Indsats", f"{oms:.0f} kr.")
    m2.metric("Samlet Udbetaling", f"{udb:.0f} kr.")
    m3.metric("Overskud / Underskud", f"{netto:+.0f} kr.")

    f1, f2, f3 = st.tabs(["⏳ Afventer", "✅ Afgjorte", "🗂️ Alle"])
    with f1:
        _tegn_kuponer([r for r in filtreret if r.get("status") == "[AFVENTER]"], "afv")
    with f2:
        _tegn_kuponer([r for r in filtreret if r.get("status") in ("VUNDET", "TABT")], "afg")
    with f3:
        _tegn_kuponer(filtreret, "all")
