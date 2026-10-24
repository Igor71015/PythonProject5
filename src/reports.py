from datetime import datetime
import functools
import os
from typing import Any, Callable, Optional
import pandas as pd


def report_to_file(filename: Optional[str] = None) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
            df_result = func(*args, **kwargs)

            if filename:
                out_file = filename
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                out_file = f"report_{func.__name__}_{timestamp}.xlsx"

            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)

            output_dir = os.path.join(project_root, "reports_output")
            os.makedirs(output_dir, exist_ok=True)

            full_path = os.path.join(output_dir, out_file)

            if isinstance(df_result, pd.DataFrame) and not df_result.empty:
                if full_path.endswith(".csv"):
                    df_result.to_csv(full_path, index=False, encoding="utf-8")
                else:
                    df_result.to_excel(full_path, index=False)

            return df_result

        return wrapper

    if callable(filename):
        actual_func = filename
        filename = None
        return decorator(actual_func)

    return decorator


def _get_three_months_range(df: pd.DataFrame, current_date_str: Optional[str]) -> pd.DataFrame:
    if df.empty or "Дата операции" not in df.columns:
        return pd.DataFrame()

    if current_date_str:
        try:
            if " " in current_date_str:
                end_date = datetime.strptime(current_date_str, "%Y-%m-%d %H:%M:%S")
            else:
                end_date = datetime.strptime(current_date_str, "%Y-%m-%d")
        except ValueError:
            end_date = datetime.now()
    else:
        end_date = datetime.now()

    start_date = end_date - pd.DateOffset(months=3)

    df_copy = df.copy()
    df_copy["Дата операции"] = pd.to_datetime(df_copy["Дата операции"])

    mask = (df_copy["Дата операции"] >= start_date) & (df_copy["Дата операции"] <= end_date)
    return df_copy[mask]


@report_to_file
def spending_by_category(
        transactions: pd.DataFrame, category: str, date: Optional[str] = None
) -> pd.DataFrame:
    df_filtered = _get_three_months_range(transactions, date)
    if df_filtered.empty:
        return pd.DataFrame(columns=["Дата операции", "Сумма платежа", "Категория", "Описание"])

    result = df_filtered[(df_filtered["Категория"] == category) & (df_filtered["Сумма платежа"] < 0)]
    return result[
        ["Дата операции", "Сумма платежа", "Категория", "Описание"]
        if "Описание" in result.columns
        else ["Дата операции", "Сумма платежа", "Категория"]
    ]


@report_to_file(filename="weekday_spending.xlsx")
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    df_filtered = _get_three_months_range(transactions, date)
    if df_filtered.empty:
        return pd.DataFrame(columns=["День недели", "Средние траты"])

    expenses = df_filtered[df_filtered["Сумма платежа"] < 0].copy()
    if expenses.empty:
        return pd.DataFrame(columns=["День недели", "Средние траты"])

    expenses["abs_amount"] = expenses["Сумма платежа"].abs()
    expenses["День недели"] = expenses["Дата операции"].dt.day_name()

    result = expenses.groupby("День недели")["abs_amount"].mean().reset_index()
    result.columns = ["День недели", "Средние траты"]
    return result


@report_to_file
def spending_by_workday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    df_filtered = _get_three_months_range(transactions, date)
    if df_filtered.empty:
        return pd.DataFrame(columns=["Тип дня", "Средние траты"])

    expenses = df_filtered[df_filtered["Сумма платежа"] < 0].copy()
    if expenses.empty:
        return pd.DataFrame(columns=["Тип дня", "Средние траты"])

    expenses["abs_amount"] = expenses["Сумма платежа"].abs()
    expenses["Тип дня"] = expenses["Дата операции"].dt.weekday.apply(
        lambda x: "Выходной день" if x >= 5 else "Рабочий день"
    )

    result = expenses.groupby("Тип дня")["abs_amount"].mean().reset_index()
    result.columns = ["Тип дня", "Средние траты"]
    return result
