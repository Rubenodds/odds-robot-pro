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
    "eng.1", "eng.2", "eng.3", "eng.4", "esp.1", "esp.2", "ger.1", "ger.2",
    "ita.1", "ita.2", "fra.1", "fra.2", "den.1", "den.2", "ned.1",
    "por.1", "bel.1", "nor.1", "swe.1", "uefa.champions", "uefa.europa",
]


def _norm(txt):
    t = str(txt or "").lower().strip()
    t = t.replace("athletic club", "athletic bilbao").replace("sheff wed", "sheffield wednesday")
    t = re.sub(r"\b(fc|cf|ac|sc|bk|if|fk|club|united|city)\b", "", t)
    return re.sub(r"\s+", " ", t).strip()


def _formater_ben(item):
    if isinstance(item, dict):
        hj = item.get("hj") or item.get("hjemme") or ""
        ud = item.get("ud") or item.get("ude") or ""
        kombi = ", ".join(item.get("kombinationer") or []) or item.get("spil") or ""
        odds = item.get("b365") or item.get("odds") or ""
        o_txt = f" @ {odds}" if odds else ""
        return f"{hj} - {ud} ({kombi}){o_txt}".strip()
    return str(item or "").strip()


@st.cache_data(ttl=300, show_spinner=False)
def _hent_slutresultater():
    nu = datetime.date.today()
    d_sp = f"{(nu - datetime.timedelta(days=5)).strftime('%Y%m%d')}-{nu.strftime('%Y%m%d')}"
    res = []
    for lg in LIGAER:
        try:
            u = f"https://{HOST}/apis/site/v2/sports/soccer/{lg}/scoreboard"
            data = requests.get(u, params={"dates": d_sp}, timeout=3).json()
            for ev in (data.get("events") or []):
                st_type = (((ev.get("status") or {}).get("type")) or {})
                if not (st_type.get("completed") or st_type.get("state") == "post"):
                    continue
                for comp in (ev.get("competitions") or []):
                    cs = list(comp.get("competitors") or [])
                    if len(cs) >= 2:
                        h = next((c for c in cs if c.get("homeAway") == "home"), cs.pop(0))
                        a = next((c for c in cs if c.get("homeAway") == "away"), cs.pop(0))
                        res.append({
                            "hj": _norm((h.get("team") or {}).get("displayName") or ""),
                            "ud": _norm((a.get("team") or {}).get("displayName") or ""),
                            "hs": int(float(h.get("score") or 0)),
                            "as": int(float(a.get("score") or 0)),
                        })
        except Exception:
            continue
    return res


def _match_hold(q, navn):
    q1 = _norm(q)[:6]
    n1 = _norm(navn)
    return bool(q1) and (q1 in n1 or n1[:6] in q1)


def _vurd_ben(item, res_liste):
    t = _formater_ben(item)
    m_hold = re.search(r"([A-Za-zÀ-ÿ0-9\s\.\-]+?)\s+-\s+([A-Za-zÀ-ÿ0-9\s\.\-]+?)(?:\s*\(|$)", t)
    if not m_hold:
        return None
    hj_raw, ud_raw = m_hold.group(1).strip(), m_hold.group(2).strip()
    kamp = next((r for r in res_liste if _match_hold(hj_raw, r["hj"]) and _match_hold(ud_raw, r["ud"])), None)
    if not kamp:
        return None
    hs, as_, tot = kamp["hs"], kamp["as"], kamp["hs"] + kamp["as"]
    m_sp = re.search(r"\(([^)]+)\)", t)
    spil = _norm(m_sp.group(1) if m_sp else t)
    hj_k, ud_k = _norm(hj_raw)[:5], _norm(ud_raw)[:5]
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
        elif "el. uafgjort" in d or "eller uafgjort" in d or "1x" in d or "x2" in d:
            if (hj_k in d and not (hs >= as_)) or (ud_k in d and not (as_ >= hs)):
                return False
        elif "vinder" in d:
            if (hj_k in d and not (hs > as_)) or (ud_k in d and not (as_ > hs)):
                return False
    return True


def _auto_tjek_afventende(raekker):
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
        with st.expander(f"📁 {dag} ({len(kuponer)} kupon{'er' if len(kuponer) != 1 else ''})", expanded=False):
            for r in kuponer:
                kid = r["id"]
                st_ikon = {"VUNDET": "✅", "TABT": "❌"}.get(r.get("status"), "⏳")
                st.markdown(f"**{st_ikon} Kupon #{kid}** • Odds **{r.get('odds')}** • Indsats **{r.get('indsats', 100):.0f} kr.** • Gevinst **{r.get('mulig_gevinst')} kr.**")
                raw = r.get("detaljer") or r.get("kampe")
                try:
                    kampe = json.loads(raw) if isinstance(raw, str) and raw.startswith("[") else [raw]
                except Exception:
                    kampe = [raw]
                for k in kampe:
                    st.caption(f"⚽ {_formater_ben(k)}")
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
    if fejl or not tok:
        st.warning(f"⚠️ Cloud-status: {fejl or 'Mangler GitHub-token i Secrets'}")

    raekker = _auto_tjek_afventende(list(hent_alle_kuponer()))
    if not raekker:
        st.info("Ingen gemte kuponer endnu.")
        return

    aar_liste = sorted({str(r.get("dato", ""))[6:10] for r in raekker if len(str(r.get("dato", ""))) >= 10}, reverse=True)
    aktuelt_aar = str(datetime.date.today().year)
    if aktuelt_aar not in aar_liste:
        aar_liste.insert(0, aktuelt_aar)

    c_aar, c_btn = st.columns((3, 1))
    valgt_aar = c_aar.selectbox("📅 Regnskabsår", aar_liste + ["Alle år (Total)"], index=0, key="regnskab_aar", label_visibility="collapsed")
    if c_btn.button("🔄 Tjek", key="btn_synk_cloud", use_container_width=True):
        st.cache_data.clear()
        st.session_state.pop("kupon_ram_cache", None)
        st.rerun()

    filtreret = raekker if valgt_aar.startswith("Alle") else [r for r in raekker if str(r.get("dato", ""))[6:10] == valgt_aar]
    df = pd.DataFrame(filtreret) if filtreret else pd.DataFrame(columns=["status", "indsats", "mulig_gevinst"])
    afg = df[df["status"].isin(["VUNDET", "TABT"])]
    vun = df[df["status"] == "VUNDET"]
    oms = float(afg["indsats"].sum()) if not afg.empty else 0.0
    udb = float(vun["mulig_gevinst"].sum()) if not vun.empty else 0.0
    netto = udb - oms
    hit = (len(vun) / len(afg) * 100.0) if len(afg) else 0.0
    roi = (udb / oms * 100.0) if oms else 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Netto", f"{netto:+.0f} kr.", f"Indsats: {oms:.0f} kr.")
    m2.metric("🎯 Hitrate", f"{hit:.1f}%", f"{len(vun)}/{len(afg)} vundet")
    m3.metric("📈 Tilbagebetaling", f"{roi:.1f}%", f"Udbetalt: {udb:.0f} kr.")

    f1, f2, f3 = st.tabs(["⏳ Afventer", "✅ Afgjorte", "🗂️ Alle"])
    with f1:
        _tegn_kuponer([r for r in filtreret if r.get("status") == "[AFVENTER]"], "afv")
    with f2:
        _tegn_kuponer([r for r in filtreret if r.get("status") in ("VUNDET", "TABT")], "afg")
    with f3:
        _tegn_kuponer(filtreret, "all")
