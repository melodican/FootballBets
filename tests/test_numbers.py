"""Verify the Numbers maths against the book's own worked examples."""

import math

from stringtheory import numbers


def test_required_price_matches_books_table():
    # Chapter 11 table: strike rate% -> min price. Book uses 1/p (no commission).
    for pct, price in numbers.STRIKE_RATE_TABLE.items():
        assert math.isclose(numbers.required_price(pct), price, abs_tol=0.02), pct


def test_required_price_key_values():
    assert math.isclose(numbers.required_price(80), 1.25, abs_tol=1e-9)
    assert math.isclose(numbers.required_price(70), 1.4286, abs_tol=1e-3)
    assert math.isclose(numbers.required_price(50), 2.0, abs_tol=1e-9)


def test_required_price_with_commission_is_higher():
    # Commission taxes the winning side, so you need a slightly bigger price.
    assert numbers.required_price(80, commission=0.02) > numbers.required_price(80)


def test_back_profit_book_examples():
    # "£10 at 1.4 = 40% ROI - £4 profit" (book quotes gross, pre-commission).
    assert math.isclose(numbers.back_profit(10, 1.4, commission=0.0), 4.0, abs_tol=1e-9)
    # "£50 at 1.63 = 63% ROI - £31.50 profit"
    assert math.isclose(numbers.back_profit(50, 1.63, commission=0.0), 31.5, abs_tol=1e-9)
    # "£30 at 5 = (30 x 5 - 30) = £120 profit"
    assert math.isclose(numbers.back_profit(30, 5, commission=0.0), 120.0, abs_tol=1e-9)
    # "£100 at 7 = £600 profit"
    assert math.isclose(numbers.back_profit(100, 7, commission=0.0), 600.0, abs_tol=1e-9)


def test_commission_reduces_winnings():
    assert math.isclose(numbers.back_profit(100, 2.0, commission=0.02), 98.0, abs_tol=1e-9)


def test_assess_value_flags_the_books_o15_trade():
    # Book: O1.5 comes ~91% of the time; break-even ~1.10; they got ~1.9 -> big value.
    v = numbers.assess_value(strike_rate=91, offered_price=1.9)
    assert v.is_value is True
    assert v.edge_probability > 0
    assert math.isclose(v.required_price, 1.0 / 0.91, abs_tol=1e-6)


def test_assess_value_rejects_a_short_price():
    # 70% strike rate needs 1.42; being offered 1.30 is NOT value.
    v = numbers.assess_value(strike_rate=70, offered_price=1.30)
    assert v.is_value is False
    assert v.edge_probability < 0


def test_implied_probability():
    assert math.isclose(numbers.implied_probability(2.0), 0.5, abs_tol=1e-9)
    assert math.isclose(numbers.implied_probability(1.25), 0.8, abs_tol=1e-9)
