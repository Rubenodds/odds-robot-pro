import requests
import streamlit as st

@st.cache_data(ttl=1800, show_spinner=False)
def hent_stadion_vejr(by_navn):
    """
    Henter ægte vejrudsigt (vind m/s, temperatur, regn) via Open-Meteo (gratis, ingen API-nøgle).
    Bruges til at justere sandsynlighed for mål, hjørnespark og målspark.
    """
    if not by_navn:
        return None
    try:
        geo = requests.get(
            f"https://open-meteo.com{by_navn}&count=1&language=da&format=json",
            timeout=4,
        ).json()
        results = geo.get("results")
        if not results:
            return None
        lat, lon = results["latitude"], results["longitude"]
        vejr = requests.get(
            f"https://open-meteo.com{lat}&longitude={lon}&current=temperature_2m,precipitation,wind_speed_10m&wind_speed_unit=ms",
            timeout=4,
        ).json().get("current", {})

        vind = float(vejr.get("wind_speed_10m", 0.0))
        temp = float(vejr.get("temperature_2m", 10.0))
        regn = float(vejr.get("precipitation", 0.0))

        effekt = "Normalt spilvejr"
        if vind >= 9.0 or regn >= 1.5:
            effekt = "🌬️ Kraftig vind/regn (Flere målspark/hjørne, færre lange mål)"
        return {"temp": temp, "vind": vind, "regn": regn, "effekt": effekt}
    except Exception:
        return None


def analyser_kamp_kontekst(comp, hjemme_hold, ude_hold):
    """
    Udtrækker ægte form (hjemme/ude), H2H-historik, dommer og stadionvejr fra kampdata.
    Returnerer en samlet intelligens-pakke samt en matematisk justeringsfaktor.
    """
    # 1. Dommer (hvis offentliggjort i kampens officials-liste)
    dommer = "Ikke offentliggjort endnu"
    for off in comp.get("officials", []):
        if "referee" in str(off.get("position", {}).get("name", "")).lower() or off.get("displayName"):
            dommer = off.get("displayName", dommer)
            break

    # 2. Hjemme- og Udeform (udtrækkes fra competitors records)
    hj_form, ud_form = "Ingen formdata", "Ingen formdata"
    for c in comp.get("competitors", []):
        recs = c.get("records", [])
        form_str = next((r.get("summary") for r in recs if r.get("type") in ("total", "home", "road")), None)
        if c.get("homeAway") == "home" and form_str:
            hj_form = form_str
        elif c.get("homeAway") == "away" and form_str:
            ud_form = form_str

    # 3. Stadionby -> Vejr & Vind
    venue = comp.get("venue", {})
    by_navn = venue.get("address", {}).get("city") or hjemme_hold
    vejr_info = hent_stadion_vejr(by_navn)

    # 4. H2H-notat fra event-detaljer (hvis tilgængelig)
    h2h_tekst = "H2H synkroniseres ved kampanalyse"
    notes = comp.get("notes", [])
    if notes and isinstance(notes, list):
        h2h_tekst = notes.get("headline", h2h_tekst)

    # Matematisk justering baseret på vind/vejr (kun ægte målte værdier)
    justering_pct = 0.0
    if vejr_info and vejr_info["vind"] >= 10.0:
        justering_pct -= 2.5  # Høj vind øger uforudsigelighed på direkte spil

    return {
        "dommer": dommer,
        "hj_form": hj_form,
        "ud_form": ud_form,
        "h2h": h2h_tekst,
        "vejr": vejr_info,
        "justering_pct": justering_pct,
    }
