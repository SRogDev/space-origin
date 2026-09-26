"""Unit tests for the safe event-trigger predicate evaluator (no eval())."""

import pytest

from api.events import evaluate_expr


@pytest.mark.parametrize(
    "expr, ctx, expected",
    [
        ("population.unrest > 0.6", {"population": {"unrest": 0.7}}, True),
        ("population.unrest > 0.6", {"population": {"unrest": 0.5}}, False),
        (
            "resources.food_stock < population.size * 0.5",
            {"resources": {"food_stock": 100}, "population": {"size": 1000}},
            True,
        ),
        (
            "resources.food_stock < population.size * 0.5",
            {"resources": {"food_stock": 600}, "population": {"size": 1000}},
            False,
        ),
        ("year > 2280", {"year": 2281}, True),
        ("year > 2280", {"year": 2280}, False),
        ("year >= 2280", {"year": 2280}, True),
        ("year == 2280", {"year": 2280}, True),
        ("year != 2280", {"year": 2281}, True),
        ("year <= 2290", {"year": 2291}, False),
        # and / or / not
        (
            "year > 2280 and population.unrest > 0.6",
            {"year": 2281, "population": {"unrest": 0.7}},
            True,
        ),
        (
            "year > 2280 and population.unrest > 0.6",
            {"year": 2281, "population": {"unrest": 0.1}},
            False,
        ),
        (
            "year > 2290 or population.unrest > 0.6",
            {"year": 2281, "population": {"unrest": 0.7}},
            True,
        ),
        ("not (year > 2290)", {"year": 2281}, True),
        # arithmetic precedence
        ("1 + 2 * 3 == 7", {}, True),
        ("(1 + 2) * 3 == 9", {}, True),
        ("10 / 4 == 2.5", {}, True),
        ("-5 + 10 == 5", {}, True),
        # safety: unknown paths, bad syntax, div-by-zero -> False, never raise
        ("colony.moons > 2", {"colony": {"name": "x"}}, False),
        ("totally_unknown > 1", {}, False),
        ("year >", {"year": 2281}, False),
        ("", {"year": 2281}, False),
        ("population.size / 0 > 1", {"population": {"size": 100}}, False),
        ("year > '2280'", {"year": 2281}, False),  # strings not supported
    ],
)
def test_evaluate_expr(expr, ctx, expected):
    assert evaluate_expr(expr, ctx) is expected
