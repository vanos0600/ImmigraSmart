"""
pii_scrubber.py — ImmigraSmart GDPR Layer
Strips Personally Identifiable Information (PII) from user queries
before they are sent to any external LLM API.

Covered entities:
  - Passport / travel document numbers
  - Czech residence permit numbers (formats: AB1234567, 12-digit IDs)
  - Phone numbers (Czech +420 and international)
  - Email addresses
  - Full dates of birth
  - Bank account / IBAN numbers
  - Full person names (heuristic: 2+ capitalised consecutive words)
  - Czech personal ID numbers (rodné číslo: YYMMDD/XXXX)

Design principle: OVER-scrub rather than under-scrub.
If uncertain, replace with a placeholder. The immigration question
is still answerable without the user's personal details.
"""

import re
from dataclasses import dataclass, field

# ── Replacement tokens ─────────────────────────────────────────────────────────

REPLACEMENTS = {
    "passport":   "[PASSPORT_NUMBER]",
    "permit":     "[PERMIT_NUMBER]",
    "phone":      "[PHONE_NUMBER]",
    "email":      "[EMAIL_ADDRESS]",
    "dob":        "[DATE_OF_BIRTH]",
    "iban":       "[BANK_ACCOUNT]",
    "name":       "[PERSON_NAME]",
    "personal_id":"[PERSONAL_ID]",
}

# ── Regex patterns ─────────────────────────────────────────────────────────────

PATTERNS = [
    # Czech/Slovak passport: 2 letters + 7 digits  e.g. AB1234567
    ("passport",    re.compile(r'\b[A-Z]{2}\d{7}\b')),

    # Czech residence permit card number: starts with letters/digits, 9 chars
    ("permit",      re.compile(r'\b[A-Z]{2}\d{7}\b|\b\d{9,12}\b')),

    # Czech rodné číslo (personal ID): YYMMDD/XXXX or YYMMDDXXXX
    ("personal_id", re.compile(r'\b\d{6}[/\-]?\d{3,4}\b')),

    # IBAN (all countries): up to 34 chars
    ("iban",        re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b')),

    # Email addresses
    ("email",       re.compile(r'\b[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}\b')),

    # Phone: Czech +420, international +XX, or 9-digit local
    ("phone",       re.compile(r'(\+420[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{3}|\+\d{1,3}[\s\-]?\d{6,14}|\b\d{9}\b)')),

    # Dates of birth: DD.MM.YYYY  DD/MM/YYYY  YYYY-MM-DD  MM/DD/YYYY
    ("dob",         re.compile(r'\b(\d{1,2}[./]\d{1,2}[./]\d{4}|\d{4}-\d{2}-\d{2})\b')),

    # Full names: 2–4 capitalised words in sequence (heuristic — comes last)
    # Excludes common Czech legal/place terms that are capitalised
    ("name",        re.compile(
        r'\b(?!(?:Czech|OAMP|MOI|MVČR|Prague|Brno|Ostrava|Schengen|EU|VZP|PVZP|SIMI|OPU)\b)'
        r'[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]{1,20}'
        r'(?:\s+[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]{1,20}){1,3}\b'
    )),
]


# ── Scrubber ──────────────────────────────────────────────────────────────────

@dataclass
class ScrubResult:
    clean_text: str
    was_modified: bool
    entities_found: list[str] = field(default_factory=list)


def scrub(text: str) -> ScrubResult:
    """
    Scrubs PII from `text` and returns a ScrubResult.

    Usage:
        result = scrub("My passport is AB1234567 and I arrive on 12.03.2025")
        # result.clean_text  → "My passport is [PASSPORT_NUMBER] and I arrive on [DATE_OF_BIRTH]"
        # result.was_modified → True
        # result.entities_found → ["passport", "dob"]
    """
    original = text
    entities_found = []

    for entity_type, pattern in PATTERNS:
        replaced, count = pattern.subn(REPLACEMENTS[entity_type], text)
        if count > 0:
            entities_found.append(entity_type)
            text = replaced

    return ScrubResult(
        clean_text=text,
        was_modified=(text != original),
        entities_found=entities_found,
    )


def scrub_text(text: str) -> str:
    """Convenience wrapper — returns only the cleaned string."""
    return scrub(text).clean_text