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
        return "💡 **Hvorfor?** Verificeret bookmaker-marked."
    ctx = _hent_ekstra_ctx(k)
    k["ctx"] = ctx
    hj, ud = k.get("hj", "Hjemmehold"), k.get("ud", "Udehold")
    valgt = str(k.get("valgt_hold") or hj)
    modst = ud if valgt.lower().strip() == hj.lower().strip() else hj
    odds = float(k.get("b365") or k.get("odds") or 0.0)
    imp = round(100.0 / max(1.01, odds), 1) if odds > 1.0 else 0.0

    hf, uf = str(ctx.get("hj_form") or ""), str(ctx.get("ud_form") or "")
    valgt_form = uf if valgt == ud else hf
    modst_form = hf if valgt == ud else uf
    vw, mw = valgt_form.count("W"), modst_form.count("W")

    dele = []
    if valgt_form and modst_form and vw > mw:
        dele.append(f"**{valgt}** har bedre dokumenteret form ({_form_til_dansk(valgt_form)}) end {modst} ({_form_til_dansk(modst_form)})")
    elif odds > 1.0:
        dele.append(f"Verificeret bookmaker-odds **{odds}** på **{valgt}** ({imp}% markedssandsynlighed)")
    else:
        dele.append(f"Ingen verificerede bookmaker-odds fundet på **{valgt}** i API'et")

    if k.get("api_kilde"):
        dele.append(f"kilde: {k['api_kilde']}")

    meta_dele = []
    dommer = str(ctx.get("dommer") or "").strip()
    if dommer and "ikke" not in dommer.lower():
        meta_dele.append(f"🟨 **Dommer:** {dommer}")
    else:
        meta_dele.append("🟨 **Dommer:** Ikke offentliggjort i API endnu")

    h2h = str(ctx.get("h2h") or "").strip()
    if h2h:
        meta_dele.append(f"⚔️ **H2H:** {h2h}")
    else:
        meta_dele.append(f"📈 **Form (5 kampe):** {hj} {_form_til_dansk(hf)} vs {ud} {_form_til_dansk(uf)}")

    hvorfor_linje = "💡 **Fakta:** " + ". ".join(dele) + "."
    return f"{hvorfor_linje}\n\n{' | '.join(meta_dele)}"

def _hent_kun_rigtigt_marked(k, maal_pr_kamp, kun_res=False):
    # 1. Hent rigtige markeder fra The Odds API via marked_motor
    try:
        from udvidelser.marked_motor import hent_reelle_muligheder
        muligheder, kilde, _ = hent_reelle_muligheder({
            "id": k.get("id", ""),
            "liga_kode": (k.get("ctx") or {}).get("slug") or k.get("liga_kode", "eng.1"),
            "hjemme": k.get("hj", ""),
            "ude": k.get("ud", ""),
            "odds_api_id": k.get("odds_api_id", ""),
        })
        valgt = str(k.get("valgt_hold") or "").lower().strip()
        if valgt:
            hold_matchet = [m for m in muligheder if valgt in str(m.get("valg", "")).lower()]
            if hold_matchet:
                muligheder = hold_matchet
        if kun_res:
            muligheder = [m for m in muligheder if any(x in m["marked"].lower() for x in ("kampvinder", "dobbeltchance", "uafgjort", "handicap"))]
        gyldige = [m for m in muligheder if float(m.get("b365") or 0) > 1.01]
        if gyldige:
            bedst = min(gyldige, key=lambda m: abs(float(m["b365"]) - maal_pr_kamp))
            return f"[{bedst['marked']}] {bedst['valg']}", round(float(bedst["b365"]), 2), kilde
    except Exception:
        pass

    # 2. Hent evt. verificeret 1X2-basisodds direkte fra kamp-objektet (uden at opfinde noget)
    direkte_odds = float(k.get("b365") or k.get("odds") or 0.0)
    if direkte_odds > 1.01:
        valgt = k.get("valgt_hold") or k.get("hj", "Hjemmehold")
        return f"{valgt} vinder (1X2)", round(direkte_odds, 2), "Kampfeed"

    return None, None, ""

def _sikr_kamp(k, maal_pr_kamp=1.85, kun_res=False):
    ny = dict(k) if isinstance(k, dict) else {}
    ny["ctx"] = _hent_ekstra_ctx(ny)
    valg, odds, kilde = _hent_kun_rigtigt_marked(ny, maal_pr_kamp, kun_res)
    if not valg or not odds:
        return None
    ny["api_kilde"] = kilde
    pct = round(100.0 / max(1.01, odds), 1)
    ny.setdefault("hj", ny.get("hjemme", "Hjemmehold"))
    ny.setdefault("ud", ny.get("ude", "Udehold"))
    ny.setdefault("liga", "Øvrige")
    ny.setdefault("start", "I dag")
    ny.update({
        "spil": valg,
        "odds": odds,
        "b365": odds,
        "unibet": float(ny.get("unibet") or odds),
        "ds": float(ny.get("ds") or odds),
        "kombinationer": [valg],
        "vinderchance_pct": pct,
        "pct": pct,
    })
    ny["stj"] = max(1, min(5, int(round((pct * odds) / 20.0))))
    ny["flm"] = max(1, min(5, int(round((100.0 - pct) / 17.0))))
    return ny

def byg_forslag(maal_liste, maks_odds=10.0, kun_res=False):
    liste = list(maal_liste or [])
    if not liste:
        return {"kampe": [], "total_odds": 1.0, "odds": 1.0}
    maal_total = max(1.15, float(maks_odds))
    maal_pr_kamp = maal_total ** (1.0 / len(liste))
    forslag, samlet = [], 1.0
    for k in liste:
        ny = _sikr_kamp(k, maal_pr_kamp, kun_res)
        if ny is not None:
            forslag.append(ny)
            samlet *= ny["b365"]
    return {"kampe": forslag, "total_odds": round(samlet, 2), "odds": round(samlet, 2)}
