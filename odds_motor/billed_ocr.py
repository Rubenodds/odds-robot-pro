import base64
import io
import json
import os
import re
import time
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


def _find_aktiv_model(host: str, api_key: str) -> str:
    try:
        list_url = "https://" + host + "/v1beta/models?key=" + api_key
        with urllib.request.urlopen(list_url, timeout=10) as resp:
            info = json.loads(resp.read().decode("utf-8"))
        kandidater = []
        for m in info.get("models", []):
            navn = m.get("name", "").replace("models/", "")
            metoder = m.get("supportedGenerationMethods", [])
            if "generateContent" in metoder and "flash" in navn and "tts" not in navn and "image" not in navn:
                kandidater.append(navn)
        for foretrukken in ("gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash-lite"):
            if foretrukken in kandidater:
                return foretrukken
        if kandidater:
            return kandidater.pop()
    except Exception:
        pass
    return "gemini-3.8-flash"


def _laes_med_gemini(billede_bytes: bytes, api_key: str):
    img = Image.open(io.BytesIO(billede_bytes)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")

    prompt = (
        "Du aflæser et skærmbillede af en fodbold-kupon fra en bookmaker "
        "(f.eks. Bet365, Danske Spil, Unibet, Betano, NordicBet m.fl.). "
        "Udtræk KUN kampe hvor BEGGE holdnavne (hjemmehold og udehold) er synlige. "
        "Ignorer afklippede halvkampe hvor et af holdnavnene mangler, "
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
        "generationConfig": {"response_mime_type": "application/json"},
    }

    host = ".".join(["generativelanguage", "googleapis", "com"])
    hoved_model = _find_aktiv_model(host, api_key)
    modeller_at_proeve = [hoved_model, "gemini-3.5-flash-lite", "gemini-3.8-flash"]

    data = None
    sidste_fejl = None
    for m_navn in modeller_at_proeve:
        sti = "/v1beta/models/" + m_navn + ":generateContent"
        url = "https://" + host + sti + "?key=" + api_key
        for _ in range(2):
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=25) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                break
            except Exception as err:
                sidste_fejl = err
                time.sleep(2)
        if data is not None:
            break

    if data is None:
        raise sidste_fejl or RuntimeError("Kunne ikke hente svar fra Gemini")

    kandidat = data.get("candidates", [{}]).pop(0)
    del_obj = kandidat.get("content", {}).get("parts", [{}]).pop(0)
    tekst = del_obj.get("text", "{}").strip()
    tekst = re.sub(r"^```json\s*|\s*```$", "", tekst).strip()
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
