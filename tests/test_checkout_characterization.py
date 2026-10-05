"""Testes de caracterização: registram o comportamento ATUAL do sistema.

Foram escritos ANTES da refatoração e validados contra o código legado.
Servem de rede de segurança: se algum quebrar, o comportamento mudou.
"""
import pytest

import legacy_checkout
from legacy_checkout import process_order


def make_customer(kind="regular", name="Cliente"):
    return {"name": name, "type": kind}


def make_item(price=100, qty=1, weight=0, name="Item"):
    return {"name": name, "price": price, "qty": qty, "weight": weight}


@pytest.fixture(autouse=True)
def clean_orders_history():
    legacy_checkout.ORDERS_PROCESSED.clear()
    yield
    legacy_checkout.ORDERS_PROCESSED.clear()


# ---------- descontos por tipo de cliente ----------

def test_regular_customer_below_threshold_has_no_discount():
    result = process_order(make_customer("regular"), [make_item(price=799)])
    assert result["discount"] == 0


def test_regular_customer_at_800_receives_5_percent_discount():
    result = process_order(make_customer("regular"), [make_item(price=800)])
    assert result["discount"] == 40


def test_vip_customer_below_1000_receives_10_percent_discount():
    result = process_order(make_customer("vip"), [make_item(price=999)])
    assert result["discount"] == pytest.approx(99.9)


def test_vip_customer_at_1000_receives_15_percent_discount():
    result = process_order(make_customer("vip"), [make_item(price=1000)])
    assert result["discount"] == 150


def test_employee_receives_20_percent_discount():
    result = process_order(make_customer("employee"), [make_item(price=100)])
    assert result["discount"] == 20


def test_unknown_customer_type_receives_no_discount():
    result = process_order(make_customer("visitor"), [make_item(price=1000)])
    assert result["discount"] == 0


# ---------- cupons ----------

def test_promo10_adds_10_percent_discount():
    result = process_order(make_customer(), [make_item(price=100)], coupon="PROMO10")
    assert result["discount"] == 10


def test_promo20_applies_when_subtotal_is_at_least_500():
    result = process_order(make_customer(), [make_item(price=500)], coupon="PROMO20")
    assert result["discount"] == 100


def test_promo20_is_ignored_when_subtotal_is_below_500():
    result = process_order(make_customer(), [make_item(price=499)], coupon="PROMO20")
    assert result["discount"] == 0


def test_vip50_gives_fixed_discount_to_vip_customer():
    result = process_order(make_customer("vip"), [make_item(price=100)], coupon="VIP50")
    assert result["discount"] == 25


def test_vip50_gives_fixed_discount_without_cap_when_order_is_large():
    result = process_order(make_customer("vip"), [make_item(price=400)], coupon="VIP50")
    assert result["discount"] == 90


def test_vip50_is_ignored_for_non_vip_customer():
    result = process_order(make_customer("regular"), [make_item(price=400)], coupon="VIP50")
    assert result["discount"] == 0


def test_unknown_coupon_is_ignored():
    result = process_order(make_customer(), [make_item(price=100)], coupon="INVALIDO")
    assert result["discount"] == 0


def test_coupons_are_case_sensitive_in_current_behavior():
    result = process_order(make_customer(), [make_item(price=100)], coupon="promo10")
    assert result["discount"] == 0


# ---------- limite de desconto ----------

def test_total_discount_is_capped_at_25_percent_of_subtotal():
    result = process_order(make_customer("employee"), [make_item(price=100)], coupon="PROMO10")
    assert result["discount"] == 25


def test_discount_at_exactly_25_percent_is_not_changed():
    result = process_order(make_customer("regular"), [make_item(price=1000)], coupon="PROMO20")
    assert result["discount"] == 250


# ---------- subtotal ----------

def test_items_with_zero_quantity_are_ignored_in_subtotal():
    items = [make_item(price=100, qty=2), make_item(price=999, qty=0, name="Fantasma")]
    result = process_order(make_customer(), items)
    assert result["subtotal"] == 200


def test_subtotal_sums_price_times_quantity_of_all_items():
    items = [make_item(price=10, qty=3, name="A"), make_item(price=5.5, qty=2, name="B")]
    result = process_order(make_customer(), items)
    assert result["subtotal"] == 41


