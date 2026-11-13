import io, streamlit as st
from PIL import Image
from historik import gem_data
from odds_motor import billed_hjaelp

try:
    from rapidocr_onnxruntime import RapidOCR
    OCR_MOTOR = RapidOCR()
except Exception:
    OCR_MOTOR = None

def _koer_ocr(b_data):
    if OCR_MOTOR is not None:
        for img_bytes in (b_data, billed_hjaelp.klargoer_billede(b_data)):
            try:
                res, _ = OCR_MOTOR(img_bytes)
                linjer = [str(p[1] if isinstance(p, (list, tuple)) and len(p) >= 2 else p).strip() for p in (res or [])]
                linjer = [l for l in linjer if l]
                if linjer: return linjer, ""
            except Exception:
                pass
    return billed_hjaelp.aflaes_via_cloud_ocr(billed_hjaelp.klargoer_billede(b_data))

def _vurder_kupon(odds_v):
    pct = round(max(3.0, min(92.0, (100.0 / max(1.01, odds_v)) * 0.94)), 1)
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
            with st.spinner("🔍 Aflæser kupon og beregner risiko & odds-målzone..."):
                linjer, fejl = _koer_ocr(b_data)
                k_liste, s_ind = billed_hjaelp.udtraek_kupon_liste(linjer)
                st.session_state.update({"sidst_scannede_fil_id": fid, "scan_liste": k_liste, "scan_indsats": float(s_ind), "scan_raa": "\n".join(linjer), "scan_fejl": fejl, "ny_kupon_klar": False})

    kampe = st.session_state.get("scan_liste", [])
    if not kampe:
        if up is not None:
            st.warning(f"OCR-status: {st.session_state.get('scan_fejl') or 'Ingen kampe fundet'}")
            if st.session_state.get("scan_raa"): st.code(st.session_state["scan_raa"])
        else:
            st.info("Upload en kupon ovenfor. Robotten holder sig til dine valgte kampe, analyserer risiko og giver 2–3 odds-justerede forslag pr. kamp.")
        return

    gl_odds = 1.0
    for k in kampe: gl_odds *= float(k["odds"])
    gl_odds = round(gl_odds, 2)
    min_maal, max_maal = round(gl_odds * 0.88, 2), round(gl_odds * 1.12, 2)
    st.info(f"🎯 **Oprindeligt kupon-odds:** `{gl_odds:.2f}` | **Robottens målzone ved ændringer:** `{min_maal:.2f} – {max_maal:.2f}` (±12 %)")

    nye_valg, gamle_valg, ny_odds = [], [], 1.0
    for idx, item in enumerate(kampe):
        faktor = max(0.75, min(1.30, (gl_odds / max(1.01, ny_odds * (item["odds"] ** (len(kampe) - idx)))) ** (1.0 / max(1, len(kampe) - idx))))
        res = billed_hjaelp.analyser_kamp_med_maalzone(item["kamp"], item["spil"], item["odds"], faktor)
        gl_txt = f"{item['kamp']} ({item['spil']}) @ {item['odds']:.2f}"
        gamle_valg.append(gl_txt)
        with st.container(border=True):
            st.markdown(f"**{idx+1}. {item['kamp']}** | Odds: `{item['odds']:.2f}` | **{res['pct']}%** | {'⭐'*res['stj']} | {'🔥'*res['flm']}")
            st.caption(res["tekst"])
            opts = [f"Behold oprindelig: {item['spil']} ({item['odds']:.2f})"] + [f"{f['txt']} ({f['odds']:.2f})" for f in res["forslag"]]
            if res["erstat_raad"]:
                opts.append(f"⚠️ Helt på månen (🔥5): Bed robotten finde en helt anden erstatningskamp ({item['odds']:.2f})")
            valg_i = st.radio("Vælg strategi for denne kamp:", opts, key=f"rad_k_{idx}")
            if valg_i.startswith("Behold"):
                valgt_s, valgt_o = f"{item['kamp']} ({item['spil']})", float(item["odds"])
            elif valg_i.startswith("⚠️"):
                valgt_s, valgt_o = f"[Erstatningskamp ønsket for {item['kamp']}]", float(item["odds"])
            else:
                f_idx = opts.index(valg_i) - 1
                valgt_s, valgt_o = res["forslag"][f_idx]["txt"], float(res["forslag"][f_idx]["odds"])
            nye_valg.append(f"{valgt_s} @ {valgt_o:.2f}")
            ny_odds = round(ny_odds * valgt_o, 2)

    indsats = st.number_input("Indsats kr. (Std. 100 kr.):", min_value=1.0, value=max(1.0, float(st.session_state.get("scan_indsats", 100.0))), step=10.0, key="in_s_ind")
    if st.button("✅ SAMMENLIGN GAMMEL VS. NY KUPON", use_container_width=True, key="btn_aktiver_ok"):
        st.session_state["ny_kupon_klar"] = True

    if st.session_state.get("ny_kupon_klar"):
        gl_p, gl_s, gl_f = _vurder_kupon(gl_odds)
        ny_p, ny_s, ny_f = _vurder_kupon(ny_odds)
        c1, c2 = st.columns(2)
        with c1: st.info(f"**📄 GAMMEL KUPON**\n\n" + "\n".join(f"- {x}" for x in gamle_valg) + f"\n\n**Samlet odds:** `{gl_odds:.2f}` | **{gl_p}%** | {'⭐'*gl_s} | {'🔥'*gl_f}")
        with c2: st.success(f"**✨ NY KUPON**\n\n" + "\n".join(f"- {x}" for x in nye_valg) + f"\n\n**Samlet odds:** `{ny_odds:.2f}` | **{ny_p}%** | {'⭐'*ny_s} | {'🔥'*ny_f}")
        kupon_valg = st.radio("Hvilken kupon vil du sende til statistikken?", ["✨ Ny Kupon", "📄 Gammel Kupon"], horizontal=True, key="rad_kupon_valg")
        if st.button("🚀 SPILLET (Gem valgte kupon i statistik + Supabase)", type="primary", use_container_width=True, key="btn_spillet_billede"):
            k_str = ", ".join(nye_valg) if "Ny" in kupon_valg else ", ".join(gamle_valg)
            o_val = ny_odds if "Ny" in kupon_valg else gl_odds
            s_val = ny_s if "Ny" in kupon_valg else gl_s
            if gem_data.gem_kupon_i_historik(["Universel Billed-Kupon"], [k_str], o_val, o_val, o_val, kupon_valg, s_val, indsats):
                st.session_state["ny_kupon_klar"] = False
                st.success(f"✓ {kupon_valg} er markeret som SPILLET og gemt permanent i Supabase!")
                st.rerun()
