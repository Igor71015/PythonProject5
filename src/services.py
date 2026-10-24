import json
import logging
import re
from math import ceil
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def get_profitable_cashback_categories(transactions: List[Dict[str, Any]], year: int, month: int) -> str:
    target_month_str = f"{year}-{month:02d}"
    monthly_txs = [
        tx
        for tx in transactions
        if tx.get("Дата операции") and str(tx["Дата операции"]).startswith(target_month_str)
    ]

    cashback_by_category: Dict[str, float] = {}
    for tx in monthly_txs:
        amount = tx.get("Сумма платежа", 0)
        category = tx.get("Категория")

        if amount and amount < 0 and category:
            spent = abs(float(amount))
            cashback = int(spent // 100)
            cashback_by_category[category] = cashback_by_category.get(category, 0) + cashback

    sorted_categories = sorted(cashback_by_category.items(), key=lambda item: item, reverse=True)
    result_dict = {cat: amt for cat, amt in sorted_categories if amt > 0}

    return json.dumps(result_dict, ensure_ascii=False, indent=2)


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    total_saved = 0.0

    monthly_txs = filter(
        lambda tx: tx.get("Дата операции") and str(tx["Дата операции"]).startswith(month),
        transactions
    )

    for tx in monthly_txs:
        amount = tx.get("Сумма операции", 0)
        if amount and amount < 0:
            spent = abs(float(amount))
            rounded_amount = ceil(spent / limit) * limit
            saved = rounded_amount - spent
            total_saved += saved

    return round(total_saved, 2)


def simple_search(query: str, transactions: List[Dict[str, Any]]) -> str:
    if not query:
        return json.dumps([], ensure_ascii=False)

    query_lower = query.lower()

    results = [
        tx
        for tx in transactions
        if (tx.get("Описание") and query_lower in str(tx["Описание"]).lower())
        or (tx.get("Категория") and query_lower in str(tx["Категория"]).lower())
    ]

    return json.dumps(results, ensure_ascii=False, indent=2)


def search_by_phone_numbers(transactions: List[Dict[str, Any]]) -> str:
    phone_pattern = re.compile(r"(\+7|8)\s*\(?\d{3}\)?\s*\d{3}[\s-]*\d{2}[\s-]*\d{2}")

    results = []
    for tx in transactions:
        description = tx.get("Описание")
        if description and phone_pattern.search(str(description)):
            results.append(tx)

    return json.dumps(results, ensure_ascii=False, indent=2)


def search_physical_person_transfers(transactions: List[Dict[str, Any]]) -> str:
    person_pattern = re.compile(r"[А-Я][а-я]+\s+[А-Я]\.")

    results = []
    for tx in transactions:
        category = tx.get("Категория")
        description = tx.get("Описание")

        if category == "Переводы" and description and person_pattern.search(str(description)):
            results.append(tx)

    return json.dumps(results, ensure_ascii=False, indent=2)
