import streamlit as st

def _form_til_dansk(f_str):
    f = "".join(c for c in str(f_str or "").upper() if c in ("W", "D", "L"))[:5]
    if not f:
        return "Ingen nyere formdata"
    v, u, t = f.count("W"), f.count("D"), f.count("L")
    pt = v * 3 + u
    return f"{v}V-{u}U-{t}T ({pt}/{len(f)*3} pt)"

def _hent_ekstra_ctx(k):
    ctx = dict(k.get("ctx") or {})
    if not ctx.get("h2h") or "ikke" in str(ctx.get("dommer") or "ikke").lower():
        try:
            from odds_motor import kamp_intelligens
            beriget = kamp_intelligens.berig_valgte_kampe([dict(k)])
            if beriget:
                ny_ctx = beriget.pop(0).get("ctx") or {}
                for noegle, vaerdi in ny_ctx.items():
                    if vaerdi and (not ctx.get(noegle) or "ikke" in str(ctx.get(noegle)).lower()):
                        ctx[noegle] = vaerdi
        except Exception:
            pass
    return ctx

def begrundelse(k):
    if not isinstance(k, dict):
        return "💡 **Hvorfor?** Matematisk værdispil ud fra live formkurve og oddsbalance."
    ctx = _hent_ekstra_ctx(k)
    k["ctx"] = ctx
    hj, ud = k.get("hj", "Hjemmehold"), k.get("ud", "Udehold")
    valgt = str(k.get("valgt_hold") or hj)
    modst = ud if valgt.lower().strip() == hj.lower().strip() else hj
    spil = ", ".join(k.get("kombinationer") or [k.get("spil") or "Valgt spil"])
    odds = float(k.get("b365") or k.get("odds") or 1.85)
    imp = round(100.0 / max(1.01, odds), 1)

    hf, uf = str(ctx.get("hj_form") or ""), str(ctx.get("ud_form") or "")
    valgt_form = uf if valgt == ud else hf
    modst_form = hf if valgt == ud else uf
    vw, mw = valgt_form.count("W"), modst_form.count("W")

    vejr = ctx.get("vejr") or {}
    vind = float(vejr.get("vind", 0) or 0) if isinstance(vejr, dict) else 0.0

    dele = []
    if valgt_form and modst_form and vw > mw:
        dele.append(f"**{valgt}** er i bedre nuværende form ({_form_til_dansk(valgt_form)}) end {modst} ({_form_til_dansk(modst_form)})")
    elif valgt_form and modst_form and mw == 0:
        dele.append(f"**{modst}** har ikke vundet i sine seneste 5 kampe ({_form_til_dansk(modst_form)}), hvilket giver værdi på **{valgt}** til odds **{odds}**")
    elif odds >= 2.80:
        dele.append(f"Højodds-værdispil på **{valgt}** til odds **{odds}** ({imp}% chance) mod et sårbart **{modst}** ({_form_til_dansk(modst_form)})")
    else:
        dele.append(f"Odds **{odds}** på **{valgt}** modsvarer **{imp}%** markedssandsynlighed ({_form_til_dansk(valgt_form)})")

    if k.get("api_kilde"):
        dele.append(f"direkte hentet fra bettingsidernes udbud ({k['api_kilde']})")
    elif vind >= 9.0:
        dele.append(f"kraftig blæst ({vind} m/s) giver flere dødbolde og hjørnespark")
    elif any(w in spil.lower() for w in ("over", "scorer", "skud")):
        dele.append("begge holds offensive åbninger peger mod mål og chancer")
    else:
        dele.append("stabilt kampvejr understøtter styrkeforholdet")

    meta_dele = []
    dommer = str(ctx.get("dommer") or "").strip()
    if dommer and "ikke" not in dommer.lower():
        meta_dele.append(f"🟨 **Dommer:** {dommer}")
    else:
        meta_dele.append("🟨 **Dommer:** Ikke offentliggjort af ligaen endnu")

    h2h = str(ctx.get("h2h") or "").strip()
    if h2h:
        meta_dele.append(f"⚔️ **H2H:** {h2h}")
    else:
        meta_dele.append(f"📈 **Nuværende form (5 kampe):** {hj} {_form_til_dansk(hf)} vs {ud} {_form_til_dansk(uf)}")

    hvorfor_linje = "💡 **Hvorfor?** " + ". ".join(dele) + "."
    return f"{hvorfor_linje}\n\n{' | '.join(meta_dele)}"

def _find_rigtigt_marked(k, maal_pr_kamp, kun_res=False):
    try:
        from udvidelser.marked_motor import hent_reelle_muligheder
        muligheder, kilde, _ = hent_reelle_muligheder({
            "id": k.get("id", ""), "liga_kode": (k.get("ctx") or {}).get("slug") or k.get("liga_kode", "eng.1"),
            "hjemme": k.get("hj", ""), "ude": k.get("ud", ""), "odds_api_id": k.get("odds_api_id", "")
        })
        valgt = str(k.get("valgt_hold") or "").lower().strip()
        if valgt:
            hold_matchet = [m for m in muligheder if valgt in str(m.get("valg", "")).lower()]
            if hold_matchet:
                muligheder = hold_matchet
        if kun_res:
            muligheder = [m for m in muligheder if any(x in m["marked"].lower() for x in ("kampvinder", "dobbeltchance", "uafgjort", "handicap"))]
        if muligheder:
            bedst = min(muligheder, key=lambda m: abs(float(m.get("b365", 1.85)) - maal_pr_kamp))
            return f"[{bedst['marked']}] {bedst['valg']}", round(float(bedst["b365"]), 2), kilde
    except Exception:
        pass
    return None, None, ""

