import base64
import io
import json
import os
import re
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



def _laes_med_gemini(billede_bytes: bytes, api_key: str):
    img = Image.open(io.BytesIO(billede_bytes)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")

    prompt = (
        "Du aflæser et skærmbillede af en fodbold-kupon fra en bookmaker (f.eks. Bet365, Danske Spil, Unibet, Betano, NordicBet m.fl.). "
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
    if not api_key:
        if st is not None:
            st.error("❌ GEMINI_API_KEY blev ikke fundet i Streamlit Secrets.")
        return [], 100.0, 0.0
    try:
        return _laes_med_gemini(billede_bytes, api_key)
    except Exception as e:
        if st is not None:
            st.error(f"❌ Gemini-fejl ved billedlæsning: {e}")
        return [], 100.0, 0.0
