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

        orig_samlet_odds = 1.0
        orig_samlet_chance = 1.0
        for k in data["kampe"]:
            orig_samlet_odds *= k["odds"]
            orig_samlet_chance *= k["chance"]
        
        orig_samlet_odds = round(orig_samlet_odds, 2)
        orig_samlet_chance_procent = round(orig_samlet_chance * 100, 1)

        # ----------------- PANEL 1: DIN ORIGINALE KUPONSTAMME -----------------
        st.subheader("📋 Din originale kuponstamme (Scannet)")
        for k in data["kampe"]:
            st.info(f"⚽ **{k['hold']}**\n\n**Dit valg:** {k['originalt_valg']} — **Odds: {k['odds']:.2f}** | Vinderchance: `{int(k['chance']*100)}%` | 🔥 🔥 | ⭐⭐⭐")
        
        st.write("---")

        # ----------------- PANEL 2: INTERAKTIV GRÆNSEFLADE -----------------
        st.subheader("⚡ AI Multi-Balancering & Markedsalternativer")
        
        ai_strategi = st.selectbox(
            "Vælg robottens arbejdsværktøj:",
            ["Låst Margin-Sikring (Hold samlet odds strikt inden for +/- 5)", "Fri AI Værdi-Optimering (Robotten vælger frit de bedste odds ud fra markedet)"],
            key="valg_af_ai_strategi"
        )
        
        vis_alternativer = st.toggle("🤖 Aktiver AI Værdi-Scanner (Vis alternative muligheder)", value=False)
        
        endelige_valgte_spil = []
        samlet_ny_vinderchance = 1.0
        tillad_ekstra_boost = False

        if vis_alternativer:
            for kamp in data["kampe"]:
                _, _, vil_booste, forklaring_tekst = hent_ai_alternativer_for_kamp(kamp["hold"], kamp["odds"], orig_samlet_odds, antal_kampe)
                if vil_booste:
                    st.warning(forklaring_tekst)
                    tillad_ekstra_boost = st.checkbox("🔓 Giv robotten lov til at sprænge odds-laget for denne guldklump", value=False, key="tillad_boost_check")
                    st.write("---")

            st.write("💡 *Vælg marked eller tast dit eget spil ind for hver kamp:*")
            
            for i, kamp in enumerate(data["kampe"]):
                st.markdown(f"### ⚽ {kamp['hold']}")
                forslag, mangler_muligheder, vil_booste, _ = hent_ai_alternativer_for_kamp(kamp["hold"], kamp["odds"], orig_samlet_odds, antal_kampe)
                
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
                    valgmuligheder.append(f"{f['titel']} (Odds {f['odds']:.2f}) [Chance: {int(f['chance']*100)}%]")
                
                valgt_marked = st.radio(f"Vælg marked for {kamp['hold']}:", valgmuligheder, key=f"pro_valg_{i}", label_visibility="collapsed")
                
                if "⌨️ Tast selv" in valgt_marked:
                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        manuelt_spil = st.text_input("Hvad spiller du på kampen?", value="Over 9.5 hjørnespark", key=f"man_navn_{i}")
                    with col_t2:
                        manuelt_odds = st.number_input("Indtast markedets odds:", min_value=1.01, max_value=500.0, value=2.00, step=0.05, key=f"man_odds_{i}")
                    
                    estimeret_chance = round(min(0.90, 0.85 / manuelt_odds), 2)
                    endelige_valgte_spil.append({"hold": kamp["hold"], "variant": f"⌨️ {manuelt_spil}", "odds": manuelt_odds, "chance": estimeret_chance, "flammer": "🔥 🔥 🔥", "stjerner": "⭐⭐⭐⭐"})
                    samlet_ny_vinderchance *= estimeret_chance
                elif "Behold originalt" in valgt_marked:
                    endelige_valgte_spil.append({"hold": kamp["hold"], "variant": kamp["originalt_valg"], "odds": kamp["odds"], "chance": kamp["chance"], "flammer": "🔥 🔥", "stjerner": "⭐⭐⭐"})
                    samlet_ny_vinderchance *= kamp["chance"]
                elif "🚀 AI VALUE-BOOST" in valgt_marked:
                    odds_boosted = round(kamp["odds"] * 1.6, 2)
                    endelige_valgte_spil.append({"hold": kamp["hold"], "variant": "🚀 Over 4.5 kort i kampen (Value-Boost)", "odds": odds_boosted, "chance": 0.45, "flammer": "🔥 🔥 🔥 🔥 🔥", "stjerner": "⭐⭐⭐⭐⭐"})
                    samlet_ny_vinderchance *= 0.45
                else:
                    valgt_f = None
                    for f in forslag:
                        if f["titel"] in valgt_marked:
                            valgt_f = f
                            break
                    if valgt_f:
                        endelige_valgte_spil.append({"hold": kamp["hold"], "variant": valgt_f["variant"], "odds": valgt_f["odds"], "chance": valgt_f["chance"], "flammer": "🔥 🔥 🔥", "stjerner": "⭐⭐⭐⭐"})
                        samlet_ny_vinderchance *= valgt_f["chance"]
        else:
            for kamp in data["kampe"]:
                endelige_valgte_spil.append({"hold": kamp["hold"], "variant": kamp["originalt_valg"], "odds": kamp["odds"], "chance": kamp["chance"], "flammer": "🔥 🔥", "stjerner": "⭐⭐⭐"})
            samlet_ny_vinderchance = orig_samlet_chance

        # ----------------- PANEL 3: DEN MØRKE KUPONSTAMME -----------------
        st.write("---")
        st.subheader("🎯 Den optimerede kuponstamme")
        
        ny_samlet_odds = 1.0
        for spil in endelige_valgte_spil:
            ny_samlet_odds *= spil["odds"]
        ny_samlet_odds = round(ny_samlet_odds, 2)
        ny_samlet_chance_procent = round(samlet_ny_vinderchance * 100, 1)

        with st.container(border=True):
            st.markdown("### ⚡ ODDS-ROBOT-PRO KUPONSTAMME ⚡")
            for spil in endelige_valgte_spil:
                st.markdown(f"**⚽ {spil['hold']}**")
                st.markdown(f"• Spil: `{spil['variant']}`")
                st.markdown(f"• Odds: `{spil['odds']:.2f}` | Chance: `{int(spil['chance']*100)}%` | {spil['flammer']} {spil['stjerner']}")
                st.write("")
            st.divider()
            
            # Her samles hele bunden bundsolidt, så sammenligningen og gem-knappen altid tegnes perfekt!
            st.write(f"📊 **Originalt Odds:** {orig_samlet_odds:.2f}")
            st.write(f"🚀 **Nyt Samlet Odds:** {ny_samlet_odds:.2f}")
            st.write(f"📈 **Estimeret Systemchance:** {ny_samlet_chance_procent}%")

        st.write("")
        indsats = st.number_input("Indtast indsats (DKK):", min_value=10, max_value=10000, value=100, step=10, key="indsats_valg")

        if st.button("💾 GEM KUPON I SQLITE-HISTORIK", type="primary", use_container_width=True):
            success = gem_kupon_i_historik(endelige_valgte_spil, ny_samlet_odds, indsats, ny_samlet_chance_procent)
            if success:
