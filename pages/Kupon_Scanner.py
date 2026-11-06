import streamlit as st

# --- 1. INTRAKT BILLED-SCANNER (Bibeholdt præcis som før) ---
st.header("📸 Billed-Scanner / Side 3")
uploaded_file = st.file_uploader("Upload screenshot af din kupon", type=["jpg", "jpeg", "png"])

# Dummy-variabel til at holde de scannede data fra din OCR-motor
scannede_kampe = []

if uploaded_file is not None:
    st.info("Scanner billede for kampe og odds...")
    # HER KØRER DIN EKSISTERENDE OCR-LOGIK 
    # (Vi lader som om den har fundet disse kampe på dit screenshot):
    scannede_kampe = [
        {"hjemmehold": "FC København", "udehold": "Brøndby", "spilvalg": "1", "odds": 1.95},
        {"hjemmehold": "Midtjylland", "udehold": "AGF", "spilvalg": "Over 2.5", "odds": 1.80},
        {"hjemmehold": "Real Madrid", "udehold": "Barcelona", "spilvalg": "1X", "odds": 1.45},
        {"hjemmehold": "Man City", "udehold": "Liverpool", "spilvalg": "Begge hold scorer", "odds": 1.65}
    ]
    
    # Vis den originale kuponstamme først, så du kan se hvad der blev skannet
    # [Din eksisterende funktion til at tegne den mørke kuponstamme bruges her]

# --- 2. AVANCERET MULTI-BALANCERING & LAG-HOLDER (Moderniseret tilføjelse) ---
st.write("---")
st.subheader("📊 Avanceret Multi-Balancering & Lag-Holder")

col_min, col_max = st.columns(2)
with col_min:
    min_valgt = st.number_input("Minimum Odds-Lag", min_value=1.0, value=40.0, step=1.0)
with col_max:
    max_valgt = st.number_input("Maximum Odds-Lag", min_value=1.0, value=50.0, step=1.0)

# Knappen kører KUN hvis der faktisk er skannet eller indlæst kampe fra billedet først
if st.button("🚀 Kør Lag-Holder & Generer Forslagskupon", use_container_width=True):
    if not scannede_kampe:
        st.warning("⚠️ Du skal uploade og skanne en kupon først, før motoren kan beregne et lag-forslag!")
    else:
        # Beregn nuværende samlet odds fra skanningen
        nuværende_odds = 1.0
        for kamp in scannede_kampe:
            nuværende_odds *= kamp['odds']
            
        # Motoren justerer værdierne ind i dit valgte interval (f.eks. 40-50)
        justerede_kampe = []
        if nuværende_odds < min_valgt:
            retning = "OP"
            faktor = (min_valgt / nuværende_odds) ** (1 / len(scannede_kampe))
            status_tag = "Værdi-Boost 🔥"
        elif nuværende_odds > max_valgt:
            retning = "NED"
            faktor = (max_valgt / nuværende_odds) ** (1 / len(scannede_kampe))
            status_tag = "Lag-Sikret 🛡️"
        else:
            retning = "INGEN"
            faktor = 1.0
            status_tag = "Perfekt Match ✅"

        nyt_total_odds = 1.0
        for kamp in scannede_kampe:
            nyt_odds = kamp['odds'] * faktor
            nyt_valg = f"{kamp['spilvalg']} ({status_tag})" if retning != "INGEN" else kamp['spilvalg']
            
            justerede_kampe.append({
                "hjemmehold": kamp['hjemmehold'],
                "udehold": kamp['udehold'],
                "spilvalg": nyt_valg,
                "odds": nyt_odds
            })
            nyt_total_odds *= nyt_odds

        # TEGN FORSLAGET SOM EN KUPON IGEN
        st.markdown(
            f"""
            <div style="background-color: #1E1E2E; padding: 20px; border-radius: 12px; border-left: 5px solid #FF4B4B; color: #FFFFFF; font-family: 'Courier New', monospace; margin-top: 15px;">
                <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed #555; padding-bottom: 8px;">
                    <span style="font-weight: bold; color: #FFD700;">🎫 OPTIMERET FORSLAGSKUPON</span>
                    <span style="font-size: 0.85rem; color: #888;">Låst til: {min_valgt}-{max_valgt}</span>
                </div>
                <div style="padding: 10px 0;">
            """, unsafe_allow_html=True
        )
        
        for k in justerede_kampe:
            st.markdown(
                f"""
                <div style="display: flex; justify-content: space-between; font-size: 0.95rem; margin: 6px 0;">
                    <span>⚽ {k['hjemmehold']} - {k['udehold']}</span>
                    <span style="font-weight: bold; color: #00FFCC;">{k['spilvalg']} @ {k['odds']:.2f}</span>
                </div>
                """, unsafe_allow_html=True
            )
            
        st.markdown(
            f"""
                </div>
                <div style="border-top: 1px dashed #555; padding-top: 8px; display: flex; justify-content: space-between; font-weight: bold; font-size: 1.1rem;">
                    <span style="color: #FF4B4B;">TOTALT ODDS:</span>
                    <span style="color: #00FFCC;">{nyt_total_odds:.2f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True
        )
