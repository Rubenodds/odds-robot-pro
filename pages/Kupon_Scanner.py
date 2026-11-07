import streamlit as st
from PIL import Image
from historik.gem_data import gem_kupon_i_historik
from bookmaker_scanner.scanner_motor import hent_ai_alternativer_for_kamp

st.set_page_config(page_title="AI Billed-Scanner & Kupon-Optimering", page_icon="📸", layout="centered")

st.title("📸 AI Billed-Scanner & Kupon-Optimering")
st.write("Sæt flueben ved de AI-alternativer, du vil erstatte dine oprindelige valg med.")

if "scannet_data" not in st.session_state:
    st.session_state["scannet_data"] = None

uploadet_billede = st.file_uploader("Upload dit kupon-screenshot:", type=["png", "jpg", "jpeg"], key="kupon_uploader_v3")

if uploadet_billede:
    if st.session_state["scannet_data"] is None or st.button("🔄 SCAN / NULSTIL"):
        st.session_state["scannet_data"] = {
            "kampe": [
                {"hold": "OB vs. Viborg", "originalt_valg": "Viborg vinder & Over 3 hjørnespark", "odds": 3.00},
                {"hold": "Leeds vs. Tottenham", "originalt_valg": "Tottenham vinder", "odds": 2.60},
                {"hold": "Bristol City vs. Norwich", "originalt_valg": "Norwich vinder & Begge hold scorer", "odds": 4.40}
            ]
        }

    if st.session_state["scannet_data"] is not None:
        data = st.session_state["scannet_data"]
        
        endelige_valgte_spil = 
        samlet_ny_vinderchance = 100.0
        
        st.subheader("🎟️ Interaktiv Kupon-Håndtering")
        st.write("Klik på de alternativer, du vil have med på kuponen i stedet for dit originale spil:")

        for i, kamp in enumerate(data["kampe"]):
            st.markdown(f"### ⚽ {kamp['hold']}")
            
            # Vis det originale valg som en fast information i toppen af kampen
            st.info(f"**Dit originale valg:** {kamp['originalt_valg']} — **Odds: {kamp['odds']:.2f}**")
            
            # Hent AI forslagene
            forslag = hent_ai_alternativer_for_kamp(kamp["hold"], kamp["odds"])
            
            kamp_ændret = False
            
            # Loop igennem forslagene og lav dem som flueben
            for j, f in enumerate(forslag):
                flueben = st.checkbox(
                    f"Erstat med {f['variant']} (Odds {f['odds']:.2f})", 
                    key=f"flueben_{i}_{j}"
                )
                
                if flueben:
                    # Hvis brugeren sætter flueben, tilføjer vi AI-spillet i stedet
                    endelige_valgte_spil.append({"hold": kamp["hold"], "variant": f['variant'], "odds": f['odds']})
                    samlet_ny_vinderchance *= (f["chance"] / 100)
                    kamp_ændret = True
                    
                    # Vis den flotte grønne boks med analysen for det valgte flueben
                    st.success(f"🎯 **Valgt:** {f['flammer']} | {f['stjerner']} | **Chance:** {f['chance']}%\n\n*Analyse: {f['analyse']}*")
            
            # Hvis der IKKE er sat nogen flueben ved denne kamp, beholder vi automatisk dit originale valg!
            if not kamp_ændret:
                endelige_valgte_spil.append({"hold": kamp["hold"], "variant": kamp["originalt_valg"], "odds": kamp["odds"]})
                samlet_ny_vinderchance *= (max(5, int(80 / kamp["odds"])) / 100)

            st.write("---")

        # ----------------- LIVE BEREGNING I BUNDEN -----------------
        st.subheader("🔮 Dynamisk AI-Resultat")
        
        # Regner det samlede produkt ud live baseret på dine flueben
        reelt_samlet_odds = 1.0
        for spil in endelige_valgte_spil:
            reelt_samlet_odds *= spil["odds"]
            
        endelig_chance = round(samlet_ny_vinderchance * 100, 1)

        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric(label="Samlet Dynamisk Odds (Live opdateret)", value=f"{reelt_samlet_odds:.2f}")
        with col_res2:
            st.metric(label="Samlet AI Vinderchance", value=f"{max(1, int(endelig_chance))}%")

        if st.button("💾 LÅS OG GEM DEN DYNAMISKE KUPON", type="primary", key="btn_gem_dynamisk_låst"):
            gem_kupon_i_historik(
                [spil["variant"] for spil in endelige_valgte_spil],
                [spil["hold"] for spil in endelige_valgte_spil],
                reelt_samlet_odds, reelt_samlet_odds * 0.96, reelt_samlet_odds * 0.93,
                "Bet365 (Live Fluebens-Scan)", 5
            )
            st.success("✅ Din skræddersyede kuponstamme er låst og gemt i din SQLite historik!")
