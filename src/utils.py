import json
import logging
import os
from typing import Any, Dict, List
import pandas as pd

logger = logging.getLogger(__name__)


def load_user_settings(path: str = "user_settings.json") -> Dict[str, Any]:
    try:
        if not os.path.exists(path):
            return {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке настроек: {e}")
        return {"user_currencies": [], "user_stocks": []}


def _clean_amount_column(series: pd.Series) -> pd.Series:
    if series.dtype == object:
        cleaned = series.astype(str).str.replace(r"[a-zA-Z\s]", "", regex=True)
        return pd.to_numeric(cleaned, errors="coerce").fillna(0.0)
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def load_transactions_excel(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_excel(file_path)

        if "Дата операции" in df.columns:
            df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True, errors="coerce")
        if "Дата платежа" in df.columns:
            df["Дата платежа"] = pd.to_datetime(df["Дата платежа"], dayfirst=True, errors="coerce")

        if "Сумма операции" in df.columns:
            df["Сумма операции"] = _clean_amount_column(df["Сумма операции"])
        if "Сумма платежа" in df.columns:
            df["Сумма платежа"] = _clean_amount_column(df["Сумма платежа"])

        return df
    except Exception as e:
        logger.error(f"Ошибка при чтении Excel файла {file_path}: {e}")
        return pd.DataFrame()


def transactions_to_dict_list(df: pd.DataFrame) -> List[Dict[str, Any]]:
    df_copy = df.copy()

    if "Дата операции" in df_copy.columns:
        df_copy["Дата операции"] = df_copy["Дата операции"].dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")
    if "Дата платежа" in df_copy.columns:
        df_copy["Дата платежа"] = df_copy["Дата платежа"].dt.strftime("%Y-%m-%d").fillna("")

    df_filled = df_copy.astype(object).where(pd.notnull(df_copy), None)
    return df_filled.to_dict(orient="records")
