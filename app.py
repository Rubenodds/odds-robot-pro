import streamlit as st
import sys
import os

# Tvinger Python til at søge i ALLE undermapper i projektet efter filerne
root_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_path)
for root, dirs, files in os.walk(root_path):
    for d in dirs:
        sys.path.append(os.path.join(root, d))

# DE FEJLSIKREDE IMPORTS (Nu uden mapperelaterede præfikser)
try:
    from dansk_tid import hent_dansk_tid
except ModuleNotFoundError:
    from undermapper.dansk_tid import hent_dansk_tid

try:
    from hent_kampe import hent_dagens_kampprogram
except ModuleNotFoundError:
    from undermapper.hent_kampe import hent_dagens_kampprogram

try:
    from resultat_tjekker import tjek_og_opdater_resultater
except ModuleNotFoundError:
    from undermapper.resultat_tjekker import tjek_og_opdater_resultater

try:
    from Kupon_Scanner import scan_kupon_billede
except ModuleNotFoundError:
    from undermapper.Kupon_Scanner import scan_kupon_billede

try:
    from historik import gem_data
except ModuleNotFoundError:
    def gem_data(data):
        st.info("Historik gemmes direkte i Supabase Cloud...")
        return True
