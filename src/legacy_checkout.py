"""Processamento de pedidos (checkout)."""

from collections import Counter
from dataclasses import dataclass

ORDERS_PROCESSED = []

# --- Descontos por tipo de cliente ---
VIP_DISCOUNT_RATE = 0.10
VIP_PREMIUM_DISCOUNT_RATE = 0.15
VIP_PREMIUM_MIN_SUBTOTAL = 1000
EMPLOYEE_DISCOUNT_RATE = 0.20
REGULAR_DISCOUNT_RATE = 0.05
REGULAR_DISCOUNT_MIN_SUBTOTAL = 800
MAX_DISCOUNT_RATE = 0.25

# --- Cupons ---
PROMO10_DISCOUNT_RATE = 0.10
PROMO20_DISCOUNT_RATE = 0.20
PROMO20_MIN_SUBTOTAL = 500
VIP50_FIXED_DISCOUNT = 50

# --- Frete ---
FREE_SHIPPING_MIN_SUBTOTAL = 500
SOUTHEAST_STATES = {"MG", "SP", "RJ", "ES"}
SOUTHEAST_BASE_SHIPPING = 20
SOUTHEAST_SHIPPING_PER_KG = 0.4
OTHER_STATES_BASE_SHIPPING = 35
OTHER_STATES_SHIPPING_PER_KG = 0.6
EXPRESS_SHIPPING_MULTIPLIER = 1.8

# --- Impostos ---
TAX_RATES = {
    "MG": 0.07,
    "SP": 0.09,
    "RJ": 0.08,
    "ES": 0.07,
}
DEFAULT_TAX_RATE = 0.12

# --- Pontos de fidelidade ---
VIP_POINTS_DIVISOR = 5
DEFAULT_POINTS_DIVISOR = 10


def calculate_subtotal(items):
    """Soma preço x quantidade dos itens com quantidade positiva."""
    subtotal = 0
    for item in items:
        if item["qty"] > 0:
            subtotal += item["price"] * item["qty"]
    return subtotal


def calculate_total_weight(items):
    """Soma peso x quantidade; item sem peso conta como 0."""
    total_weight = 0
    for item in items:
        total_weight += item.get("weight", 0) * item["qty"]
    return total_weight


def calculate_customer_discount(customer_type, subtotal):
    """Desconto de acordo com o tipo de cliente."""
    if customer_type == "vip":
        rate = (
            VIP_PREMIUM_DISCOUNT_RATE
            if subtotal >= VIP_PREMIUM_MIN_SUBTOTAL
            else VIP_DISCOUNT_RATE
        )
        return subtotal * rate
    if customer_type == "employee":
        return subtotal * EMPLOYEE_DISCOUNT_RATE
    if customer_type == "regular" and subtotal >= REGULAR_DISCOUNT_MIN_SUBTOTAL:
        return subtotal * REGULAR_DISCOUNT_RATE
    return 0


def calculate_coupon_discount(coupon, customer_type, subtotal):
    """Desconto adicional concedido pelo cupom (0 se inválido/inaplicável)."""
    if coupon == "PROMO10":
        return subtotal * PROMO10_DISCOUNT_RATE
    if coupon == "PROMO20" and subtotal >= PROMO20_MIN_SUBTOTAL:
        return subtotal * PROMO20_DISCOUNT_RATE
    if coupon == "VIP50" and customer_type == "vip":
        return VIP50_FIXED_DISCOUNT
    return 0


def calculate_discount(customer_type, coupon, subtotal):
    """Desconto total (cliente + cupom), limitado a MAX_DISCOUNT_RATE do subtotal."""
    discount = calculate_customer_discount(customer_type, subtotal)
    discount += calculate_coupon_discount(coupon, customer_type, subtotal)
    return min(discount, subtotal * MAX_DISCOUNT_RATE)


def calculate_shipping(subtotal, weight, state, express):
    """Frete por região e peso; grátis a partir de um valor, exceto se expresso."""
    if subtotal >= FREE_SHIPPING_MIN_SUBTOTAL and not express:
        return 0

    if state in SOUTHEAST_STATES:
        shipping = SOUTHEAST_BASE_SHIPPING + weight * SOUTHEAST_SHIPPING_PER_KG
    else:
        shipping = OTHER_STATES_BASE_SHIPPING + weight * OTHER_STATES_SHIPPING_PER_KG

    if express:
        shipping *= EXPRESS_SHIPPING_MULTIPLIER
    return shipping


def calculate_tax(discounted_value, state):
    """Imposto sobre o valor já com desconto, conforme o estado."""
    return discounted_value * TAX_RATES.get(state, DEFAULT_TAX_RATE)


def calculate_points(customer_type, order_total):
    """Pontos de fidelidade (VIP ganha mais por valor gasto)."""
    divisor = VIP_POINTS_DIVISOR if customer_type == "vip" else DEFAULT_POINTS_DIVISOR
    return int(order_total / divisor)


def find_duplicate_products(items):
    """Nomes de produtos repetidos, na ordem da primeira aparição (O(n))."""
    name_counts = Counter(item["name"] for item in items)
    return [name for name, count in name_counts.items() if count > 1]


@dataclass(frozen=True)
class OrderCalculation:
    """Valores calculados de um pedido (sem arredondar)."""

    subtotal: float
    discount: float
    shipping: float
    tax: float
    total: float
    points: int


def calculate_order(customer, items, coupon, state, express):
    """Aplica todas as regras de negócio. Função pura: não imprime nem grava."""
    customer_type = customer["type"]

    subtotal = calculate_subtotal(items)
    discount = calculate_discount(customer_type, coupon, subtotal)
    discounted_value = subtotal - discount

    shipping = calculate_shipping(
        subtotal, calculate_total_weight(items), state, express
    )
    tax = calculate_tax(discounted_value, state)
    total = discounted_value + shipping + tax

    return OrderCalculation(
        subtotal=subtotal,
        discount=discount,
        shipping=shipping,
        tax=tax,
        total=total,
        points=calculate_points(customer_type, total),
    )


def build_order_result(customer_name, calculation, duplicate_products):
    """Monta o dicionário de resultado com valores monetários arredondados."""
    return {
        "customer": customer_name,
        "subtotal": round(calculation.subtotal, 2),
        "discount": round(calculation.discount, 2),
        "shipping": round(calculation.shipping, 2),
        "tax": round(calculation.tax, 2),
        "total": round(calculation.total, 2),
        "points": calculation.points,
        "duplicate_products": duplicate_products,
    }


def print_order_summary(customer_name, calculation, rounded_total):
    print("Pedido processado para " + customer_name)
    print("Subtotal:", calculation.subtotal)
    print("Desconto:", calculation.discount)
    print("Frete:", calculation.shipping)
    print("Imposto:", calculation.tax)
    print("TOTAL:", rounded_total)


def process_order(customer, items, coupon="", state="MG", express=False):
    """Processa um pedido: calcula, registra no histórico e imprime o resumo."""
    calculation = calculate_order(customer, items, coupon, state, express)
    result = build_order_result(
        customer["name"], calculation, find_duplicate_products(items)
    )

    ORDERS_PROCESSED.append(result)
    print_order_summary(customer["name"], calculation, result["total"])

    return result
