from src.services import investment_bank, search_by_phone_numbers


def test_investment_bank():
    transactions = [
        {"Дата операции": "2026-10-01 10:00:00", "Сумма операции": -1712.0},
        {"Дата операции": "2026-10-02 12:00:00", "Сумма операции": -50.0},
        {"Дата операции": "2026-11-01 15:00:00", "Сумма операции": -100.0}
    ]
    result = investment_bank("2026-10", transactions, limit=50)
    assert result == 38.0


def test_search_by_phone_numbers():
    transactions = [
        {"Описание": "Оплата МТС +79211122333"},
        {"Описание": "Обычный магазин"}
    ]
    result = search_by_phone_numbers(transactions)
    assert "+79211122333" in result
