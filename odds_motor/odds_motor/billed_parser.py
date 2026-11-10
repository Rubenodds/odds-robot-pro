import streamlit as st
from PIL import Image
from historik import gem_data

def vis_billed_scanner():
    uploadet_fil = st.file_uploader("Upload kupon-screenshot (PNG, JPG):", type=["png", "jpg", "jpeg"], key="scan_up")
    
    if uploadet_fil:
        billede = Image.open(uploadet_fil)
        st.image(billede, caption="Indlæst kupon (Afventer godkendelse)", use_container_width=True)
        
        st.write("### 🔍 Detekterede kampe & rettelser")
        kampe_tekst = st.text_input("Ret eller tilføj kampe på kuponen:", value="Kamp 1 vs Kamp 2 (1)")
        odds_val = st.number_input("Samlet kupon-odds:", min_value=1.01, value=12.50, step=0.50)
        indsats_val = st.number_input("Indsats i kr. (Standard 100 kr.):", min_value=1.0, value=100.0, step=10.0)
        
        if st.button("🚀 SPILLET (Send til statistik & Supabase)", type="primary", key="btn_spillet_billede"):
            gemt = gem_data.gem_kupon_i_historik(
                ["Visuel Kupon"], [kampe_tekst], odds_val, odds_val, odds_val, "Agnostisk", 5, indsats_val
            )
            if gemt:
                st.success("✓ Kuponen er markeret som SPILLET og gemt permanent i din statistik!")
                st.rerun()
            else:
                st.error("❌ Kunne ikke gemme i Supabase. Tjek dine Secrets.")
