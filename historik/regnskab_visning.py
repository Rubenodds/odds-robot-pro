import csv, io
import streamlit as st
from historik import gem_data as gd

def _status_og_aar(kupon):
    strat = str(kupon.get("strategi") or "")
    status = "VUNDET" if "[VUNDET]" in strat else ("TABT" if "[TABT]" in strat else "AFVENTER")
    ts = str(kupon.get("timestamp") or "")
    aar = ts[:4] if len(ts) >= 4 and ts[:4].isdigit() else "Ukendt"
    return status, aar

def _beregn_tal(liste):
    oms, udb, vundne, afgjorte = 0.0, 0.0, 0, 0
    for s in liste:
        ind = float(s.get("indsats") or 100.0)
        odds = float(s.get("odds") or 1.0)
        st_navn, _ = _status_og_aar(s)
        oms += ind
        if st_navn == "VUNDET":
            udb += ind * odds
            vundne += 1
            afgjorte += 1
        elif st_navn == "TABT":
            afgjorte += 1
    netto = round(udb - oms, 2)
    hitrate = round((vundne / afgjorte) * 100.0, 1) if afgjorte else 0.0
    roi = round((udb / oms) * 100.0, 1) if oms > 0 else 0.0
    return round(oms, 2), round(udb, 2), netto, hitrate, roi, vundne, afgjorte

def vis_regnskab():
    st.subheader("📊 Permanent Regnskab, Årsoversigt & Kuponstyring")
    alle = gd.hent_alle_kuponer()
    oms, udb, total_sum, hitrate, roi, vundne, afgjorte = _beregn_tal(alle)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 PERMANENT TOTAL SUM", f"{total_sum:+.2f} kr.")
    c2.metric("🎯 Hitrate", f"{hitrate}% ({vundne}/{afgjorte})")
    c3.metric("📈 Tilbagebetaling", f"{roi}%")
    c4.metric("💵 Samlet Indsats", f"{oms:.2f} kr.")

    if alle:
        st.markdown("#### 📅 Årsregnskab (År for År)")
        aar_grupper = {}
        for s in alle:
            _, aar = _status_og_aar(s)
            aar_grupper.setdefault(aar, []).append(s)
        for aar in sorted(aar_grupper.keys(), reverse=True):
            a_oms, a_udb, a_net, a_hit, a_roi, _, _ = _beregn_tal(aar_grupper[aar])
            st.info(f"**År {aar}** | Kuponer: {len(aar_grupper[aar])} | Indsats: {a_oms:.2f} kr. | Udbetalt: {a_udb:.2f} kr. | Resultat: **{a_net:+.2f} kr.** | Hitrate: {a_hit}% | ROI: {a_roi}%")

        st.markdown("#### 🎫 Afgør & Administrer Kuponer")
        for s in alle:
            kid = s.get("id")
            st_navn, aar = _status_og_aar(s)
            ind = float(s.get("indsats") or 100.0)
            odds = float(s.get("odds") or 1.0)
            farve = "🟢" if st_navn == "VUNDET" else ("🔴" if st_navn == "TABT" else "🟡")
            st.markdown(f"{farve} **#{kid}** ({aar}) — {s.get('kampe')} | Odds: `{odds:.2f}` | Indsats: `{ind:.0f} kr.` | Status: **{st_navn}**")
            b1, b2, b3 = st.columns(3)
            if b1.button("✅ Vundet", key=f"v_{kid}", use_container_width=True):
                gd.opdater_kupon_status(kid, "VUNDET")
                st.rerun()
            if b2.button("❌ Tabt", key=f"t_{kid}", use_container_width=True):
                gd.opdater_kupon_status(kid, "TABT")
                st.rerun()
            if b3.button("⏳ Afventer", key=f"a_{kid}", use_container_width=True):
                gd.opdater_kupon_status(kid, "AFVENTER")
                st.rerun()
    else:
        st.info("0-stillet start (0,00 kr.). Dine kuponer vises her, så snart du trykker 🚀 SPILLET i Mappe 1, 2 eller 3.")

    with st.expander("📥 Importer historiske spil fra tidligere sæsoner (CSV)"):
        fil = st.file_uploader("Upload CSV (kolonner: kampe, odds, indsats, status)", type=["csv"])
        if fil and st.button("Importer CSV til Supabase"):
            rdr = csv.DictReader(io.StringIO(fil.read().decode("utf-8", errors="ignore")))
            antal = 0
            for r in rdr:
                ok = gd.gem_kupon_i_historik(
                    [r.get("status", "AFVENTER")], [r.get("kampe", "Historisk spil")],
                    r.get("odds", 2.0), 0, 0, "CSV Import", 3,
                    indsats=r.get("indsats", 100.0), kilde="Robot"
                )
                if ok:
                    antal += 1
            st.success(f"Importerede {antal} historiske spil til Supabase!")
            st.rerun()
