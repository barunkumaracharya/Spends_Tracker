"""
Test spaCy transaction parser with realistic STT input.
"""

from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rasa_parser import SpacyTransactionParser


def test_spacy_parser():
    """Test spaCy semantic parser with previously failing examples."""
    parser = SpacyTransactionParser()
    now = datetime(2026, 4, 9, 19, 49, 31)
    
    test_cases = [
        # Noisy STT input that previously failed
        {
            "text": "i today i spent ten rupees them chocolate",
            "expected_amount": 10.0,
            "expected_category": "chocolate",
        },
        # Month name parsing
        {
            "text": "spent six thousand rupees on shoes on january nine",
            "expected_amount": 6000.0,
            "expected_category": "shoes",
        },
        # Multiple transactions in one utterance
        {
            "text": "i spent four hundred rupees on swiggy yesterday i spent six hundred rupees on biryani day before yesterday",
            "expected_amount": 400.0,
            "expected_category": "swiggy",
        },
        # Standard format
        {
            "text": "spent five hundred rupees on clothing",
            "expected_amount": 500.0,
            "expected_category": "clothing",
        },
        # Comma-separated thousand amount
        {
            "text": "Hello, I spent 10,000 rupees in January",
            "expected_amount": 10000.0,
            "expected_category": "rupees",
        },
        # Decimal amount
        {
            "text": "I spent 1234.56 rupees on stationery",
            "expected_amount": 1234.56,
            "expected_category": "stationery",
        },
        # With filler
        {
            "text": "the key then i spent two hundred rupees yesterday on food",
            "expected_amount": 200.0,
            "expected_category": "food",
        },
        # With merchant
        {
            "text": "i paid 450 rupees for groceries at dmart",
            "expected_amount": 450.0,
            "expected_category": "groceries",
        },
        # New category (bicycle)
        {
            "text": "I spent 500 rupees buying as bicycle",
            "expected_amount": 500.0,
            "expected_category": "bicycle",
        },
    ]
    
    for i, test in enumerate(test_cases):
        print(f"\nTest {i+1}: {test['text']}")
        result = parser.parse_transaction(test["text"], now=now)
        
        if result:
            print(f"✓ Parsed: amount={result.transaction_amount}, category={result.category}, date={result.date}")
            assert abs(result.transaction_amount - test["expected_amount"]) < 0.01, \
                f"Amount mismatch: {result.transaction_amount} != {test['expected_amount']}"
            assert result.category == test["expected_category"], \
                f"Category mismatch: {result.category} != {test['expected_category']}"
        else:
            print(f"✗ Failed to parse")
            raise AssertionError(f"Failed to parse: {test['text']}")
    
    print("\n✓ All tests passed!")


if __name__ == "__main__":
    test_spacy_parser()
