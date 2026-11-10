import io
import re
import streamlit as st
from historik import gem_data
from odds_motor import liga_favoritter

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
    detekterede_kampe = []
    alle_odds = []
    fundet_indsats = 100.0

    kamp_moenster = re.compile(r"([A-Za-zÆØÅæøå0-9\.\-\s]{2,28})\s+(?:-|–|vs\.?|v)\s+([A-Za-zÆØÅæøå0-9\.\-\s]{2,28})", re.IGNORECASE)
    odds_moenster = re.compile(r"\b(\d{1,3}[.,]\d{2})\b")
    indsats_moenster = re.compile(r"(?:indsats|stake|beløb|spillet|kr\.?|dkk)\s*[:\-]?\s*(\d+(?:[.,]\d{1,2})?)", re.IGNORECASE)
    ignorer_ord = ["indsats", "gevinst", "udbetaling", "total", "samlet", "kupon", "odds", "spillet", "dato", "tid", "live"]

    kandidat_linjer = []

    for linje in raatekst_linjer:
        ren_linje = str(linje).strip()
        if not ren_linje:
            continue

        m_indsats = indsats_moenster.search(ren_linje)
        if m_indsats:
            try:
                val = float(m_indsats.group(1).replace(",", "."))
                if val > 0:
                    fundet_indsats = val
            except ValueError:
                pass

        for match in odds_moenster.findall(ren_linje):
            try:
                tal = float(match.replace(",", "."))
                if 1.01 <= tal <= 500.0:
                    alle_odds.append(tal)
            except ValueError:
                pass

        m_kamp = kamp_moenster.search(ren_linje)
        if m_kamp and not any(ord_i in ren_linje.lower() for ord_i in ignorer_ord):
            hjemme = m_kamp.group(1).strip()
            ude = m_kamp.group(2).strip()
            detekterede_kampe.append(f"{hjemme} - {ude}")
        elif len(ren_linje) >= 3 and not any(c.isdigit() for c in ren_linje) and not any(ord_i in ren_linje.lower() for ord_i in ignorer_ord):
            kandidat_linjer.append(ren_linje)

    if not detekterede_kampe and len(kandidat_linjer) >= 2:
        for i in range(0, len(kandidat_linjer) - 1, 2):
            detekterede_kampe.append(f"{kandidat_linjer[i]} - {kandidat_linjer[i+1]}")

    samlet_odds = max(alle_odds) if alle_odds else 2.00
    kampe_streng = ", ".join(dict.fromkeys(detekterede_kampe)) if detekterede_kampe else ""
    return kampe_streng, samlet_odds, fundet_indsats


def vis_billed_scanner():
    st.markdown("""
        <style>
        .kupon-stamme {
            background: linear-gradient(145deg, #161b22, #1f2630);
            border: 1px solid #00E676;
            border-radius: 12px;
            padding: 16px;
            margin-top: 10px;
            margin-bottom: 14px;
            color: #f0f6fc;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- SEKTION 1: LIGA-FAVORITTER (TILFØJ & FJERN) ---
    liga_liste = liga_favoritter.hent_favorit_ligaer()
    valgt_liga = st.selectbox(
        f"🏆 Vælg Liga ({len(liga_liste)} Favoritter aktive):",
        liga_liste,
        key="aktiv_favorit_liga"
    )

    with st.expander("⚙️ Administrer dine favoritligaer (Tilføj ny eller fjern valgt)"):
        col_tilfoej, col_fjern = st.columns(2)
        with col_tilfoej:
            ny_liga_input = st.text_input("➕ Ny favoritliga:", placeholder="F.eks. Brasilien - Serie A", key="ny_liga_txt")
            if st.button("Tilføj til favoritter", key="btn_gem_ny_liga"):
                if liga_favoritter.tilfoej_ny_favorit_liga(ny_liga_input):
                    st.success(f"Tilføjet: {ny_liga_input}")
                    st.rerun()
        with col_fjern:
            st.write(f"Valgt liga: **{valgt_liga}**")
            if st.button("🗑️ Fjern denne liga fra favoritter", key="btn_fjern_liga"):
                if liga_favoritter.fjern_favorit_liga(valgt_liga):
                    st.warning(f"Fjernet: {valgt_liga}")
                    st.rerun()

    # --- SEKTION 2: BILLED-UPLOAD & OCR ---
    uploadet_fil = st.file_uploader(
        "📸 Upload kupon-screenshot (PNG, JPG):",
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
                        raatekst = [punkt for punkt in resultat if len(punkt) > 1]
                        detekteret_kampe, detekteret_odds, detekteret_indsats = _udtraek_kupon_moenstre(raatekst)
                except Exception as e:
                    print(f"[OCR-Advarsel]: {e}")

            st.session_state["sidst_scannede_fil_id"] = fil_id
            st.session_state["scan_kampe"] = detekteret_kampe
            st.session_state["scan_odds"] = float(detekteret_odds)
            st.session_state["scan_indsats"] = float(detekteret_indsats)
            st.session_state["scan_raatekst"] = "\n".join(raatekst)

        if st.session_state.get("scan_raatekst"):
            with st.expander("Vis rå aflæst tekst fra billedet"):
                st.text(st.session_state["scan_raatekst"])

    # --- SEKTION 3: MØRK KUPONSTAMME ---
    st.markdown(f'<div class="kupon-stamme"><h4>🎯 Aktiv Kuponstamme ({valgt_liga})</h4><p style="margin:0; font-size:0.9em; color:#8b949e;">Ret aflæste kampe eller tilføj dine egne kampe nedenfor, før du godkender med SPILLET.</p></div>', unsafe_allow_html=True)

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
    st.caption(f"Beregnet potentiel udbetaling: **{potentiel_gevinst:.2f} kr.** (Intet gemmes før du trykker SPILLET)")

    if st.button("🚀 SPILLET (Godkend & send til statistik + Supabase)", type="primary", key="btn_spillet_billede"):
        if not kampe_tekst.strip():
            st.warning("Skriv mindst én kamp i feltet ovenfor (f.eks. 'FCK - AGF (1)'), før du trykker SPILLET.")
        else:
            gemt = gem_data.gem_kupon_i_historik(
                [valgt_liga, marked_type],
                [kampe_tekst.strip()],
                odds_val,
                odds_val,
                odds_val,
                "Agnostisk Kupon",
                5,
                indsats_val
            )
            if gemt:
                st.session_state["scan_kampe"] = ""
                st.success("✓ Kuponen er markeret som SPILLET og gemt permanent i Supabase!")
                st.rerun()
            else:
                st.error("❌ Kunne ikke gemme i Supabase. Tjek dine Secrets.")
