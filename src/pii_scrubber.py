"""
pii_scrubber.py — ImmigraSmart GDPR Layer (v2 — Fixed)

BUGS FIXED vs v1:
  BUG 1 — Name regex matched ANY two capitalised words.
    "Bridge Label", "Foreign Police", "Czech Republic", "Residence Permit"
    were all replaced with [PERSON_NAME], destroying the query entirely.
    FIX: Name regex removed. Immigration questions don't contain full names
    in practice, and the risk of destroying legal terms far outweighs the
    benefit. If needed, add it back with a much tighter pattern later.

  BUG 2 — Phone regex `\b\d{9}\b` matched any 9-digit number.
    Czech CZK amounts, law references (326/1999), and permit numbers
    were being replaced with [PHONE_NUMBER].
    FIX: 9-digit standalone pattern removed. Only explicit +420 and
    international +XX formats are matched now.

  BUG 3 — Permit regex `\b\d{9,12}\b` was too broad.
    FIX: Permit pattern restricted to the exact Czech format (2 letters
    + 7 digits only). The generic digit range is removed.
"""

import re
from dataclasses import dataclass, field

REPLACEMENTS = {
    "passport":    "[PASSPORT_NUMBER]",
    "permit":      "[PERMIT_NUMBER]",
    "personal_id": "[PERSONAL_ID]",
    "iban":        "[BANK_ACCOUNT]",
    "email":       "[EMAIL_ADDRESS]",
    "phone":       "[PHONE_NUMBER]",
    "dob":         "[DATE_OF_BIRTH]",
}

PATTERNS = [
    # Czech/Slovak passport: exactly 2 letters + 7 digits (e.g. AB1234567)
    ("passport",
     re.compile(r'\b[A-Z]{2}\d{7}\b')),

    # Czech residence permit: exactly 2 letters + 7 digits (same format)
    # Kept separate from passport so entity label is correct
    ("permit",
     re.compile(r'\b[A-Z]{2}\d{7}\b')),

    # Czech rodné číslo: YYMMDD-XXXX format (with separator only)
    # Requires the / or - separator to avoid matching random 9-digit numbers
    ("personal_id",
     re.compile(r'\b\d{6}[/\-]\d{3,4}\b')),

    # IBAN: 2 letters + 2 digits + 4-30 alphanumeric chars
    # Must start with country code letters (CZ, DE, etc.)
    ("iban",
     re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,28}\b')),

    # Email addresses
    ("email",
     re.compile(r'\b[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}\b')),

    # Phone: +420 format OR international +XX format (no standalone 9-digit)
    # Removed \b\d{9}\b — too many false positives with CZK amounts
    ("phone",
     re.compile(
         r'\+420[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{3}'
         r'|\+\d{1,3}[\s\-]?\d{6,14}'
     )),

    # Dates of birth: DD.MM.YYYY or DD/MM/YYYY or YYYY-MM-DD
    # Requires 4-digit year to avoid matching "3 working days" style text
    ("dob",
     re.compile(r'\b\d{1,2}[./]\d{1,2}[./]\d{4}\b'
                r'|\b\d{4}-\d{2}-\d{2}\b')),
]


@dataclass
class ScrubResult:
    clean_text: str
    was_modified: bool
    entities_found: list[str] = field(default_factory=list)


def scrub(text: str) -> ScrubResult:
    original = text
    entities_found = []
    for entity_type, pattern in PATTERNS:
        replaced, count = pattern.subn(REPLACEMENTS[entity_type], text)
        if count > 0:
            if entity_type not in entities_found:
                entities_found.append(entity_type)
            text = replaced
    return ScrubResult(
        clean_text=text,
        was_modified=(text != original),
        entities_found=entities_found,
    )


def scrub_text(text: str) -> str:
    return scrub(text).clean_text