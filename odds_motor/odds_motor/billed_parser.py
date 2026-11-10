import io
import re
import streamlit as st
from historik import gem_data

try:
    from PIL import Image
    PIL_TILGAENGELIG = True
except ImportError:
    PIL_TILGAENGELIG = False

try:
    from rapidocr_onnxruntime import RapidOCR
    OCR_MOTOR = RapidOCR()
except Exception:
    OCR_MOTOR = None


def _udtraek_kupon_moenstre(raatekst_linjer):
    """
    Bookmaker-agnostisk mønster-parser:
    Udtrækker kampe, markeder, samlet odds og indsats uden hardkodede bookmaker-navne.
    """
    detekterede_kampe = []
    alle_odds = []
    fundet_indsats = 100.0

    # Mønstre for kampnavne (f.eks. "Arsenal - Chelsea" eller "FCK vs Brøndby")
    kamp_moenster = re.compile(r"([A-Za-zÆØÅæøå0-9\.\-\s]{2,28})\s+(?:-|–|vs\.?|v)\s+([A-Za-zÆØÅæøå0-9\.\-\s]{2,28})", re.IGNORECASE)
    # Mønstre for odds-tal (f.eks. 1.85 eller 12,50)
    odds_moenster = re.compile(r"\b(\d{1,3}[.,]\d{2})\b")
    # Mønstre for indsats i kr./DKK
    indsats_moenster = re.compile(r"(?:indsats|stake|beløb|spillet|kr\.?|dkk)\s*[:\-]?\s*(\d+(?:[.,]\d{1,2})?)", re.IGNORECASE)

    for linje in raatekst_linjer:
        ren_linje = linje.strip()
        if not ren_linje:
            continue

        # Tjek for indsats
        m_indsats = indsats_moenster.search(ren_linje)
        if m_indsats:
            try:
                val = float(m_indsats.group(1).replace(",", "."))
                if val > 0:
                    fundet_indsats = val
            except ValueError:
                pass

        # Tjek for kampnavne
        m_kamp = kamp_moenster.search(ren_linje)
        if m_kamp and not any(ord_i_linje in ren_linje.lower() for ord_i_linje in ["indsats", "gevinst", "udbetaling", "total", "samlet"]):
            hjemme = m_kamp.group(1).strip()
            ude = m_kamp.group(2).strip()
            detekterede_kampe.append(f"{hjemme} - {ude}")

        # Opsaml alle valide decimaltal som potentielle odds
        for match in odds_moenster.findall(ren_linje):
            try:
                tal = float(match.replace(",", "."))
                if 1.01 <= tal <= 500.0:
                    alle_odds.append(tal)
            except ValueError:
                pass

    samlet_odds = max(alle_odds) if alle_odds else 2.00
    kampe_streng = ", ".join(dict.fromkeys(detekterede_kampe)) if detekterede_kampe else ""
    return kampe_streng, samlet_odds, fundet_indsats


def vis_billed_scanner():
    st.markdown("""
        <style>
        .kupon-stamme {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 16px;
            margin-top: 10px;
            margin-bottom: 14px;
            color: #f0f6fc;
        }
        </style>
    """, unsafe_allow_html=True)

    uploadet_fil = st.file_uploader(
        "Upload kupon-screenshot (PNG, JPG):",
        type=["png", "jpg", "jpeg"],
        key="scan_up"
    )

    if uploadet_fil is not None:
        fil_bytes = uploadet_fil.getvalue()

        if PIL_TILGAENGELIG:
            billede = Image.open(io.BytesIO(fil_bytes))
            st.image(billede, caption="Indlæst kupon (Afventer din aktive SPILLET-godkendelse)", use_container_width=True)
        else:
            st.image(fil_bytes, caption="Indlæst kupon (Afventer din aktive SPILLET-godkendelse)", use_container_width=True)

        # Automatisk OCR & mønster-analyse (køres kun én gang pr. uploadet fil)
        fil_id = f"{uploadet_fil.name}_{len(fil_bytes)}"
        if st.session_state.get("sidst_scannede_fil_id") != fil_id:
            detekteret_kampe = ""
            detekteret_odds = 2.00
            detekteret_indsats = 100.0
            raatekst = []

            if OCR_MOTOR is not None:
                try:
                    resultat, _ = OCR_MOTOR(fil_bytes)
                    if resultat:
                        raatekst = [punkt[1] for punkt in resultat if len(punkt) > 1]
                        detekteret_kampe, detekteret_odds, detekteret_indsats = _udtraek_kupon_moenstre(raatekst)
                except Exception as e:
                    print(f"[OCR-Advarsel]: {e}")

            st.session_state["sidst_scannede_fil_id"] = fil_id
            st.session_state["scan_kampe"] = detekteret_kampe
            st.session_state["scan_odds"] = float(detekteret_odds)
            st.session_state["scan_indsats"] = float(detekteret_indsats)
            st.session_state["scan_raatekst"] = "\n".join(raatekst)

        st.markdown('<div class="kupon-stamme"><h4>🎯 Kuponstamme – Gennemse, ret eller tilføj før godkendelse</h4></div>', unsafe_allow_html=True)

        if st.session_state.get("scan_raatekst"):
            with st.expander("Vis rå aflæst tekst fra billedet"):
                st.text(st.session_state["scan_raatekst"])

        marked_type = st.selectbox(
            "Markedstype / Kategori:",
            [
                "Standard (1X2 / Mål)",
                "Hjørnespark (Over/Under/Flest)",
                "Spillerskud & Skud på mål",
                "Tacklinger & Målmandsredninger",
                "Kort-sandsynlighed (Gule/Røde)",
                "Målscorere (Anytime/Første)",
                "Kombinationskupon"
            ],
            key="scan_marked_type"
        )

        kampe_tekst = st.text_input(
            "Kampe & udfald på kuponen (ret eller tilføj):",
            value=st.session_state.get("scan_kampe", ""),
            placeholder="F.eks. FCK - AGF (1), Arsenal - Chelsea (Over 2.5 mål)",
            key="input_scan_kampe"
        )

        col1, col2 = st.columns(2)
        with col1:
            odds_val = st.number_input(
                "Samlet kupon-odds:",
                min_value=1.01,
                value=max(1.01, float(st.session_state.get("scan_odds", 2.00))),
                step=0.10,
                key="input_scan_odds"
            )
        with col2:
            indsats_val = st.number_input(
                "Indsats i kr. (Standard 100 kr.):",
                min_value=1.0,
                value=max(1.0, float(st.session_state.get("scan_indsats", 100.0))),
                step=10.0,
                key="input_scan_indsats"
            )

        potentiel_gevinst = round(odds_val * indsats_val, 2)
        st.caption(f"Beregnet potentiel udbetaling: **{potentiel_gevinst:.2f} kr.** (Intet er gemt før du trykker SPILLET)")

        if st.button("🚀 SPILLET (Godkend & send til statistik + Supabase)", type="primary", key="btn_spillet_billede"):
            if not kampe_tekst.strip():
                st.warning("Indtast eller ret mindst én kamp på kuponen, før du trykker SPILLET.")
            else:
                gemt = gem_data.gem_kupon_i_historik(
                    [marked_type],
                    [kampe_tekst.strip()],
                    odds_val,
                    odds_val,
                    odds_val,
                    "Agnostisk Kupon",
                    5,
                    indsats_val
                )
                if gemt:
                    st.success("✓ Kuponen er markeret som SPILLET og gemt permanent i Supabase!")
                    st.rerun()
                else:
                    st.error("❌ Kunne ikke gemme i Supabase. Tjek dine Secrets og netværksforbindelse.")
