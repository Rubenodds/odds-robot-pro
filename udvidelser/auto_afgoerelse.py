import datetime
import json
import re
import requests
import streamlit as st
from historik import gem_data

FANE_TITEL = "🏁 Auto-Resultat Tjekker"
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
                st_type = (((ev.get("status") or {}).get("type")) or {})
                if not st_type.get("completed"):
                    continue
                for comp in (ev.get("competitions") or []):
                    cs = list(comp.get("competitors") or [])
                    if len(cs) >= 2:
                        h = next((c for c in cs if c.get("homeAway") == "home"), cs.pop(0))
                        a = next((c for c in cs if c.get("homeAway") == "away"), cs.pop(0))
                        hn = str((h.get("team") or {}).get("displayName") or "")
                        an = str((a.get("team") or {}).get("displayName") or "")
                        hs = int(float(h.get("score") or 0))
                        as_ = int(float(a.get("score") or 0))
                        res.append({"hj": hn, "ud": an, "hs": hs, "as": as_})
        except Exception:
            continue
    return res


def _vurd_ben(tekst, res_liste):
    t = str(tekst or "")
    tl = t.lower()
    m_hold = re.search(r"([A-Za-zÀ-ÿ0-9\s\.\-]+?)\s+-\s+([A-Za-zÀ-ÿ0-9\s\.\-]+?)(?:\s*\(|$)", t)
    if not m_hold:
        return None, "Kan ikke aflæse holdnavne"
    hj_q = m_hold.group(1).strip().lower()[:5]
    ud_q = m_hold.group(2).strip().lower()[:5]
    kamp = next((r for r in res_liste if hj_q in r["hj"].lower() and ud_q in r["ud"].lower()), None)
    if not kamp:
        return None, "Ikke færdigspillet endnu"

    hs, as_, tot = kamp["hs"], kamp["as"], kamp["hs"] + kamp["as"]
    sc = f"({hs}-{as_})"
    m_sp = re.search(r"\(([^)]+)\)", t)
    spil = (m_sp.group(1) if m_sp else t).lower()
    dele = [p.strip() for p in spil.split("&")]

    for d in dele:
        if "begge hold scorer" in d:
            ok = (hs > 0 and as_ > 0) if "nej" not in d else (hs == 0 or as_ == 0)
            if not ok:
                return False, f"Tabt {sc}"
        elif "over " in d and "mål" in d:
            m_tal = re.search(r"over\s+(\d+(?:\.\d+)?)", d)
            if m_tal and not (tot > float(m_tal.group(1))):
                return False, f"Tabt {sc}"
        elif "under " in d and "mål" in d:
            m_tal = re.search(r"under\s+(\d+(?:\.\d+)?)", d)
            if m_tal and not (tot < float(m_tal.group(1))):
                return False, f"Tabt {sc}"
        elif "el. uafgjort" in d or "1x" in d or "x2" in d:
            if hj_q in d and not (hs >= as_):
                return False, f"Tabt {sc}"
            if ud_q in d and not (as_ >= hs):
                return False, f"Tabt {sc}"
        elif "vinder" in d:
            if hj_q in d and not (hs > as_):
                return False, f"Tabt {sc}"
            if ud_q in d and not (as_ > hs):
                return False, f"Tabt {sc}"
    return True, f"Vundet {sc}"


def vis_modul():
    st.subheader("🏁 Automatisk Resultat-Tjekker")
    st.caption("Tjekker dine afventende kuponer mod officielle slutresultater og opdaterer Fane 4 automatisk.")
    alle = list(gem_data.hent_alle_kuponer())
    afv = [r for r in alle if r.get("status") == "[AFVENTER]"]
    if not afv:
        st.success("✅ Ingen afventende kuponer i køen lige nu.")
        return

    st.info(f"⏳ Du har **{len(afv)} afventende kupon(er)** klar til tjek.")
    if st.button("🔍 TJEK & AFGØR KUPONER NU", type="primary", use_container_width=True, key="btn_auto_res_run"):
        with st.spinner("⏳ Henter officielle slutresultater..."):
            res_liste = _hent_slutresultater()
        opdateret = 0
        for r in alle:
            if r.get("status") != "[AFVENTER]":
                continue
            raw = r.get("detaljer") or r.get("kampe")
            try:
                ben = json.loads(raw) if isinstance(raw, str) and raw.startswith("[") else [raw]
            except Exception:
                ben = [raw]
            udfald = [_vurd_ben(b, res_liste) for b in ben]
            if any(u[0] is False for u in udfald):
                r["status"] = "TABT"
                opdateret += 1
            elif udfald and all(u[0] is True for u in udfald):
                r["status"] = "VUNDET"
                opdateret += 1

        if opdateret > 0:
            st.session_state["kupon_ram_cache"] = alle
            _, sha = gem_data._gh_laes()
            gem_data._gh_skriv(alle, sha)
            st.success(f"🎉 **{opdateret} kupon(er)** blev automatisk afgjort og opdateret i Regnskabet!")
            st.rerun()
        else:
            st.warning("⚠️ Ingen af de afventende kuponer var færdigspillet eller matchet endnu.")
