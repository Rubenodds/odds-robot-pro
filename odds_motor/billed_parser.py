import streamlit as st
from odds_motor import billed_ocr as ocr, billed_hjaelp as bh

def _gem_til_historik(kampe, odds, indsats):
    try:
        from historik import gem_data as gd
        forslag = [f"{k['kamp']}: {k['spil']} (@ {k['odds']:.2f})" for k in kampe]
        return gd.gem_kupon_i_historik(kilde="Billed Scanner", kampe=forslag, odds=odds, indsats=indsats)
    except Exception as e:
        st.error(f"Kunne ikke gemme kupon: {e}")
        return False

def _godt_og_skidt(a):
    o, p = float(a.get("odds", 1.85)), float(a.get("pct", 50.0))
    godt = f"Stærk værdi på {a['spil']} ({p}% træfsikkerhed)" if p >= 52 else f"Høj udbetalingsfaktor (@ {o:.2f}) ved fuld træffer"
    skidt = f"Høj varians og lav hitrate ({p}%) gør kampen til kuponens risikopunkt" if o >= 2.25 else f"Lavere enkeltodds (@ {o:.2f}) kræver fuld disciplin uden uventede røde kort"
    return godt, skidt

def vis_billed_scanner():
    st.markdown("### 🧾 Kupon & Billed Scanner")
    if msg := st.session_state.pop("sidste_gem_ok", None):
        st.success(msg)

    fil = st.file_uploader("Upload screenshot af kupon", type=["png", "jpg", "jpeg"])
    if fil is not None and st.session_state.get("sidste_fil_navn") != fil.name:
        kampe, indsats, _ = ocr.udtraek_kupon_fra_billede(fil.read())
        st.session_state.update({"kupon_kampe": kampe, "kupon_indsats": indsats, "sidste_fil_navn": fil.name})

    kampe = st.session_state.get("kupon_kampe", [])
    indsats = st.number_input("Indsats (kr. — std. 100 kr.)", min_value=1.0, value=float(st.session_state.get("kupon_indsats", 100.0)), step=10.0)
    if not kampe:
        st.info("Upload et kuponbillede for at se robottens scanning og kuponanalyse.")
        return

    oprindelige, aktive_valg = [], []
    for idx, k in enumerate(kampe):
        a = bh.analyser_kupon_kamp(k)
        oprindelige.append({"kamp": a["kamp"], "spil": a["spil"], "odds": a["odds"], "pct": a["pct"]})
        godt, skidt = _godt_og_skidt(a)
        meta_html = f"<div style='font-size:12px;color:#60A5FA;margin-top:4px;'>{a['meta']}</div>" if a.get("meta") else ""
        st.markdown(
            f"<div style='background:#141923;color:#F3F4F6;padding:14px;border-radius:10px;border-left:4px solid #10B981;margin-bottom:8px;'>"
            f"<div style='font-size:16px;font-weight:700;'>{idx+1}. {a['kamp']} &nbsp;|&nbsp; Odds: <span style='color:#34D399;'>{a['odds']:.2f}</span> ({a['pct']}%)</div>"
            f"<div style='font-size:13px;color:#9CA3AF;margin:4px 0;'>Spil: <b>{a['spil']}</b> &nbsp;|&nbsp; {'⭐'*a['stjerner']} &nbsp;|&nbsp; {'🔥'*a['risiko']}</div>"
            f"<div style='font-size:13px;color:#34D399;margin-top:4px;'>✅ <b>Godt:</b> {godt}</div>"
            f"<div style='font-size:13px;color:#FBBF24;margin-top:2px;'>⚠️ <b>Skidt:</b> {skidt}</div>"
            f"{meta_html}</div>",
            unsafe_allow_html=True,
        )
        v_spil, v_odds, v_pct = a["spil"], a["odds"], a["pct"]
        if a.get("alternativer"):
            with st.expander(f"💡 Robotten har {len(a['alternativer'])} forslag til kamp {idx+1} (vælg ét eller flere)"):
                valgte_alt = []
                for i_alt, alt in enumerate(a["alternativer"]):
                    if st.checkbox(f"{alt['label']} @ {alt['odds']:.2f} ({alt['pct']}%)", key=f"alt_{idx}_{i_alt}"):
                        valgte_alt.append(alt)
                    hvorfor = alt.get("hvorfor") or f"Øger sandsynligheden til {alt['pct']}% og balancerer kuponens samlede risiko bedre end {a['spil']}."
                    st.caption(f"💡 **Hvorfor?** {hvorfor}")
                if valgte_alt:
                    v_spil = " + ".join(x["label"].split(": ")[-1] for x in valgte_alt)
                    rabat = 0.90 if len(valgte_alt) > 1 else 1.0
                    komb_o, komb_p = 1.0, 1.0
                    for x in valgte_alt:
                        komb_o *= x["odds"]
                        komb_p *= (x["pct"] / 100.0)
                    v_odds = round(komb_o * rabat, 2)
                    v_pct = round(min(85.0, komb_p * 100.0 * (1.08 if len(valgte_alt) > 1 else 1.0)), 1)
                    st.caption(f"✅ Aktivt valg på kamp {idx+1}: {v_spil} @ {v_odds:.2f} ({v_pct}%)")
        aktive_valg.append({"kamp": a["kamp"], "spil": v_spil, "odds": v_odds, "pct": v_pct})

    gl_a, ny_a = bh.samlet_kupon_analyse(oprindelige, indsats), bh.samlet_kupon_analyse(aktive_valg, indsats)
    er_aendret = any(o["spil"] != n["spil"] for o, n in zip(oprindelige, aktive_valg))
    titel = "🔄 Ny Kuponanalyse (efter dine justeringer)" if er_aendret else "🎯 Kuponanalyse af dit scannede spil"
    sml_html = f"<div style='font-size:12px;color:#FBBF24;margin-top:8px;'>Sammenligning: Oprindeligt odds {gl_a['odds']:.2f} ({gl_a['pct']}%) → Nyt odds {ny_a['odds']:.2f} ({ny_a['pct']}%)</div>" if er_aendret else ""

    st.markdown(
        f"<div style='background:#0F172A;color:#F8FAFC;padding:16px;border-radius:10px;border:1px solid #334155;margin-top:10px;'>"
        f"<div style='font-size:16px;font-weight:700;color:#34D399;'>{titel}</div>"
        f"<div style='font-size:14px;color:#CBD5E1;margin-top:4px;'>Totalodds: <b>{ny_a['odds']:.2f}</b> &nbsp;|&nbsp; Træfsikkerhed: <b>{ny_a['pct']}%</b> &nbsp;|&nbsp; Mulig gevinst: <b>{ny_a['gevinst']:.2f} kr.</b></div>"
        f"<div style='font-size:13px;color:#E2E8F0;margin-top:8px;'>{ny_a['dom']}</div>{sml_html}</div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    if c1.button("🚀 SPILLET — Gem kupon", type="primary", use_container_width=True):
        if _gem_til_historik(aktive_valg, ny_a["odds"], indsats):
            st.rerun()
    if c2.button("🗑️ Ryd kupon", use_container_width=True):
        st.session_state.pop("kupon_kampe", None)
        st.session_state.pop("sidste_fil_navn", None)
        st.rerun()