# ---------- frete ----------

def test_shipping_is_free_for_subtotal_at_least_500_without_express():
    result = process_order(make_customer(), [make_item(price=500, weight=10)])
    assert result["shipping"] == 0


def test_shipping_in_southeast_state_uses_base_20_plus_weight_rate():
    result = process_order(make_customer(), [make_item(price=100, weight=5)], state="MG")
    assert result["shipping"] == 22


def test_shipping_outside_southeast_uses_base_35_plus_higher_weight_rate():
    result = process_order(make_customer(), [make_item(price=100, weight=5)], state="BA")
    assert result["shipping"] == 38


def test_express_shipping_multiplies_regular_shipping_by_1_8():
    result = process_order(make_customer(), [make_item(price=100, weight=5)], state="MG", express=True)
    assert result["shipping"] == 39.6


def test_express_shipping_is_charged_even_for_orders_above_500():
    result = process_order(make_customer(), [make_item(price=500)], state="MG", express=True)
    assert result["shipping"] == 36


def test_shipping_weight_multiplies_weight_by_quantity():
    result = process_order(make_customer(), [make_item(price=10, qty=3, weight=2)], state="MG")
    assert result["shipping"] == 22.4


def test_item_without_weight_counts_as_zero_weight():
    item = {"name": "Digital", "price": 50, "qty": 1}
    result = process_order(make_customer(), [item], state="MG")
    assert result["shipping"] == 20


# ---------- impostos ----------

@pytest.mark.parametrize(
    "state, expected_tax",
    [("MG", 7), ("SP", 9), ("RJ", 8), ("ES", 7), ("BA", 12)],
)
def test_tax_rate_depends_on_state(state, expected_tax):
    result = process_order(make_customer(), [make_item(price=100)], state=state)
    assert result["tax"] == expected_tax


def test_tax_is_calculated_over_discounted_value():
    result = process_order(make_customer("employee"), [make_item(price=100)], state="MG")
    assert result["tax"] == 5.6


# ---------- total e pontos ----------

def test_total_is_discounted_value_plus_shipping_plus_tax():
    result = process_order(make_customer(), [make_item(price=100, weight=5)], state="MG")
    assert result["total"] == 129


def test_regular_customer_earns_one_point_per_10_currency_units():
    result = process_order(make_customer("regular"), [make_item(price=100, weight=5)], state="MG")
    assert result["points"] == 12


def test_vip_customer_earns_one_point_per_5_currency_units():
    result = process_order(make_customer("vip"), [make_item(price=100, weight=5)], state="MG")
    assert result["points"] == 23


# ---------- produtos duplicados ----------

def test_no_duplicates_returns_empty_list():
    items = [make_item(name="A"), make_item(name="B")]
    assert process_order(make_customer(), items)["duplicate_products"] == []


def test_duplicate_name_is_reported_only_once_even_if_repeated_three_times():
    items = [make_item(name="A"), make_item(name="A"), make_item(name="A")]
    assert process_order(make_customer(), items)["duplicate_products"] == ["A"]


def test_duplicates_are_reported_in_order_of_first_appearance():
    items = [make_item(name="B"), make_item(name="A"), make_item(name="A"), make_item(name="B")]
    assert process_order(make_customer(), items)["duplicate_products"] == ["B", "A"]


# ---------- efeitos colaterais e formato ----------

def test_order_result_is_stored_in_history():
    result = process_order(make_customer(name="Ana"), [make_item()])
    assert legacy_checkout.ORDERS_PROCESSED == [result]


def test_result_contains_expected_keys():
    result = process_order(make_customer(name="Ana"), [make_item()])
    assert set(result) == {
        "customer", "subtotal", "discount", "shipping",
        "tax", "total", "points", "duplicate_products",
    }
    assert result["customer"] == "Ana"


def test_order_summary_is_printed(capsys):
    process_order(make_customer(name="Ana"), [make_item(price=100)])
    output = capsys.readouterr().out
    assert "Pedido processado para Ana" in output
    assert "TOTAL:" in output
