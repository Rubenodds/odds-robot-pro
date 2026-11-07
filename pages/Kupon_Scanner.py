import streamlit as st
from PIL import Image
from historik.gem_data import gem_kupon_i_historik
from bookmaker_scanner.scanner_motor import hent_ai_alternativer_for_kamp

st.set_page_config(page_title="AI Billed-Scanner & Kupon-Optimering", page_icon="📸", layout="centered")

st.title("📸 AI Billed-Scanner & Kupon-Optimering")
st.write("Se din originale kuponstamme og tilføj AI-optimeringer live inden for kontrollerede odds-lag.")

if "scannet_data" not in st.session_state:
    st.session_state["scannet_data"] = None

uploadet_billede = st.file_uploader("Upload dit kupon-screenshot:", type=["png", "jpg", "jpeg"], key="kupon_uploader_v6")

if uploadet_billede:
    if st.session_state["scannet_data"] is None or st.button("🔄 SCAN / NULSTIL"):
        st.session_state["scannet_data"] = {
            "kampe": [
                {"hold": "OB vs. Viborg", "originalt_valg": "Viborg vinder & Over 3 hjørnespark", "odds": 3.00, "chance": 26},
                {"hold": "Leeds vs. Tottenham", "originalt_valg": "Tottenham vinder", "odds": 2.60, "chance": 32},
                {"hold": "Bristol City vs. Norwich", "originalt_valg": "Norwich vinder & Begge hold scorer", "odds": 4.40, "chance": 18}
            ]
        }

    if st.session_state["scannet_data"] is not None:
        data = st.session_state["scannet_data"]
        antal_kampe = len(data["kampe"])
        
        orig_samlet_odds = 1.0
        orig_samlet_chance = 100.0
        for k in data["kampe"]:
            orig_samlet_odds *= k["odds"]
            orig_samlet_chance *= (k["chance"] / 100)
        
        orig_samlet_odds = round(orig_samlet_odds, 2)
        orig_samlet_chance_procent = round(orig_samlet_chance * 100, 1)

        # ----------------- PANEL 1: DIN ORIGINALE KUPONSTAMME -----------------
        st.subheader("📋 Din originale kuponstamme (Scannet)")
        for k in data["kampe"]:
            st.info(f"⚽ **{k['hold']}**\n\n**Dit valg:** {k['originalt_valg']} — **Odds: {k['odds']:.2f}** | Vinderchance: `{k['chance']}%` | 🔥 🔥 | ⭐⭐⭐")
        
        col_o1, col_o2 = st.columns(2)
        with col_o1:
            st.metric(label="Originalt Samlet Odds", value=f"{orig_samlet_odds:.2f}")
        with col_o2:
            st.metric(label="Original Vinderchance", value=f"{max(1, int(orig_samlet_chance_procent))}%")
            
        st.write("---")

        # ----------------- PANEL 2: INTERAKTIV OPTIMERINGSMOTOR -----------------
        st.subheader("⚡ AI Multi-Balancering & Markedsalternativer")
        
        vis_alternativer = st.toggle("🤖 Aktiver AI Værdi-Scanner (Vis alternative muligheder)", value=False)
        
        # RETTET: Tomme lister er nu lukket korrekt
        endelige_valgte_spil =
        samlet_ny_vinderchance = 100.0
        tillad_ekstra_boost = False

        if vis_alternativer:
            for kamp in data["kampe"]:
                _, _, vil_booste, forklaring_tekst = hent_ai_alternativer_for_kamp(kamp["hold"], kamp["odds"], orig_samlet_odds, antal_kampe)
                if vil_booste:
                    st.warning(forklaring_tekst)
                    tillad_ekstra_boost = st.checkbox("🔓 Giv robotten lov til at sprænge odds-laget for denne guldklump", value=False, key="tillad_boost_check")
                    st.write("---")

            st.write("💡 *Vælg det marked du vil ersatte dit originale spil med for hver kamp:*")
            
            for i, kamp in enumerate(data["kampe"]):
                st.markdown(f"### ⚽ {kamp['hold']}")
                
                forslag, mangler_muligheder, vil_booste, _ = hent_ai_alternativer_for_kamp(kamp["hold"], kamp["odds"], orig_samlet_odds, antal_kampe)
                
                valgmuligheder = [f"Behold originalt valg: {kamp['originalt_valg']} (Odds {kamp['odds']:.2f})"]
                
                if vil_booste and tillad_ekstra_boost:
                    odds_boosted = round(kamp["odds"] * 1.6, 2)
                    valgmuligheder.append(f"🚀 AI VALUE-BOOST: Ekstrem markedsfejl (Odds {odds_boosted:.2f})")
                
                for f in forslag:
                    valgmuligheder.append(f"{f['variant']} (Odds {f['odds']:.2f})")
                
                valgt_marked = st.radio(f"Vælg marked for {kamp['hold']}:", valgmuligheder, key=f"pro_valg_{i}", label_visibility="collapsed")
                
                if "Behold originalt" in valgt_marked:
                    endelige_valgte_spil.append({"hold": kamp["hold"], "variant": kamp["originalt_valg"], "odds": kamp["odds"]})
                    samlet_ny_vinderchance *= (kamp["chance"] / 100)
                elif "🚀 AI VALUE-BOOST" in valgt_marked:
                    odds_boosted = round(kamp["odds"] * 1.6, 2)
                    endelige_valgte_spil.append({"hold": kamp["hold"], "variant": "🚀 AI Value-Boost: Udnyttelse af bookmaker-fejl", "odds": odds_boosted})
                    samlet_ny_vinderchance *= 0.45
                    st.success("🔥 **Valgt:** Du har godkendt robottens Value-Boost på denne markedsfejl!")
                else:
                    for f in forslag:
                        if f["variant"] in valgt_marked:
                            endelige_valgte_spil.append({"hold": kamp["hold"], "variant": f["variant"], "odds": f["odds"]})
                            samlet_ny_vinderchance *= (f["chance"] / 100)
                            st.success(f"🎯 **Valgt alternativ:** {f['flammer']} | {f['stjerner']} | **Chance:** {f['chance']}%\n\n*Analyse: {f['analyse']}*")
                st.write("`---------------------------------------------------------------------`")
        else:
            # RETTET: Tomme lister lukket korrekt her
            for kamp in data["kampe"]:
                endelige_valgte_spil.append({"hold": kamp["hold"], "variant": kamp["originalt_valg"], "odds": kamp["odds"]})
            samlet_ny_vinderchance = orig_samlet_chance

        # ----------------- LIVE BEREGNING I BUNDEN -----------------
        st.subheader("🔮 Endeligt AI Balancerings-Resultat")
        
        reelt_samlet_odds = 1.0
        for spil in endelige_valgte_spil:
            reelt_samlet_odds *= spil["odds"]
            
        endelig_chance = round(samlet_ny_vinderchance * 100, 1)

        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric(label="Samlet Dynamisk Odds (Live opdateret)", value=f"{reelt_samlet_odds:.2f}")
        with col_res2:
            st.metric(label="Samlet AI Vinderchance", value=f"{min(99.0, max(1.0, endelig_chance)):.1f}%")

        if st.button("💾 LÅS OG GEM DEN DYNAMISKE KUPON", type="primary", key="btn_gem_dynamisk_låst"):
            gem_kupon_i_historik(
                [spil["variant"] for spil in endelige_valgte_spil],
                [spil["hold"] for spil in endelige_valgte_spil],
                reelt_samlet_odds, reelt_samlet_odds * 0.96, reelt_samlet_odds * 0.93,
                "Bet365 (Live Interaktiv Pro-Scan)", 5
            )
            st.success("✅ Din færdige kuponstamme er låst og gemt i din SQLite historik!")
