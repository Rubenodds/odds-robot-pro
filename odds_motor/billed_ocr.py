import base64
import io
import json
import os
import re
import urllib.request
from PIL import Image, ImageOps

try:
    import streamlit as st
except Exception:
    st = None

try:
    import pytesseract
except Exception:
    pytesseract = None


def _hent_gemini_noegle() -> str:
    if st is not None:
        try:
            if "GEMINI_API_KEY" in st.secrets:
                return str(st.secrets["GEMINI_API_KEY"]).strip()
        except Exception:
            pass
    return os.environ.get("GEMINI_API_KEY", "").strip()


def _laes_med_gemini(billede_bytes: bytes, api_key: str):
    img = Image.open(io.BytesIO(billede_bytes)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")

    prompt = (
        "Du aflæser et skærmbillede af en Bet365 fodbold-kupon. "
        "Udtræk KUN kampe hvor BEGGE holdnavne (hjemmehold og udehold) er synlige på billedet. "
        "Ignorer afklippede halvkampe i toppen eller bunden hvor et af holdnavnene mangler, "
        "og ignorer live-stillinger (f.eks. 0-0, 1. halvleg - Slut) og bundmenuer. "
        "Returner KUN ren JSON i præcis dette format uden markdown: "
        '{"indsats": 100.0, "kampe": [{"hjemme": "Hold A", "ude": "Hold B", "spil": "Valgt spil", "odds": 1.52}]}'
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": b64_img}},
                ]
            }
        ],
        "generationConfig": {"temperature": 0.0, "response_mime_type": "application/json"},
    }

    url = f"https://googleapis.com{api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    tekst = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    tekst = re.sub(r"^```json\s*|\s*```$", "", tekst).strip()
    parsed = json.loads(tekst)

    indsats = float(parsed.get("indsats") or 100.0)
    kampe = []
    for item in parsed.get("kampe", []):
        hjemme = str(item.get("hjemme", "")).strip()
        ude = str(item.get("ude", "")).strip()
        spil = str(item.get("spil", "Kampresultat")).strip()
        odds = float(str(item.get("odds", 0)).replace(",", "."))
        if hjemme and ude and odds > 1.01:
            kampe.append(
                {
                    "kamp": f"{hjemme} - {ude}",
                    "hjemme": hjemme,
                    "ude": ude,
                    "spil": spil,
                    "odds": round(odds, 2),
                }
            )

    total_odds = 1.0
    for k in kampe:
        total_odds *= k["odds"]
    return kampe, indsats, round(total_odds, 2) if kampe else 0.0


def udtraek_kupon_fra_billede(billede_bytes: bytes):
    api_key = _hent_gemini_noegle()
    if api_key:
        try:
            kampe, indsats, total = _laes_med_gemini(billede_bytes, api_key)
            if kampe:
                return kampe, indsats, total
        except Exception:
            pass

    if pytesseract is None:
        return [], 100.0, 0.0
    img = ImageOps.grayscale(Image.open(io.BytesIO(billede_bytes)))
    w, h = img.size
    if w < 1600:
        skala = 2 if w >= 800 else 3
        img = img.resize((w * skala, h * skala))
    tekst = pytesseract.image_to_string(img, lang="dan+eng", config="--psm 6")
    return parse_kupon_tekst(tekst)


def parse_kupon_tekst(tekst: str):
    return [], 100.0, 0.0
