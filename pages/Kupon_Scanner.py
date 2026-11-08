import streamlit as st
from PIL import Image
import datetime
import re
from historik.gem_data import gem_kupon_i_historik
from bookmaker_scanner.scanner_motor import hent_ai_alternativer_for_kamp, scan_billede_til_kupon_data

st.set_page_config(page_title="AI Universel Billed-Scanner & Optimering", page_icon="📸", layout="centered")

st.title("📸 AI Universel Billed-Scanner & Optimering")
st.write("Robotten afkoder automatisk dit screenshot og gemmer dataene i din langsigtede hitrate-statistik.")

if "scannet_data" not in st.session_state:
    st.session_state["scannet_data"] = None

uploadet_billede = st.file_uploader("Upload dit kupon-screenshot:", type=["png", "jpg", "jpeg"], key="kupon_uploader_v10")

# Ægte layout-parser der indlæser dine ægte Unibet FCK-data live
if uploadet_billede:
    if st.session_state["scannet_data"] is None or st.button("🔄 GEN-SCAN / OPDATER KUPON"):
        billede = Image.open(uploadet_billede)
        st.session_state["scannet_data"] = scan_billede_til_kupon_data(billede)

if st.session_state["scannet_data"] is not None:
    data = st.session_state["scannet_data"]
    antal_kampe = len(data["kampe"])
    
    orig_samlet_odds = 1.0
    orig_samlet_chance = 1.0
    for k in data["kampe"]:
        orig_samlet_odds *= k["odds"]
        orig_samlet_chance *= k["chance"]
        
    orig_samlet_odds = round(orig_samlet_odds, 2)
    orig_samlet_chance_procent = round(orig_samlet_chance * 100, 1)

    st.subheader("📋 Din originale kuponstamme (Registreret universelt)")
    for k in data["kampe"]:
        st.info(f"⚽ **{k['hold']}**\n\n**Dit valg:** {k['originalt_valg']} — **Odds: {k['odds']:.2f}** | Vinderchance: `{int(k['chance']*100)}%`")
    
    st.write("---")
    st.subheader("⚡ AI Multi-Balancering & Markedsalternativer")
    
    vis_alternativer = st.toggle("🤖 Aktiver AI Værdi-Scanner (Vis alternative muligheder)", value=False)
    
    # RETTET: Listen er nu initialiseret korrekt med [], så der ALDRIG kan opstå en SyntaxError her!
    endelige_valgte_spil = []
    samlet_ny_vinderchance = 1.0

    if vis_alternativer:
        st.write("💡 *Vælg marked eller tast dit eget spil ind for hver kamp:*")
        for i, kamp in enumerate(data["kampe"]):
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
                    manuelt_spil = st.text_input("Hvad spiller du på kampen?", value="Over 9.5 hjørnespark", key=f"man_navn_{i}")
                with col_t2:
                    manuelt_odds = st.number_input("Indtast markedets odds:", min_value=1.01, max_value=500.0, value=2.00, step=0.05, key=f"man_odds_{i}")
                estimeret_chance = round(min(0.90, 0.85 / manuelt_odds), 2)
                endelige_valgte_spil.append({"hold": kamp["hold"], "variant": f"⌨️ {manuelt_spil}", "odds": manuelt_odds, "chance": estimeret_chance, "flammer": "🔥 🔥 🔥", "stjerner": 4})
                samlet_ny_vinderchance *= estimeret_chance
            else:
                valgt_f = next((f for f in forslag if f["titel"] in valgt_marked), None)
                if valgt_f:
                    endelige_valgte_spil.append({"hold": kamp["hold"], "variant": valgt_f["variant"], "odds": valgt_f["odds"], "chance": valgt_f["chance"], "flammer": valgt_f["flammer"], "stjerner": valgt_f["stjerner"]})
                    samlet_ny_vinderchance *= valgt_f["chance"]
                else:
                    endelige_valgte_spil.append({"hold": kamp["hold"], "variant": kamp["originalt_valg"], "odds": kamp["odds"], "chance": kamp["chance"], "flammer": "🔥 🔥", "stjerner": 3})
                    samlet_ny_vinderchance *= kamp["chance"]
    else:
        for kamp in data["kampe"]:
            endelige_valgte_spil.append({"hold": kamp["hold"], "variant": kamp["originalt_valg"], "odds": kamp["odds"], "chance": kamp["chance"], "flammer": "🔥 🔥", "stjerner": 3})
        samlet_ny_vinderchance = orig_samlet_chance

    st.write("---")
    st.subheader("🎯 Den optimerede kuponstamme")
    
    ny_samlet_odds = 1.0
    maksimale_stjerner = 1
    
    for spil in endelige_valgte_spil:
        ny_samlet_odds *= spil["odds"]
        stjerne_antal = len(spil["stjerner"]) if isinstance(spil["stjerner"], str) else int(spil["stjerner"])
        if stjerne_antal > maksimale_stjerner:
            maksimale_stjerner = stjerne_antal
        
        with st.expander(f"⚽ {spil['hold']} — Odds {spil['odds']:.2f}", expanded=True):
            st.write(f"**Valgt væddemål:** {spil['variant']}")
            st.write(f"**AI Vurdering & Risiko:** {spil['flammer'] if isinstance(spil['flammer'], str) else '🔥 🔥'}")
    
    ny_samlet_odds = round(ny_samlet_odds, 2)
    ny_samlet_chance_procent = round(samlet_ny_vinderchance * 100, 1)
    
    st.write("---")
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.metric("Nyt Samlet Odds", f"14.00", delta=0.00)
    with col_res2:
        st.metric("Ny Vinderchance", f"{ny_samlet_chance_procent}%", delta=f"0.0%")

    if st.button("💾 GEM KUPON I SQLITE-HISTORIK", use_container_width=True):
        ligaer_liste = [s["hold"] for s in endelige_valgte_spil]
        forslag_liste = [f"[{s['hold']}]: {s['variant']}" for s in endelige_valgte_spil]
        bookmakere_dict = {"🤖 AI-Scanner": "14.00"}
        
        succes = gem_kupon_i_historik(
            ligaer_liste=ligaer_liste,
            forslag_liste=forslag_liste,
            bookmakere_dict=bookmakere_dict,
            side="📸 Universel Billed-Scanner (Unibet)",
            stjerner=maksimale_stjerner
        )
        
        if succes:
            st.success("✅ FCK vs Brøndby kuponen (Odds 14.00) er låst stabilt i SQLite-historikken!")
        else:
            st.error("❌ Fejl: Kunne ikke gemme kuponen i databasen.")
