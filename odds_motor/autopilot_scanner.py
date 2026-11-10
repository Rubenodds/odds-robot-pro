import requests
import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from odds_motor import liga_favoritter, byg_kupon, kamp_intelligens
from historik import gem_data

API = "https://espn.com{}/scoreboard"
SLUGS = {
    "Danmark - Superliga": "den.1", "Danmark - 1. Division": "den.2", "Danmark - Pokalen": "den.cup",
    "England - Premier League": "eng.1", "England - Championship": "eng.2", "England - League One": "eng.3",
    "England - FA Cup": "eng.fa", "England - EFL Cup": "eng.league_cup",
    "Spanien - La Liga": "esp.1", "Spanien - Segunda División": "esp.2", "Spanien - Copa del Rey": "esp.copa_del_rey",
    "Italien - Serie A": "ita.1", "Italien - Serie B": "ita.2", "Italien - Coppa Italia": "ita.coppa_italia",
    "Tyskland - Bundesliga": "ger.1", "Tyskland - 2. Bundesliga": "ger.2", "Tyskland - DFB Pokal": "ger.dfb_pokal",
    "Frankrig - Ligue 1": "fra.1", "Frankrig - Ligue 2": "fra.2", "Frankrig - Coupe de France": "fra.coupe_de_france",
    "Norge - Eliteserien": "nor.1", "Norge - OBOS-ligaen": "nor.2", "Sverige - Allsvenskan": "swe.1",
    "Holland - Eredivisie": "ned.1", "Portugal - Liga Portugal": "por.1",
    "Brasilien - Serie A": "bra.1", "Brasilien - Serie B": "bra.2",
    "Japan - J1 League": "jpn.1", "Japan - J2 League": "jpn.2",
    "UEFA - Champions League": "uefa.champions", "UEFA - Europa League": "uefa.europa",
    "UEFA - Conference League": "uefa.europa.conf", "UEFA - Nations League": "uefa.nations",
    "Landskampe - FIFA / UEFA": "fifa.friendly", "Landskampe - VM Kvalifikation": "fifa.worldq.uefa",
}
LANDSKAMPE = ["UEFA - Nations League", "Landskampe - FIFA / UEFA", "Landskampe - VM Kvalifikation"]
MARKEDER = [
    "Standard (Mål / Kampvinder)", "Hjørnespark (Over/Under & Flest)", "Spillerskud & Skud på mål",
    "Tacklinger & Målmandsredninger", "Kort-sandsynlighed (Gule/Røde)", "Målscorer (Anytime/Første)", "Offsides",
]

def _find_slug(liga):
    norm = liga_favoritter.normaliser_liga_navn(liga)
    for navn in (norm, liga):
        if navn in SLUGS:
            return SLUGS[navn]
    for k, slug in SLUGS.items():
        if k.split(" - ")[-1].lower() in liga.lower() or liga.lower() in k.lower():
            return slug
    return None

def _parse_event(ev, liga, nu, dk_tz, sete):
    ev_id = ev.get("id")
    if not ev_id or ev_id in sete or ev.get("status", {}).get("type", {}).get("state") != "pre":
        return None
    dk_dt = datetime.fromisoformat(ev["date"].replace("Z", "+00:00")).astimezone(dk_tz)
    diff = (dk_dt - nu).total_seconds() / 3600.0
    if diff <= 0:
        return None
    comps = ev.get("competitions") or []
    comp = comps[0] if comps else {}
    teams = comp.get("competitors") or []
    hj = next((c["team"]["displayName"] for c in teams if c.get("homeAway") == "home"), None)
    ud = next((c["team"]["displayName"] for c in teams if c.get("homeAway") == "away"), None)
    if not (hj and ud):
        return None
    sete.add(ev_id)
    try:
        ctx = kamp_intelligens.analyser_kamp_kontekst(comp, hj, ud)
        pct = round(max(35.0, min(95.0, byg_kupon.beregn_sandsynlighed_fra_odds(1.85) + ctx.get("justering_pct", 0.0))), 1)
    except Exception:
        ctx = {"justering_pct": 0.0, "hj_form": "Ukendt", "ud_form": "Ukendt", "dommer": "Afventer", "vejr": None}
        pct = 54.0
    return {"label": f"{hj} vs {ud} ({liga} | {dk_dt.strftime('%d-%m %H:%M')})", "liga": liga, "hj": hj, "ud": ud, "dk_dt": dk_dt, "start": dk_dt.strftime("%d-%m-%Y kl. %H:%M"), "timer": round(diff, 2), "pct": pct, "ctx": ctx}

