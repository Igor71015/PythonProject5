from datetime import datetime
import json
import logging
import pandas as pd

from src.external_api import get_currency_rates, get_stock_prices
from src.utils import load_user_settings

logger = logging.getLogger(__name__)


def get_greeting(dt: datetime) -> str:
    hour = dt.hour
    if 6 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def get_date_range_mask(df: pd.DataFrame, end_date: datetime, period: str = "M") -> pd.Series:
    if "Дата операции" not in df.columns or df.empty:
        return pd.Series([False] * len(df))

    dates = pd.to_datetime(df["Дата операции"])

    if period == "W":
        start_date = end_date - pd.Timedelta(days=end_date.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "Y":
        start_date = datetime(end_date.year, 1, 1)
    elif period == "ALL":
        return dates <= end_date
    else:
        start_date = datetime(end_date.year, end_date.month, 1)

    return (dates >= start_date) & (dates <= end_date)


def page_main(date_str: str, df: pd.DataFrame) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        logger.error(f"Некорректный формат даты: {date_str}")
        return json.dumps({"error": "Invalid date format"}, ensure_ascii=False)

    greeting = get_greeting(dt)
    mask = get_date_range_mask(df, dt, "M")
    filtered_df = df[mask].copy()

    cards_data = []
    if not filtered_df.empty and "Номер карты" in filtered_df.columns:
        expenses_df = filtered_df[filtered_df["Сумма платежа"] < 0]
        grouped = expenses_df.groupby("Номер карты")["Сумма платежа"].sum()

        for card, total_spent_neg in grouped.items():
            if pd.isna(card):
                continue
            total_spent = abs(float(total_spent_neg))
            cashback = round(total_spent / 100, 2)
            cards_data.append(
                {
                    "last_digits": str(card).strip("*")[-4:],
                    "total_spent": round(total_spent, 2),
                    "cashback": cashback,
                }
            )

    top_transactions = []
    if not filtered_df.empty:
        filtered_df["abs_amount"] = filtered_df["Сумма платежа"].abs()
        top_df = filtered_df.sort_values(by="abs_amount", ascending=False).head(5)

        for _, row in top_df.iterrows():
            top_transactions.append(
                {
                    "date": pd.to_datetime(row["Дата операции"]).strftime("%d.%m.%Y"),
                    "amount": float(row["Сумма платежа"]),
                    "category": str(row.get("Категория", "")),
                    "description": str(row.get("Описание", "")),
                }
            )

    settings = load_user_settings()
    currency_rates = get_currency_rates(settings.get("user_currencies", []))
    stock_prices = get_stock_prices(settings.get("user_stocks", []))

    response = {
        "greeting": greeting,
        "cards": cards_data,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }

    return json.dumps(response, ensure_ascii=False, indent=2)


def page_events(date_str: str, df: pd.DataFrame, period: str = "M") -> str:
    try:
        if " " in date_str:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        logger.error(f"Некорректный формат даты в событиях: {date_str}")
        return json.dumps({"error": "Invalid date format"}, ensure_ascii=False)

    mask = get_date_range_mask(df, dt, period)
    filtered_df = df[mask].copy()

    expenses_df = filtered_df[filtered_df["Сумма платежа"] < 0].copy()
    income_df = filtered_df[filtered_df["Сумма платежа"] > 0].copy()

    total_expenses = round(abs(expenses_df["Сумма платежа"].sum())) if not expenses_df.empty else 0
    total_income = round(income_df["Сумма платежа"].sum()) if not income_df.empty else 0

    main_expenses = []
    transfers_and_cash = []

    if not expenses_df.empty and "Категория" in expenses_df.columns:
        expenses_df["abs_amount"] = expenses_df["Сумма платежа"].abs()

        tc_mask = expenses_df["Категория"].isin(["Переводы", "Наличные"])
        tc_df = expenses_df[tc_mask]
        main_exp_df = expenses_df[~tc_mask]

        if not tc_df.empty:
            tc_grouped = tc_df.groupby("Категория")["abs_amount"].sum().reset_index()
            tc_grouped = tc_grouped.sort_values(by="abs_amount", ascending=False)
            for _, row in tc_grouped.iterrows():
                transfers_and_cash.append({"category": row["Категория"], "amount": round(row["abs_amount"])})

        if not main_exp_df.empty:
            me_grouped = main_exp_df.groupby("Категория")["abs_amount"].sum().reset_index()
            me_grouped = me_grouped.sort_values(by="abs_amount", ascending=False)

            if len(me_grouped) > 7:
                top_7 = me_grouped.head(7)
                others_amount = me_grouped.iloc[7:]["abs_amount"].sum()
                for _, row in top_7.iterrows():
                    main_expenses.append({"category": row["Категория"], "amount": round(row["abs_amount"])})
                main_expenses.append({"category": "Остальное", "amount": round(others_amount)})
            else:
                for _, row in me_grouped.iterrows():
                    main_expenses.append({"category": row["Категория"], "amount": round(row["abs_amount"])})

    main_income = []
    if not income_df.empty and "Категория" in income_df.columns:
        inc_grouped = income_df.groupby("Категория")["Сумма платежа"].sum().reset_index()
        inc_grouped = inc_grouped.sort_values(by="Сумма платежа", ascending=False)
        for _, row in inc_grouped.iterrows():
            main_income.append({"category": row["Категория"], "amount": round(row["Сумма платежа"])})

    settings = load_user_settings()
    currency_rates = get_currency_rates(settings.get("user_currencies", []))
    stock_prices = get_stock_prices(settings.get("user_stocks", []))

    response = {
        "expenses": {
            "total_amount": total_expenses,
            "main": main_expenses,
            "transfers_and_cash": transfers_and_cash,
        },
        "income": {"total_amount": total_income, "main": main_income},
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }

    return json.dumps(response, ensure_ascii=False, indent=2)
