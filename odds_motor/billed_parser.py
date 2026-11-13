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

def _koer_ocr(b_data):
    ren_bytes = billed_hjaelp.klargoer_billede(b_data)
    if OCR_MOTOR is not None:
        try:
            res, _ = OCR_MOTOR(ren_bytes)
            linjer = [str(p[1] if isinstance(p, (list, tuple)) and len(p) >= 2 else p).strip() for p in (res or [])]
            linjer = [l for l in linjer if l]
            if linjer: return linjer, ""
        except Exception:
            pass
    return billed_hjaelp.aflaes_via_cloud_ocr(ren_bytes)

def _vurder_kupon(odds_v):
    pct = round(max(4.0, min(92.0, (100.0 / max(1.01, odds_v)) * 0.94)), 1)
    stj = max(1, min(5, int(round((pct * odds_v) / 21.0))))
    flm = max(1, min(5, int(round((100.0 - pct) / 17.0))))
    return pct, stj, flm

def vis_billed_scanner():
    up = st.file_uploader("📸 Upload kupon-screenshot (PNG, JPG):", type=["png", "jpg", "jpeg"], key="scan_up")
    if up is not None:
        b_data = up.getvalue()
        st.image(Image.open(io.BytesIO(b_data)), caption="Indlæst kupon (0,00 kr. gemt før SPILLET)", use_container_width=True)
        fid = f"{up.name}_{len(b_data)}"
        if st.session_state.get("sidst_scannede_fil_id") != fid:
            with st.spinner("🔍 Aflæser kupon og analyserer hver enkelt kamp..."):
                linjer, fejl = _koer_ocr(b_data)
                k_liste, s_odds, s_ind = billed_hjaelp.udtraek_kupon_liste(linjer)
                st.session_state.update({"sidst_scannede_fil_id": fid, "scan_liste": k_liste, "scan_odds": float(s_odds), "scan_indsats": float(s_ind), "scan_raa": "\n".join(linjer), "scan_fejl": fejl, "ny_kupon_klar": False})

    kampe_liste = st.session_state.get("scan_liste", [])
    if not kampe_liste:
        if up is not None:
            st.warning(f"OCR-status: {st.session_state.get('scan_fejl') or 'Ingen kampe parret'}")
            if st.session_state.get("scan_raa"): st.code(st.session_state["scan_raa"])
        else:
            st.info("Upload et kupon-screenshot ovenfor, så analyserer robotten hver kamp og foreslår optimeringer.")
        return

    st.subheader("1️⃣ Komplet Analyse & Forslag pr. Kamp/Linje")
    gamle_linjer, nye_linjer = [], []
    for idx, item in enumerate(kampe_liste):
        res = billed_hjaelp.analyser_enkelt_kamp(item["kamp"], item["spil"], item["odds"])
        gl_txt = f"{item['kamp']} ({item['spil']})"
        gamle_linjer.append(gl_txt)
        with st.container(border=True):
            st.markdown(f"**Kamp {idx+1}: {item['kamp']}** | Odds: `{item['odds']:.2f}` | **{res['pct']}%** | {'⭐'*res['stj']} | {'🔥'*res['flm']}")
            st.write(f"🧠 **Samlet kampanalyse:** {res['analyse']}")
            brug = st.checkbox(f"💡 Brug forslag: {res['forslag']}", key=f"chk_f_{idx}")
            valgt_txt = st.text_input("Ret eller tilpas din linje:", value=(res["forslag"] if brug else gl_txt), key=f"txt_k_{idx}")
            if valgt_txt.strip(): nye_linjer.append(valgt_txt.strip())

    c1, c2 = st.columns(2)
    with c1: gl_odds = st.number_input("Gammel kupon odds:", min_value=1.01, value=max(1.01, float(st.session_state.get("scan_odds", 2.00))), step=0.10, key="in_gl_odds")
    with c2: ny_odds = st.number_input("Ny kupon odds:", min_value=1.01, value=max(1.01, round(gl_odds * 0.85, 2)), step=0.10, key="in_ny_odds")
    indsats = st.number_input("Indsats kr. (Std. 100 kr.):", min_value=1.0, value=max(1.0, float(st.session_state.get("scan_indsats", 100.0))), step=10.0, key="in_s_ind")

    if st.button("✅ BRUG VALGTE ÆNDRINGER (Sammenlign Gammel vs. Ny Kupon)", use_container_width=True, key="btn_aktiver_ok"):
        st.session_state["ny_kupon_klar"] = True

    if st.session_state.get("ny_kupon_klar"):
        st.subheader("2️⃣ Sammenligning: Gammel Kupon vs. Ny Kupon")
        gl_pct, gl_stj, gl_flm = _vurder_kupon(gl_odds)
        ny_pct, ny_stj, ny_flm = _vurder_kupon(ny_odds)
        col_g, col_n = st.columns(2)
        with col_g:
            st.info(f"**📄 GAMMEL KUPON**\n\n{', '.join(gamle_linjer)}\n\nOdds: **{gl_odds:.2f}** | Chance: **{gl_pct}%**\n\nVærdi: {'⭐'*gl_stj} | Risiko: {'🔥'*gl_flm}")
        with col_n:
            st.success(f"**✨ NY KUPON**\n\n{', '.join(nye_linjer)}\n\nOdds: **{ny_odds:.2f}** | Chance: **{ny_pct}%**\n\nVærdi: {'⭐'*ny_stj} | Risiko: {'🔥'*ny_flm}")

        valg = st.radio("Vælg hvilken kupon du vil tilføje til statistikken:", ["✨ Ny Kupon", "📄 Gammel Kupon"], horizontal=True, key="rad_kupon_valg")
        if st.button("🚀 SPILLET (Tilføj valgte kupon til statistik + Supabase)", type="primary", use_container_width=True, key="btn_spillet_billede"):
            k_str = ", ".join(nye_linjer) if "Ny" in valg else ", ".join(gamle_linjer)
            o_val = ny_odds if "Ny" in valg else gl_odds
            s_val = ny_stj if "Ny" in valg else gl_stj
            if gem_data.gem_kupon_i_historik(["Universel Billed-Kupon"], [k_str], o_val, o_val, o_val, valg, s_val, indsats):
                st.session_state["ny_kupon_klar"] = False
                st.success(f"✓ {valg} er markeret som SPILLET og gemt permanent i Supabase!")
                st.rerun()
