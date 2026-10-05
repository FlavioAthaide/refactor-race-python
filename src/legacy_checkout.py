"""Processamento de pedidos (checkout)."""

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


def process_order(customer, items, coupon="", state="MG", express=False):
    subtotal = calculate_subtotal(items)
    desconto = calculate_discount(customer["type"], coupon, subtotal)
    valor_com_desconto = subtotal - desconto

    peso = calculate_total_weight(items)
    frete = calculate_shipping(subtotal, peso, state, express)
    imposto = calculate_tax(valor_com_desconto, state)

    pontos = calculate_points(customer["type"], valor_com_desconto + frete + imposto)

    # procura produtos repetidos de forma bem pouco elegante
    duplicados = []

    for i in range(len(items)):
        for j in range(len(items)):
            if i != j:
                if items[i]["name"] == items[j]["name"]:
                    if items[i]["name"] not in duplicados:
                        duplicados.append(items[i]["name"])

    total_final = round(valor_com_desconto + frete + imposto, 2)

    resultado = {
        "customer": customer["name"],
        "subtotal": round(subtotal, 2),
        "discount": round(desconto, 2),
        "shipping": round(frete, 2),
        "tax": round(imposto, 2),
        "total": total_final,
        "points": pontos,
        "duplicate_products": duplicados
    }

    ORDERS_PROCESSED.append(resultado)

    print("Pedido processado para " + customer["name"])
    print("Subtotal:", subtotal)
    print("Desconto:", desconto)
    print("Frete:", frete)
    print("Imposto:", imposto)
    print("TOTAL:", total_final)

    return resultado
