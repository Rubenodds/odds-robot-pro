import streamlit as st
import traceback

def vis_manuel_scanner():
    st.success("✅ FORBINDELSE OPRETTET TIL MANUEL_SCANNER.PY!")
    try:
        from odds_motor import autopilot_scanner as ap
        from odds_motor import byg_kupon, liga_favoritter
        from historik import gem_data
        st.write("Alle imports OK!")
    except Exception:
        st.error("Import-fejl fundet:")
        st.code(traceback.format_exc())
