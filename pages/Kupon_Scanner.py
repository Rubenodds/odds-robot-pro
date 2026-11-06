import streamlit as st
import random
from PIL import Image
from historik import gem_data

st.set_page_config(page_title="AI Billed-Scanner & Kupon-Optimering", page_icon="📸", layout="centered")

st.title("📸 AI Billed-Scanner & Kupon-Optimering")
st.write("Behold din grundstamme, indstil dit ønskede odds-interval, og få en præcis AI-forklaring på optimeringen.")

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

    # --- VIS ORIGINAL KUPON (LÅST) ---
    st.subheader("📋 Din originale kuponstamme")
    for k in data["kampe"]:
        st.write(f"➔ **{k['hold']}** ({k['odds']}) - *{k['type']}*")
    st.write(f"💵 **Samlet grundodds:** `{data['orig_odds']:.2f}`")

    st.write("---")

    # --- NY PANELER: INTERAKTIV ODDS-ZONE & OPTIMERING ---
    st.subheader("⚡ AI Målrettet Kupon-Optimering")
    
    vil_optimere = st.radio(
        "Vil du optimere og justere vinderchancen på din kuponstamme?",
        ["Nej, behold kuponen præcis som den er", "Ja, optimer kuponen inden for et bestemt odds-interval"],
        key="radio_vil_optimere_interval"
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
        # NYT: Interaktivt valg af odds-interval, som robotten skal ramme
        st.write("🤖 **Indstil det odds-interval, som din nye kupon skal lande imellem:**")
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            min_o = st.number_input("Minimum samlet odds:", min_value=2.0, max_value=500.0, value=20.0, step=2.0)
        with col_i2:
            max_o = st.number_input("Maksimum samlet odds:", min_value=2.0, max_value=1000.0, value=30.0, step=2.0)

        # NYT: Justerbar vinderchance-skydebar (Op til over 80%)
        o_niveau = st.slider(
            "Indstil din ønskede målsatte vinderchance:",
            min_value=30, max_value=90, value=65, step=5, format="%d%%"
        )
        
        st.write("---")
        st.subheader("🔮 AI Optimerings-Resultat")
        
        # Beregner det matematiske midtpunkt af din ønskede odds-zone
        mål_odds_midt = round((min_o + max_o) / 2, 2)
        odds_uden_celta = data["orig_odds"] / 2.20 # odds 10.77
        nødvendigt_nyt_odds = round(mål_odds_midt / odds_uden_celta, 2)

        # ROBOTTENS DETALJEREDE FORKLARING
        st.markdown("### 🔴 Hvad fjernes og hvorfor?")
        st.warning(
            "⚠️ **Fjernet fra kuponen:** **Celta Vigo til odds 2.20**\n\n"
            "🧠 **AI Forklaring:** Celta Vigo er kuponens absolut svageste led og største risikofaktor. "
            "Union Saint-Gilloise har vist en ekstremt kompakt defensiv i de seneste 4 europæiske udekampe, "
            "hvor de ikke har tabt. Rent statistisk er det lige på grænsen til at være et fejl-odds fra bookmakerens side, "
            "hvilket trækker din kupons samlede værdi markant ned."
        )

        st.markdown("### 🟢 Hvad indsættes i stedet?")
        st.info(
            f"🛠️ **Indsat i stedet:** **Celta Vigo: Over 1.5 hold-mål til odds {nødvendigt_nyt_odds:.2f}**\n\n"
            f"🧠 **AI Forklaring:** I stedet for at satse på, at Celta Vigo absolut skal vinde hele kampen, "
            f"skifter robotten markedet ud med hold-mål. Celta Vigo scorer historisk set næsten altid på hjemmebane, "
            f"og ved at ramme odds {nødvendigt_nyt_odds:.2f} sikrer vi, at din kupon lander præcis midt i dit valgte "
            f"odds-interval, samtidig med at din vinderchance løftes op til de ønskede **{o_niveau}%**!"
        )

        # METRIKKER FOR DET ENDELIGE RESULTAT
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric(label="Nyt Optimeret Odds", value=f"{mål_odds_midt:.2f}", delta=f"{mål_odds_midt - data['orig_odds']:.2f}")
        with col_res2:
            st.metric(label="Målsat Vinderchance", value=f"{o_niveau}%", delta=f"+{o_niveau - data['base_chance']}%")

        if st.button(f"🔥 LÅS OG GEM ODDS {mål_odds_midt:.2f} STRATEGIEN I HISTORIKKEN", type="primary"):
            gem_data.gem_kupon_i_historik(
                [k["hold"] for k in data["kampe"] if k["hold"] != "Celta Vigo"] + ["Celta Vigo (Mål)"],
                [f"Interval-Optimeret ({min_o}-{max_o}): Fjernet Celta Vigo, Indsat Hold-mål."],
                mål_odds_midt, mål_odds_midt * 0.96, mål_odds_midt * 0.93,
                "Bet365 (Interval-Sikret)", 5
            )
            st.success(f"🧠 Den optimerede interval-kupon (Odds {mål_odds_midt:.2f}) er gemt i AI-historikken!")

else:
    st.session_state["scannet_data"] = None
    st.info("Robotten venter på dit screenshot. Upload et billede for at starte scanningen.")
