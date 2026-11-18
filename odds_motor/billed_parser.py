import re
import streamlit as st
from PIL import Image
from odds_motor import billed_ocr as ocr, billed_hjaelp as bh
from historik import gem_data


def _normaliser_tekst(txt: str) -> str:
    return "".join(ch.lower() for ch in str(txt) if ch.isalnum())


def _er_gyldig_kamp(k: dict) -> bool:
    kamp = str(k.get("kamp", "")).strip()
    if not kamp or " - " not in kamp:
        return False
    hjemme, ude = [x.strip() for x in kamp.split(" - ", 1)]
    if len(hjemme) < 3 or len(ude) < 3:
        return False
    for del_navn in (hjemme, ude):
        lav = del_navn.lower()
        if any(s in lav for s in ("tillaegstid", "tillægstid", "ila2", "halvleg", "vaeddemal", "væddemål", "casino", "live")):
            return False
        if re.search(r"[(){}\[\]?!@#$%^&*=<>]", del_navn):
            return False
        bogstaver = sum(1 for c in del_navn if c.isalpha())
        if bogstaver < 3 or (bogstaver / max(1, len(del_navn))) < 0.65:
            return False
    return True


def _er_dublet(k: dict, sete_kampe: list) -> bool:
    kamp_norm = _normaliser_tekst(k.get("kamp", ""))
    odds_val = round(float(k.get("odds", 0.0)), 2)
    hjemme = _normaliser_tekst(k.get("hjemme", ""))
    ude = _normaliser_tekst(k.get("ude", ""))

    for s in sete_kampe:
        if kamp_norm and kamp_norm == s["kamp"]:
            return True
        if odds_val > 1.0 and abs(odds_val - s["odds"]) < 0.02:
            if (hjemme and len(hjemme) >= 4 and (hjemme in s["kamp"] or s["hjemme"] in hjemme)) or (
                ude and len(ude) >= 4 and (ude in s["kamp"] or s["ude"] in ude)
            ):
                return True
    return False


def _godt_og_skidt(a):
    o, p = float(a.get("odds", 1.85)), float(a.get("pct", 50.0))
    godt = (
        f"Stærk værdi på {a['spil']} ({p}% træfsikkerhed)"
        if p >= 52
        else f"Høj udbetalingsfaktor (@ {o:.2f}) ved fuld træffer"
    )
    skidt = (
        f"Høj varians og lav hitrate ({p}%) gør kampen til kuponens risikopunkt"
        if o >= 2.25
        else f"Lavere enkeltodds (@ {o:.2f}) kræver fuld disciplin uden uventede røde kort"
    )
    return godt, skidt


