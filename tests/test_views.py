from datetime import datetime
from src.views import get_greeting


def test_get_greeting():
    assert get_greeting(datetime(2026, 10, 24, 9, 0, 0)) == "Доброе утро"
    assert get_greeting(datetime(2026, 10, 24, 15, 0, 0)) == "Добрый день"
    assert get_greeting(datetime(2026, 10, 24, 20, 0, 0)) == "Добрый вечер"
    assert get_greeting(datetime(2026, 10, 24, 2, 0, 0)) == "Доброй ночи"
