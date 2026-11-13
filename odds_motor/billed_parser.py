import io, streamlit as st
from PIL import Image
from historik import gem_data
from odds_motor import billed_hjaelp, billed_ocr

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
            with st.spinner("🔍 Aflæser alle kampe lokalt på serveren..."):
                linjer, fejl = billed_ocr.laes_tekst_lokalt(b_data)
                k_liste, s_ind = billed_ocr.udtraek_kupon_liste(linjer)
                st.session_state.update({"sidst_scannede_fil_id": fid, "scan_liste": k_liste, "scan_indsats": float(s_ind), "scan_raa": "\n".join(linjer), "scan_fejl": fejl, "ny_kupon_klar": False})

    kampe = st.session_state.get("scan_liste", [])
    if not kampe:
        if up is not None:
            st.warning(f"OCR-status: {st.session_state.get('scan_fejl') or 'Ingen kampe fundet'}")
            if st.session_state.get("scan_raa"): st.code(st.session_state["scan_raa"])
        else:
            st.info("Upload en kupon ovenfor. Robotten analyserer alle kampe og giver 3 odds-justerede forslag med % pr. kamp.")
        return

    gl_odds = round(eval("*".join(str(k["odds"]) for k in kampe)), 2)
    st.info(f"🎯 **Oprindeligt kupon-odds:** `{gl_odds:.2f}` ({len(kampe)} kampe) | **Robottens målzone:** `{round(gl_odds*0.88,2):.2f} – {round(gl_odds*1.12,2):.2f}` (±12 %)")

    nye_valg, gamle_valg, ny_odds = [], [], 1.0
    for idx, item in enumerate(kampe):
        faktor = max(0.75, min(1.30, (gl_odds / max(1.01, ny_odds * (item["odds"] ** (len(kampe) - idx)))) ** (1.0 / max(1, len(kampe) - idx))))
        res = billed_hjaelp.analyser_kamp_med_maalzone(item["kamp"], item["spil"], item["odds"], faktor)
        gamle_valg.append(f"{item['kamp']} ({item['spil']}) @ {item['odds']:.2f} ({res['pct']}%)")
        with st.container(border=True):
            st.markdown(f"**{idx+1}. {item['kamp']}** | Odds: `{item['odds']:.2f}` | **{res['pct']}%** | {'⭐'*res['stj']} | {'🔥'*res['flm']}")
            st.caption(res["tekst"])
            opts = [f"Behold oprindelig: {item['spil']} @ {item['odds']:.2f} ({res['pct']}%)"] + [f"{f['txt']} @ {f['odds']:.2f} ({f['pct']}%)" for f in res["forslag"]]
            valg_i = st.radio("Vælg strategi for denne kamp:", opts, key=f"rad_k_{idx}")
            if valg_i.startswith("Behold"):
                valgt_s, valgt_o, valgt_p = f"{item['kamp']} ({item['spil']})", float(item["odds"]), res["pct"]
            else:
                f_obj = res["forslag"][opts.index(valg_i) - 1]
                valgt_s, valgt_o, valgt_p = f_obj["txt"], float(f_obj["odds"]), f_obj["pct"]
            if res["svaer_match"]:
                st.caption("💬 *Jeg har svært ved at finde et alternativt odds på denne kamp der matcher kuponens niveau – skal vi finde en helt anden kamp til dig?*")
                if st.checkbox("Ja, find en anden kamp i stedet for denne", key=f"chk_alt_{idx}"):
                    valgt_s = f"[Bed robotten finde erstatningskamp for {item['kamp']}]"
            nye_valg.append(f"{valgt_s} @ {valgt_o:.2f} ({valgt_p}%)")
            ny_odds = round(ny_odds * valgt_o, 2)

    indsats = st.number_input("Indsats kr. (Std. 100 kr.):", min_value=1.0, value=max(1.0, float(st.session_state.get("scan_indsats", 100.0))), step=10.0, key="in_s_ind")
    if st.button("✅ SAMMENLIGN GAMMEL VS. NY KUPON", use_container_width=True, key="btn_aktiver_ok"):
        st.session_state["ny_kupon_klar"] = True

    if st.session_state.get("ny_kupon_klar"):
        gl_p, gl_s, gl_f = _vurder_kupon(gl_odds)
        ny_p, ny_s, ny_f = _vurder_kupon(ny_odds)
        gl_txt_a = "Høj samlet varians på flere kombinerede udfald." if gl_f >= 4 else "Solid oprindelig sammensætning."
        ny_txt_a = f"Forbedret træfsikkerhed (+{round(ny_p-gl_p,1)}%) med lavere risiko." if ny_p > gl_p else "Højere samlet odds og større gevinstpotentiale."
        c1, c2 = st.columns(2)
        with c1: st.info(f"**📄 GAMMEL KUPON**\n\n" + "\n".join(f"- {x}" for x in gamle_valg) + f"\n\n**Analyse:** {gl_txt_a}\n\n**Samlet odds:** `{gl_odds:.2f}` | **{gl_p}%** | {'⭐'*gl_s} | {'🔥'*gl_f}")
        with c2: st.success(f"**✨ NY KUPON**\n\n" + "\n".join(f"- {x}" for x in nye_valg) + f"\n\n**Analyse:** {ny_txt_a}\n\n**Samlet odds:** `{ny_odds:.2f}` | **{ny_p}%** | {'⭐'*ny_s} | {'🔥'*ny_f}")
        kupon_valg = st.radio("Hvilken kupon vil du sende til statistikken?", ["✨ Ny Kupon", "📄 Gammel Kupon"], horizontal=True, key="rad_kupon_valg")
        if st.button("🚀 SPILLET (Gem valgte kupon i statistik + Supabase)", type="primary", use_container_width=True, key="btn_spillet_billede"):
            k_str = ", ".join(nye_valg) if "Ny" in kupon_valg else ", ".join(gamle_valg)
            o_val, s_val = (ny_odds, ny_s) if "Ny" in kupon_valg else (gl_odds, gl_s)
            if gem_data.gem_kupon_i_historik(["Universel Billed-Kupon"], [k_str], o_val, o_val, o_val, kupon_valg, s_val, indsats):
                st.session_state["ny_kupon_klar"] = False
                st.success(f"✓ {kupon_valg} er markeret som SPILLET og gemt permanent i Supabase!")
                st.rerun()
