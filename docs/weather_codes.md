# Open-Meteo の天気の種類

Open-Meteo は、天気を「WMO 天気コード」という数値で返す。ライブラリ `tobira_weather` では、29種類のコードを6つの大まかな天気（`Weather`）にまとめて返す。`summarize=False` を指定すると、まとめずにコードごとの天気（`WeatherDetail`）を返す。

## 天気コードの一覧

| まとめた天気（`Weather`） | 天気コード | まとめない天気（`WeatherDetail`） | `WeatherDetail` のメンバー |
| --- | --- | --- | --- |
| 晴れ | 0 | 快晴 | `CLEAR` |
| 晴れ | 1 | おおむね晴れ | `MAINLY_CLEAR` |
| 晴れ | 2 | 一部くもり | `PARTLY_CLOUDY` |
| くもり | 3 | くもり | `OVERCAST` |
| 霧 | 45 | 霧 | `FOG` |
| 霧 | 48 | 着氷性の霧 | `RIME_FOG` |
| 雨 | 51 | 弱い霧雨 | `LIGHT_DRIZZLE` |
| 雨 | 53 | 霧雨 | `DRIZZLE` |
| 雨 | 55 | 強い霧雨 | `DENSE_DRIZZLE` |
| 雨 | 56 | 弱い着氷性の霧雨 | `LIGHT_FREEZING_DRIZZLE` |
| 雨 | 57 | 強い着氷性の霧雨 | `DENSE_FREEZING_DRIZZLE` |
| 雨 | 61 | 弱い雨 | `LIGHT_RAIN` |
| 雨 | 63 | 雨 | `RAIN` |
| 雨 | 65 | 強い雨 | `HEAVY_RAIN` |
| 雨 | 66 | 弱い着氷性の雨 | `LIGHT_FREEZING_RAIN` |
| 雨 | 67 | 強い着氷性の雨 | `HEAVY_FREEZING_RAIN` |
| 雪 | 71 | 弱い雪 | `LIGHT_SNOW` |
| 雪 | 73 | 雪 | `SNOW` |
| 雪 | 75 | 強い雪 | `HEAVY_SNOW` |
| 雪 | 77 | 霧雪 | `SNOW_GRAINS` |
| 雨 | 80 | 弱いにわか雨 | `LIGHT_SHOWERS` |
| 雨 | 81 | にわか雨 | `SHOWERS` |
| 雨 | 82 | 激しいにわか雨 | `VIOLENT_SHOWERS` |
| 雪 | 85 | 弱いにわか雪 | `LIGHT_SNOW_SHOWERS` |
| 雪 | 86 | 強いにわか雪 | `HEAVY_SNOW_SHOWERS` |
| 雷雨 | 95 | 雷雨 | `THUNDERSTORM` |
| 雷雨 | 96 | 弱いひょうを伴う雷雨 | `THUNDERSTORM_WITH_LIGHT_HAIL` |
| 雷雨 | 97 | 強い雷雨 | `HEAVY_THUNDERSTORM` |
| 雷雨 | 99 | 強いひょうを伴う雷雨 | `THUNDERSTORM_WITH_HEAVY_HAIL` |

## 補足

- コード2（一部くもり）は「晴れ」に含めている。「くもり」にしたい場合は、`tobira_weather/weather.py` の `WeatherDetail.PARTLY_CLOUDY` の `Weather.SUNNY` を `Weather.CLOUDY` に書き換える。
- 一覧にないコードが返ってきた場合は、まとめた天気もまとめない天気も「不明」（`Weather.UNKNOWN`、`WeatherDetail.UNKNOWN`）になる。`kyoto_weather.py` は「不明 (天気コード XX)」と表示する。
- `kyoto_weather.py` は、表示した天気に対応する画像をブラウザで開く。画像は `images/` にあり、晴れ `sunny.svg`、くもり `cloudy.svg`、霧 `fog.svg`、雨 `rain.svg`、雪 `snow.svg`、雷雨 `thunder.svg`、不明 `unknown.svg`。
- 96 と 99（ひょう）は、ひょうを予報する気象モデル（DWD ICON、UKMO など）を使ったときだけ返る。それ以外のモデルでは 95 か 97 になる。
- 2026-10-31 に京都の今後8日分の予報で実際に出ていたコードは、0、1、2、3、51、53、55、61、63、80、81。
- コードの公式の一覧は https://open-meteo.com/en/docs の「WMO Weather interpretation codes」にある。
