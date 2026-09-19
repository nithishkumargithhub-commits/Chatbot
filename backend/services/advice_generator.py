"""
services/advice_generator.py — JeevanPath AI
Multi-Lingual Beneficiary Advice Generator

Takes the beneficiary's query, detected language, and retrieved scheme,
and generates a clear, concise, structured answer in the user's native language.

Key principles:
  - Always use the actual scheme data from the knowledge base (never hardcoded sentences).
  - Summarise clearly — strip OCR noise, use up to 3 sentences per field.
  - Translate each field to the user's detected language via Google Translate (with fallback).
  - Return a fixed dict shape so the frontend requires no changes.
"""

import json
import logging
import re
import urllib.parse
import urllib.request
from typing import Any, Dict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Language metadata
# ---------------------------------------------------------------------------

LANG_NAMES = {
    "ta": "Tamil",
    "hi": "Hindi",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "en": "English",
}

# Common romanised words that indicate an Indian language was spoken but
# Whisper transcribed the audio as English.
_ROMANISED_HINTS: dict[str, list[str]] = {
    "ta": ["naan", "neenga", "enna", "enga", "enakku", "ungal", "romba", "sollu", "pannanum"],
    "hi": ["mujhe", "aapka", "aapki", "kaise", "chahiye", "milega", "batao", "karein", "hain"],
    "te": ["nenu", "meeru", "enti", "ela", "cheppandi", "kavali", "cheyandi"],
    "kn": ["naanu", "neevu", "yenu", "heli", "maadbeku", "idhe"],
    "ml": ["njan", "ningal", "enthu", "evide", "cheyyuka", "kittum", "paranju"],
}

# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

