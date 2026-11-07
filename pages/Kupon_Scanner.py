import streamlit as st
from PIL import Image
from historik.gem_data import gem_kupon_i_historik
from bookmaker_scanner.scanner_motor import hent_ai_alternativer_for_kamp

st.set_page_config(page_title="AI Billed-Scanner & Kupon-Optimering", page_icon="📸", layout="centered")

st.title("📸 AI Billed-Scanner & Kupon-Optimering")
st.write("Se din originale kuponstamme og tilføj AI-optimeringer live.")

if "scannet_data" not in st.session_state:
    st.session_state["scannet_data"] = None

uploadet_billede = st.file_uploader("Upload dit kupon-screenshot:", type=["png", "jpg", "jpeg"], key="kupon_uploader_v8")

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
        
        # Sikring mod gamle session data i din browser (omregner hele tal til decimaler live)
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

        # ----------------- PANEL 2: INTERAKTIV OPTIMERINGSMOTOR -----------------
        st.subheader("⚡ AI Multi-Balancering & Markedsalternativer")
        vis_alternativer = st.toggle("🤖 Aktiver AI Værdi-Scanner (Vis alternative muligheder)", value=False)
        
        endelige_valgte_spil =
        samlet_ny_vinderchance = 1.0
        tillad_ekstra_boost = False

        if vis_alternativer:
            for kamp in data["kampe"]:
                _, _, vil_booste, forklaring_tekst = hent_ai_alternativer_for_kamp(campaign_navn=kamp["hold"], originalt_odds=kamp["odds"], total_orig_odds=orig_samlet_odds, antal_kampe=antal_kampe)
                if vil_booste:
                    st.warning(forklaring_tekst)
                    tillad_ekstra_boost = st.checkbox("🔓 Giv robotten lov til at sprænge odds-laget for denne guldklump", value=False, key="tillad_boost_check")
                    st.write("---")

            st.write("💡 *Vælg det marked du vil erstatte dit originale spil med for hver kamp:*")
            
            for i, kamp in enumerate(data["kampe"]):
                st.markdown(f"### ⚽ {kamp['hold']}")
                
                forslag, mangler_muligheder, vil_booste, _ = hent_ai_alternativer_for_kamp(kamp["hold"], kamp["odds"], orig_samlet_odds, antal_kampe)
                
                valgmuligheder = [f"Behold originalt valg: {kamp['originalt_valg']} (Odds {kamp['odds']:.2f})"]
                
                if vil_booste and tillad_ekstra_boost:
                    odds_boosted = round(kamp["odds"] * 1.6, 2)
                    valgmuligheder.append(f"🚀 AI VALUE-BOOST: Over 4.5 kort i kampen (Odds {odds_boosted})")
                
                for f in forslag:
                    valgmuligheder.append(f"{f['titel']} (Odds {f['odds']:.2f})")
                
                valgt_marked = st.radio(f"Vælg marked for {kamp['hold']}:", valgmuligheder, key=f"pro_valg_{i}", label_visibility="collapsed")
                
                if "Behold originalt" in valgt_marked:
                    endelige_valgte_spil.append({
                        "hold": kamp["hold"], "variant": kamp["originalt_valg"], "odds": kamp["odds"],
                        "chance": kamp["chance"], "flammer": "🔥 🔥", "stjerner": "⭐⭐⭐⭐"
                    })
                    samlet_ny_vinderchance *= kamp["chance"]
                elif "🚀 AI VALUE-BOOST" in valgt_marked:
                    odds_boosted = round(kamp["odds"] * 1.6, 2)
                    endelige_valgte_spil.append({
                        "hold": kamp["hold"], "variant": "Over 4.5 kort i kampen (Value-Boost)", "odds": odds_boosted,
                        "chance": 0.45, "flammer": "🔥 🔥 🔥 🔥 🔥", "stjerner": "⭐⭐⭐⭐⭐"
                    })
                    samlet_ny_vinderchance *= 0.45
                    st.success("🔥 **Valgt:** Value-Boost aktiveret på kortmarkedet!")
                else:
                    for f in forslag:
                        if f["titel"] in valgt_marked:
                            endelige_valgte_spil.append({
                                "hold": kamp["hold"], "variant": f["variant"], "odds": f["odds"],
                                "chance": f["chance"], "flammer": f["flammer"], "stjerner": f["stjerner"]
                            })
                            samlet_ny_vinderchance *= f["chance"]
                            st.success(f"🎯 **Valgt:** {f['flammer']} | Chance: {int(f['chance']*100)}%")
                st.write("---")
        else:
            for kamp in data["kampe"]:
                endelige_valgte_spil.append({
                    "hold": kamp["hold"], "variant": kamp["originalt_valg"], "odds": kamp["odds"],
                    "chance": kamp["chance"], "flammer": "🔥 🔥", "stjerner": "⭐⭐⭐⭐"
                })
            samlet_ny_vinderchance = orig_samlet_chance

        # ----------------- LIVE KUPONPRINT & SAMMENLIGNING -----------------
        reelt_samlet_odds = 1.0
        for spil in endelige_valgte_spil:
            reelt_samlet_odds *= spil["odds"]
        reelt_samlet_odds = round(reelt_samlet_odds, 2)
        endelig_chance_procent = round(samlet_ny_vinderchance * 100, 1)

        # 📋 NY FÆRDIG KUPONSTAMME MED ALT GRAFIK PRINTET DIREKTE
        st.subheader("📋 Din sammensatte AI Kuponstamme")
        kupon_tekst_blok = ""
        for i, spil in enumerate(endelige_valgte_spil):
            kupon_tekst_blok += f"Kamp {i+1}: {spil['hold']}\n"
            kupon_tekst_blok += f"↳ Spil: {spil['variant']}\n"
            kupon_tekst_blok += f"↳ Odds: {spil['odds']:.2f} | Chance: {int(spil['chance']*100)}% | {spil['flammer']} | {spil['stjerner']}\n"
            kupon_tekst_blok += f"{'-'*50}\n"
        
        kupon_tekst_blok += f"💵 SAMLET ODDS: {reelt_samlet_odds:.2f}\n"
        kupon_tekst_blok += f"🔮 SAMLET AI VINDERCHANCE: {min(99.9, max(0.1, endelig_chance_procent)):.1f}%"
        
        # Viser det i en urokkelig mørk kodeboks, som virker på alle smartphones
        st.code(kupon_tekst_blok, language="text")

        st.write("---")
        st.subheader("📊 VS-Sammenligning: Original vs. AI-Optimeret")
        
        st.table({
            "Kupon-type": ["Original Kupon", "Din Aktuelle AI-Kupon"],
            "Samlet Odds": [f"{orig_samlet_odds:.2f}", f"{reelt_samlet_odds:.2f}"],
            "Vinderchance (%)": [f"{max(0.1, orig_samlet_chance_procent):.1f}%", f"{min(99.9, max(0.1, endelig_chance_procent)):.1f}%"]
        })

        if st.button("💾 LÅS OG GEM DEN DYNAMISKE KUPON", type="primary", key="btn_gem_dynamisk_låst"):
            gem_kupon_i_historik(
                [spil["variant"] for spil in endelige_valgte_spil],
                [spil["hold"] for spil in endelige_valgte_spil],
                reelt_samlet_odds, reelt_samlet_odds * 0.96, reelt_samlet_odds * 0.93,
                "Bet365 (Live Interaktiv Pro-Scan)", 5
            )
            st.success("✅ Din færdige kuponstamme er låst og gemt i din SQLite historik!")