@st.cache_data(ttl=120, show_spinner=False)
def _hent_kampe_v3(ligaer_tuple):
    dk_tz = ZoneInfo("Europe/Copenhagen")
    nu = datetime.now(dk_tz)
    d_str = f"{nu.strftime('%Y%m%d')}-{(nu + timedelta(days=4)).strftime('%Y%m%d')}"
    kampe, sete = [], set()
    noegleord = {l.split(" - ")[-1].lower(): l for l in ligaer_tuple}

    for liga in ligaer_tuple:
        slug = _find_slug(liga)
        if not slug:
            continue
        try:
            r = requests.get(f"{API.format(slug)}?dates={d_str}", timeout=6)
            if r.status_code == 200:
                for ev in r.json().get("events", []):
                    k = _parse_event(ev, liga, nu, dk_tz, sete)
                    if k:
                        kampe.append(k)
        except Exception:
            continue

    try:
        r_all = requests.get(f"{API.format('all')}?dates={d_str}", timeout=8)
        if r_all.status_code == 200:
            for ev in r_all.json().get("events", []):
                lg_navn = (ev.get("league") or {}).get("name", "") or (ev.get("season") or {}).get("slug", "")
                match_liga = next((orig for kw, orig in noegleord.items() if kw in lg_navn.lower()), None)
                if match_liga:
                    k = _parse_event(ev, match_liga, nu, dk_tz, sete)
                    if k:
                        kampe.append(k)
    except Exception:
        pass
    return sorted(kampe, key=lambda x: x["dk_dt"])

def _vaelg_bedste_kombination(kandidater, min_o, max_o, max_kampe):
    sorteret = sorted(kandidater, key=lambda x: x["pct"], reverse=True)
    maal = round((min_o + max_o) / 2.0, 2)
    antal = next((n for n in range(1, min(len(sorteret), max_kampe) + 1) if 1.45 <= maal ** (1.0 / n) <= 3.20), min(len(sorteret), max_kampe))
    return sorteret[:antal], maal

