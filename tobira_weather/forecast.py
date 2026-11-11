import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

from .prefecture import Prefecture

API_URL = "https://api.open-meteo.com/v1/forecast"
JST = ZoneInfo("Asia/Tokyo")
MAX_DAYS = 15
"""get_weather_in_days で指定できる最大の日数。Open-Meteo の予報は今日を含めて 16 日分。"""


class Weather(StrEnum):
    """大まかな天気。値は表示名。"""

    SUNNY = "晴れ"
    CLOUDY = "くもり"
    FOG = "霧"
    RAIN = "雨"
    SNOW = "雪"
    THUNDER = "雷雨"
    UNKNOWN = "不明"


# WMO 天気コードを大まかな天気にまとめる
# 一覧: https://open-meteo.com/en/docs の "WMO Weather interpretation codes"
WEATHER_BY_CODE = {
    **dict.fromkeys([0, 1, 2], Weather.SUNNY),
    3: Weather.CLOUDY,
    **dict.fromkeys([45, 48], Weather.FOG),
    **dict.fromkeys([51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82], Weather.RAIN),
    **dict.fromkeys([71, 73, 75, 77, 85, 86], Weather.SNOW),
    **dict.fromkeys([95, 96, 97, 99], Weather.THUNDER),
}


@dataclass(frozen=True)
class Forecast:
    prefecture: Prefecture
    time: datetime
    """予報の対象の時刻 (日本時間、分以下は切り捨て)。"""
    code: int
    """Open-Meteo が返した WMO 天気コード。"""

    @property
    def weather(self) -> Weather:
        return WEATHER_BY_CODE.get(self.code, Weather.UNKNOWN)


class WeatherError(Exception):
    """天気を取得できなかった。範囲外の日時を指定した場合も含む。"""


def get_weather(prefecture: Prefecture | str, when: datetime) -> Forecast:
    """都道府県庁の位置の、when の時刻の予報を返す。

    時刻はすべて日本時間で扱う。タイムゾーンのない when は日本時間とみなし、
    タイムゾーンの付いた when は日本時間に直す。予報は 1 時間単位のため、分以下は切り捨てる。
    取得できるのはおよそ 3 か月前から MAX_DAYS 日後まで。
    知らない都道府県名は ValueError、取得の失敗は WeatherError。
    """
    prefecture = Prefecture(prefecture)
    when = when.replace(tzinfo=JST) if when.tzinfo is None else when.astimezone(JST)
    hour = when.replace(minute=0, second=0, microsecond=0)
    hour_param = hour.strftime("%Y-%m-%dT%H:%M")
    query = urllib.parse.urlencode({
        "latitude": prefecture.latitude,
        "longitude": prefecture.longitude,
        "hourly": "weather_code",
        "timezone": JST.key,
        "start_hour": hour_param,
        "end_hour": hour_param,
    })
    try:
        with urllib.request.urlopen(f"{API_URL}?{query}", timeout=30) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        raise WeatherError(_error_reason(error)) from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise WeatherError(f"Open-Meteo に接続できませんでした: {error}") from error
    return Forecast(prefecture, hour, data["hourly"]["weather_code"][0])


def get_weather_in_days(prefecture: Prefecture | str, days: int) -> Forecast:
    """days 日後の、今と同じ時刻 (日本時間) の予報を返す。days は 1 から MAX_DAYS。"""
    if not 1 <= days <= MAX_DAYS:
        raise ValueError(f"days は 1 から {MAX_DAYS} の範囲で指定してください: {days}")
    return get_weather(prefecture, datetime.now(JST) + timedelta(days=days))


def _error_reason(error: urllib.error.HTTPError) -> str:
    # Open-Meteo は失敗の理由を {"error": true, "reason": "..."} で返す
    try:
        return json.load(error)["reason"]
    except (ValueError, KeyError):
        return str(error)
