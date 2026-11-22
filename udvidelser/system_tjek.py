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
                    har_dommer_txt = "Ikke offentliggjort" in kode or "hent_dommer" in kode
                    rapport.append({
                        "fil": sti,
                        "tegn": len(kode),
                        "funktioner": funk,
                        "dommer_ref": har_dommer_txt,
                        "fejl": "",
                    })
                except Exception as e:
                    rapport.append({"fil": sti, "tegn": 0, "funktioner": [], "dommer_ref": False, "fejl": str(e)})
    return rapport


def vis_system_tjek(hj="Osasuna", ud="Málaga"):
    with st.expander("🔧 Systemtjek & Live Arkitektur-kort (Kun til udvikling)", expanded=False):
        rapport = _scan_repo()
        fejl_filer = [r for r in rapport if r["fejl"]]
        if fejl_filer:
            for ff in fejl_filer:
                st.error(f"Syntaksfejl i {ff['fil']}: {ff['fejl']}")
        else:
            st.success(f"Alle {len(rapport)} Python-filer er syntaks-ok!")

        st.markdown("**Filer der styrer dommer-tekst:**")
        for r in rapport:
            if r["dommer_ref"]:
                st.code(f"{r['fil']} ({r['tegn']} tegn) -> Funktioner: {', '.join(r['funktioner'])}")

        if st.button("🧪 Test live dommer-kald nu", key="btn_test_dommer_sys"):
            try:
                from odds_motor import dommer_intelligens as di
                d = di.hent_dommer(hj, ud)
                eff, txt = di.dommer_effekt(d, hj=hj, ud=ud)
                st.info(f"Resultat for {hj} vs {ud}: dommer='{d}' | effekt={eff} | tekst='{txt}'")
            except Exception:
                st.error(traceback.format_exc())

        kort = "\n".join(f"- {r['fil']} ({r['tegn']}t): {', '.join(r['funktioner'])}" for r in rapport)
        st.text_area("📋 Kopiér dette arkitektur-kort til AI ved ny chat:", kort, height=160)
