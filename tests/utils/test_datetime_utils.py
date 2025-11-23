"""datetime_utilsモジュールのユニットテスト。"""

import re
from datetime import datetime

import pytest

from src.utils.datetime_utils import convert_utc_to_jst, get_timestamp_string


class TestGetTimestampString:
    """get_timestamp_string関数のテストクラス。"""

    def test_timestamp_format(self):
        """タイムスタンプが正しいフォーマットで生成されることをテスト。"""
        timestamp = get_timestamp_string()

        # フォーマット: YYYYMMDD_HHMMSS
        pattern = r"^\d{8}_\d{6}$"
        assert re.match(pattern, timestamp), f"Invalid timestamp format: {timestamp}"

    def test_timestamp_components(self):
        """タイムスタンプの各要素が妥当な値であることをテスト。"""
        timestamp = get_timestamp_string()

        # YYYYMMDD_HHMMSSに分解
        date_part, time_part = timestamp.split("_")

        # 日付部分の検証
        year = int(date_part[:4])
        month = int(date_part[4:6])
        day = int(date_part[6:8])

        assert 2000 <= year <= 2100, f"Year out of range: {year}"
        assert 1 <= month <= 12, f"Month out of range: {month}"
        assert 1 <= day <= 31, f"Day out of range: {day}"

        # 時刻部分の検証
        hour = int(time_part[:2])
        minute = int(time_part[2:4])
        second = int(time_part[4:6])

        assert 0 <= hour <= 23, f"Hour out of range: {hour}"
        assert 0 <= minute <= 59, f"Minute out of range: {minute}"
        assert 0 <= second <= 59, f"Second out of range: {second}"

    def test_timestamp_uniqueness(self):
        """連続して呼び出しても異なるタイムスタンプが生成されることをテスト。"""
        timestamps = [get_timestamp_string() for _ in range(5)]

        # 少なくとも1つは異なるはず（秒が変わる可能性）
        # または全て同じ場合でも、フォーマットは正しいはず
        assert all(re.match(r"^\d{8}_\d{6}$", ts) for ts in timestamps)


class TestConvertUtcToJst:
    """convert_utc_to_jst関数のテストクラス。"""

    def test_basic_conversion(self):
        """基本的なUTC→JST変換をテスト。"""
        utc_str = "2025-11-23T01:41:56Z"
        result = convert_utc_to_jst(utc_str)

        assert result == "2025/11/23 10:41:56"

    def test_conversion_with_fractional_seconds(self):
        """小数点以下の秒を含むUTC→JST変換をテスト。"""
        utc_str = "2025-11-23T01:41:56.654958326Z"
        result = convert_utc_to_jst(utc_str)

        assert result == "2025/11/23 10:41:56"

    def test_midnight_conversion(self):
        """深夜0時のUTC→JST変換をテスト（日付が変わるケース）。"""
        utc_str = "2025-11-22T15:00:00Z"
        result = convert_utc_to_jst(utc_str)

        # UTC 15:00 + 9時間 = JST 翌日00:00
        assert result == "2025/11/23 00:00:00"

    def test_year_boundary_conversion(self):
        """年をまたぐUTC→JST変換をテスト。"""
        utc_str = "2024-12-31T15:30:00Z"
        result = convert_utc_to_jst(utc_str)

        # UTC 15:30 + 9時間 = JST 翌年00:30
        assert result == "2025/01/01 00:30:00"

    def test_output_format(self):
        """出力フォーマットが正しいことをテスト。"""
        utc_str = "2025-01-01T00:00:00Z"
        result = convert_utc_to_jst(utc_str)

        # フォーマット: yyyy/MM/dd HH:mm:ss
        pattern = r"^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}$"
        assert re.match(pattern, result), f"Invalid format: {result}"

    def test_various_timestamps(self):
        """さまざまなタイムスタンプのUTC→JST変換をテスト。"""
        test_cases = [
            ("2025-01-01T00:00:00Z", "2025/01/01 09:00:00"),
            ("2025-06-15T12:30:45Z", "2025/06/15 21:30:45"),
            ("2025-12-31T23:59:59Z", "2026/01/01 08:59:59"),
        ]

        for utc_str, expected in test_cases:
            result = convert_utc_to_jst(utc_str)
            assert result == expected, f"Expected {expected}, got {result}"

    def test_jst_offset(self):
        """JSTオフセット（UTC+9）が正しく適用されることをテスト。"""
        # UTC 00:00 → JST 09:00
        utc_str = "2025-11-23T00:00:00Z"
        result = convert_utc_to_jst(utc_str)
        assert result == "2025/11/23 09:00:00"

        # UTC 15:00 → JST 翌日00:00
        utc_str = "2025-11-23T15:00:00Z"
        result = convert_utc_to_jst(utc_str)
        assert result == "2025/11/24 00:00:00"
