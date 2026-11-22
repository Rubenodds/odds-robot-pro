import ast
import os
import traceback
import streamlit as st

VIS_BETA_TJEK = True


def _scan_repo():
    rapport = []
    for rod, mapper, filer in os.walk("."):
        mapper[:] = [m for m in mapper if not m.startswith(".") and m != "__pycache__"]
        for f in sorted(filer):
            if f.endswith(".py"):
                sti = os.path.join(rod, f).lstrip("./")
                try:
                    with open(sti, "r", encoding="utf-8") as fp:
                        kode = fp.read()
                    trae = ast.parse(kode)
                    funk = [n.name for n in trae.body if isinstance(n, ast.FunctionDef)]
                    rapport.append({"fil": sti, "tegn": len(kode), "funktioner": funk, "fejl": ""})
                except Exception as e:
                    rapport.append({"fil": sti, "tegn": 0, "funktioner": [], "fejl": str(e)})
    return rapport


def vis_system_tjek():
    if not VIS_BETA_TJEK:
        return
    with st.expander("🔧 Beta Systemtjek & Arkitektur-kort", expanded=False):
        rapport = _scan_repo()
        for ff in [r for r in rapport if r["fejl"]]:
            st.error(f"Syntaksfejl i {ff['fil']}: {ff['fejl']}")

        c1, c2 = st.columns(2)
        h_test = c1.text_input("Hjemmehold", "Brøndby IF", key="sys_hj")
        u_test = c2.text_input("Udehold", "FC Midtjylland", key="sys_ud")

        if st.button("🧪 Test dommer-kilder", key="btn_test_dommer_sys"):
            try:
                from odds_motor import dommer_intelligens as di
                e = di._espn_dommer(h_test, u_test)
                w = di._web_dommer(h_test, u_test)
                samlet = di.hent_dommer(h_test, u_test)
                st.session_state["sys_dom_res"] = f"ESPN='{e}' | Web='{w}' | Samlet='{samlet}'"
            except Exception:
                st.session_state["sys_dom_res"] = traceback.format_exc()

        if "sys_dom_res" in st.session_state:
            st.info(st.session_state["sys_dom_res"])

        kort = "\n".join(f"- {r['fil']} ({r['tegn']}t): {', '.join(r['funktioner'])}" for r in rapport)
        st.text_area("📋 Live Arkitektur-kort:", kort, height=130)
