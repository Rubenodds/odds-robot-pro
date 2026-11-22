import ast
import os
import traceback
import streamlit as st


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


def _uddrag(sti, soegeord=("dommer", "official", "Ikke offentliggjort")):
    if not os.path.exists(sti):
        return ""
    ud = []
    with open(sti, "r", encoding="utf-8") as fp:
        for nr, linje in enumerate(fp, 1):
            if any(o.lower() in linje.lower() for o in soegeord):
                ud.append(f"L{nr}: {linje.rstrip()}")
    return "\n".join(ud[:25])


def vis_system_tjek(hj="Liverpool", ud="Manchester City"):
    with st.expander("🔧 Systemtjek & Live Arkitektur-kort (Kun til udvikling)", expanded=True):
        rapport = _scan_repo()
        for ff in [r for r in rapport if r["fejl"]]:
            st.error(f"Syntaksfejl i {ff['fil']}: {ff['fejl']}")

        if st.button("🧪 Test live dommer-kald nu", key="btn_test_dommer_sys"):
            try:
                from odds_motor import dommer_intelligens as di
                d = di.hent_dommer(hj, ud)
                eff, txt = di.dommer_effekt(d, hj=hj, ud=ud)
                st.session_state["sys_dommer_test"] = f"{hj} vs {ud} -> dommer='{d}' | effekt={eff} | tekst='{txt}'"
            except Exception:
                st.session_state["sys_dommer_test"] = traceback.format_exc()

        if "sys_dommer_test" in st.session_state:
            st.info(st.session_state["sys_dommer_test"])

        for f_sti in ("odds_motor/kamp_intelligens.py", "odds_motor/manuel_hjaelp.py"):
            snit = _uddrag(f_sti)
            if snit:
                st.caption(f"Dommer-linjer i {f_sti}:")
                st.code(snit)

        kort = "\n".join(f"- {r['fil']} ({r['tegn']}t): {', '.join(r['funktioner'])}" for r in rapport)
        st.text_area("📋 Kopiér dette arkitektur-kort til AI:", kort, height=140)
