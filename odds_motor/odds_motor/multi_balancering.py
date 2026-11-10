import streamlit as st
from historik import gem_data

def beregn_lag_holder_odds(min_odds, max_odds, sikret_odds_produkt):
    """Beregner baglæns det nødvendige værdi-odds for at ramme det ønskede odds-lag."""
    maal_odds = round((min_odds + max_odds) / 2, 2)
    if sikret_odds_produkt <= 0:
        return maal_odds, 1.0
    noedvendigt_odds = round(maal_odds / sikret_odds_produkt, 2)
    return maal_odds, noedvendigt_odds

def gem_balanceret_kupon(kampe_liste, min_o, max_o, maal_odds, stjerner=5):
    """Sender den balancerede kupon direkte til Supabase Cloud via historik-modulet."""
    strategi_tekst = [f"Balanceret-Lag ({min_o}-{max_o})"]
    return gem_data.gem_kupon_i_historik(
        kampe_liste,
        strategi_tekst,
        maal_odds,
        maal_odds * 0.96,
        maal_odds * 0.93,
        "Agnostisk (Visuel)",
        stjerner
    )
