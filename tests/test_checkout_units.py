"""Testes unitários das funções extraídas na refatoração."""
import pytest

from legacy_checkout import (
    calculate_coupon_discount,
    calculate_customer_discount,
    calculate_discount,
    calculate_order,
    calculate_points,
    calculate_shipping,
    calculate_subtotal,
    calculate_tax,
    calculate_total_weight,
    find_duplicate_products,
)


def test_calculate_subtotal_of_empty_list_is_zero():
    assert calculate_subtotal([]) == 0


def test_calculate_subtotal_ignores_non_positive_quantities():
    items = [{"price": 10, "qty": 2}, {"price": 99, "qty": 0}, {"price": 99, "qty": -1}]
    assert calculate_subtotal(items) == 20


def test_calculate_total_weight_defaults_missing_weight_to_zero():
    items = [{"qty": 2, "weight": 1.5}, {"qty": 4}]
    assert calculate_total_weight(items) == 3


@pytest.mark.parametrize(
    "customer_type, subtotal, expected",
    [
        ("vip", 999, 99.9),
        ("vip", 1000, 150),
        ("employee", 100, 20),
        ("regular", 800, 40),
        ("regular", 799, 0),
        ("other", 5000, 0),
    ],
)
def test_customer_discount_by_type_and_subtotal(customer_type, subtotal, expected):
    assert calculate_customer_discount(customer_type, subtotal) == pytest.approx(expected)


@pytest.mark.parametrize(
    "coupon, customer_type, subtotal, expected",
    [
        ("PROMO10", "regular", 100, 10),
        ("PROMO20", "regular", 500, 100),
        ("PROMO20", "regular", 499, 0),
        ("VIP50", "vip", 100, 50),
        ("VIP50", "regular", 100, 0),
        ("", "vip", 100, 0),
    ],
)
def test_coupon_discount_rules(coupon, customer_type, subtotal, expected):
    assert calculate_coupon_discount(coupon, customer_type, subtotal) == expected


def test_total_discount_never_exceeds_25_percent_of_subtotal():
    assert calculate_discount("employee", "PROMO10", 200) == 50


def test_shipping_is_zero_for_large_non_express_order():
    assert calculate_shipping(500, 100, "BA", express=False) == 0


def test_express_shipping_applies_multiplier_on_far_state():
    assert calculate_shipping(100, 10, "BA", express=True) == pytest.approx((35 + 6) * 1.8)


def test_unknown_state_uses_default_tax_rate():
    assert calculate_tax(100, "XX") == 12


def test_vip_points_use_smaller_divisor():
    assert calculate_points("vip", 100) == 20
    assert calculate_points("regular", 100) == 10


def test_points_are_truncated_not_rounded():
    assert calculate_points("regular", 19.99) == 1


def test_find_duplicate_products_handles_empty_list():
    assert find_duplicate_products([]) == []


def test_calculate_order_is_pure_and_returns_unrounded_values(capsys):
    customer = {"name": "Ana", "type": "regular"}
    items = [{"name": "A", "price": 100, "qty": 1, "weight": 5}]
    calculation = calculate_order(customer, items, "", "MG", False)
    assert calculation.subtotal == 100
    assert calculation.shipping == 22
    assert capsys.readouterr().out == ""
