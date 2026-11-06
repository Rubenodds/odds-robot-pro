import streamlit as st

def tegn_betting_kupon_forslag(overskrift, kamp_liste, samlet_odds, info_tekst=""):
    """
    Genererer en visuel, mørk betting-kupon til optimerede forslag.
    Denne erstatter den rå tekstvisning.
    """
    # Starten på den mørke kuponstamme med betting-tema
    st.markdown(
        f"""
        <div style="
            background-color: #12121A; 
            padding: 22px; 
            border-radius: 14px; 
            border: 2px solid #2A2A3A;
            border-left: 6px solid #FF4B4B;
            box-shadow: 0px 6px 15px rgba(0,0,0,0.5);
            color: #E2E2E2;
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            max-width: 480px;
            margin: 20px auto 20px 0;
        ">
            <!-- Kupon Header -->
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px dashed #3A3A50; padding-bottom: 12px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.3rem;">🎫</span>
                    <span style="font-weight: 800; letter-spacing: 0.5px; color: #FFFFFF; font-size: 1.05rem;">{overskrift.upper()}</span>
                </div>
                <span style="background-color: #222235; color: #FFD700; font-size: 0.75rem; padding: 4px 8px; border-radius: 6px; font-weight: bold; border: 1px solid #444460;">
                    {info_tekst}
                </span>
            </div>
            
            <!-- Kampvalg -->
            <div style="display: flex; flex-direction: column; gap: 12px; padding: 4px 0;">
        """, 
        unsafe_allow_html=True
    )
    
    # Løkke igennem de foreslåede kampe
    for kamp in kamp_liste:
        # Tjek om det er et risiko/sikkert valg for at farve ikonet derefter
        ikon = "🔥" if "boost" in kamp.get('type', '').lower() else "🛡️"
        
        st.markdown(
            f"""
            <div style="background-color: #1A1A26; padding: 10px 12px; border-radius: 8px; border: 1px solid #252538; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; flex-direction: column; gap: 2px;">
                    <span style="font-size: 0.82rem; color: #8A8A9F; font-weight: 500;">⚽ {kamp['hjemmehold']} - {kamp['udehold']}</span>
                    <span style="font-size: 0.92rem; color: #FFFFFF; font-weight: 600;">{kamp['spilvalg']}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span style="font-size: 0.85rem;">{ikon}</span>
                    <span style="background-color: #00FFCC; color: #051510; font-weight: 800; font-size: 0.95rem; padding: 3px 8px; border-radius: 4px; min-width: 45px; text-align: center;">
                        {kamp['odds']:.2f}
                    </span>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    # Kupon Bund / Total Odds
    st.markdown(
        f"""
            </div>
            <div style="margin-top: 14px; border-top: 2px dashed #3A3A50; padding-top: 12px; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #FF4B4B; font-weight: 800; font-size: 1.05rem; letter-spacing: 0.5px;">SAMLET ODDS:</span>
                <span style="color: #00FFCC; font-weight: 900; font-size: 1.4rem; text-shadow: 0px 0px 8px rgba(0,255,204,0.3);">
                    {samlet_odds:.2f}
                </span>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
