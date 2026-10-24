from datetime import datetime
import os

from src.utils import load_transactions_excel, transactions_to_dict_list
from src.views import page_events, page_main
from src.services import (
    get_profitable_cashback_categories,
    investment_bank,
    search_by_phone_numbers,
    search_physical_person_transfers
)
from src.reports import spending_by_category, spending_by_weekday, spending_by_workday


def main() -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excel_path = os.path.join(base_dir, "data", "operations.xls")

    if not os.path.exists(excel_path):
        print(f"Ошибка! Поместите ваш скачанный файл по пути: {excel_path}")
        return

    print(f"Файл {excel_path} успешно обнаружен. Начинаю анализ реальных транзакций...")

    df_transactions = load_transactions_excel(excel_path)
    dict_transactions = transactions_to_dict_list(df_transactions)

    if not df_transactions.empty and "Дата операции" in df_transactions.columns:
        latest_dt = df_transactions["Дата операции"].max()
        test_date_main = latest_dt.strftime("%Y-%m-%d %H:%M:%S")
        test_date_events = latest_dt.strftime("%Y-%m-%d")
    else:
        test_date_main = "2021-12-31 12:00:00"
        test_date_events = "2021-12-31"

    print("\n=== ПРОВЕРКА МОДУЛЯ ВЕБ-СТРАНИЦ (views.py) ===")
    print(f"\nЗапрос страницы 'Главная' на дату {test_date_main}:")
    print(page_main(test_date_main, df_transactions))

    print(f"\nЗапрос страницы 'События' на дату {test_date_events}:")
    print(page_events(test_date_events, df_transactions, period="M"))

    print("\n=== ПРОВЕРКА МОДУЛЯ СЕРВИСОВ (services.py) ===")
    dt_obj = datetime.strptime(test_date_events, "%Y-%m-%d")

    print(f"\nВыгодные категории кешбэка за {dt_obj.strftime('%B %Y')}:")
    print(get_profitable_cashback_categories(dict_transactions, dt_obj.year, dt_obj.month))

    saved_money = investment_bank(f"{dt_obj.year}-{dt_obj.month:02d}", dict_transactions, limit=50)
    print(f"\nНакоплено в инвесткопилке (шаг 50) за этот месяц: {saved_money} руб.")

    print("\nПоиск транзакций с номерами телефонов:")
    print(search_by_phone_numbers(dict_transactions))

    print("\nПоиск переводов физлицам:")
    print(search_physical_person_transfers(dict_transactions))

    print("\n=== ПРОВЕРКА МОДУЛЯ ОТЧЕТОВ (reports.py) ===")
    print("Формирую аналитические отчеты...")

    test_category = "Супермаркеты"
    if not df_transactions.empty and "Категория" in df_transactions.columns:
        valid_cats = df_transactions["Категория"].dropna()
        if not valid_cats.empty:
            test_category = str(valid_cats.iloc)

    spending_by_category(df_transactions, test_category, test_date_events)
    spending_by_weekday(df_transactions, test_date_events)
    spending_by_workday(df_transactions, test_date_events)

    print("Отчеты успешно сформированы!")


if __name__ == "__main__":
    main()
