import base64
import io
import json
import os
import re
import time
import urllib.error
import urllib.request
from PIL import Image

try:
    import streamlit as st
except Exception:
    st = None


def _hent_gemini_noegle() -> str:
    if st is not None:
        try:
            for k, v in st.secrets.items():
                if str(k).strip().upper() == "GEMINI_API_KEY" and isinstance(v, str):
                    return v.strip()
                if isinstance(v, dict):
                    for k2, v2 in v.items():
                        if str(k2).strip().upper() == "GEMINI_API_KEY" and isinstance(v2, str):
                            return v2.strip()
        except Exception:
            pass
    return os.environ.get("GEMINI_API_KEY", "").strip()


def _flet_billeder_til_et(billeder_bytes_liste: list) -> bytes:
    billeder = [Image.open(io.BytesIO(b)).convert("RGB") for b in billeder_bytes_liste]
    if len(billeder) == 1:
        buf = io.BytesIO()
        billeder.pop(0).save(buf, format="JPEG", quality=85)
        return buf.getvalue()

    maks_bredde = max(im.width for im in billeder)
    skalerede = []
    for im in billeder:
        if im.width != maks_bredde:
            ny_h = int(im.height * (maks_bredde / im.width))
            im = im.resize((maks_bredde, ny_h))
        skalerede.append(im)

    samlet_hoejde = sum(im.height for im in skalerede)
    samlet = Image.new("RGB", (maks_bredde, samlet_hoejde), (18, 22, 28))
    y = 0
    for im in skalerede:
        samlet.paste(im, (0, y))
        y += im.height

    buf = io.BytesIO()
    samlet.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _laes_med_gemini(billede_bytes: bytes, api_key: str):
    b64_img = base64.b64encode(billede_bytes).decode("utf-8")

    prompt = (
        "Dette billede er ét eller flere sammenhængende screenshots af den SAMME fodbold-kupon fra en bookmaker. "
        "Udtræk alle unikke kampe på kuponen og fjern automatisk eventuelle dubletter fra overlappende screenshots. "
        "Medtag KUN kampe hvor BEGGE holdnavne (hjemmehold og udehold) er synlige. "
        "Returner KUN ren JSON: "
        '{"indsats": 100.0, "kampe": [{"hjemme": "Hold A", "ude": "Hold B", "spil": "Spil", "odds": 1.52}]}'
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": b64_img}}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }

    host = ".".join(["generativelanguage", "googleapis", "com"])
    modeller = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]

    data = None
    sidste_fejl = None
    for m_navn in modeller:
        url = "https://" + host + "/v1beta/models/" + m_navn + ":generateContent?key=" + api_key
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as err:
            sidste_fejl = err
            if err.code in (404, 429, 503):
                time.sleep(1.5)
                continue
            raise

    if data is None:
        raise sidste_fejl or RuntimeError("Alle Gemini-modeller har midlertidigt ramt kvotegrænsen (429)")

    kandidat = data.get("candidates", [{}]).pop(0)
    del_obj = kandidat.get("content", {}).get("parts", [{}]).pop(0)
    tekst = re.sub(r"^```json\s*|\s*```$", "", del_obj.get("text", "{}")).strip()
    parsed = json.loads(tekst)

    indsats = float(parsed.get("indsats") or 100.0)
    kampe = []
    for item in parsed.get("kampe", []):
        hjemme = str(item.get("hjemme") or "").strip()
        ude = str(item.get("ude") or "").strip()
        spil = str(item.get("spil") or "Kampresultat").strip()
        raa_odds = item.get("odds")
        if raa_odds in (None, "", "None", "null"):
            continue
        try:
            odds = float(str(raa_odds).replace(",", "."))
        except ValueError:
            continue
        if hjemme and ude and odds > 1.01:
            kampe.append({"kamp": f"{hjemme} - {ude}", "hjemme": hjemme, "ude": ude, "spil": spil, "odds": round(odds, 2)})

    total = 1.0
    for k in kampe:
        total *= k["odds"]
    return kampe, indsats, round(total, 2) if kampe else 0.0


def udtraek_kupon_fra_flere_billeder(billeder_bytes_liste: list):
    if not billeder_bytes_liste:
        return [], 100.0, 0.0
    api_key = _hent_gemini_noegle()
    if not api_key:
        if st is not None:
            st.error("❌ GEMINI_API_KEY mangler i Secrets.")
        return [], 100.0, 0.0
    try:
        samlet_bytes = _flet_billeder_til_et(billeder_bytes_liste)
        return _laes_med_gemini(samlet_bytes, api_key)
    except Exception as e:
        if st is not None:
            st.error(f"❌ Gemini-fejl: {e}")
        return [], 100.0, 0.0


def udtraek_kupon_fra_billede(billede_bytes: bytes):
    return udtraek_kupon_fra_flere_billeder([billede_bytes])
