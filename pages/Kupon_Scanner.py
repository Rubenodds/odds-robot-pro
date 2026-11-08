import streamlit as st
from PIL import Image
import datetime
from historik.gem_data import gem_kupon_i_historik
from bookmaker_scanner.scanner_motor import hent_ai_alternativer_for_kamp, scan_billede_til_kupon_data

st.set_page_config(page_title="AI Universel Billed-Scanner & Optimering", page_icon="📸", layout="centered")

st.title("📸 AI Universel Billed-Scanner & Optimering")
st.write("Robotten afkoder automatisk dit screenshot og integrerer det live med dine statistikker.")

if "scannet_data" not in st.session_state:
    st.session_state["scannet_data"] = None

uploadet_billede = st.file_uploader("Upload dit kupon-screenshot:", type=["png", "jpg", "jpeg"], key="kupon_uploader_v10")

if uploadet_billede:
    if st.session_state["scannet_data"] is None or st.button("🔄 GEN-SCAN SCREENSHOT"):
        # Sender både billedet og filnavnet ind for at sikre præcis OCR-parring
        st.session_state["scannet_data"] = scan_billede_til_kupon_data(Image.open(uploadet_billede), uploadet_billede.name)

if st.session_state["scannet_data"] is not None:
    data = st.session_state["scannet_data"]
    
    if not data.get("kampe"):
        st.warning("⚠️ Kunne ikke afkode tekst automatisk fra dette screenshot. Sørg for at billedet er skarpt.")
    else:
        antal_kampe = len(data["kampe"])
        
        # Bruger enten det scannede samlede odds eller regner det ud automatisk
        orig_samlet_odds = data.get("samlet_odds_override", 1.0)
        if orig_samlet_odds == 1.0:
            for k in data["kampe"]: orig_samlet_odds *= k["odds"]
            
        orig_samlet_odds = round(orig_samlet_odds, 2)

        st.subheader("📋 Din originale kuponstamme (Registreret dynamisk)")
        for k in data["kampe"]:
            st.info(f"⚽ **{k['hold']}**\n\n**Dit valg:** {k['originalt_valg']} — **Odds: {k['odds']:.2f}**")
        
        st.write("---")
        st.subheader("⚡ AI Multi-Balancering & Markedsalternativer")
        
        vis_alternativer = st.toggle("🤖 Aktiver AI Værdi-Scanner (Vis alternative muligheder)", value=False)
        
        endelige_valgte_spil = []
        samlet_ny_vinderchance = 1.0

        if vis_alternativer:
            st.write("💡 *Vælg marked eller tast dit eget spil ind for hver kamp:*")
            for i, kamp in enumerate(data["kampe"]):
                st.markdown(f"### ⚽ {kamp['hold']}")
                forslag, _, _, _ = hent_ai_alternativer_for_kamp(kamp["hold"], kamp["odds"], orig_samlet_odds, antal_kampe)
                
                valgmuligheder = [
                    f"Behold originalt valg: {kamp['originalt_valg']} (Odds {kamp['odds']:.2f})",
                    "⌨️ Tast selv mit eget valg..."
                ]
                for f in forslag: valgmuligheder.append(f"{f['titel']} (Odds {f['odds']:.2f})")
                
                valgt_marked = st.radio(f"Marked {i}:", valgmuligheder, key=f"pro_valg_{i}", label_visibility="collapsed")
                
                if "⌨️ Tast selv" in valgt_marked:
                    col_t1, col_t2 = st.columns(2)
                    with col_t1: manuelt_spil = st.text_input("Spil:", value="Over 2.5 mål", key=f"man_navn_{i}")
                    with col_t2: manuelt_odds = st.number_input("Odds:", min_value=1.01, value=2.00, key=f"man_odds_{i}")
                    endelige_valgte_spil.append({"hold": kamp["hold"], "variant": f"⌨️ {manuelt_spil}", "odds": manuelt_odds, "flammer": "🔥 🔥 🔥", "stjerner": 4})
                else:
                    valgt_f = next((f for f in forslag if f["titel"] in valgt_marked), None)
                    if valgt_f:
                        endelige_valgte_spil.append({"hold": kamp["hold"], "variant": valgt_f["variant"], "odds": valgt_f["odds"], "flammer": valgt_f["flammer"], "stjerner": valgt_f["stjerner"]})
                    else:
                        endelige_valgte_spil.append({"hold": kamp["hold"], "variant": kamp["originalt_valg"], "odds": kamp["odds"], "flammer": "🔥 🔥", "stjerner": 3})
        else:
            for kamp in data["kampe"]:
                endelige_valgte_spil.append({"hold": kamp["hold"], "variant": kamp["originalt_valg"], "odds": kamp["odds"], "flammer": "🔥 🔥", "stjerner": 3})

        st.write("---")
        st.subheader("🎯 Den optimerede kuponstamme")
        
        ny_samlet_odds = 1.0
        maksimale_stjerner = 1
        
        for spil in endelige_valgte_spil:
            if not vis_alternativer and data.get("samlet_odds_override"):
                ny_samlet_odds = data["samlet_odds_override"]
            else:
                ny_samlet_odds *= spil["odds"]
            stjerne_antal = len(spil["stjerner"]) if isinstance(spil["stjerner"], str) else int(spil["stjerner"])
            if stjerne_antal > maksimale_stjerner: maksimale_stjerner = stjerne_antal
            
            with st.expander(f"⚽ {spil['hold']} — Odds {spil['odds']:.2f}", expanded=True):
                st.write(f"**Valgt væddemål:** {spil['variant']}")
        
        ny_samlet_odds = round(ny_samlet_odds, 2)
        
        st.write("---")
        col_res1, col_res2 = st.columns(2)
        with col_res1: st.metric("Samlet Odds", f"{ny_samlet_odds:.2f}")
        with col_res2: st.metric("Registreret Platform", "Universel Scanner")

        # 📊 RIGTIG STATISTIK KNAP: Gemmer kuponen direkte i SQLite og låser dens hitrate
        if st.button("💾 TILFØJ KUPON TIL SPIL-STATISTIK", use_container_width=True):
            ligaer_liste = [s["hold"] for s in endelige_valgte_spil]
            forslag_liste = [f"[{s['hold']}]: {s['variant']}" for s in endelige_valgte_spil]
            
            succes = gem_kupon_i_historik(
                ligaer_liste=ligaer_liste,
                forslag_liste=forslag_liste,
                bookmakere_dict={"🤖 AI-Scanner": f"{ny_samlet_odds:.2f}"},
                side="📸 Billed-Scanner",
                stjerner=maksimale_stjerner
            )
            
            if succes:
                st.success(f"✅ Kuponen (Odds {ny_samlet_odds:.2f}) er tilføjet til din langsigtede succesrate og sat til 'Afventer'!")
                st.balloons()
            else:
                st.error("❌ Kunne ikke forbinde til SQLite-databasen.")
