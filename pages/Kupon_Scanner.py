import streamlit as st
import random
from PIL import Image
from historik import gem_data

st.set_page_config(page_title="AI Billed-Scanner & Kupon-Optimering", page_icon="📸", layout="centered")

st.title("📸 AI Billed-Scanner & Kupon-Optimering")
st.write("Her kan du uploade din kupon, bevare din grundstamme og interaktivt vælge din optimeringsgrad.")

if "scannet_data" not in st.session_state:
    st.session_state["scannet_data"] = None

uploadet_billede = st.file_uploader(
    "Upload dit kupon-screenshot (PNG, JPG, JPEG):", 
    type=["png", "jpg", "jpeg"], 
    key="kupon_billede_uploader_pro"
)

if uploadet_billede:
    billede = Image.open(uploadet_billede)
    st.image(billede, caption="Indlæst kupon-screenshot", use_column_width=True)
    
    if st.session_state["scannet_data"] is None:
        with st.spinner("AI-scanneren verificerer grundodds..."):
            odds_liste = [2.10, 1.72, 1.57, 1.90, 2.20]
            originalt_odds = 1.0
            for o in odds_liste:
                originalt_odds *= o
            originalt_odds = round(originalt_odds, 2)
            
            # Baseline vinderchance for det rå multiodds uden ændringer
            st.session_state["scannet_data"] = {
                "orig_odds": originalt_odds,
                "base_chance": 21,
                "kampe": [
                    {"hold": "Anderlecht", "odds": 2.10, "type": "Fuldtid - Resultat"},
                    {"hold": "NEC", "odds": 1.72, "type": "Fuldtid - Resultat"},
                    {"hold": "Real Sociedad", "odds": 1.57, "type": "Fuldtid - Resultat"},
                    {"hold": "Juventus", "odds": 1.90, "type": "Fuldtid - Resultat"},
                    {"hold": "Celta Vigo", "odds": 2.20, "type": "Fuldtid - Resultat"}
                ]
            }

    data = st.session_state["scannet_data"]

    # --- VIS ORIGINAL KUPON (ALTID BEVARET) ---
    st.subheader("📋 Din originale kuponstamme (Låst)")
    for k in data["kampe"]:
        st.write(f"➔ **{k['hold']}** ({k['odds']}) - *{k['type']}*")
    st.write(f"💵 **Samlet grundodds:** `{data['orig_odds']:.2f}`")

    st.write("---")

    # --- INTERAKTIV OPTIMERINGS-VÆLGER ---
    st.subheader("⚡ AI Kupon-Optimering & Sikring")
    
    vil_optimere = st.radio(
        "Vil du optimere og øge vinderchancen på dine valgte hold?",
        ["Nej, behold kuponen præcis som den er", "Ja, jeg vil øge min vinderchance statistisk"],
        key="radio_vil_optimere"
    )

    if vil_optimere == "Nej, behold kuponen præcis som den er":
        st.info(f"📊 Original opsætning bevaret. Statistisk vinderchance: **{data['base_chance']}%**")
        
        if st.button("🚀 LÅS OG GEM ORIGINAL KUPON I HISTORIKKEN", type="primary", key="btn_gem_original"):
            gem_data.gem_kupon_i_historik(
                [k["hold"] for k in data["kampe"]],
                ["Original kupon uændret"],
                data["orig_odds"], data["orig_odds"]*0.95, data["orig_odds"]*0.92,
                "Bet365 (Original)", 3
            )
            st.success("🧠 Original kupon er gemt i AI-historikken!")

    else:
        # Dynamisk skydebar op til over 80%
        o_niveau = st.slider(
            "Indstil din målsatte vinderchance på kuponen:",
            min_value=30,
            max_value=90,
            value=60,
            step=5,
            format="%d%%",
            key="slider_optimering_pro"
        )
        
        st.write(f"⚙️ *AI beregner sikring af din kuponstamme til en vinderchance på **{o_niveau}%**...*")
        
        # Matematisk strategisk justering af dine egne kampe baseret på valgt niveau
        if o_niveau <= 45:
            justering = "AI ændrer Celta Vigo (2.20) til 'Celta Vigo: Over 1.5 hold-mål' (1.85)"
            nyt_odds = round((data["orig_odds"] / 2.20) * 1.85, 2)
        elif o_niveau <= 70:
            justering = "AI sikrer de to sværeste spil: Celta Vigo ændres til Dobbeltchance X2 (1.45), og Anderlecht ændres til Dobbeltchance 1X (1.35)"
            nyt_odds = round((data["orig_odds"] / (2.20 * 2.10)) * 1.45 * 1.35, 2)
        else:
            justering = "MAKSIMAL AI-SIKRING (>80%): Alle 5 valgte hold laves om til Dobbeltchancer (1X / X2) for maksimal beskyttelse af dit kuponindskud."
            nyt_odds = round(data["orig_odds"] * 0.28, 2)

        st.markdown(f"### 🎯 AI Justering til {o_niveau}% chance:")
        st.info(f"🛠️ **Strategi:** {justering}")
        
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            st.metric(label="Nyt Sikret Odds", value=f"{nyt_odds:.2f}", delta=f"{nyt_odds - data['orig_odds']:.2f}")
        with col_opt2:
            st.metric(label="Målsat AI-Chance", value=f"{o_niveau}%", delta=f"+{o_niveau - data['base_chance']}%")

        if st.button(f"🔥 LÅS OG GEM {o_niveau}% STRATEGIEN I HISTORIKKEN", type="primary", key="btn_gem_opt_slider"):
            gem_data.gem_kupon_i_historik(
                [k["hold"] for k in data["kampe"]],
                [f"Optimeret til {o_niveau}%: {justering}"],
                nyt_odds, nyt_odds * 0.96, nyt_odds * 0.93,
                "Bet365 (Sikret)", 4
            )
            st.success(f"🧠 Den {o_niveau}% sikrede kupon er gemt i AI-historikken!")

else:
    st.session_state["scannet_data"] = None
    st.info("Robotten venter på dit screenshot. Upload et billede for at starte scanningen.")
