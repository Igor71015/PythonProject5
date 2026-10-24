import pandas as pd
from src.reports import spending_by_category


def test_spending_by_category_empty():
    df = pd.DataFrame()
    result = spending_by_category(df, "Супермаркеты")
    assert result.empty
