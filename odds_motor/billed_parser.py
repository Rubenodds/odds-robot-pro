import streamlit as st
from PIL import Image
from odds_motor import billed_ocr
from odds_motor.kupon_hjaelp import beregn_total_odds, ryd_hele_kuponen


def _normaliser_kamp(kamp_str: str) -> str:
    return "".join(ch.lower() for ch in kamp_str if ch.isalnum())


def _kald_ocr(fil_bytes: bytes) -> list:
    for navn in (
        "udtraek_kampe_fra_billede",
        "scan_billede_for_kampe",
        "parse_billede",
        "analyser_billede",
        "udtraek_kupon_fra_billede",
    ):
        fn = getattr(billed_ocr, navn, None)
        if callable(fn):
            return fn(fil_bytes)
    for attr in dir(billed_ocr):
        if not attr.startswith("_"):
            fn = getattr(billed_ocr, attr)
            if callable(fn):
                try:
                    res = fn(fil_bytes)
                    if isinstance(res, list):
                        return res
                except Exception:
                    continue
    return []


def vis_billed_scanner():
    """Uploader af et eller flere Bet365-skærmbilleder og tilføjer alle kampe uden dubletter."""
    st.markdown("### 📸 Scan Bet365-kupon (1 eller flere skærmbilleder)")
    st.caption(
        "Har du en lang kupon? Vælg 2-3 skærmbilleder på én gang — robotten fletter dem sammen og fjerner automatisk overlap."
    )

    filer = st.file_uploader(
        "Vælg eller træk ét eller flere skærmbilleder ind her",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="bet365_multi_billede_upload",
    )

    if not filer:
        return

    cols = st.columns(min(len(filer), 3))
    for idx, fil in enumerate(filer):
        with cols[idx % 3]:
            st.image(
                Image.open(fil),
                caption=f"Billede {idx + 1}: {fil.name}",
                use_container_width=True,
            )

    if st.button(
        f"🔍 Scan {len(filer)} {'billede' if len(filer) == 1 else 'billeder'} og indlæs kupon",
        type="primary",
        use_container_width=True,
    ):
        alle_fundne = []
        sete_kampe = set()
        dubletter = 0

        with st.spinner("Aflæser skærmbilleder og fletter kuponen sammen..."):
            for fil in filer:
                fil.seek(0)
                kampe_fra_fil = _kald_ocr(fil.read())
                for k in kampe_fra_fil:
                    noegle = _normaliser_kamp(k.get("kamp", ""))
                    if noegle and noegle in sete_kampe:
                        dubletter += 1
                        continue
                    if noegle:
                        sete_kampe.add(noegle)
                    alle_fundne.append(k)

        if not alle_fundne:
            st.error(
                "Kunne ikke finde hele kamp-linjer (Hold A - Hold B) på billederne. Tjek at begge holdnavne er synlige."
            )
            return

        ryd_hele_kuponen()
        for k in alle_fundne:
            st.session_state["kupon_kampe"].append(k)

        st.session_state["kupon_indsats"] = 100.0
        st.session_state["kupon_total_odds"] = beregn_total_odds(alle_fundne)

        msg = f"✅ {len(alle_fundne)} kampe indlæst fra {len(filer)} billeder!"
        if dubletter > 0:
            msg += f" ({dubletter} overlappende kamp{'e' if dubletter > 1 else ''} filtreret fra)"
        st.success(msg)
        st.rerun()
