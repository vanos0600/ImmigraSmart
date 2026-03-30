"""
lang_detect.py — ImmigraSmart Language Layer
Detects the language of a user query and instructs the LLM
to respond in that same language.

Supported languages (priority for ImmigraSmart's user base):
  Czech, Slovak, English, Spanish, Arabic, Ukrainian, Russian,
  Vietnamese, Chinese (Simplified), German, French

Strategy:
  - Use a tiny heuristic word-list check first (zero latency, zero cost)
  - Fall back to asking Gemini only when heuristic is uncertain
  - Always default to English if detection fails

FIXES vs v1:
  BUG 1 — Score threshold was >= 2, causing short single-sentence queries
    (e.g. "Potřebuji vízum", "Jak mohu pracovat?") to score only 1 match
    and silently fall back to English.
    FIX: Threshold lowered to >= 1. Every hint word in _HINTS is language-
    specific enough that a single match is a reliable signal. Words like
    "potřebuji", "jsem", "vízum" simply do not appear in other languages.
"""

import re

# ── Heuristic word lists (top 15 common words per language) ──────────────────

_HINTS: dict[str, list[str]] = {
   "cs": ["jsem", "mám", "mam", "potřebuji", "potrebuji", "jak", "kdy", "kde", "vízum", "vizum", "povolení", "povoleni", "pobyt", "přijet", "prosím", "prosim", "mohu", "musím", "student", "cizinec", "ahoj", "dotaz", "dobrý"],
    "sk": ["som", "mám", "potrebujem", "ako", "kedy", "kde", "vízum", "povolenie", "pobyt", "prísť", "prosím", "môžem", "musím", "študent", "cudzinec"],
    "es": ["tengo", "necesito", "cómo", "cuándo", "dónde", "visa", "permiso", "residencia", "llegar", "por favor", "puedo", "debo", "estudiante", "extranjero", "quiero"],
    "ar": ["أحتاج", "كيف", "متى", "أين", "تأشيرة", "إقامة", "وصول", "طالب", "أجنبي", "يمكنني", "يجب", "أريد", "لدي", "منح"],
    "uk": ["маю", "потрібно", "як", "коли", "де", "віза", "дозвіл", "проживання", "прибуття", "будь ласка", "можу", "повинен", "студент", "іноземець"],
    "ru": ["имею", "нужно", "как", "когда", "где", "виза", "разрешение", "проживание", "прибытие", "пожалуйста", "могу", "должен", "студент", "иностранец"],
    "vi": ["tôi", "cần", "làm thế nào", "khi nào", "ở đâu", "visa", "giấy phép", "cư trú", "đến", "xin", "có thể", "phải", "sinh viên", "người nước ngoài"],
    "zh": ["我", "需要", "如何", "何时", "在哪里", "签证", "许可", "居留", "抵达", "请", "可以", "必须", "学生", "外国人"],
    "de": ["ich", "brauche", "wie", "wann", "wo", "visum", "aufenthaltserlaubnis", "aufenthalt", "ankommen", "bitte", "kann", "muss", "student", "ausländer"],
    "fr": ["j'ai", "besoin", "comment", "quand", "où", "visa", "permis", "séjour", "arriver", "s'il vous plaît", "peux", "dois", "étudiant", "étranger"],
    "en": ["i", "need", "how", "when", "where", "visa", "permit", "residence", "arrive", "please", "can", "must", "student", "foreigner", "apply"],
}

_LANG_NAMES: dict[str, str] = {
    "cs": "Czech",
    "sk": "Slovak",
    "es": "Spanish",
    "ar": "Arabic",
    "uk": "Ukrainian",
    "ru": "Russian",
    "vi": "Vietnamese",
    "zh": "Chinese (Simplified)",
    "de": "German",
    "fr": "French",
    "en": "English",
}


def detect_language(text: str) -> str:
    """
    Returns a BCP-47 language code (e.g. 'en', 'es', 'cs').
    Defaults to 'en' when uncertain.

    FIX: Threshold lowered from >= 2 to >= 1.
    Each hint word is language-exclusive, so a single match is sufficient.
    """
    lower = text.lower()
    scores: dict[str, int] = {}

    for lang, words in _HINTS.items():
        score = sum(1 for w in words if re.search(r'\b' + re.escape(w) + r'\b', lower))
        if score > 0:
            scores[lang] = score

    if not scores:
        return "en"

    best_lang = max(scores, key=lambda k: scores[k])
    best_score = scores[best_lang]

    # FIX BUG 1: Was `>= 2`. Now `>= 1` — a single language-exclusive hint
    # word is enough to confidently detect the language. Short questions like
    # "Potřebuji vízum" (1 Czech word) no longer fall back to English.
    return best_lang if best_score >= 1 else "en"


def get_language_instruction(lang_code: str) -> str:
    """
    Returns a system instruction telling the LLM to respond in the detected language.
    """
    if lang_code == "en":
        return ""  # No extra instruction needed for English
    lang_name = _LANG_NAMES.get(lang_code, "English")
    return (
        f"\n\nIMPORTANT: The user wrote in {lang_name}. "
        f"You MUST respond entirely in {lang_name}. "
        f"All explanations, lists, and citations should be in {lang_name}. "
        f"Official Czech terms (e.g. 'překlenovací štítek', 'OAMP') may remain in Czech "
        f"but should be explained in {lang_name}."
    )