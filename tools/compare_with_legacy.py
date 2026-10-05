"""Compara o código refatorado com o legado original em pedidos aleatórios.

Uso (na raiz do repositório):
    python tools/compare_with_legacy.py

O código legado é lido do histórico do Git (commit da baseline, antes de
qualquer refatoração). Compara o dicionário de resultado e o texto impresso
de cada pedido.
"""
import contextlib
import importlib.util
import io
import random
import subprocess
import sys
import tempfile
from pathlib import Path

BASELINE_COMMIT = "83f6327"  # chore: adiciona configuração do pytest...
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import legacy_checkout as refactored


def load_legacy_module():
    source = subprocess.run(
        ["git", "show", f"{BASELINE_COMMIT}:src/legacy_checkout.py"],
        cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "legacy_original.py"
        path.write_text(source, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("legacy_original", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


def random_order(rng):
    customer = {"name": "X", "type": rng.choice(["vip", "regular", "employee", "visitor"])}
    items = []
    for _ in range(rng.randint(0, 6)):
        item = {
            "name": rng.choice("ABCDE"),
            "price": round(rng.uniform(1, 900), 2),
            "qty": rng.choice([-1, 0, 1, 2, 3, 5]),
        }
        if rng.random() < 0.8:
            item["weight"] = round(rng.uniform(0, 10), 2)
        items.append(item)
    options = {
        "coupon": rng.choice(["", "PROMO10", "PROMO20", "VIP50", "promo10", "X"]),
        "state": rng.choice(["MG", "SP", "RJ", "ES", "BA", "RS"]),
        "express": rng.choice([True, False]),
    }
    return customer, items, options


def run(module, customer, items, options):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        result = module.process_order(customer, items, **options)
    return result, buffer.getvalue()


def main(total=20000, seed=42):
    legacy = load_legacy_module()
    rng = random.Random(seed)
    for _ in range(total):
        customer, items, options = random_order(rng)
        old = run(legacy, customer, items, options)
        new = run(refactored, customer, items, options)
        if old != new:
            print("DIFERENÇA ENCONTRADA:", customer, items, options, old, new)
            sys.exit(1)
    print(f"OK: legado e refatorado idênticos em {total} pedidos aleatórios.")


if __name__ == "__main__":
    main()
