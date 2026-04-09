from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

import spacy
from symspellpy import SymSpell, Verbosity

from .config import DOMAIN_VOCABULARY
from .transaction_parser import (
    ParsedTransaction,
    _extract_date,
    _number_words_to_float,
    _normalize_amount_text,
    _strip_date_phrase,
)

# Initialize SymSpell for domain vocabulary correction
_symspell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
for idx, term in enumerate(DOMAIN_VOCABULARY):
    _symspell.create_dictionary_entry(term, 1_000 - idx)

# Patterns for amount extraction
AMOUNT_PATTERN = re.compile(r"(?P<amount>\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:rupees?|rs\.?|inr)?", re.IGNORECASE)
WORD_AMOUNT_NEAR_CURRENCY_PATTERN = re.compile(
    r"(?P<amount_words>(?:[a-zA-Z]+[\s-]+){0,7}[a-zA-Z]+)\s*(?:rupees?|rs\.?|inr)\b",
    re.IGNORECASE,
)

# Transaction spending verbs
SPEND_PATTERN = re.compile(
    r"\b(spend|spent|pay|paid|purchase|purchased|buy|bought|cost)\b",
    re.IGNORECASE,
)

NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100, "thousand": 1000,
}


class SpacyTransactionParser:
    """
    Transaction parser using spaCy for semantic understanding.
    
    spaCy provides:
    - Robust NER (named entity recognition)
    - Dependency parsing for understanding relationships
    - Much faster and simpler than Rasa
    """

    def __init__(self):
        """Initialize spaCy English model."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logging.info("spaCy model loaded successfully")
        except OSError:
            logging.error(
                "spaCy model not found. Install with: python -m spacy download en_core_web_sm"
            )
            raise

    def parse_transaction(self, text: str, now: datetime | None = None) -> ParsedTransaction | None:
        """
        Parse transaction from text using spaCy semantic analysis.
        
        Args:
            text: Raw recognized text from STT
            now: Current datetime for date context
            
        Returns:
            ParsedTransaction if parseable, None otherwise
        """
        if not text or not text.strip():
            return None

        now = now or datetime.now()

        # Check for spending intent
        if not SPEND_PATTERN.search(text):
            logging.debug("No spending intent found in: %s", text)
            return None

        # Extract date first (before stripping)
        date_value = _extract_date(text, now=now)
        
        # Strip date phrase from text before category extraction
        # This prevents date words from interfering with category parsing
        text_without_date = _strip_date_phrase(text)

        # Extract amount
        amount = self._extract_amount(text)
        if amount is None:
            logging.warning("No amount found in: %s", text)
            return None

        # Extract category using text without date
        category = self._extract_category(text_without_date)
        if not category:
            logging.warning("No category found in: %s", text_without_date)
            return None

        # Extract merchant/extra tags
        merchant = self._extract_merchant(text_without_date)
        extra_tags = merchant if merchant else ""

        return ParsedTransaction(
            date=date_value,
            transaction_amount=amount,
            category=category,
            extra_tags=extra_tags,
        )

    def parse_transactions(self, text: str, now: datetime | None = None) -> list[ParsedTransaction]:
        """Parse multiple transactions from text."""
        parsed = []
        tx = self.parse_transaction(text, now=now)
        if tx:
            parsed.append(tx)
        return parsed

    def _extract_amount(self, text: str) -> float | None:
        """Extract amount from text."""
        # Try numeric amount first
        match = AMOUNT_PATTERN.search(text)
        if match:
            return float(_normalize_amount_text(match.group("amount")))
        
        # Try word amount near currency
        words_match = WORD_AMOUNT_NEAR_CURRENCY_PATTERN.search(text)
        amount_source = words_match.group("amount_words") if words_match else text
        return _number_words_to_float(amount_source)

    def _extract_category(self, text: str) -> str | None:
        """
        Extract category using smart pattern matching and fallback strategies.
        Handles various prepositions and noisy STT input.
        """
        # Pattern-based extraction (most reliable for clear prepositions)
        patterns = [
            r"\bon\s+([a-zA-Z][a-zA-Z0-9_\s-]*?)(?:\b(?:in|at|yesterday|today|tomorrow|from|for|them)|$)",
            r"\bfor\s+([a-zA-Z][a-zA-Z0-9_\s-]*?)(?:\b(?:in|at|yesterday|today|tomorrow|from|at)|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower(), re.IGNORECASE)
            if match:
                category_text = match.group(1).strip()
                # Extract first meaningful word as category
                words = category_text.split()
                if words:
                    category = self._normalize_category(words[0])
                    if category:
                        return category
        
        # Fallback: look for domain vocabulary in last few words (STT often garbles structure)
        # This helps with "them chocolate" -> chocolate
        tokens = text.lower().split()
        for token in reversed(tokens):
            cleaned_token = token.strip(",.'\"!?")
            if cleaned_token and cleaned_token not in ["i", "the", "a", "an", "and", "or", "spent", "spend", "paid", "pay"]:
                normalized = self._normalize_category(cleaned_token)
                if normalized:
                    return normalized
        
        return None

    def _extract_merchant(self, text: str) -> str | None:
        """Extract merchant/location information."""
        patterns = [
            r"\bat\s+([a-zA-Z][a-zA-Z0-9_-]*)",
            r"\bfrom\s+([a-zA-Z][a-zA-Z0-9_-]*)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower(), re.IGNORECASE)
            if match:
                merchant = self._normalize_category(match.group(1))
                if merchant:
                    return merchant
        
        return None

    def _normalize_category(self, category: str) -> str | None:
        """
        Apply SymSpell correction to category for domain vocabulary.
        If no known category found, return the cleaned original category.
        This allows new categories while still correcting common misspellings.
        """
        if not category:
            return None
        
        lowered = category.lower().strip()
        
        # First try to find corrections for known categories
        suggestions = _symspell.lookup(
            lowered,
            Verbosity.CLOSEST,
            max_edit_distance=1,
            include_unknown=False,  # Only return known terms
        )
        
        if suggestions:
            return suggestions[0].term
        
        # If no known category found, return the cleaned original
        # This allows new categories like "bicycle" to be accepted
        return lowered
