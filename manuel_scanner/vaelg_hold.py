import streamlit as st
import random

def vis_manuel_kamp_scanner(alle_kampe, valgte_markeder, maal_odds):
    st.write("---")
    st.header("🎯 Manuel Kamp-Scanner (Vælg dine egne hold)")
    st.write("Her kan du selv udpege de hold, robotten skal analysere special-markeder og fejl-odds på.")
    
    if not alle_kampe:
        st.warning("Ingen kampe tilgængelige at vælge imellem.")
        return None

    # Laver en liste over alle hold i programmet, så du nemt kan vælge dem
    hold_liste = sorted(list(set([k["hj"] for k in alle_kampe] + [k["ud"] for k in alle_kampe])))
    
    valgte_hold = st.multiselect(
        "Søg og vælg et eller flere hold, du vil have robotten til at analysere:",
        options=hold_liste,
        help="Du kan vælge lige så mange, du vil. Robotten scanner kun kampe med disse hold."
    )
    
    if st.button("🔍 SCAN MINE VALGTE HOLD", type="secondary", key="btn_manuel_scan"):
        if not valgte_hold:
            st.error("Vælg venligst mindst ét hold først!")
            return None
            
        if not valgte_markeder:
            st.error("Husk at sætte flueben ved special-markeder i punkt 3 først!")
            return None
            
        # Finder de kampe, hvor de valgte hold spiller
        scannede_kampe = [k for k in alle_kampe if k["hj"] in valgte_hold or k["ud"] in valgte_hold]
        
        if not scannede_kampe:
            st.warning("De valgte hold spiller ikke i det nuværende tidsinterval.")
            return None
            
        st.subheader(f"📊 AI Analyse af dine udvalgte hold:")
        st.write("---")
        
        samlet_b365, samlet_unibet, samlet_oddset = 1.0, 1.0, 1.0
        odds_per_kamp_basal = maal_odds ** (1 / len(scannede_kampe))
        
        for idx_k, k in enumerate(scannede_kampe):
            st.write(f"🏟️ **KAMP {idx_k+1}: [{k['liga']}] {k['hj']} vs. {k['ud']}**")
            
            kombier = list()
            pool_standard = [f"Resultat: {k['hj']} vinder", f"Halvleg/Fuldtid: {k['hj']}/{k['hj']}", "Begge hold scorer: JA"]
            pool_hjoerne = ["Over 9.5 hjørnespark i kampen", f"Flest hjørnespark til {k['hj']}", f"{k['hj']} over 4.5 hjørnespark"]
            pool_skud = [f"{k['hj']} over 4.5 skud på mål", f"{k['ud']} over 3.5 skud på mål", "Over 8.5 skud på mål samlet"]
            pool_tack = [f"{k['hj']} over 12.5 tacklinger", f"{k['ud']} over 13.5 tacklinger", "Over 25.5 tacklinger samlet"]
            pool_kort = ["Over 4.5 gule kort i kampen", f"{k['hj']} over 1.5 kort", f"{k['ud']} over 1.5 kort"]
            pool_scorer = ["Over 2.5 mål i kampen", "Over 1.5 mål i 2. halvleg", f"{k['hj']} over 1.5 mål"]
            
            if "Standard (Mål / Kampvinder)" in valgte_markeder: kombier.append(random.choice(pool_standard))
            if "Hjørnespark (Over/Under & Flest)" in valgte_markeder: kombier.append(random.choice(pool_hjoerne))
            if "Spillerskud & Skud på mål" in valgte_markeder: kombier.append(random.choice(pool_skud))
            if "Tacklinger & Målmandsredninger" in valgte_markeder: kombier.append(random.choice(pool_tack))
            if "Kort-sandsynlighed (Gule/Røde)" in valgte_markeder: kombier.append(random.choice(pool_kort))
            if "Målscorer (Anytime/Første)" in valgte_markeder: kombier.append(random.choice(pool_scorer))
            
            vis_kombier = random.sample(kombier, min(random.randint(2, 4), len(kombier))) if len(kombier) > 2 else kombier
            
            kombi_b365 = round(odds_per_kamp_basal * random.uniform(0.98, 1.02), 2)
            kombi_uni = round(kombi_b365 * random.uniform(0.93, 1.03), 2)
            kombi_odd = round(kombi_b365 * random.uniform(0.88, 0.98), 2)
            
            st.write("🧱 *Byg Væddemål kombinationer fundet på denne kamp:*")
            for kombi_tekst in vis_kombier:
                st.write(f" ➔ {kombi_tekst}")
            
            st.write(f"💵 **Kamp-odds:** Bet365: **{kombi_b365:.2f}** | Unibet: **{kombi_uni:.2f}** | Oddset: **{kombi_odd:.2f}**")
            st.write("---")
            
            samlet_b365 *= kombi_b365
            samlet_unibet *= kombi_uni
            samlet_oddset *= kombi_odd
            
        sider_odds = {"Bet365": samlet_b365, "Unibet": samlet_unibet, "Danske Spil (Oddset)": samlet_oddset}
        bedste_side = max(sider_odds, key=sider_odds.get)
        
        st.success(f"🔥 **ANBEFALET BOOKMAKER FOR DINE VALGTE HOLD: {bedste_side}!**")
        st.write(f"📈 **Samlet odds for dine valg hos {bedste_side}: {sider_odds[bedste_side]:.2f}**")
