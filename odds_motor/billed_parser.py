import io
import streamlit as st
from PIL import Image
from historik import gem_data
from odds_motor import billed_hjaelp

try:
    from rapidocr_onnxruntime import RapidOCR
    OCR_MOTOR = RapidOCR()
except Exception:
    OCR_MOTOR = None

try:
    import pytesseract
    TESS_OK = True
except Exception:
    TESS_OK = False

def _koer_ocr(b_data):
    ren_bytes, pil_img = billed_hjaelp.klargoer_billede(b_data)
    linjer = []
    if OCR_MOTOR is not None:
        try:
            res, _ = OCR_MOTOR(ren_bytes)
            linjer = billed_hjaelp.parse_ocr_resultat(res)
        except Exception:
            pass
    if not linjer and TESS_OK:
        try:
            txt = pytesseract.image_to_string(pil_img)
            linjer = [l.strip() for l in txt.splitlines() if l.strip()]
        except Exception:
            pass
    return linjer

def vis_billed_scanner():
    up = st.file_uploader("📸 Upload kupon-screenshot (PNG, JPG):", type=["png", "jpg", "jpeg"], key="scan_up")
    if up is not None:
        b_data = up.getvalue()
        st.image(Image.open(io.BytesIO(b_data)), caption="Indlæst kupon (0,00 kr. gemt før SPILLET)", use_container_width=True)
        fid = f"{up.name}_{len(b_data)}"
        if st.session_state.get("sidst_scannede_fil_id") != fid:
            linjer = _koer_ocr(b_data)
            k_liste, s_odds, s_ind = billed_hjaelp.udtraek_kupon_liste(linjer)
            st.session_state.update({"sidst_scannede_fil_id": fid, "scan_liste": k_liste, "scan_odds": float(s_odds), "scan_indsats": float(s_ind), "scan_raa": "\n".join(linjer), "ny_kupon_klar": False})

    kampe_liste = st.session_state.get("scan_liste", [])
    if not kampe_liste:
        if up is not None and st.session_state.get("scan_raa"):
            with st.expander("Se rå aflæsning fra billedet"):
                st.text(st.session_state["scan_raa"])
        st.info("Upload et kupon-screenshot ovenfor, så analyserer robotten hver enkelt kamp med stjerner, flammer, % og ændringsforslag.")
        return

    st.subheader("🔍 Robottens Kamp-for-Kamp Analyse & Tilpasning")
    valgte_linjer = []
    for idx, item in enumerate(kampe_liste):
        res = billed_hjaelp.analyser_enkelt_kamp(item["kamp"], item["spil"], item["odds"])
        with st.container(border=True):
            st.markdown(f"**{idx+1}. {item['kamp']}** — Odds: `{item['odds']:.2f}` | Chance: **{res['pct']}%** | {'⭐'*res['stj']} | {'🔥'*res['flm']}")
            st.caption(f"🧠 {res['analyse']}")
            brug_forslag = st.checkbox(f"💡 Robot-forslag: Skift til '{res['forslag']}'", key=f"chk_f_{idx}") if res["forslag"] else False
            std_txt = res["forslag"] if brug_forslag else f"{item['kamp']} ({item['spil']})"
            egen_txt = st.text_input("Dit spil på denne kamp (ret eller skriv eget):", value=std_txt, key=f"txt_k_{idx}")
            if egen_txt.strip():
                valgte_linjer.append(egen_txt.strip())

    col1, col2 = st.columns(2)
    with col1:
        samlet_odds = st.number_input("Samlet kupon-odds:", min_value=1.01, value=max(1.01, float(st.session_state.get("scan_odds", 2.00))), step=0.10, key="in_s_odds")
    with col2:
        indsats = st.number_input("Indsats kr. (Std. 100 kr.):", min_value=1.0, value=max(1.0, float(st.session_state.get("scan_indsats", 100.0))), step=10.0, key="in_s_ind")

    if st.button("✅ AKTIVER OK (Dan ny kupon & samlet analyse)", use_container_width=True, key="btn_aktiver_ok"):
        st.session_state["ny_kupon_klar"] = True

    if st.session_state.get("ny_kupon_klar") and valgte_linjer:
        ny_kupon_str = ", ".join(valgte_linjer)
        samlet_pct = round(max(4.0, min(92.0, (100.0 / samlet_odds) * 0.94)), 1)
        stj_tot = max(1, min(5, int(round((samlet_pct * samlet_odds) / 21.0))))
        flm_tot = max(1, min(5, int(round((100.0 - samlet_pct) / 17.0))))
        st.success(f"🎯 **Ny Kupon Klar:** {ny_kupon_str}\n\n📊 **Samlet Vurdering:** {samlet_pct}% chance | Værdi: {'⭐'*stj_tot} | Risiko: {'🔥'*flm_tot} | Potentiel gevinst: **{samlet_odds * indsats:.2f} kr.**")
        if st.button("🚀 SPILLET (Godkend & send til statistik + Supabase)", type="primary", use_container_width=True, key="btn_spillet_billede"):
            if gem_data.gem_kupon_i_historik(["Universel Billed-Kupon"], [ny_kupon_str], samlet_odds, samlet_odds, samlet_odds, "Billed-Scanner", stj_tot, indsats):
                st.session_state["ny_kupon_klar"] = False
                st.success("✓ Kuponen er markeret som SPILLET og gemt i Supabase!")
                st.rerun()
