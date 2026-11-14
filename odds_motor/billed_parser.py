import streamlit as st
from odds_motor import billed_ocr as ocr
from odds_motor import billed_hjaelp as bh

def _gem_til_supabase(kampe, odds, indsats):
    try:
        from historik import supabase_klient as sb
        if hasattr(sb, "gem_spil"):
            sb.gem_spil(kampe, odds, indsats, kilde="Billed Scanner")
            return True
    except Exception:
        pass
    return False

def vis_billed_scanner():
    st.markdown("### 🧾 Kupon & Billed Scanner")
    fil = st.file_uploader("Upload screenshot af kupon", type=["png", "jpg", "jpeg"])
    if fil is not None and st.session_state.get("sidste_fil_navn") != fil.name:
        kampe, indsats, _ = ocr.udtraek_kupon_fra_billede(fil.read())
        st.session_state["kupon_kampe"] = kampe
        st.session_state["kupon_indsats"] = indsats
        st.session_state["sidste_fil_navn"] = fil.name

    kampe = st.session_state.get("kupon_kampe", [])
    indsats = st.number_input("Indsats (kr. — std. 100 kr.)", min_value=1.0, value=float(st.session_state.get("kupon_indsats", 100.0)), step=10.0)

    if not kampe:
        st.info("Upload et kuponbillede for at se robottens scanning og kuponanalyse.")
        return

    oprindelige, aktive_valg = [], []
    for idx, k in enumerate(kampe):
        a = bh.analyser_kupon_kamp(k)
        oprindelige.append({"kamp": a["kamp"], "spil": a["spil"], "odds": a["odds"], "pct": a["pct"]})
        meta_html = f"<div style='font-size:12px;color:#60A5FA;margin-top:4px;'>{a['meta']}</div>" if a["meta"] else ""
        st.markdown(
            f"<div style='background:#141923;color:#F3F4F6;padding:14px;border-radius:10px;border-left:4px solid #10B981;margin-bottom:8px;'>"
            f"<div style='font-size:16px;font-weight:700;'>{idx+1}. {a['kamp']} &nbsp;|&nbsp; Odds: <span style='color:#34D399;'>{a['odds']:.2f}</span> ({a['pct']}%)</div>"
            f"<div style='font-size:13px;color:#9CA3AF;margin:4px 0;'>Spil: <b>{a['spil']}</b> &nbsp;|&nbsp; {'⭐'*a['stjerner']} &nbsp;|&nbsp; {'🔥'*a['risiko']}</div>"
            f"<div style='font-size:13px;color:#E5E7EB;margin-top:6px;'>{a['begrundelse']}</div>"
            f"{meta_html}"
            f"</div>",
            unsafe_allow_html=True,
        )
        v_spil, v_odds, v_pct = a["spil"], a["odds"], a["pct"]
        if a["alternativer"]:
            with st.expander(f"💡 Robotten har {len(a['alternativer'])} forslag til at styrke kamp {idx+1}"):
                valg_liste = [f"Behold dit valg: {a['spil']} @ {a['odds']:.2f} ({a['pct']}%)"] + [
                    f"{alt['label']} @ {alt['odds']:.2f} ({alt['pct']}%)" for alt in a["alternativer"]
                ]
                valg = st.radio("Vælg linje:", valg_liste, key=f"alt_{idx}")
                if not valg.startswith("Behold"):
                    i_alt = valg_liste.index(valg) - 1
                    v_spil = a["alternativer"][i_alt]["label"]
                    v_odds = a["alternativer"][i_alt]["odds"]
                    v_pct = a["alternativer"][i_alt]["pct"]
        aktive_valg.append({"kamp": a["kamp"], "spil": v_spil, "odds": v_odds, "pct": v_pct})

    gl_a = bh.samlet_kupon_analyse(oprindelige, indsats)
    ny_a = bh.samlet_kupon_analyse(aktive_valg, indsats)
    er_aendret = any(o["spil"] != n["spil"] for o, n in zip(oprindelige, aktive_valg))
    titel = "🔄 Ny Kuponanalyse (efter dine justeringer)" if er_aendret else "🎯 Kuponanalyse af dit scannede spil"
    sml_html = f"<div style='font-size:12px;color:#FBBF24;margin-top:8px;'>Sammenligning: Oprindeligt odds {gl_a['odds']:.2f} ({gl_a['pct']}%) → Nyt odds {ny_a['odds']:.2f} ({ny_a['pct']}%)</div>" if er_aendret else ""

    st.markdown(
        f"<div style='background:#0F172A;color:#F8FAFC;padding:16px;border-radius:10px;border:1px solid #334155;margin-top:10px;'>"
        f"<div style='font-size:16px;font-weight:700;color:#34D399;'>{titel}</div>"
        f"<div style='font-size:14px;color:#CBD5E1;margin-top:4px;'>Totalodds: <b>{ny_a['odds']:.2f}</b> &nbsp;|&nbsp; Træfsikkerhed: <b>{ny_a['pct']}%</b> &nbsp;|&nbsp; Mulig gevinst: <b>{ny_a['gevinst']:.2f} kr.</b></div>"
        f"<div style='font-size:13px;color:#E2E8F0;margin-top:8px;'>{ny_a['dom']}</div>"
        f"{sml_html}"
        f"</div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    if c1.button("🚀 SPILLET — Gem kupon", type="primary", use_container_width=True):
        _gem_til_supabase(aktive_valg, ny_a["odds"], indsats)
        st.success(f"Gemt i Supabase ({indsats:.2f} kr. @ {ny_a['odds']:.2f})!")
    if c2.button("🗑️ Ryd kupon", use_container_width=True):
        st.session_state.pop("kupon_kampe", None)
        st.session_state.pop("sidste_fil_navn", None)
        st.rerun()
