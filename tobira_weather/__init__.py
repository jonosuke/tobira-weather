"""Open-Meteo から、都道府県と日時を指定して天気を取得するライブラリ。

    from datetime import datetime
    from tobira_weather import Prefecture, get_weather

    forecast = get_weather(Prefecture.KYOTO, datetime(2026, 11, 18, 15))
    print(forecast.weather)   # 晴れ

都道府県は名前の文字列 (get_weather("京都府", ...)) でも指定できる。
標準ライブラリだけで動く (Raspberry Pi OS Trixie の Python 3.13 で確認)。
"""
from .forecast import Forecast, Weather, WeatherError, get_weather
from .prefecture import Prefecture

__all__ = ["Forecast", "Prefecture", "Weather", "WeatherError", "get_weather"]