def vis_autopilot_scanner():
    st.subheader("🌐 1. Autopilot Scanner (Form, H2H, Dommer & Vejr)")
    favs = list(liga_favoritter.hent_favorit_ligaer())
    if st.checkbox("🌍 Inkludér Landskampe (UEFA Nations League / FIFA)", value=True, key="auto_landskampe"):
        favs.extend(l for l in LANDSKAMPE if l not in favs)

    c1, c2, c3 = st.columns(3)
    timer = c1.slider("⏱️ Tidsramme frem (timer):", 1, 72, 48, key="auto_timer")
    min_o, max_o = c2.slider("🎯 Ønsket odds-lag:", 2.0, 200.0, (20.0, 50.0), key="auto_odds")
    max_kampe = c3.slider("🎫 Maks. kampe på kupon:", 1, 12, 4, key="auto_max_kampe")

    alle = _hent_kampe_v3(tuple(favs))
    aktive = [k for k in alle if 0 < k["timer"] <= timer]
    ligaer = sorted({k["liga"] for k in aktive})

    if ligaer:
        v_ligaer = st.multiselect(f"🏆 Vælg ligaer med kampe ({len(ligaer)} aktive i {timer}T):", ligaer, default=ligaer, key="auto_ligaer")
        filt = [k for k in aktive if k["liga"] in v_ligaer]
        v_labels = st.multiselect(f"⚽ Vælg kampe ({len(filt)} tilgængelige):", [k["label"] for k in filt], default=[k["label"] for k in filt], key="auto_kampe_valgt")
        kandidater = [k for k in filt if k["label"] in v_labels]
    else:
        kandidater = []
        naeste = f" Næste kamp: **{alle[0]['hj']} vs {alle[0]['ud']}** ({alle[0]['start']})." if alle else ""
        st.info(f"📭 Ingen favoritligaer har kampe inden for **{timer} timer**.{naeste}")

    with st.expander(f"⚙️ Administrer favoritter ({len(liga_favoritter.hent_favorit_ligaer())} aktive)"):
        ny = st.text_input("➕ Ny favoritliga:", key="auto_ny")
        if st.button("Gem favorit", key="auto_add") and liga_favoritter.tilfoej_ny_favorit_liga(ny):
            st.cache_data.clear()
            st.rerun()
        fjern = st.selectbox("🗑️ Fjern liga:", liga_favoritter.hent_favorit_ligaer(), key="auto_del_sel")
        if st.button("Fjern liga", key="auto_del") and liga_favoritter.fjern_favorit_liga(fjern):
            st.cache_data.clear()
            st.rerun()

    markeder = st.multiselect("📊 Specialmarkeder:", MARKEDER, default=MARKEDER[:3], key="auto_mark")
    b1, b2 = st.columns(2)
    if (b1.button("🔍 FIND MEST SANDSYNLIGE KUPON", type="primary", key="btn_scan") or b2.button("⚡ SCAN ALLE VALGTE KAMPE", key="btn_scan_alle")) and kandidater and markeder:
        udv, maal = (sorted(kandidater, key=lambda x: x["pct"], reverse=True), round((min_o + max_o) / 2.0, 2)) if st.session_state.get("btn_scan_alle") else _vaelg_bedste_kombination(kandidater, min_o, max_o, max_kampe)
        kupon = byg_kupon.byg_kombineret_kupon(udv, markeder, maal)
        for k_obj, u_obj in zip(kupon["kampe"], udv):
            k_obj["ctx"] = u_obj["ctx"]
        st.session_state["auto_kupon"] = kupon

    if kupon := st.session_state.get("auto_kupon"):
        for i, k in enumerate(kupon["kampe"], 1):
            ctx = k.get("ctx", {})
            v = ctx.get("vejr")
            v_txt = f"{v['temp']}°C, {v['vind']} m/s ({v['effekt']})" if v else "Afventer"
            st.write(f"**{i}. {k['hj']} vs {k['ud']}** ({k['liga']} | **{k['start']}**)")
            st.caption(f"Spil: {', '.join(k['kombinationer'])} | Odds: {k['b365']} | Chance: {k['vinderchance_pct']}% | Form: {ctx.get('hj_form')} vs {ctx.get('ud_form')} | Dommer: {ctx.get('dommer')} | Vejr: {v_txt}")
        st.info(f"⭐ {'⭐' * kupon['styrke']} | Bedste profil: {kupon['bedste_side']} | Samlet odds: **{kupon['bedste_odds']}**")
        indsats = st.number_input("Indsats (kr.):", min_value=1.0, value=100.0, step=10.0, key="auto_kr")
        if st.button("🚀 SPILLET (Gem i Supabase)", type="primary", key="btn_auto_spillet") and gem_data.gem_kupon_i_historik(list({k["liga"] for k in kupon["kampe"]}), [f"{k['hj']} - {k['ud']} [{k['start']}]" for k in kupon["kampe"]], kupon["bedste_odds"], kupon["samlet_unibet"], kupon["samlet_oddset"], kupon["bedste_side"], kupon["styrke"], indsats):
            st.success("✅ Kupon gemt i Supabase!")
