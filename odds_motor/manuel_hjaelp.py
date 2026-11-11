import streamlit as st
from odds_motor import autopilot_scanner as ap
from odds_motor import byg_kupon
from historik import gem_data

def form_score(f):
    if not f or any(w in str(f).lower() for w in ("ingen", "ukendt")):
        return 0.0
    t = str(f).upper()
    if "W" in t or "V" in t:
        return (t.count("W") + t.count("V")) * 1.5 - (t.count("L") + t.count("T")) * 1.2
    d = [int(x) for x in t.split("-") if x.isdigit()]
    if len(d) >= 3:
        sejre, _, tab = d[:3]
        return (sejre * 1.5) - (tab * 1.2)
    return 0.0

def begrundelse(k, res=False):
    pct = float(k.get("vinderchance_pct") or k.get("pct") or 55.0)
    ctx = k.get("ctx") or {}
    hf, uf, dom, fok = str(ctx.get("hj_form", "")), str(ctx.get("ud_form", "")), str(ctx.get("dommer", "")), k.get("valgt_hold")
    dele = [f"Fokus på **{fok}** ({pct:.1f}% chance)" if fok else (f"**{k['hj']}** har statistisk overtag ({pct:.1f}%)" if pct >= 58 else (f"**{k['ud']}** stærkest ude ({pct:.1f}%)" if pct <= 44 else f"Jævnbyrdigt opgør ({pct:.1f}% chance)"))]
    if hf and uf and not any(w in (hf + uf).lower() for w in ("ingen", "ukendt")):
        dele.append(f"form {hf} mod {uf}")
    if not res and dom and not any(w in dom.lower() for w in ("afventer", "ikke offentliggjort")):
        dele.append(f"dommer {dom} trækker kort op")
    return "💡 *Begrundelse:* " + ", ".join(dele) + "."

def byg_forslag(udvalgte, maal, kun_res=False):
    try:
        hist = gem_data.hent_alle_kuponer() or []
        vundne = sum(1 for s in hist if str(s.get("status", "")).lower() in ("vundet", "won", "gevinst"))
        h_just = round(((vundne / len(hist)) - 0.5) * 6.0, 1) if (hist and vundne > 0) else 0.0
    except Exception:
        h_just = 0.0
    if not kun_res:
        try:
            kup = byg_kupon.byg_kombineret_kupon(udvalgte, ap.MARKEDER, maal)
            if isinstance(kup, dict) and kup.get("kampe"):
                for ko, uo in zip(kup["kampe"], udvalgte):
                    ko["ctx"] = uo.get("ctx", {})
                    if uo.get("valgt_hold"):
                        ko["valgt_hold"] = uo["valgt_hold"]
                    ko["begrundelse"] = begrundelse(ko, False)
                return kup
        except Exception:
            pass
    out = []
    for u in udvalgte:
        kp = dict(u)
        ctx = kp.get("ctx") or {}
        fok = kp.get("valgt_hold")
        fd = form_score(ctx.get("hj_form")) - form_score(ctx.get("ud_form"))
        cj = float(ctx.get("justering_pct", 0.0))
        st_pct = max(25.0, min(85.0, float(kp.get("pct", 55.0)) + fd + cj + h_just))
        if kun_res:
            if fok == kp["hj"] or (not fok and st_pct >= 57.0):
                cf, rp = ("2-0", round(min(24.0, st_pct * 0.28), 1)) if st_pct >= 68 else (("2-1", round(min(21.0, st_pct * 0.26), 1)) if st_pct >= 61.5 else ("1-0", round(min(19.5, st_pct * 0.25), 1)))
                f_txt = [f"Resultatspil: {kp['hj']} vinder ({cf})"]
            elif fok == kp["ud"] or (not fok and st_pct <= 45.0):
                us = 100.0 - st_pct
                cf, rp = ("0-2", round(min(22.0, us * 0.27), 1)) if us >= 66 else (("1-2", round(min(19.5, us * 0.25), 1)) if us >= 59 else ("0-1", round(min(18.0, us * 0.24), 1)))
                f_txt = [f"Resultatspil: {kp['ud']} vinder ({cf})"]
            else:
                cf, rp = ("0-0", 14.5) if abs(fd) < 1.5 and 48 <= st_pct <= 53 else ("1-1", round(15.0 + (55.0 - abs(50.0 - st_pct)) * 0.08, 1))
                f_txt = [f"Resultatspil: Uafgjort ({cf})"]
            od = round(max(4.5, min(14.0, (100.0 / max(rp, 8.0)) * 1.08)), 2)
            kp["vinderchance_pct"] = rp
        else:
            f_txt = [f"Kampvinder / DNB: {fok}" if fok else (f"Kampvinder: {kp['hj']}" if st_pct >= 58 else (f"Kampvinder: {kp['ud']}" if st_pct <= 44 else "Standard: Over 1.5 mål"))]
            if cj >= 1.5:
                f_txt.append("Hjørnespark: Over 8.5 total")
            dom = str(ctx.get("dommer", ""))
            if dom and not any(w in dom.lower() for w in ("afventer", "ikke offentliggjort")):
                f_txt.append("Kort: Over 3.5 kort")
            od = round(max(1.35, min(3.6, (100.0 / max(st_pct, 30.0)) * 1.04)), 2)
            kp["vinderchance_pct"] = round(st_pct, 1)
        kp["b365"], kp["unibet"], kp["oddset"] = od, round(od * 0.98, 2), round(od * 0.95, 2)
        kp["kombinationer"], kp["begrundelse"] = f_txt, begrundelse(kp, kun_res)
        out.append(kp)
    return {"kampe": out}
