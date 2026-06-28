from datetime import datetime
from zoneinfo import ZoneInfo
import unittest

from market_calendar import expected_china_morning_report_date


class MarketCalendarTest(unittest.TestCase):
    def assert_expected(self, china_time: str, expected: str | None) -> None:
        now = datetime.strptime(china_time, "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("Asia/Shanghai"))
        actual = expected_china_morning_report_date(now)
        self.assertEqual(actual.isoformat() if actual else None, expected)

    def test_regular_week_china_morning_schedule(self) -> None:
        self.assert_expected("2026-06-23 09:05", "2026-06-22")
        self.assert_expected("2026-06-24 09:05", "2026-06-23")
        self.assert_expected("2026-06-25 09:05", "2026-06-24")
        self.assert_expected("2026-06-26 09:05", "2026-06-25")
        self.assert_expected("2026-06-27 09:05", "2026-06-26")

    def test_china_sunday_and_monday_skip_to_avoid_duplicate_friday(self) -> None:
        self.assert_expected("2026-06-28 09:05", None)
        self.assert_expected("2026-06-29 09:05", None)

    def test_us_market_holidays_skip_without_replaying_old_data(self) -> None:
        self.assert_expected("2026-06-19 09:05", "2026-06-18")
        self.assert_expected("2026-06-20 09:05", None)
        self.assert_expected("2026-09-08 09:05", None)
        self.assert_expected("2026-09-09 09:05", "2026-09-08")
        self.assert_expected("2026-12-26 09:05", None)
        self.assert_expected("2026-12-29 09:05", "2026-12-28")


if __name__ == "__main__":
    unittest.main()
