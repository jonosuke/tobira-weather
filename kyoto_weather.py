"""1 週間後の現在時刻の京都の天気を表示し、天気に対応する画像 (images/*.svg) をブラウザで開く。

    python3 kyoto_weather.py

ブラウザは epiphany があればそれを使い (Pi Zero W で動くのは epiphany だけ)、
なければ OS の既定のブラウザを使う。SSH から実行しても VM / 実機の画面 (:0) に表示する。
"""
import os
import shutil
import subprocess
import sys
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

from tobira_weather import Prefecture, Weather, WeatherError, get_weather

IMAGE_DIR = Path(__file__).resolve().parent / "images"


def open_image(weather: Weather):
    url = (IMAGE_DIR / f"{weather.name.lower()}.svg").as_uri()
    if shutil.which("epiphany"):
        env = {**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")}
        subprocess.Popen(["epiphany", url], env=env, start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        webbrowser.open(url)


def main():
    try:
        forecast = get_weather(Prefecture.KYOTO, datetime.now().astimezone() + timedelta(days=7))
    except WeatherError as error:
        sys.exit(f"天気を取得できませんでした: {error}")
    name = forecast.weather.value
    if forecast.weather is Weather.UNKNOWN:
        name += f" (天気コード {forecast.code})"
    print(f"{forecast.time:%Y-%m-%d %H:%M} の京都の天気: {name}")
    open_image(forecast.weather)


if __name__ == "__main__":
    main()
