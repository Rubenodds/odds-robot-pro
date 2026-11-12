from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st

DK_TZ = ZoneInfo("Europe/Copenhagen")

UGEDAGE = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag", "Søndag"]
MAANEDER = [
    "", "januar", "februar", "marts", "april", "maj", "juni",
    "juli", "august", "september", "oktober", "november", "december",
]

def hent_dansk_nu():
    return datetime.now(DK_TZ)

def formater_dansk_tid(dt=None):
    nu = dt.astimezone(DK_TZ) if dt else hent_dansk_nu()
    ugedag = UGEDAGE[nu.weekday()]
    maaned = MAANEDER[nu.month]
    zone = "sommertid" if nu.dst() else "normaltid"
    return f"{ugedag} d. {nu.day}. {maaned} {nu.year} kl. {nu.strftime('%H:%M')} (Dansk {zone})"

def konverter_til_dansk(iso_str):
    if not iso_str:
        return hent_dansk_nu()
    tekst = str(iso_str).strip()
    if len(tekst) == 17 and tekst.endswith("Z"):
        tekst = tekst[:-1] + ":00Z"
    return datetime.fromisoformat(tekst.replace("Z", "+00:00")).astimezone(DK_TZ)

def vaelg_tidsramme(prefix="tid", standard=12):
    k_seg, k_num = f"{prefix}_seg", f"{prefix}_num"
    if k_num not in st.session_state:
        st.session_state[k_num] = standard
    def _sync():
        if st.session_state.get(k_seg):
            st.session_state[k_num] = int(st.session_state[k_seg])
    c1, c2 = st.columns([2, 1])
    c1.segmented_control("⏱️ Hurtig tidsramme:", [3, 6, 9, 12], default=standard, format_func=lambda x: f"{x}T", key=k_seg, on_change=_sync)
    return int(c2.number_input("Eller tast timer:", min_value=1, max_value=168, step=1, key=k_num))
