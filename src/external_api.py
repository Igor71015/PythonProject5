import logging
from typing import Any, Dict, List
import requests

logger = logging.getLogger(__name__)

API_KEY_CURRENCY = "1454fcf6e9bbc447c12c49b5"
API_KEY_STOCKS = ""


def get_currency_rates(currencies: List[str]) -> List[Dict[str, Any]]:
    rates_list = []

    if not API_KEY_CURRENCY or "your_free" in API_KEY_CURRENCY:
        for cur in currencies:
            rates_list.append({"currency": cur, "rate": 73.21 if cur == "USD" else 87.08})
        return rates_list

    try:
        url = f"https://exchangerate-api.com{API_KEY_CURRENCY.strip()}/latest/RUB"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            conversion_rates = data.get("conversion_rates", {})
            for cur in currencies:
                if cur in conversion_rates and conversion_rates[cur] > 0:
                    rub_rate = round(1 / conversion_rates[cur], 2)
                    rates_list.append({"currency": cur, "rate": float(rub_rate)})
                else:
                    rates_list.append({"currency": cur, "rate": 73.21 if cur == "USD" else 87.08})
        else:
            raise requests.RequestException("Неверный статус ответа")

    except Exception as e:
        logger.error(f"Ошибка при обращении к API валют: {e}. Применены стандартные курсы.")
        for cur in currencies:
            rates_list.append({"currency": cur, "rate": 73.21 if cur == "USD" else 87.08})

    return rates_list


def get_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    stock_list = []
    defaults = {"AAPL": 150.12, "AMZN": 3173.18, "GOOGL": 2742.39, "MSFT": 296.71, "TSLA": 1007.08}

    for ticker in stocks:
        stock_list.append({"stock": ticker, "price": defaults.get(ticker, 100.0)})

    return stock_list
