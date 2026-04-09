from datetime import datetime

from src.transaction_parser import has_transaction_intent, parse_transaction, parse_transactions


def test_parse_with_extra_tag_and_today():
    now = datetime(2026, 4, 9, 9, 30, 0)
    tx = parse_transaction("I spent 300 rupees on food today on swiggy", now=now)

    assert tx is not None
    assert tx.date == "2026-04-09"
    assert tx.transaction_amount == 300.0
    assert tx.category == "food"
    assert tx.extra_tags == "swiggy"


def test_parse_with_yesterday():
    now = datetime(2026, 4, 9, 9, 30, 0)
    tx = parse_transaction("yesterday, i spent 20 rupees on chocolate", now=now)

    assert tx is not None
    assert tx.date == "2026-04-08"
    assert tx.transaction_amount == 20.0
    assert tx.category == "chocolate"
    assert tx.extra_tags == ""


def test_parse_paid_for_with_merchant_tag():
    now = datetime(2026, 4, 9, 9, 30, 0)
    tx = parse_transaction("i paid 450 rupees for groceries at dmart", now=now)

    assert tx is not None
    assert tx.date == "2026-04-09"
    assert tx.transaction_amount == 450.0
    assert tx.category == "groceries"
    assert tx.extra_tags == "dmart"


def test_parse_number_words_and_normalization_and_filler():
    now = datetime(2026, 4, 9, 9, 30, 0)
    text = "the key then i spent two hundred rupees yesterday on foot"
    tx = parse_transaction(text, now=now)

    assert tx is not None
    assert tx.date == "2026-04-08"
    assert tx.transaction_amount == 200.0
    assert tx.category == "food"
    assert tx.extra_tags == ""


def test_parse_with_month_name_day():
    now = datetime(2026, 4, 9, 9, 30, 0)
    tx = parse_transaction("i spent six thousand rupees on shoes on january nine", now=now)

    assert tx is not None
    assert tx.date == "2026-01-09"
    assert tx.transaction_amount == 6000.0
    assert tx.category == "shoes"
    assert tx.extra_tags == ""


def test_parse_with_month_name_only():
    now = datetime(2026, 4, 9, 9, 30, 0)
    tx = parse_transaction("i spent six thousand rupees in january on shoes", now=now)

    assert tx is not None
    assert tx.date == "2026-01-09"
    assert tx.transaction_amount == 6000.0
    assert tx.category == "shoes"
    assert tx.extra_tags == ""


def test_symspell_domain_correction_for_merchant():
    now = datetime(2026, 4, 9, 9, 30, 0)
    tx = parse_transaction("i spent 300 rupees on food on swigy", now=now)

    assert tx is not None
    assert tx.transaction_amount == 300.0
    assert tx.category == "food"
    assert tx.extra_tags == "swiggy"


def test_intent_detection():
    assert has_transaction_intent("I spent 100 rupees on tea")
    assert has_transaction_intent("I bought a snack for 50")
    assert not has_transaction_intent("what is the weather today")


def test_parse_two_transactions_in_single_transcript():
    now = datetime(2026, 4, 9, 9, 30, 0)
    text = "i spent four hundred rupees on swiggy yesterday i spent six hundred rupees on biryani day before yesterday"
    txs = parse_transactions(text, now=now)

    assert len(txs) == 2
    assert txs[0].transaction_amount == 400.0
    assert txs[0].category == "swiggy"
    assert txs[0].date == "2026-04-08"

    assert txs[1].transaction_amount == 600.0
    assert txs[1].category == "biryani"
    assert txs[1].date == "2026-04-07"
