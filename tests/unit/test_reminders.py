import pytest

from src.infrastructure.db.models.user import User
from src.services.reminders import content
from src.services.reminders.scheduler import _cron_kwargs


def _user(**overrides: object) -> User:
    defaults = {
        "telegram_id": 1,
        "xp": 0,
        "streak_days": 0,
        "current_level": "A2",
        "target_level": "B2",
    }
    return User(**{**defaults, **overrides})


def test_daily_message_mentions_streak_when_active() -> None:
    text = content.build_daily_message(_user(streak_days=5))
    assert "5 day(s)" in text


def test_daily_message_omits_streak_line_when_zero() -> None:
    text = content.build_daily_message(_user(streak_days=0))
    assert "Current streak" not in text


def test_weekly_message_nudges_on_quiet_week() -> None:
    text = content.build_weekly_message(_user(), new_vocab=0, mistakes_logged=0)
    assert "Quiet week" in text


def test_cron_kwargs_daily() -> None:
    assert _cron_kwargs("daily", 19, 30) == {"hour": 19, "minute": 30}


def test_cron_kwargs_weekly() -> None:
    assert _cron_kwargs("weekly", 9, 0) == {"day_of_week": "mon", "hour": 9, "minute": 0}


def test_cron_kwargs_monthly() -> None:
    assert _cron_kwargs("monthly", 9, 0) == {"day": 1, "hour": 9, "minute": 0}


def test_cron_kwargs_rejects_unknown_type() -> None:
    with pytest.raises(ValueError):
        _cron_kwargs("yearly", 0, 0)
