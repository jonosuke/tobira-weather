import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .prefecture import Prefecture
from .weather import Weather, WeatherDetail

API_URL = "https://api.open-meteo.com/v1/forecast"
JST = ZoneInfo("Asia/Tokyo")
MAX_DAYS = 15
"""get_weather_in_days で指定できる最大の日数。Open-Meteo の予報は今日を含めて 16 日分。"""


@dataclass(frozen=True)
class Forecast:
    latitude: float
    longitude: float
    time: datetime
    """予報の対象の時刻 (日本時間、分以下は切り捨て)。"""
    code: int
    """Open-Meteo が返した WMO 天気コード。"""
    weather: Weather | WeatherDetail
    """summarize=True なら Weather (大まかな天気)、False なら WeatherDetail (天気コードごとの天気)。"""
    temperature: float
    """気温 (℃、地上 2 m)。"""
    wind_speed: float
    """風速 (m/s、地上 10 m)。"""


class WeatherError(Exception):
    """天気を取得できなかった。範囲外の日時や緯度経度を指定した場合も含む。"""


def get_weather_at(latitude: float, longitude: float, when: datetime, *,
                   summarize: bool = True) -> Forecast:
    """緯度 latitude・経度 longitude の、when の時刻の予報 (天気・気温・風速) を返す。

    時刻はすべて日本時間で扱う。タイムゾーンのない when は日本時間とみなし、
    タイムゾーンの付いた when は日本時間に直す。予報は 1 時間単位のため、分以下は切り捨てる。
    取得できるのはおよそ 3 か月前から MAX_DAYS 日後まで。取得の失敗は WeatherError。
    """
    when = when.replace(tzinfo=JST) if when.tzinfo is None else when.astimezone(JST)
    hour = when.replace(minute=0, second=0, microsecond=0)
    hour_param = hour.strftime("%Y-%m-%dT%H:%M")
    query = urllib.parse.urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "weather_code,temperature_2m,wind_speed_10m",
        "wind_speed_unit": "ms",
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
    hourly = data["hourly"]
    code = hourly["weather_code"][0]
    detail = WeatherDetail.from_code(code)
    return Forecast(latitude, longitude, hour, code, detail.weather if summarize else detail,
                    hourly["temperature_2m"][0], hourly["wind_speed_10m"][0])


def get_weather(prefecture: Prefecture | str, when: datetime, *, summarize: bool = True) -> Forecast:
    """都道府県庁の位置の、when の時刻の予報を返す。知らない都道府県名は ValueError。"""
    prefecture = Prefecture(prefecture)
    return get_weather_at(prefecture.latitude, prefecture.longitude, when, summarize=summarize)


def get_weather_in_days(prefecture: Prefecture | str, days: int, *, summarize: bool = True) -> Forecast:
    """days 日後の、今と同じ時刻 (日本時間) の予報を返す。days は 1 から MAX_DAYS。"""
    if not 1 <= days <= MAX_DAYS:
        raise ValueError(f"days は 1 から {MAX_DAYS} の範囲で指定してください: {days}")
    return get_weather(prefecture, datetime.now(JST) + timedelta(days=days), summarize=summarize)


def _error_reason(error: urllib.error.HTTPError) -> str:
    # Open-Meteo は失敗の理由を {"error": true, "reason": "..."} で返す
    try:
        return json.load(error)["reason"]
    except (ValueError, KeyError):
        return str(error)
