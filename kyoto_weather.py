"""Open-Meteo から、1 週間後の現在時刻の京都の天気を取得して表示する。

予報は 1 時間単位のため、現在時刻の「時」(分は切り捨て) の予報を使う。
標準ライブラリだけで動く (Raspberry Pi OS Trixie の Python 3.13 で確認)。

    python3 kyoto_weather.py
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

API_URL = "https://api.open-meteo.com/v1/forecast"
KYOTO_LATITUDE = 35.0116
KYOTO_LONGITUDE = 135.7681
TIMEZONE = ZoneInfo("Asia/Tokyo")

# WMO 天気コードを大まかな天気にまとめる
# 一覧: https://open-meteo.com/en/docs の "WMO Weather interpretation codes"
WEATHER_BY_CODE = {
    **dict.fromkeys([0, 1, 2], "晴れ"),
    3: "くもり",
    **dict.fromkeys([45, 48], "霧"),
    **dict.fromkeys([51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82], "雨"),
    **dict.fromkeys([71, 73, 75, 77, 85, 86], "雪"),
    **dict.fromkeys([95, 96, 97, 99], "雷雨"),
}


def fetch_weather_code(target: datetime) -> int:
    hour = target.strftime("%Y-%m-%dT%H:00")
    query = urllib.parse.urlencode({
        "latitude": KYOTO_LATITUDE,
        "longitude": KYOTO_LONGITUDE,
        "hourly": "weather_code",
        "timezone": TIMEZONE.key,
        "start_hour": hour,
        "end_hour": hour,
    })
    with urllib.request.urlopen(f"{API_URL}?{query}", timeout=30) as response:
        data = json.load(response)
    return data["hourly"]["weather_code"][0]


def main():
    target = (datetime.now(TIMEZONE) + timedelta(days=7)).replace(minute=0, second=0, microsecond=0)
    try:
        code = fetch_weather_code(target)
    except (urllib.error.URLError, TimeoutError) as error:
        sys.exit(f"天気を取得できませんでした: {error}")
    weather = WEATHER_BY_CODE.get(code, f"不明 (天気コード {code})")
    print(f"{target:%Y-%m-%d %H:%M} の京都の天気: {weather}")


if __name__ == "__main__":
    main()
