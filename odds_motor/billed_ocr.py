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


def _find_model(host: str, api_key: str) -> str:
    try:
        u = "https://" + host + "/v1beta/models?key=" + api_key
        with urllib.request.urlopen(u, timeout=6) as r:
            info = json.loads(r.read().decode("utf-8"))
        for m in info.get("models", []):
            navn = m.get("name", "").replace("models/", "")
            if "generateContent" in m.get("supportedGenerationMethods", []) and "flash" in navn:
                return navn
    except Exception:
        pass
    return "gemini-3.8-flash"


def _laes_med_gemini(billede_bytes: bytes, api_key: str):
    img = Image.open(io.BytesIO(billede_bytes)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")

    prompt = (
        "Aflæs dette kupon-screenshot. Medtag KUN kampe hvor BEGGE holdnavne er synlige. "
        "Returner KUN JSON: "
        '{"indsats": 100.0, "kampe": [{"hjemme": "Hold A", "ude": "Hold B", "spil": "Spil", "odds": 1.52}]}'
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": b64_img}}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }

    host = ".".join(["generativelanguage", "googleapis", "com"])
    model_navn = _find_model(host, api_key)
    url = "https://" + host + "/v1beta/models/" + model_navn + ":generateContent?key=" + api_key

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = json.loads(resp.read().decode("utf-8"))

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


def udtraek_kupon_fra_billede(billede_bytes: bytes):
    api_key = _hent_gemini_noegle()
    if not api_key:
        if st is not None:
            st.error("❌ GEMINI_API_KEY mangler i Secrets.")
        return [], 100.0, 0.0
    try:
        return _laes_med_gemini(billede_bytes, api_key)
    except Exception as e:
        if st is not None:
            st.error(f"❌ Gemini-fejl: {e}")
        return [], 100.0, 0.0