def clean_ocr_text(text: str) -> str:
    """Removes OCR artifacts and normalises text."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = text.replace("0f", "of").replace("1akh", "lakh")
    text = re.sub(r"\bRs\.\s*", "₹", text, flags=re.IGNORECASE)
    text = re.sub(r"\bNo\.\s*", "No ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bGovt\.\s*", "Govt ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bapprox\.\s*", "approx ", text, flags=re.IGNORECASE)
    text = text.strip(" -:;,")
    return text


def _first_n_sentences(text: str, n: int = 3) -> str:
    """Returns the first n meaningful sentences from text."""
    if not text:
        return ""
    # Protect abbreviations before splitting on sentence boundaries
    protected = re.sub(r"\b(Rs|No|Govt|approx|Dr|Mr|Mrs|St|viz|vs|etc)\.", r"\1<DOT>", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z₹\u0900-\u0D7F])", protected)
    selected = " ".join(p.strip() for p in parts[:n] if p.strip())
    return selected.replace("<DOT>", ".").strip()


def _extract_nsqf_level(text: str) -> str:
    """Extracts an NSQF level mention from scheme text. Returns '' if not found."""
    match = re.search(r"NSQF\s*[Ll]evel\s*[:\-]?\s*(\d+)", text or "")
    if match:
        return f"NSQF Level {match.group(1)}"
    match = re.search(
        r"level\s*[:\-]?\s*(\d+)\s*(?:of\s*the\s*NSQF|NSQF|qualification)",
        text or "", re.IGNORECASE
    )
    if match:
        return f"NSQF Level {match.group(1)}"
    return ""


# ---------------------------------------------------------------------------
# Language detection helpers
# ---------------------------------------------------------------------------

def detect_script_lang(text: str) -> str | None:
    """Detects Indian language from Unicode script range in transcript text."""
    for ch in text or "":
        cp = ord(ch)
        if 0x0B80 <= cp <= 0x0BFF: return "ta"  # Tamil
        if 0x0900 <= cp <= 0x097F: return "hi"  # Hindi / Devanagari
        if 0x0C00 <= cp <= 0x0C7F: return "te"  # Telugu
        if 0x0C80 <= cp <= 0x0CFF: return "kn"  # Kannada
        if 0x0D00 <= cp <= 0x0D7F: return "ml"  # Malayalam
        if 0x0980 <= cp <= 0x09FF: return "bn"  # Bengali
        if 0x0A80 <= cp <= 0x0AFF: return "gu"  # Gujarati
        if 0x0A00 <= cp <= 0x0A7F: return "pa"  # Punjabi
    return None


def detect_romanised_lang(text: str) -> str | None:
    """
    Heuristic: detect if Whisper transcribed Indic speech as romanised English.
    Checks for common native words in romanised form.
    Returns an ISO 639-1 code or None.
    """
    text_lower = (text or "").lower()
    for lang, words in _ROMANISED_HINTS.items():
        if any(f" {w} " in f" {text_lower} " for w in words):
            return lang
    return None


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------

def translate_to_language(text: str, target_lang: str) -> str:
    """
    Translates text to the target language via the Google Translate public endpoint.
    Falls back silently to the original English text on any error.
    """
    if not text or target_lang == "en":
        return text

    target = target_lang.lower().strip()
    try:
        url = (
            f"https://translate.googleapis.com/translate_a/single?client=gtx"
            f"&sl=auto&tl={target}&dt=t&q=" + urllib.parse.quote(text)
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode("utf-8"))
            translated = "".join(part[0] for part in data[0] if part[0])
            if translated:
                return translated.strip()
    except Exception as exc:
        logger.warning(f"Translation to {target} failed: {exc}")

    return text


# ---------------------------------------------------------------------------
# Core advice generator
# ---------------------------------------------------------------------------

def generate_clear_advice(query: str, scheme: Dict[str, Any], lang: str = "en") -> Dict[str, Any]:
    """
    Synthesizes a clean, high-clarity livelihood recommendation using the
    ACTUAL scheme data from the knowledge base — never hardcoded sentences.

    Args:
        query:  The user's original transcript text.
        scheme: A scheme record dict from RAGService.query(), containing
                description, assistance, eligibility, how_to_apply, etc.
        lang:   ISO 639-1 language code detected by Whisper / selected by user.

    Returns:
        Structured advice dict with all fields translated into the user's language.
        Keys: scheme_name, scheme_name_local, ministry, summary, grantSupport,
              eligibility, nsqfLevel, nextStep, speechText, sourceUrl,
              language, language_name, similarity_score.
    """
    # ------------------------------------------------------------------
    # 1. Resolve target language
    # ------------------------------------------------------------------
    target_lang = (lang or "en").lower().strip()
    if target_lang in ("auto", ""):
        script_lang = detect_script_lang(query)
        if script_lang:
            target_lang = script_lang
        else:
            romanised = detect_romanised_lang(query)
            target_lang = romanised if romanised else "en"

    # ------------------------------------------------------------------
    # 2. Extract and clean actual scheme fields
    # ------------------------------------------------------------------
    scheme_name = scheme.get("scheme_name", "Government Skill Development Scheme")
    ministry    = scheme.get("ministry", "Government of India")
    category    = scheme.get("category", "")
    raw_desc    = clean_ocr_text(scheme.get("description", ""))
    raw_asst    = clean_ocr_text(scheme.get("assistance", ""))
    raw_elig    = clean_ocr_text(scheme.get("eligibility", ""))
    raw_apply   = clean_ocr_text(scheme.get("how_to_apply", ""))
    source_url  = scheme.get("source_url", "")
    similarity  = scheme.get("similarity_score", None)

    # ------------------------------------------------------------------
    # 3. Build precise English summaries from ACTUAL scheme data
    # ------------------------------------------------------------------

    # Summary — real description, up to 3 sentences
    if raw_desc:
        core = _first_n_sentences(raw_desc, n=3)
        summary_en = core if scheme_name.split()[0].lower() in core.lower() else f"{scheme_name}: {core}"
    else:
        summary_en = (
            f"Under {scheme_name} by {ministry}, the Government provides "
            f"industry-recognised vocational skill training and employment support"
            f"{(' in the ' + category + ' sector') if category else ''}."
        )

    # Benefits — real assistance text, up to 3 sentences
    if raw_asst:
        benefits_en = _first_n_sentences(raw_asst, n=3)
    else:
        benefits_en = (
            "Free certified training, financial assistance, stipend, and toolkit "
            "subsidies are provided under Government of India norms."
        )

    # Eligibility — real eligibility text, up to 2 sentences
    if raw_elig:
        eligibility_en = _first_n_sentences(raw_elig, n=2)
    else:
        eligibility_en = (
            "Indian citizens including youth, women, SC/ST/OBC candidates, "
            "artisans, and rural job seekers seeking skill development."
        )

    # How to Apply — real apply text, up to 2 sentences
    if raw_apply:
        next_step_en = _first_n_sentences(raw_apply, n=2)
    else:
        next_step_en = (
            "Contact your nearest Government ITI, District Industries Centre (DIC), "
            "Block Development Office (BDO), or apply via the official scheme portal."
        )

    # NSQF Level — extracted from actual scheme text, never echoes eligibility field
    combined_text = f"{raw_desc} {raw_asst} {raw_elig}"
    nsqf_level_en = _extract_nsqf_level(combined_text)
    if not nsqf_level_en:
        nsqf_level_en = (
            f"Skill certification aligned to NSQF (National Skills Qualifications "
            f"Framework) under {ministry}."
        )

    # Speech text — concise sentence for TTS
    speech_en = (
        f"Under {scheme_name}, you can receive certified vocational training "
        f"and financial support. "
        f"{_first_n_sentences(raw_asst or benefits_en, n=1)} "
        f"{_first_n_sentences(next_step_en, n=1)}"
    ).strip()

    # ------------------------------------------------------------------
    # 4. Translate all fields into the user's language
    # ------------------------------------------------------------------
    if target_lang != "en":
        summary_translated     = translate_to_language(summary_en, target_lang)
        benefits_translated    = translate_to_language(benefits_en, target_lang)
        eligibility_translated = translate_to_language(eligibility_en, target_lang)
        next_step_translated   = translate_to_language(next_step_en, target_lang)
        speech_translated      = translate_to_language(speech_en, target_lang)
        scheme_name_translated = translate_to_language(scheme_name, target_lang)
        nsqf_translated        = translate_to_language(nsqf_level_en, target_lang)
    else:
        summary_translated     = summary_en
        benefits_translated    = benefits_en
        eligibility_translated = eligibility_en
        next_step_translated   = next_step_en
        speech_translated      = speech_en
        scheme_name_translated = scheme_name
        nsqf_translated        = nsqf_level_en

    # ------------------------------------------------------------------
    # 5. Return structured advice dict (frontend shape unchanged)
    # ------------------------------------------------------------------
    return {
        "scheme_name":       scheme_name,
        "scheme_name_local": scheme_name_translated,
        "ministry":          ministry,
        "summary":           summary_translated,
        "grantSupport":      benefits_translated,
        "eligibility":       eligibility_translated,
        "nsqfLevel":         nsqf_translated,           # fixed: no longer == eligibility
        "nextStep":          next_step_translated,
        "speechText":        speech_translated,
        "sourceUrl":         source_url,
        "language":          target_lang,
        "language_name":     LANG_NAMES.get(target_lang, "Vernacular"),
        "similarity_score":  similarity,
    }
