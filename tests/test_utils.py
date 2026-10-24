from src.utils import load_user_settings


def test_load_user_settings():
    settings = load_user_settings()
    assert "user_currencies" in settings
    assert "user_stocks" in settings