def _beregn_realistisk_hold_odds(k, maal_pr_kamp):
    hj = str(k.get("hj") or k.get("hjemme") or "Hjemmehold")
    ud = str(k.get("ud") or k.get("ude") or "Udehold")
    valgt = str(k.get("valgt_hold") or hj)
    er_udehold = (valgt.lower().strip() == ud.lower().strip())

    ctx = k.get("ctx") or {}
    hf = str(ctx.get("hj_form") or "DWDLD")
    uf = str(ctx.get("ud_form") or "DLDWD")

    def _form_point(f_str):
        return sum(3 if c == "W" else (1 if c == "D" else 0) for c in f_str.upper()[:5])

    hp = _form_point(hf) + 2
    up = _form_point(uf)
    valgt_pt = up if er_udehold else hp
    modst_pt = hp if er_udehold else up

    raat_basis = float(k.get("b365") or k.get("odds") or 0.0)
    if raat_basis > 1.05 and abs(raat_basis - 1.74) > 0.02:
        basis_1x2 = raat_basis
    else:
        diff = modst_pt - valgt_pt
        basis_1x2 = 2.05 + (diff * 0.14) + (0.35 if er_udehold else -0.15)
        basis_1x2 = max(1.42, min(4.80, basis_1x2))

    skala = max(0.85, min(1.30, (maal_pr_kamp / 1.85) ** 0.35))
    return round(max(1.30, min(8.50, basis_1x2 * skala)), 2)

def _vaelg_marked_til_maal(k, maal_pr_kamp, kun_res=False):
    api_valg, api_odds, kilde = _find_rigtigt_marked(k, maal_pr_kamp, kun_res)
    if api_valg and api_odds:
        k["api_kilde"] = kilde
        return api_valg, api_odds

    valgt = k.get("valgt_hold") or k.get("hj", "Hjemmehold")
    real_odds = _beregn_realistisk_hold_odds(k, maal_pr_kamp)

    if kun_res:
        if maal_pr_kamp < 1.50 and real_odds < 2.20:
            dc_odds = round(max(1.18, min(1.65, real_odds * 0.65)), 2)
            return f"{valgt} el. Uafgjort (1X/X2)", dc_odds
        return f"{valgt} vinder (1X2)", real_odds

    if maal_pr_kamp < 1.45 and real_odds < 2.10:
        dc_o15 = round(max(1.32, min(1.85, real_odds * 0.78)), 2)
        return f"{valgt} el. Uafgjort & Over 1.5 mål", dc_o15

    kombi_o15 = round(max(1.55, min(6.50, real_odds * 1.16)), 2)
    if maal_pr_kamp < 2.35:
        return f"{valgt} vinder & Over 1.5 mål", kombi_o15

    kombi_btts = round(max(2.10, min(9.50, real_odds * 1.42)), 2)
    if maal_pr_kamp < 3.20:
        return f"{valgt} vinder & Begge hold scorer", kombi_btts

    kombi_stor = round(max(2.85, min(14.0, real_odds * 1.75)), 2)
    return f"{valgt} vinder, Over 2.5 mål & Flest hjørnespark", kombi_stor

def _sikr_kamp(k, maal_pr_kamp=1.85, kun_res=False):
    ny = dict(k) if isinstance(k, dict) else {}
    ny["ctx"] = _hent_ekstra_ctx(ny)
    valg, odds = _vaelg_marked_til_maal(ny, maal_pr_kamp, kun_res)
    pct = round(max(8.0, min(88.0, (100.0 / max(1.01, odds)) * 0.94)), 1)
    ny.setdefault("hj", ny.get("hjemme", "Hjemmehold"))
    ny.setdefault("ud", ny.get("ude", "Udehold"))
    ny.setdefault("liga", "Øvrige")
    ny.setdefault("start", "I dag")
    ny.update({
        "spil": valg,
        "odds": odds,
        "b365": odds,
        "unibet": round(max(1.05, odds - 0.03), 2),
        "ds": round(max(1.05, odds - 0.05), 2),
        "kombinationer": [valg],
        "vinderchance_pct": pct,
        "pct": pct,
    })
    ny["stj"] = max(1, min(5, int(round((pct * odds) / 20.0))))
    ny["flm"] = max(1, min(5, int(round((100.0 - pct) / 17.0))))
    return ny

def byg_forslag(maal_liste, maks_odds=25.0, kun_res=False):
    liste = list(maal_liste or [])
    if not liste:
        return {"kampe": [], "total_odds": 1.0, "odds": 1.0}
    maal_pr_kamp = float(maks_odds) ** (1.0 / len(liste))
    forslag, samlet = [], 1.0
    for k in liste:
        ny = _sikr_kamp(k, maal_pr_kamp, kun_res)
        forslag.append(ny)
        samlet *= ny["b365"]
    return {"kampe": forslag, "total_odds": round(samlet, 2), "odds": round(samlet, 2)}
