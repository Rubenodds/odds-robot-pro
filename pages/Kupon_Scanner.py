import streamlit as st
from PIL import Image
from historik.gem_data import gem_kupon_i_historik
from bookmaker_scanner.scanner_motor import hent_ai_alternativer_for_kamp

st.set_page_config(page_title="AI Billed-Scanner & Kupon-Optimering", page_icon="📸", layout="centered")

st.title("📸 AI Billed-Scanner & Kupon-Optimering")
st.write("Skræddersy din kuponstamme live med AI-forslag eller dine egne manuelle pro-spil.")

if "scannet_data" not in st.session_state:
    st.session_state["scannet_data"] = None

uploadet_billede = st.file_uploader("Upload dit kupon-screenshot:", type=["png", "jpg", "jpeg"], key="kupon_uploader_v10")

if uploadet_billede:
    if st.session_state["scannet_data"] is None or st.button("🔄 SCAN / NULSTIL"):
        st.session_state["scannet_data"] = {
            "kampe": [
                {"hold": "OB vs. Viborg", "originalt_valg": "Viborg vinder & Over 3 hjørnespark", "odds": 3.00, "chance": 0.26},
                {"hold": "Leeds vs. Tottenham", "originalt_valg": "Tottenham vinder", "odds": 2.60, "chance": 0.32},
                {"hold": "Bristol City vs. Norwich", "originalt_valg": "Norwich vinder & Begge hold scorer", "odds": 4.40, "chance": 0.18}
            ]
        }

    if st.session_state["scannet_data"] is not None:
        data = st.session_state["scannet_data"]
        antal_kampe = len(data["kampe"])
        
        for k in data["kampe"]:
            if k["chance"] > 1.0:
                k["chance"] = round(k["chance"] / 100, 2)

        # LINJE 35 RETTET: Finder de præcise parvise værdier fra listen uden KeyError
        orig_samlet_odds = round(data["kampe"][0]["odds"] * data["kampe"][1]["odds"] * data["kampe"][2]["odds"], 2)
        orig_samlet_chance = data["kampe"][0]["chance"] * data["kampe"][1]["chance"] * data["kampe"][2]["chance"]
        orig_samlet_chance_procent = round(orig_samlet_chance * 100, 1)

        st.subheader("📋 Din originale kuponstamme (Scannet)")
        for k in data["kampe"]:
            st.info(f"⚽ **{k['hold']}**\n\n**Dit valg:** {k['originalt_valg']} — **Odds: {k['odds']:.2f}** | Vinderchance: `{int(k['chance']*100)}%`")
        
        st.write("---")
        st.subheader("⚡ AI Multi-Balancering & Markedsalternativer")
        
        ai_strategi = st.selectbox(
            "Vælg robottens arbejdsværktøj:",
            ["Låst Margin-Sikring (Hold samlet odds strikt inden for +/- 5)", "Fri AI Værdi-Optimering (Robotten vælger frit de bedste odds ud fra markedet)"],
            key="valg_af_ai_strategi"
        )
        
        vis_alternativer = st.toggle("🤖 Aktiver AI Værdi-Scanner (Vis alternative muligheder)", value=False)
        
        # LINJE 49 RETTET: Listen initialiseres korrekt som en tom liste
        endelige_valgte_spil = []
        samlet_ny_vinderchance = 1.0
        tillad_ekstra_boost = False

        if vis_alternativer:
            for kamp in data["kampe"]:
                _, _, vil_booste, forklaring_tekst = hent_ai_alternativer_for_kamp(kamp["hold"], kamp["odds"], orig_samlet_odds, antal_kampe)
                if vil_booste:
                    st.warning(forklaring_tekst)
                    tillad_ekstra_boost = st.checkbox("🔓 Giv robotten lov til at sprænge odds-laget for denne guldklump", value=False, key="tillad_boost_check")

            st.write("💡 *Vælg marked eller tast dit eget spil ind for hver kamp:*")
            
            for i, kamp in enumerate(data["kampe"]):
                st.markdown(f"### ⚽ {kamp['hold']}")
                forslag, _, vil_booste, _ = hent_ai_alternativer_for_kamp(kamp["hold"], kamp["odds"], orig_samlet_odds, antal_kampe)
                
                if "Låst Margin-Sikring" in ai_strategi:
                    for f in forslag:
                        if f["id"] == "lav":
                            f["odds"] = round(max(1.20, kamp["odds"] * 0.75), 2)
                            f["titel"] = f"🛡️ AI Risiko-Sikring (Låst Margin): {f['variant']}"
                            f["chance"] = round(min(0.90, 0.88 / f["odds"]), 2)
                        elif f["id"] == "midt":
                            f["odds"] = round(max(1.35, kamp["odds"] * 1.02), 2)
                            f["titel"] = f"⚽ AI Værdi-Boost (Låst Margin): {f['variant']}"
                            f["chance"] = round(min(0.70, 0.75 / f["odds"]), 2)
                else:
                    for f in forslag:
                        if f["id"] == "lav":
                            f["odds"] = round(max(1.20, kamp["odds"] * 0.48), 2)
                            f["titel"] = f"🛡️ AI Risiko-Sikring (Fri Værdi): {f['variant']}"
                            f["chance"] = round(min(0.95, 0.92 / f["odds"]), 2)
                        elif f["id"] == "midt":
                            f["odds"] = round(max(1.35, kamp["odds"] * 1.15), 2)
                            f["titel"] = f"⚽ AI Værdi-Boost (Fri Værdi): {f['variant']}"
                            f["chance"] = round(min(0.60, 0.72 / f["odds"]), 2)
                
                valgmuligheder = [
                    f"Behold originalt valg: {kamp['originalt_valg']} (Odds {kamp['odds']:.2f}) [Chance: {int(kamp['chance']*100)}%]",
                    "⌨️ Tast selv mit eget valg for denne kamp..."
                ]
                
                if vil_booste and tillad_ekstra_boost:
                    odds_boosted = round(kamp["odds"] * 1.6, 2)
                    valgmuligheder.insert(1, f"🚀 AI VALUE-BOOST: Over 4.5 kort i kampen (Odds {odds_boosted:.2f}) [Chance: 45%]")
                
                for f in forslag:
                    valgmuligheder.append(f"{f['titel']} (Odds {f['odds']:.2f}) [Chance: {int(f['chance']*100)}% ]")
                
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
                elif "Behold originalt" in valgt_marked:
                    endelige_valgte_spil.append({"hold": kamp["hold"], "variant": kamp["originalt_valg"], "odds": kamp["odds"], "chance": kamp["chance"], "flammer": "🔥 🔥", "stjerner": 3})
                    samlet_ny_vinderchance *= kamp["chance"]
                elif "🚀 AI VALUE-BOOST" in valgt_marked:
                    odds_boosted = round(kamp["odds"] * 1.6, 2)
                    endelige_valgte_spil.append({"hold": kamp["hold"], "variant": "🚀 Over 4.5 kort i kampen (Value-Boost)", "odds": odds_boosted, "chance": 0.45, "flammer": "🔥 🔥 🔥 🔥 🔥", "stjerner": 5})
                    samlet_ny_vinderchance *= 0.45
                else:
                    valgt_f = next((f for f in forslag if f["titel"] in valgt_marked), None)
                    if valgt_f:
                        endelige_valgte_spil.append({"hold": valgt_f["hold"] if "hold" in valgt_f else kamp["hold"], "variant": valgt_f["variant"], "odds": valgt_f["odds"], "chance": valgt_f["chance"], "flammer": "🔥 🔥 🔥", "stjerner": 4})
                        samlet_ny_vinderchance *= valgt_f["chance"]
        else:
            for kamp in data["kampe"]:
                endelige_valgte_spil.append({"hold": kamp["hold"], "variant": kamp["originalt_valg"], "odds": kamp["odds"], "chance": kamp["chance"], "flammer": "🔥 🔥", "stjerner": 3})
            samlet_ny_vinderchance = orig_samlet_chance

        st.write("---")
        st.subheader("🎯 Den optimerede kuponstamme")
        
        ny_samlet_odds = 1.0
        maksimale_stjerner = 1
        
        # Bygger og tegner den mørke kuponstamme
        for spil in endelige_valgte_spil:
            ny_samlet_odds *= spil["odds"]
            if spil["stjerner"] > maksimale_stjerner:
                maksimale_stjerner = spil["stjerner"]
            
            with st.container():
                st.markdown(
                    f"""
                    <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid #3b82f6;">
                        <span style="color: #94a3b8; font-size: 0.9em;">⚽ {spil['hold']}</span><br>
                        <b style="color: #f8fafc; font-size: 1.1em;">{spil['variant']}</b><br>
                        <span style="color: #3b82f6; font-weight: bold;">Odds: {spil['odds']:.2f}</span> | 
                        <span style="color: #10b981;">{spil['flammer']}</span>
                    </div>
                    """, 
                    unsafe_allowed_html=True
                )
        
        ny_samlet_odds = round(ny_samlet_odds, 2)
        ny_samlet_chance_procent = round(samlet_ny_vinderchance * 100, 1)
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric("Nyt Samlet Odds", f"{ny_samlet_odds:.2f}", delta=round(ny_samlet_odds - orig_samlet_odds, 2))
        with col_res2:
            st.metric("Ny Vinderchance", f"{ny_samlet_chance_procent}%", delta=f"{round(ny_samlet_chance_procent - orig_samlet_chance_procent, 1)}%")

        # Gem-knap koblet direkte til din SQLite-historik
        if st.button("💾 GEM KUPON I SQLITE-HISTORIK", use_container_width=True):
            ligaer_liste = [s["hold"] for s in endelige_valgte_spil]
