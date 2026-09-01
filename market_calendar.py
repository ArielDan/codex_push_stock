"""Small NYSE trading-day calendar for report scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


CHINA_TZ = ZoneInfo("Asia/Shanghai")
NY_TZ = ZoneInfo("America/New_York")
OPEN_WATCH_START = time(9, 58)
OPEN_WATCH_END = time(10, 12)


@dataclass(frozen=True)
class OpenWatchWindow:
    ny_now: datetime
    is_trading_day: bool
    in_window: bool
    session_date: date
    window_start: datetime
    window_end: datetime


def expected_china_morning_report_date(now: datetime) -> date | None:
    """Return the US session that a China morning run is allowed to send."""
    china_now = now.astimezone(CHINA_TZ)
    ny_date = china_now.astimezone(NY_TZ).date()
    if not is_trading_day(ny_date):
        return None
    return ny_date


def previous_trading_day(day: date) -> date:
    current = day
    while not is_trading_day(current):
        current -= timedelta(days=1)
    return current


def is_trading_day(day: date) -> bool:
    return day.weekday() < 5 and day not in nyse_holidays(day.year)


def open_watch_window_status(now: datetime) -> OpenWatchWindow:
    """Return whether a run is inside the US open +30 minute watch window."""
    ny_now = now.astimezone(NY_TZ)
    session_date = ny_now.date()
    window_start = datetime.combine(session_date, OPEN_WATCH_START, tzinfo=NY_TZ)
    window_end = datetime.combine(session_date, OPEN_WATCH_END, tzinfo=NY_TZ)
    trading_day = is_trading_day(session_date)
    return OpenWatchWindow(
        ny_now=ny_now,
        is_trading_day=trading_day,
        in_window=trading_day and window_start <= ny_now <= window_end,
        session_date=session_date,
        window_start=window_start,
        window_end=window_end,
    )


def nyse_holidays(year: int) -> set[date]:
    holidays = {
        _observed_fixed_holiday(year, 1, 1),
        _nth_weekday(year, 1, 0, 3),  # Martin Luther King Jr. Day
        _nth_weekday(year, 2, 0, 3),  # Washington's Birthday
        _good_friday(year),
        _last_weekday(year, 5, 0),  # Memorial Day
        _observed_fixed_holiday(year, 6, 19),  # Juneteenth
        _observed_fixed_holiday(year, 7, 4),  # Independence Day
        _nth_weekday(year, 9, 0, 1),  # Labor Day
        _nth_weekday(year, 11, 3, 4),  # Thanksgiving
        _observed_fixed_holiday(year, 12, 25),
    }
    return {holiday for holiday in holidays if holiday.year == year}


def _observed_fixed_holiday(year: int, month: int, day: int) -> date:
    holiday = date(year, month, day)
    if holiday.weekday() == 5:
        return holiday - timedelta(days=1)
    if holiday.weekday() == 6:
        return holiday + timedelta(days=1)
    return holiday


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    current = date(year, month, 1)
    days_until_weekday = (weekday - current.weekday()) % 7
    return current + timedelta(days=days_until_weekday + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    if month == 12:
        current = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        current = date(year, month + 1, 1) - timedelta(days=1)
    return current - timedelta(days=(current.weekday() - weekday) % 7)


def _good_friday(year: int) -> date:
    return _easter_sunday(year) - timedelta(days=2)


def _easter_sunday(year: int) -> date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)
