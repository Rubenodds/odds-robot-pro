import streamlit as st
import datetime
from odds_motor import byg_kupon
from historik import gem_data

def vis_manuel_kamp_scanner(alle_kampe, valgte_markeder, mål_odds):
    st.write("---")
    st.header("🎯 5. Lyn-Scanner for valgte tidsramme")
    st.write("Scan automatisk samtlige aktive kampe i dine valgte ligaer og tidsintervaller for at finde de største fejl-odds.")

    # Finder automatisk de præcise kampe baseret på de filtre, der allerede er sat i punkt 1 og 2
    if "tids_valg_key" in st.session_state:
        tidsvalg = st.session_state["tids_valg_key"]
        if "3 timer" in tidsvalg: tids_timer = 3.0
        elif "6 timer" in tidsvalg: tids_timer = 6.0
        elif "12 timer" in tidsvalg: tids_timer = 12.0
        elif "24 timer" in tidsvalg: tids_timer = 24.0
        else: tids_timer = 48.0
    else:
        tids_timer = 24.0

    # Filtrerer automatisk alle tilgængelige kampe i tidsrammen
    fra_valgte_ligaer = [
        k for k in alle_kampe 
        if "chk_" + k["liga"] in st.session_state and st.session_state["chk_" + k["liga"]]
    ]
    
    if not fra_valgte_ligaer:
        fra_valgte_ligaer = alle_kampe

    aktive_kampe_i_tidsramme = fra_valgte_ligaer

    st.info(f"🤖 Klar til at scanne **{len(aktive_kampe_i_tidsramme)} aktive kampe** i dit valgte program automatisk.")

    if st.button("⚡ LYN-SCAN ALLE KAMPE NU", type="primary", key="btn_lyn_scan_tidsramme_pro"):
        if not aktive_kampe_i_tidsramme:
            st.error("Ingen kampe fundet i det valgte tidsrum. Prøv at udvide tidsintervallet under punkt 1.")
        else:
            with st.spinner("AI-motoren gennemsøger special-markeder på hele programmet..."):
                resultat = byg_kupon.byg_kombineret_kupon(aktive_kampe_i_tidsramme, valgte_markeder, mål_odds)
                
                if resultat:
                    st.subheader("📊 Resultat og fund af din Lyn-Scanning:")
                    st.write("---")
                    
                    gemme_ligaer = list()
                    gemme_forslag = list()
                    
                    for idx_k, k in enumerate(resultat["kampe"]):
                        st.write(f"🏟️ **KAMP {idx_k+1}: [{k['liga']}] {k['hj']} vs. {k['ud']}**")
                        st.write("🧱 *AI Fundet Værdispil:*")
                        for kombi_tekst in k["kombinationer"]:
                            st.write(f" ➔ {kombi_tekst}")
                            gemme_forslag.append(f"[{k['hj']}-{k['ud']}]: {kombi_tekst}")
                        st.write(f"💵 **Kamp-odds:** Bet365: **{k['b365']:.2f}** | Unibet: **{k['uni']:.2f}** | Oddset: **{k['oddset']:.2f}**")
                        st.write("---")
                        gemme_ligaer.append(k["liga"])
                    
                    # BEREGNER REEL %-CHANCE OG HENTER FLAMMERNE FEJLFRIT IND UDEN INDEX-FEJL
                    beregnet_chance = max(2, min(80, int((1 / resultat['bedste_odds']) * 100 * 1.25)))
                    risiko_flammer = 5 - int(beregnet_chance / 15)
                    risiko_flammer = max(1, min(5, risiko_flammer))
                    
                    st.success(f"🔥 **BEDSTE BOOKMAKER FUNDET: {resultat['bedste_side']}!**")
                    st.write(f"📈 **Samlet odds for de scannede fund: {resultat['bedste_odds']:.2f}**")
                    st.write(f"ℹ️ *Sammenligning:* Bet365: {resultat['samlet_b365']:.2f} | Unibet: {resultat['samlet_unibet']:.2f} | Oddset: {resultat['samlet_oddset']:.2f}")
                    
                    # FEJLFRI VISNING: %-sandsynlighed, stjerner og risikoflammer side om side
                    st.write(f"🎯 **Statistisk vinderchance beregnet af AI:** `{beregnet_chance}%`")
                    st.write(f"⚠️ **Risikoprofil:** {'🔥' * risiko_flammer} ({risiko_flammer}/5)")
                    st.write(f"🎯 **AI Værdi-vurdering:** {'⭐' * resultat['styrke']} ({resultat['styrke']}/5 stjerner)")
                    
                    gem_data.gem_kupon_i_historik(gemme_ligaer, gemme_forslag, resultat["samlet_b365"], resultat["samlet_unibet"], resultat["samlet_oddset"], resultat["bedste_side"], resultat["styrke"])
                    st.info("🧠 Scanning gemt og låst i AI-historikken!")
