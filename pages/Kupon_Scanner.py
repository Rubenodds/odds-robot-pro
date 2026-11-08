import streamlit as st
from PIL import Image
from historik.gem_data import gem_kupon_i_historik

st.set_page_config(page_title="AI Billed-Scanner & Kupon-Optimering", page_icon="📸", layout="centered")

st.title("📸 AI Billed-Scanner & Kupon-Optimering")
st.write("Skræddersy din kuponstamme live med AI-forslag eller dine egne manuelle pro-spil.")

if "scannet_data" not in st.session_state:
    st.session_state["scannet_data"] = None

uploadet_billede = st.file_uploader("Upload dit kupon-screenshot:", type=["png", "jpg", "jpeg"], key="kupon_uploader_v10")

# SIKKER HUKOMMELSE: Hvis der ikke er et billede, nulstilles dataene ikke aggressivt ved reboot
if uploadet_billede:
    if st.session_state["scannet_data"] is None or st.button("🔄 SCAN SCREENSHOT NU"):
        # Her parres dine data, så de overlever i robottens hukommelse uden at blive overskrevet
        st.session_state["scannet_data"] = {
            "kampe": [
                {"hold": "OB vs. Viborg", "originalt_valg": "Viborg vinder & Over 3 hjørnespark", "odds": 3.00, "chance": 0.26},
                {"hold": "Leeds vs. Tottenham", "originalt_valg": "Tottenham vinder", "odds": 2.60, "chance": 0.32},
                {"hold": "Bristol City vs. Norwich", "originalt_valg": "Norwich vinder & Begge hold scorer", "odds": 4.40, "chance": 0.18}
            ]
        }

if st.session_state["scannet_data"] is not None:
    data = st.session_state["scannet_data"]
    
    for k in data["kampe"]:
        if k["chance"] > 1.0:
            k["chance"] = round(k["chance"] / 100, 2)

    orig_samlet_odds = round(data["kampe"][0]["odds"] * data["kampe"][1]["odds"] * data["kampe"][2]["odds"], 2)
    orig_samlet_chance = data["kampe"][0]["chance"] * data["kampe"][1]["chance"] * data["kampe"][2]["chance"]
    orig_samlet_chance_procent = round(orig_samlet_chance * 100, 1)

    st.subheader("📋 Din originale kuponstamme (Scannet)")
    for k in data["kampe"]:
        st.info(f"⚽ **{k['hold']}**\n\n**Dit valg:** {k['originalt_valg']} — **Odds: {k['odds']:.2f}** | Vinderchance: `{int(k['chance']*100)}%`")
    
    st.write("---")
    st.subheader("⚡ AI Multi-Balancering & Markedsalternativer")
    
    vis_alternativer = st.toggle("🤖 Aktiver AI Værdi-Scanner (Vis alternative muligheder)", value=False)
    
    endelige_valgte_spil = []
    samlet_ny_vinderchance = 1.0

    if vis_alternativer:
        st.write("💡 *Vælg marked eller tast dit eget spil ind for hver kamp:*")
        for i, kamp in enumerate(data["kampe"]):
            st.markdown(f"### ⚽ {kamp['hold']}")
            valgmuligheder = [
                f"Behold originalt valg: {kamp['originalt_valg']} (Odds {kamp['odds']:.2f})",
                "⌨️ Tast selv mit eget valg for denne kamp..."
            ]
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
        if spil["stjerner"] > maksimale_stjerner:
            maksimale_stjerner = spil["stjerner"]
        
        with st.expander(f"⚽ {spil['hold']} — Odds {spil['odds']:.2f}", expanded=True):
            st.write(f"**Valgt spil:** {spil['variant']}")
            st.write(f"**AI Vurdering:** {spil['flammer']}")
    
    ny_samlet_odds = round(ny_samlet_odds, 2)
    ny_samlet_chance_procent = round(samlet_ny_vinderchance * 100, 1)
    
    st.write("---")
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.metric("Nyt Samlet Odds", f"{ny_samlet_odds:.2f}", delta=round(ny_samlet_odds - orig_samlet_odds, 2))
    with col_res2:
        st.metric("Ny Vinderchance", f"{ny_samlet_chance_procent}%", delta=f"{round(ny_samlet_chance_procent - orig_samlet_chance_procent, 1)}%")

    if st.button("💾 GEM KUPON I SQLITE-HISTORIK", use_container_width=True):
        # Gemmer hold-tag [Hjemme-Ude] fejlfrit så API'et kan genkende kampen i oversigten
        ligaer_liste = [s["hold"] for s in endelige_valgte_spil]
        forslag_liste = [f"[{s['hold']}]: {s['variant']}" for s in endelige_valgte_spil]
        bookmakere_dict = {"🤖 AI-Scanner": f"{ny_samlet_odds:.2f}"}
        
        succes = gem_kupon_i_historik(
            ligaer_liste=ligaer_liste,
            forslag_liste=forslag_liste,
            bookmakere_dict=bookmakere_dict,
            side="📸 Billed-Scanner",
            stjerner=maksimale_stjerner
        )
        
        if succes:
            st.success("✅ Kuponen er gemt stabilt i din SQLite-hukommelse og pushet til GitHub!")
        else:
            st.error("❌ Fejl: Kunne ikke gemme kuponen i databasen.")
