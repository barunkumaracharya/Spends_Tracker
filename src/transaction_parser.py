from __future__ import annotations

import re
from typing import Iterable
from dataclasses import dataclass
from datetime import datetime

import dateparser
from symspellpy import SymSpell, Verbosity

from .config import DOMAIN_VOCABULARY


@dataclass
class ParsedTransaction:
    date: str
    transaction_amount: float
    category: str
    extra_tags: str


AMOUNT_PATTERN = re.compile(r"(?P<amount>\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:rupees?|rs\.?|inr)?", re.IGNORECASE)
WORD_AMOUNT_NEAR_CURRENCY_PATTERN = re.compile(
    r"(?P<amount_words>(?:[a-zA-Z]+[\s-]+){0,7}[a-zA-Z]+)\s*(?:rupees?|rs\.?|inr)\b",
    re.IGNORECASE,
)


def _normalize_amount_text(amount_text: str) -> str:
    return amount_text.replace(",", "").strip()
ON_SEGMENT_PATTERN = re.compile(r"\bon\s+([a-zA-Z][a-zA-Z0-9_-]*)", re.IGNORECASE)
FOR_SEGMENT_PATTERN = re.compile(r"\bfor\s+([a-zA-Z][a-zA-Z0-9_-]*)", re.IGNORECASE)
AT_SEGMENT_PATTERN = re.compile(r"\bat\s+([a-zA-Z][a-zA-Z0-9_-]*)", re.IGNORECASE)
FROM_SEGMENT_PATTERN = re.compile(r"\bfrom\s+([a-zA-Z][a-zA-Z0-9_-]*)", re.IGNORECASE)
MONTH_NAME_PATTERN = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
DATE_WORDS_PATTERN = re.compile(
    rf"\b(?:on|in|at|from|for)?\s*(day before yesterday|today|yesterday|tomorrow|{MONTH_NAME_PATTERN}(?:\s+\d{{1,2}}(?:st|nd|rd|th)?)?(?:\s*,?\s*\d{{2,4}})?|\d{{1,2}}[/-]\d{{1,2}}(?:[/-]\d{{2,4}})?)\b",
    re.IGNORECASE,
)
SPEND_INTENT_PATTERN = re.compile(
    r"\b(spend|spent|pay|paid|purchase|purchased|buy|bought|cost)\b",
    re.IGNORECASE,
)

NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
    "thousand": 1000,
}

WORD_NORMALIZATION = {
    "foot": "food",
    "feet": "food",
}

FILLER_PREFIXES = (
    "the key then",
    "the key thing",
)

_symspell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
for idx, term in enumerate(DOMAIN_VOCABULARY):
    _symspell.create_dictionary_entry(term, 1_000 - idx)


def _extract_date(raw_text: str, now: datetime | None = None) -> str:
    now = now or datetime.now()
    match = DATE_WORDS_PATTERN.search(raw_text)
    candidate = match.group(1) if match else "today"
    parsed = dateparser.parse(
        candidate,
        settings={
            "RELATIVE_BASE": now,
            "PREFER_DATES_FROM": "past",
        },
    )
    if parsed is None:
        parsed = now
    return parsed.date().isoformat()


def _strip_date_phrase(text: str) -> str:
    return DATE_WORDS_PATTERN.sub("", text, count=1).strip(" ,.?")


def _normalize_words(tokens: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for token in tokens:
        key = token.lower()
        replacement = WORD_NORMALIZATION.get(key, key)
        normalized.append(replacement)
    return normalized


def _normalize_domain_token(token: str) -> str:
    lowered = token.lower()
    if lowered in WORD_NORMALIZATION:
        return WORD_NORMALIZATION[lowered]

    suggestions = _symspell.lookup(
        lowered,
        Verbosity.CLOSEST,
        max_edit_distance=1,
        include_unknown=True,
    )
    if not suggestions:
        return lowered
    return suggestions[0].term


def _strip_filler_prefix(text: str) -> str:
    lowered = text.lower().strip()
    for prefix in FILLER_PREFIXES:
        if lowered.startswith(prefix):
            return lowered[len(prefix) :].lstrip(" ,.")
    return text


def _number_words_to_float(text: str) -> float | None:
    tokens = re.findall(r"[a-zA-Z]+", text.lower())
    if not tokens:
        return None

    total = 0
    current = 0
    used = False
    for token in tokens:
        if token == "and":
            continue
        if token not in NUMBER_WORDS:
            continue
        used = True
        value = NUMBER_WORDS[token]
        if value == 100:
            if current == 0:
                current = 1
            current *= value
        elif value == 1000:
            if current == 0:
                current = 1
            total += current * value
            current = 0
        else:
            current += value
    total += current
    if not used:
        return None
    return float(total) if total > 0 else None


def has_transaction_intent(text: str) -> bool:
    return bool(text and SPEND_INTENT_PATTERN.search(text))


def split_transaction_candidates(text: str) -> list[str]:
    if not text:
        return []
    matches = list(SPEND_INTENT_PATTERN.finditer(text))
    if not matches:
        return []

    chunks: list[str] = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        chunk = text[start:end].strip(" ,.;")
        if chunk:
            chunks.append(chunk)
    return chunks


def _extract_category_and_tags(command_text: str) -> tuple[str, str] | None:
    on_segments = ON_SEGMENT_PATTERN.findall(command_text)
    if on_segments:
        category = _normalize_domain_token(on_segments[0])
        extra_tags = ",".join(_normalize_domain_token(tag) for tag in on_segments[1:])
        return category, extra_tags

    for_segments = FOR_SEGMENT_PATTERN.findall(command_text)
    if for_segments:
        category = _normalize_domain_token(for_segments[0])
        merchants = AT_SEGMENT_PATTERN.findall(command_text) + FROM_SEGMENT_PATTERN.findall(command_text)
        extra_tags = ",".join(_normalize_domain_token(tag) for tag in merchants)
        return category, extra_tags

    return None


def parse_transaction(command_text: str, now: datetime | None = None) -> ParsedTransaction | None:
    if not command_text:
        return None
    # Clean up obvious filler and normalize common STT glitches.
    cleaned = _strip_filler_prefix(command_text)
    tokens = cleaned.split()
    cleaned = " ".join(_normalize_words(tokens))

    if not has_transaction_intent(cleaned):
        return None

    amount_match = AMOUNT_PATTERN.search(cleaned)
    if amount_match:
        amount = float(_normalize_amount_text(amount_match.group("amount")))
    else:
        words_match = WORD_AMOUNT_NEAR_CURRENCY_PATTERN.search(cleaned)
        amount_source = words_match.group("amount_words") if words_match else cleaned
        amount = _number_words_to_float(amount_source)
        if amount is None:
            return None

    date_value = _extract_date(cleaned, now=now)
    cleaned = _strip_date_phrase(cleaned)

    category_tags = _extract_category_and_tags(cleaned)
    if not category_tags:
        return None

    category, extra_tags = category_tags

    return ParsedTransaction(
        date=date_value,
        transaction_amount=amount,
        category=category,
        extra_tags=extra_tags,
    )


def parse_transactions(text: str, now: datetime | None = None) -> list[ParsedTransaction]:
    candidates = split_transaction_candidates(text)
    parsed: list[ParsedTransaction] = []
    for candidate in candidates:
        tx = parse_transaction(candidate, now=now)
        if tx:
            parsed.append(tx)
    return parsed