def vis_billed_scanner():
    st.markdown("### 🧾 Kupon & Billed Scanner (1 eller flere skærmbilleder)")
    st.caption(
        "Har du en lang kupon? Vælg 2-3 skærmbilleder på én gang — robotten fletter dem sammen og fjerner automatisk overlap."
    )

    filer = st.file_uploader(
        "Upload 1 eller flere screenshots af kupon",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="billed_uploader",
    )

    if filer:
        sorterede_filer = sorted(filer, key=lambda f: f.name)
        fil_sig = "|".join(f"{f.name}_{f.size}" for f in sorterede_filer)
        cols = st.columns(min(len(sorterede_filer), 3))
        for idx, fil in enumerate(sorterede_filer):
            with cols[idx % 3]:
                st.image(
                    Image.open(fil),
                    caption=f"Billede {idx + 1}: {fil.name}",
                    use_container_width=True,
                )

        if st.session_state.get("sidste_fil_id") != fil_sig:
            alle_kampe, sete_kampe, dubletter = [], [], 0
            sidste_indsats = 100.0
            with st.spinner("🔍 Aflæser skærmbilleder og fletter kuponen sammen..."):
                for fil in sorterede_filer:
                    fil.seek(0)
                    kampe_del, indsats_del, _ = ocr.udtraek_kupon_fra_billede(fil.read())
                    if indsats_del and indsats_del > 0:
                        sidste_indsats = float(indsats_del)
                    for k in kampe_del:
                        if not _er_gyldig_kamp(k):
                            continue
                        if _er_dublet(k, sete_kampe):
                            dubletter += 1
                            continue
                        sete_kampe.append(
                            {
                                "kamp": _normaliser_tekst(k.get("kamp", "")),
                                "hjemme": _normaliser_tekst(k.get("hjemme", "")),
                                "ude": _normaliser_tekst(k.get("ude", "")),
                                "odds": round(float(k.get("odds", 0.0)), 2),
                            }
                        )
                        alle_kampe.append(k)

            st.session_state.update(
                {
                    "kupon_kampe": alle_kampe,
                    "kupon_indsats": sidste_indsats,
                    "sidste_fil_id": fil_sig,
                    "scan_info": (
                        f"✅ {len(alle_kampe)} kampe indlæst fra {len(sorterede_filer)} billeder"
                        + (f" ({dubletter} dublet{'ter' if dubletter > 1 else ''} fjernet)" if dubletter else "")
                    ),
                }
            )
            st.session_state.pop("billed_gemt_ok", None)

    if info_msg := st.session_state.get("scan_info"):
        st.info(info_msg)

    kampe = st.session_state.get("kupon_kampe", [])
    indsats = st.number_input(
        "Indsats (kr. — std. 100 kr.)",
        min_value=1.0,
        value=float(st.session_state.get("kupon_indsats", 100.0)),
        step=10.0,
        key="billed_kr",
    )

    if not kampe:
        st.info("Upload ét eller flere kuponbilleder for at se robottens scanning og kuponanalyse.")
        return

    oprindelige, aktive_valg = [], []
    for idx, k in enumerate(kampe):
        a = bh.analyser_kupon_kamp(k)
        oprindelige.append({"kamp": a["kamp"], "spil": a["spil"], "odds": a["odds"], "pct": a["pct"]})
        godt, skidt = _godt_og_skidt(a)
        meta_html = (
            f"<div style='font-size:12px;color:#60A5FA;margin-top:4px;'>{a['meta']}</div>"
            if a.get("meta")
            else ""
        )
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
                    hvorfor = alt.get("hvorfor") or (
                        f"Øger sandsynligheden til {alt['pct']}% og balancerer kuponens samlede risiko bedre end {a['spil']}."
                    )
                    st.caption(f"💡 **Hvorfor?** {hvorfor}")
                if valgte_alt:
                    v_spil = " + ".join(x["label"].split(": ")[-1] for x in valgte_alt)
                    rabat = 0.90 if len(valgte_alt) > 1 else 1.0
                    komb_o, komb_p = 1.0, 1.0
                    for x in valgte_alt:
                        komb_o *= x["odds"]
                        komb_p *= x["pct"] / 100.0
                    v_odds = round(komb_o * rabat, 2)
                    v_pct = round(min(85.0, komb_p * 100.0 * (1.08 if len(valgte_alt) > 1 else 1.0)), 1)
                    st.caption(f"✅ Aktivt valg på kamp {idx+1}: {v_spil} @ {v_odds:.2f} ({v_pct}%)")
        aktive_valg.append({"kamp": a["kamp"], "spil": v_spil, "odds": v_odds, "pct": v_pct})

    gl_a = bh.samlet_kupon_analyse(oprindelige, indsats)
    ny_a = bh.samlet_kupon_analyse(aktive_valg, indsats)
    er_aendret = any(o["spil"] != n["spil"] for o, n in zip(oprindelige, aktive_valg))
    titel = "🔄 Ny Kuponanalyse (efter dine justeringer)" if er_aendret else "🎯 Kuponanalyse af dit scannede spil"

    samlet_pct = float(ny_a["pct"])
    samlet_stjerner = max(1, min(5, round(samlet_pct / 16.0)))
    samlet_risiko = max(1, min(5, 6 - samlet_stjerner))

    sml_html = (
        f"<div style='font-size:12px;color:#FBBF24;margin-top:8px;'>Sammenligning: Oprindeligt odds {gl_a['odds']:.2f} ({gl_a['pct']}%) → Nyt odds {ny_a['odds']:.2f} ({ny_a['pct']}%)</div>"
        if er_aendret
        else ""
    )

    st.markdown(
        f"<div style='background:#0F172A;color:#F8FAFC;padding:16px;border-radius:10px;border:1px solid #334155;margin-top:10px;'>"
        f"<div style='font-size:16px;font-weight:700;color:#34D399;'>{titel}</div>"
        f"<div style='font-size:14px;color:#CBD5E1;margin-top:4px;'>Totalodds: <b>{ny_a['odds']:.2f}</b> &nbsp;|&nbsp; Træfsikkerhed: <b>{samlet_pct}%</b> &nbsp;|&nbsp; Mulig gevinst: <b>{ny_a['gevinst']:.2f} kr.</b></div>"
        f"<div style='font-size:13px;color:#9CA3AF;margin-top:4px;'>Samlet vurdering: {'⭐' * samlet_stjerner} &nbsp;|&nbsp; Risiko: {'🔥' * samlet_risiko}</div>"
        f"<div style='font-size:13px;color:#E2E8F0;margin-top:8px;'>{ny_a['dom']}</div>{sml_html}</div>",
        unsafe_allow_html=True,
    )

    if ok_msg := st.session_state.get("billed_gemt_ok"):
        st.success(ok_msg)
    elif st.button("🚀 SPILLET (Gem i Historik)", type="primary", key="btn_billed_spillet", use_container_width=True):
        with st.spinner("⏳ Gemmer kupon i Cloud-historik..."):
            kamp_linjer = [f"{x['kamp']} ({x['spil']}) [@ {x['odds']:.2f}]" for x in aktive_valg]
            try:
                gem_data.gem_kupon_i_historik(
                    kilde="Billed Scanner",
                    kampe=kamp_linjer,
                    odds=float(ny_a["odds"]),
                    indsats=float(indsats),
                )
            except TypeError:
                gem_data.gem_kupon_i_historik(
                    " | ".join(kamp_linjer),
                    float(ny_a["odds"]),
                    float(indsats),
                )
            except Exception as e:
                st.error(f"❌ Kunne ikke gemme i Supabase: {e}")
                st.stop()

            st.session_state["billed_gemt_ok"] = (
                f"✅ OK – Kupon ({len(kamp_linjer)} kampe @ {ny_a['odds']:.2f}) er gemt i Supabase!"
            )
            st.rerun()

    if st.button("🗑️ Ryd kupon", key="btn_billed_ryd", use_container_width=True):
        for k_navn in ("kupon_kampe", "sidste_fil_id", "billed_gemt_ok", "scan_info"):
            st.session_state.pop(k_navn, None)
        st.rerun()
