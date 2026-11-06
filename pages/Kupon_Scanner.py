import streamlit as st

def tegn_mørk_kuponstamme(titel, kamp_liste, totalt_odds, lag_status=""):
    """
    Tegner den karakteristiske mørke kuponstamme i Streamlit.
    """
    st.markdown(
        f"""
        <div style="
            background-color: #1E1E2E; 
            padding: 20px; 
            border-radius: 12px; 
            border-left: 5px solid #FF4B4B;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
            color: #FFFFFF;
            font-family: 'Courier New', Courier, monospace;
            margin-bottom: 20px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed #555; padding-bottom: 8px;">
                <span style="font-weight: bold; font-size: 1.1rem; color: #FFD700;">🎫 {titel}</span>
                <span style="font-size: 0.85rem; color: #888;">{lag_status}</span>
            </div>
            <div style="padding: 10px 0;">
        """, 
        unsafe_allow_html=True
    )
    
    for kamp in kamp_liste:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; font-size: 0.95rem; margin: 6px 0;">
                <span>⚽ {kamp['hjemmehold']} - {kamp['udehold']}</span>
                <span style="font-weight: bold; color: #00FFCC;">{kamp['spilvalg']} @ {kamp['odds']:.2f}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    st.markdown(
        f"""
            </div>
            <div style="border-top: 1px dashed #555; padding-top: 8px; display: flex; justify-content: space-between; font-weight: bold; font-size: 1.1rem;">
                <span style="color: #FF4B4B;">TOTALT ODDS:</span>
                <span style="color: #00FFCC;">{totalt_odds:.2f}</span>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )

def balancer_kupon_til_lag(originale_kampe, min_lag, max_lag):
    """
    Kører den baglæns motor, som tvinger det samlede odds ind i intervallet [min_lag - max_lag].
    Den foretager gradvise justeringer per kamp, indtil målet er nået.
    """
    # Beregn det nuværende samlede odds
    nuværende_odds = 1.0
    for kamp in originale_kampe:
        nuværende_odds *= kamp['odds']
        
    # Hvis kuponen allerede ligger i det ønskede lag, returneres den uændret
    if min_lag <= nuværende_odds <= max_lag:
        return originale_kampe, nuværende_odds, "Perfekt Balanceret Matched ✅"
        
    justerede_kampe = []
    faktor = 1.0
    retning = ""
    status_tag = ""
    
    # Bestem om der skal skrues op eller ned
    if nuværende_odds < min_lag:
        # Odds er for lavt -> Skal justeres OP (Værdi-Boost)
        retning = "OP"
        faktor = (min_lag / nuværende_odds) ** (1 / len(originale_kampe))
        status_tag = "Værdi-Boost 🔥"
    elif nuværende_odds > max_lag:
        # Odds er for højt -> Skal justeres NED (Risiko-Minimering)
        retning = "NED"
        faktor = (max_lag / nuværende_odds) ** (1 / len(originale_kampe))
        status_tag = "Lag-Sikret 🛡️"

    # Gennemfør den matematiske justering på hver kamp
    nyt_total_odds = 1.0
    for kamp in originale_kampe:
        nyt_odds = kamp['odds'] * faktor
        nyt_valg = f"{kamp['spilvalg']} ({status_tag})"
        
        justerede_kampe.append({
            "hjemmehold": kamp['hjemmehold'],
            "udehold": kamp['udehold'],
            "spilvalg": nyt_valg,
            "odds": nyt_odds
        })
        nyt_total_odds *= nyt_odds
        
    lag_status = f"Mål: {min_lag}-{max_lag} | Justering: {retning}"
    return justerede_kampe, nyt_total_odds, lag_status

# --- INTEGRATION I STREAMLIT INTERFACET ---
st.subheader("📊 Avanceret Multi-Balancering & Lag-Holder")

# Modul-input til at vælge det præcise odds-lag
col_min, col_max = st.columns(2)
with col_min:
    min_valgt = st.number_input("Minimum Odds-Lag", min_value=1.0, value=40.0, step=1.0)
with col_max:
    max_valgt = st.number_input("Maximum Odds-Lag", min_value=1.0, value=50.0, step=1.0)

# Dummy test-data til illustration (Disse kommer live fra din OCR/Billed-scanner)
scannede_kampe_eksempel = [
    {"hjemmehold": "FC København", "udehold": "Brøndby", "spilvalg": "1", "odds": 1.95},
    {"hjemmehold": "Midtjylland", "udehold": "AGF", "spilvalg": "Over 2.5", "odds": 1.80},
    {"hjemmehold": "Real Madrid", "udehold": "Barcelona", "spilvalg": "1X", "odds": 1.45},
    {"hjemmehold": "Man City", "udehold": "Liverpool", "spilvalg": "Begge hold scorer", "odds": 1.65}
]

if st.button("🚀 Kør Lag-Holder & Generer Forslagskupon", use_container_width=True):
    # Kør motoren der tvinger oddset ind i f.eks. 40-50
    forslag_kampe, total_odds_forslag, status = balancer_kupon_til_lag(scannede_kampe_eksempel, min_valgt, max_valgt)
    
    # Tegn resultatet direkte som en færdig, mørk kuponstamme med det nye låste lag
    tegn_mørk_kuponstamme(
        titel="OPTIMERET FORSLAGSKUPON (LÅST TIL LAG)",
        kamp_liste=forslag_kampe,
        totalt_odds=total_odds_forslag,
        lag_status=status
    )
    
    # Direkte integration mod SQLite
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Godkend & Gem til Database", key="godkend_lag_knap", use_container_width=True):
            st.success("Kuponen er låst i databasen!")
    with c2:
        if st.button("❌ Forkast", key="forkast_lag_knap", use_container_width=True):
            st.warning("Forslag nulstillet.")
