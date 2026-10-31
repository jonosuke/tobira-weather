"""Open-Meteo から、1 週間後の現在時刻の京都の天気を取得して表示し、
天気に対応する画像 (images/*.svg) をブラウザで開く。

予報は 1 時間単位のため、現在時刻の「時」(分は切り捨て) の予報を使う。
標準ライブラリだけで動く (Raspberry Pi OS Trixie の Python 3.13 で確認)。

    python3 kyoto_weather.py

ブラウザは epiphany があればそれを使い (Pi Zero W で動くのは epiphany だけ)、
なければ OS の既定のブラウザを使う。SSH から実行しても VM / 実機の画面 (:0) に表示する。
"""
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

API_URL = "https://api.open-meteo.com/v1/forecast"
KYOTO_LATITUDE = 35.0116
KYOTO_LONGITUDE = 135.7681
TIMEZONE = ZoneInfo("Asia/Tokyo")
IMAGE_DIR = Path(__file__).resolve().parent / "images"

# 天気の種類ごとの表示名。画像は images/<種類>.svg
WEATHER_NAMES = {
    "sunny": "晴れ",
    "cloudy": "くもり",
    "fog": "霧",
    "rain": "雨",
    "snow": "雪",
    "thunder": "雷雨",
    "unknown": "不明",
}

# WMO 天気コードを大まかな天気にまとめる
# 一覧: https://open-meteo.com/en/docs の "WMO Weather interpretation codes"
WEATHER_BY_CODE = {
    **dict.fromkeys([0, 1, 2], "sunny"),
    3: "cloudy",
    **dict.fromkeys([45, 48], "fog"),
    **dict.fromkeys([51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82], "rain"),
    **dict.fromkeys([71, 73, 75, 77, 85, 86], "snow"),
    **dict.fromkeys([95, 96, 97, 99], "thunder"),
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


def open_image(weather: str):
    url = (IMAGE_DIR / f"{weather}.svg").as_uri()
    if shutil.which("epiphany"):
        env = {**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")}
        subprocess.Popen(["epiphany", url], env=env, start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        webbrowser.open(url)


def main():
    target = (datetime.now(TIMEZONE) + timedelta(days=7)).replace(minute=0, second=0, microsecond=0)
    try:
        code = fetch_weather_code(target)
    except (urllib.error.URLError, TimeoutError) as error:
        sys.exit(f"天気を取得できませんでした: {error}")
    weather = WEATHER_BY_CODE.get(code, "unknown")
    name = WEATHER_NAMES[weather]
    if weather == "unknown":
        name += f" (天気コード {code})"
    print(f"{target:%Y-%m-%d %H:%M} の京都の天気: {name}")
    open_image(weather)


if __name__ == "__main__":
    main()
