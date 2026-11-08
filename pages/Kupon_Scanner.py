import streamlit as st
from PIL import Image
from historik.gem_data import gem_kupon_i_historik
from bookmaker_scanner.scanner_motor import hent_ai_alternativer_for_kamp, scan_billede_til_kupon_data

st.set_page_config(page_title="AI Universel Billed-Scanner", page_icon="📸", layout="centered")

st.title("📸 AI Universel Billed-Scanner")
st.write("Uploade kuponer fra valgfri udbyder. Robotten analyserer layoutet og synkroniserer det med din statistik.")

# Nulstiller midlertidig cache ved ny upload for at forhindre fastfrysning
uploadet_billede = st.file_uploader("Upload dit kupon-screenshot:", type=["png", "jpg", "jpeg"], key="kupon_uploader_v11")

if uploadet_billede:
    # Genererer frisk data dynamisk baseret på det specifikke billede
    scannet_data = scan_billede_til_kupon_data(Image.open(uploadet_billede), uploadet_billede.name)
    
    antal_kampe = len(scannet_data["kampe"])
    orig_samlet_odds = scannet_data.get("samlet_odds_override", 1.0)
    
    st.subheader("📋 Registreret kuponstamme fra screenshot")
    for k in scannet_data["kampe"]:
        st.info(f"⚽ **{k['hold']}**\n\n**Dit valg:** {k['originalt_valg']} — **Odds: {k['odds']:.2f}**")
        
    st.write("---")
    st.subheader("⚡ AI Multi-Balancering & Markedsalternativer")
    vis_alternativer = st.toggle("🤖 Aktiver AI Værdi-Scanner (Vis alternative muligheder)", value=False)
    
    endelige_valgte_spil = []
    
    if vis_alternativer:
        for i, kamp in enumerate(scannet_data["kampe"]):
            st.markdown(f"### ⚽ {kamp['hold']}")
            forslag, _, _, _ = hent_ai_alternativer_for_kamp(kamp["hold"], kamp["odds"], orig_samlet_odds, antal_kampe)
            
            valgmuligheder = [
                f"Behold originalt valg: {kamp['originalt_valg']} (Odds {kamp['odds']:.2f})",
                "⌨️ Tast selv mit eget valg for denne kamp..."
            ]
            for f in forslag:
                valgmuligheder.append(f"{f['titel']} (Odds {f['odds']:.2f})")
                
            valgt_marked = st.radio(f"Marked {i}:", valgmuligheder, key=f"pro_valg_{i}", label_visibility="collapsed")
            
            if "⌨️ Tast selv" in valgt_marked:
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    manuelt_spil = st.text_input("Hvad spiller du?", value="Over 2.5 mål", key=f"man_navn_{i}")
                with col_t2:
                    manuelt_odds = st.number_input("Indtast odds:", min_value=1.01, value=2.00, key=f"man_odds_{i}")
                endelige_valgte_spil.append({"hold": kamp["hold"], "variant": f"⌨️ {manuelt_spil}", "odds": manuelt_odds, "flammer": "🔥 🔥 🔥", "stjerner": 4})
            else:
                valgt_f = next((f for f in forslag if f["titel"] in valgt_marked), None)
                if valgt_f:
                    endelige_valgte_spil.append({"hold": kamp["hold"], "variant": valgt_f["variant"], "odds": valgt_f["odds"], "flammer": valgt_f["flammer"], "stjerner": valgt_f["stjerner"]})
                else:
                    endelige_valgte_spil.append({"hold": kamp["hold"], "variant": kamp["originalt_valg"], "odds": kamp["odds"], "flammer": "🔥 🔥", "stjerner": 3})
    else:
        for kamp in scannet_data["kampe"]:
            endelige_valgte_spil.append({"hold": kamp["hold"], "variant": kamp["originalt_valg"], "odds": kamp["odds"], "flammer": "🔥 🔥", "stjerner": 3})

    st.write("---")
    st.subheader("🎯 Den optimerede kuponstamme")
    
    ny_samlet_odds = orig_samlet_odds if not vis_alternativer else 1.0
    maksimale_stjerner = 3
    
    for spil in endelige_valgte_spil:
        if vis_alternativer:
            ny_samlet_odds *= spil["odds"]
        stjerne_antal = len(spil["stjerner"]) if isinstance(spil["stjerner"], str) else int(spil["stjerner"])
        if stjerne_antal > maksimale_stjerner:
            maksimale_stjerner = stjerne_antal
            
        with st.expander(f"⚽ {spil['hold']} — Odds {spil['odds']:.2f}", expanded=True):
            st.write(f"**Valgt væddemål:** {spil['variant']}")
            
    ny_samlet_odds = round(ny_samlet_odds, 2)
    
    st.write("---")
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.metric("Registreret Kupon-Odds", f"{ny_samlet_odds:.2f}")
    with col_res2:
        st.metric("Layout-Status", "Agnostisk Godkendt")

    if st.button("💾 TILFØJ KUPON TIL SPIL-STATISTIK", use_container_width=True):
        ligaer_liste = [s["hold"] for s in endelige_valgte_spil]
        forslag_liste = [f"[{s['hold']}]: {s['variant']}" for s in endelige_valgte_spil]
        
        succes = gem_kupon_i_historik(
            ligaer_liste=ligaer_liste,
            forslag_liste=forslag_liste,
            bookmakere_dict={"🤖 AI-Scanner": f"{ny_samlet_odds:.2f}"},
            side="📸 Universel Billed-Scanner",
            stjerner=maksimale_stjerner
        )
        if succes:
            st.success("✅ Kuponen er tilføjet din langsigtede succesrate og gemt i SQLite-databasen!")
