from enum import StrEnum


class Weather(StrEnum):
    """大まかな天気。値は表示名。"""

    SUNNY = "晴れ"
    CLOUDY = "くもり"
    FOG = "霧"
    RAIN = "雨"
    SNOW = "雪"
    THUNDER = "雷雨"
    UNKNOWN = "不明"


class WeatherDetail(StrEnum):
    """WMO 天気コードごとの天気。値は表示名で、code と、まとめたときの weather を持つ。

    一覧: https://open-meteo.com/en/docs の "WMO Weather interpretation codes"
    96 と 99 (ひょう) は、ひょうを予報する気象モデルを使ったときだけ返る。
    """

    code: int | None
    weather: Weather

    def __new__(cls, label: str, code: int | None, weather: Weather):
        member = str.__new__(cls, label)
        member._value_ = label
        member.code = code
        member.weather = weather
        return member

    @classmethod
    def from_code(cls, code: int) -> "WeatherDetail":
        return _DETAIL_BY_CODE.get(code, cls.UNKNOWN)

    CLEAR = "快晴", 0, Weather.SUNNY
    MAINLY_CLEAR = "おおむね晴れ", 1, Weather.SUNNY
    PARTLY_CLOUDY = "一部くもり", 2, Weather.SUNNY
    OVERCAST = "くもり", 3, Weather.CLOUDY
    FOG = "霧", 45, Weather.FOG
    RIME_FOG = "着氷性の霧", 48, Weather.FOG
    LIGHT_DRIZZLE = "弱い霧雨", 51, Weather.RAIN
    DRIZZLE = "霧雨", 53, Weather.RAIN
    DENSE_DRIZZLE = "強い霧雨", 55, Weather.RAIN
    LIGHT_FREEZING_DRIZZLE = "弱い着氷性の霧雨", 56, Weather.RAIN
    DENSE_FREEZING_DRIZZLE = "強い着氷性の霧雨", 57, Weather.RAIN
    LIGHT_RAIN = "弱い雨", 61, Weather.RAIN
    RAIN = "雨", 63, Weather.RAIN
    HEAVY_RAIN = "強い雨", 65, Weather.RAIN
    LIGHT_FREEZING_RAIN = "弱い着氷性の雨", 66, Weather.RAIN
    HEAVY_FREEZING_RAIN = "強い着氷性の雨", 67, Weather.RAIN
    LIGHT_SNOW = "弱い雪", 71, Weather.SNOW
    SNOW = "雪", 73, Weather.SNOW
    HEAVY_SNOW = "強い雪", 75, Weather.SNOW
    SNOW_GRAINS = "霧雪", 77, Weather.SNOW
    LIGHT_SHOWERS = "弱いにわか雨", 80, Weather.RAIN
    SHOWERS = "にわか雨", 81, Weather.RAIN
    VIOLENT_SHOWERS = "激しいにわか雨", 82, Weather.RAIN
    LIGHT_SNOW_SHOWERS = "弱いにわか雪", 85, Weather.SNOW
    HEAVY_SNOW_SHOWERS = "強いにわか雪", 86, Weather.SNOW
    THUNDERSTORM = "雷雨", 95, Weather.THUNDER
    THUNDERSTORM_WITH_LIGHT_HAIL = "弱いひょうを伴う雷雨", 96, Weather.THUNDER
    HEAVY_THUNDERSTORM = "強い雷雨", 97, Weather.THUNDER
    THUNDERSTORM_WITH_HEAVY_HAIL = "強いひょうを伴う雷雨", 99, Weather.THUNDER
    UNKNOWN = "不明", None, Weather.UNKNOWN


_DETAIL_BY_CODE = {detail.code: detail for detail in WeatherDetail if detail.code is not None}
