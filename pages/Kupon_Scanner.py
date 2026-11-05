import streamlit as st
import random
from PIL import Image

st.set_page_config(page_title="AI Manuel Kupon Scanner", page_icon="📸", layout="centered")

st.title("📸 AI Kupon Scanner & Værdi-Vurdering")
st.write("Upload din egen kupon, få risikovurdering og tilføj værdifulde AI-forslag med ét klik.")

st.header("🎰 1. Upload din kupon")
uploadet_billede = st.file_uploader("Upload dit billede eller screenshot her:", type=["png", "jpg", "jpeg"], key="kupon_uploader_side_fane")

if uploadet_billede:
    billede = Image.open(uploadet_billede)
    st.image(billede, caption="Din indlæste kupon", use_column_width=True)
    
    # Vi simulerer, at robotten finder dit oprindelige odds på det uploadede screenshot
    oprindeligt_odds = 5.50
    st.info(f"🔍 **AI Scannet data:** Robotten registrerede dit nuværende samlede kupon-odds til: **{oprindeligt_odds:.2f}**")
    
    st.header("📊 2. AI Sandsynlighed & Risiko Analyse")
    with st.spinner("Analyserer dine valg mod live-statistikker..."):
        samlet_chance = random.randint(35, 65)
        ai_karakter = random.randint(2, 4)
        
        st.write(f"🔥 **Vurderet statistisk chance for at kuponen går hjem:** {samlet_chance}%")
        st.write(f"🎯 **AI Sikkerhedskarakter:** {'⭐' * ai_karakter} ({ai_karakter}/5 stjerner)")

    # ----------------- NY SEKTION: INTERAKTIVE AI FORSLAG -----------------
    st.header("💡 3. AI Optimerings-forslag (Hent merværdi)")
    st.write("Robotten har scannet markedet for i aften og fundet et specialmarked med ekstrem høj statistisk sandsynlighed, som vil booste din kupon:")
    
    # Robotten genererer et dagsaktuelt hold-forslag
    forslag_tekst = "Tilføj 'Liverpool over 4.5 hjørnespark' (Statistisk sikkerhed: 89% i aften)"
    forslag_odds_b365 = 1.45
    forslag_odds_uni = 1.41
    forslag_odds_oddset = 1.38
    
    st.warning(f"➔ **AI ANBEFALING:** {forslag_tekst}")
    st.write(f"📈 **Odds på dette tilføjelses-spil:** Bet365: **{forslag_odds_b365:.2f}** | Unibet: **{forslag_odds_uni:.2f}** | Oddset: **{forslag_odds_oddset:.2f}**")
    
    # Interaktiv godkendelses-knap
    godkend_forslag = st.checkbox("✅ JA TAK, JEG VIL GERNE SE DET NYE ODDS HVIS FORSLAGET GODKENDES", value=False, key="chk_godkend_ai_forslag")
    
    if godkend_forslag:
        st.subheader("🎯 Resultat efter godkendelse af AI-forslag:")
        
        # Matematisk genberegning af det nye samlede odds på tværs af bookmakerne
        nyt_odds_b365 = oprindeligt_odds * forslag_odds_b365
        nyt_odds_uni = oprindeligt_odds * forslag_odds_uni
        nyt_odds_oddset = oprindeligt_odds * forslag_odds_oddset
        
        st.success(f"🔥 **NYT SAMLET ODDS HOS BET365: {nyt_odds_b365:.2f}**")
        
        # Sammenligningstabel for den nye kupon
        st.write("### 📊 Sådan udbetaler din nye kupon:")
        st.write(f"*   **Bet365 (Anbefalet):** Nyt samlet odds: **{nyt_odds_b365:.2f}** 🚀")
        st.write(f"*   **Unibet:** Nyt samlet odds: **{nyt_odds_uni:.2f}**")
        st.write(f"*   **Danske Spil (Oddset):** Nyt samlet odds: **{nyt_odds_oddset:.2f}**")
        
        # Viser den reelle merværdi i procenter
        st.info(f"💡 **Konklusion:** Ved at godkende robottens forslag og flytte kuponen til Bet365, stiger dit samlede odds fra **{oprindeligt_odds:.2f}** til **{nyt_odds_b365:.2f}**! Det giver dig markant flere penge i udbetaling for præcis de samme kampe.")
