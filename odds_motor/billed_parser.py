import io
import streamlit as st
from historik import gem_data
from odds_motor import liga_favoritter, billed_hjaelp

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    from rapidocr_onnxruntime import RapidOCR
    OCR_MOTOR = RapidOCR()
except Exception:
    OCR_MOTOR = None

def vis_billed_scanner():
    st.markdown("<style>.kupon-stamme{background:linear-gradient(145deg,#161b22,#1f2630);border:1px solid #00E676;border-radius:12px;padding:14px;margin:10px 0;color:#f0f6fc}</style>", unsafe_allow_html=True)

    liga_liste = liga_favoritter.hent_favorit_ligaer()
    valgt_liga = st.selectbox(f"🏆 Vælg Liga ({len(liga_liste)} Favoritter aktive):", liga_liste, key="aktiv_favorit_liga")

    with st.expander("⚙️ Administrer dine favoritligaer (Tilføj ny eller fjern valgt)"):
        c1, c2 = st.columns(2)
        with c1:
            ny_liga = st.text_input("➕ Ny favoritliga:", placeholder="F.eks. Brasilien - Serie A", key="ny_liga_txt")
            if st.button("Tilføj til favoritter", key="btn_gem_ny_liga") and liga_favoritter.tilfoej_ny_favorit_liga(ny_liga):
                st.rerun()
        with c2:
            st.write(f"Valgt: **{valgt_liga}**")
            if st.button("🗑️ Fjern liga", key="btn_fjern_liga") and liga_favoritter.fjern_favorit_liga(valgt_liga):
                st.rerun()

    up = st.file_uploader("📸 Upload kupon-screenshot (PNG, JPG):", type=["png", "jpg", "jpeg"], key="scan_up")
    if up is not None:
        b_data = up.getvalue()
        st.image(Image.open(io.BytesIO(b_data)) if PIL_OK else b_data, caption="Indlæst kupon (Afventer SPILLET)", use_container_width=True)
        fid = f"{up.name}_{len(b_data)}"
        if st.session_state.get("sidst_scannede_fil_id") != fid:
            linjer = []
            if OCR_MOTOR is not None:
                try:
                    res, _ = OCR_MOTOR(b_data)
                    linjer = billed_hjaelp.parse_ocr_resultat(res)
                except Exception as e:
                    print(f"[OCR-Advarsel]: {e}")
            k_str, o_val, i_val = billed_hjaelp.udtraek_kupon_moenstre(linjer)
            st.session_state.update({"sidst_scannede_fil_id": fid, "scan_kampe": k_str, "scan_odds": float(o_val), "scan_indsats": float(i_val), "scan_raatekst": "\n".join(linjer)})

        if st.session_state.get("scan_raatekst"):
            with st.expander("Vis rå aflæst tekst fra billedet"):
                st.text(st.session_state["scan_raatekst"])

    st.markdown(f'<div class="kupon-stamme"><h4>🎯 Aktiv Kuponstamme ({valgt_liga})</h4><p style="margin:0;font-size:0.9em;color:#8b949e">Ret aflæste kampe eller tilføj egne valg før SPILLET.</p></div>', unsafe_allow_html=True)

    marked = st.selectbox("Markedstype:", ["Standard (1X2 / Mål)", "Hjørnespark (Over/Under/Flest)", "Spillerskud & Skud på mål", "Tacklinger & Målmandsredninger", "Kort-sandsynlighed (Gule/Røde)", "Målscorere (Anytime/Første)", "Kombinationskupon"], key="scan_marked_type")
    kampe_txt = st.text_input("Kampe & udfald (adskil med komma):", value=st.session_state.get("scan_kampe", ""), placeholder="F.eks. FCK - AGF (1), Arsenal - Chelsea (Over 2.5 mål)", key="input_scan_kampe")

    col1, col2 = st.columns(2)
    with col1:
        odds_val = st.number_input("Samlet odds:", min_value=1.01, value=max(1.01, float(st.session_state.get("scan_odds", 2.00))), step=0.10, key="input_scan_odds")
    with col2:
        indsats_val = st.number_input("Indsats kr. (Std. 100 kr.):", min_value=1.0, value=max(1.0, float(st.session_state.get("scan_indsats", 100.0))), step=10.0, key="input_scan_indsats")

    if kampe_txt.strip():
        berigede, chance_pct, stjerner, flammer = billed_hjaelp.analyser_kupon_kampe(kampe_txt, odds_val)
        st.info(f"📊 **Vurdering:** {chance_pct}% chance | Værdi: {'⭐'*stjerner} | Risiko: {'🔥'*flammer} | Potentiel gevinst: **{odds_val * indsats_val:.2f} kr.**")
        for bk in berigede:
            ctx = bk.get("ctx") or {}
            v = ctx.get("vejr")
            v_txt = f"{v['temp']}°C, {v['vind']} m/s ({v['effekt']})" if v else "Vejr ukendt"
            st.caption(f"⚽ **{bk.get('hj')} vs {bk.get('ud')}** | 👨‍⚖️ Dommer: {ctx.get('dommer')} | 🌦️ {v_txt}")

    if st.button("🚀 SPILLET (Godkend & send til statistik + Supabase)", type="primary", key="btn_spillet_billede"):
        if not kampe_txt.strip():
            st.warning("Skriv mindst én kamp før du trykker SPILLET.")
        elif gem_data.gem_kupon_i_historik([valgt_liga, marked], [kampe_txt.strip()], odds_val, odds_val, odds_val, "Agnostisk Kupon", 5, indsats_val):
            st.session_state["scan_kampe"] = ""
            st.success("✓ Kuponen er markeret som SPILLET og gemt i Supabase!")
            st.rerun()
