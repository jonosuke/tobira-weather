"""Open-Meteo から、都道府県と日時を指定して天気を取得するライブラリ。

    from datetime import datetime
    from tobira_weather import Prefecture, get_weather, get_weather_in_days

    forecast = get_weather(Prefecture.KYOTO, datetime(2026, 11, 18, 15))
    print(forecast.weather)   # 晴れ
    forecast = get_weather_in_days(Prefecture.NIIGATA, 10)   # 10 日後の今の時刻

時刻はすべて日本時間で扱う。都道府県は名前の文字列 (get_weather("京都府", ...)) でも指定できる。
標準ライブラリだけで動く (Raspberry Pi OS Trixie の Python 3.13 で確認)。
"""
from .forecast import MAX_DAYS, Forecast, Weather, WeatherError, get_weather, get_weather_in_days
from .prefecture import Prefecture

__all__ = [
    "MAX_DAYS", "Forecast", "Prefecture", "Weather", "WeatherError",
    "get_weather", "get_weather_in_days",
]
