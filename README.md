# tobira-weather

1 週間後の現在時刻の京都の天気を [Open-Meteo](https://open-meteo.com/) から取得して表示し、天気に対応する画像をブラウザで開くスクリプトです。Raspberry Pi Zero W で動かすことを想定しています。

```
$ python3 kyoto_weather.py
2026-11-07 23:00 の京都の天気: 晴れ
```

天気は「晴れ」「くもり」「霧」「雨」「雪」「雷雨」「不明」のどれかで表示します。どの天気コードがどれにあたるかは、[docs/weather_codes.md](docs/weather_codes.md) にまとめています。

## 必要なもの

- Raspberry Pi Zero W
- Raspberry Pi OS Trixie（32-bit、デスクトップ付き）
- インターネット接続
- ブラウザ epiphany（下の手順で入れる）

Python は OS に入っている `python3` をそのまま使います。追加の Python パッケージは不要です。

## ラズパイでの準備

ラズパイのデスクトップでターミナルを開き、次を実行します。

1. epiphany を入れる。

   ```sh
   sudo apt update
   sudo apt install -y epiphany-browser
   ```

   Raspberry Pi OS の標準のブラウザは Chromium ですが、Chromium は Pi Zero W（ARMv6）では動きません。そのため epiphany を使います。

2. epiphany の「既定のブラウザにしますか?」という確認を出さないようにする。

   ```sh
   gsettings set org.gnome.Epiphany ask-for-default false
   ```

   この確認が出ると、画像のページより前に確認の画面が出てしまいます。デスクトップにログインするユーザーで実行してください。

3. このリポジトリを取得する。

   ```sh
   git clone https://github.com/jonosuke/tobira-weather.git
   ```

   `git` が入っていない場合は、`sudo apt install -y git` で入れます。GitHub の「Code」→「Download ZIP」でダウンロードして展開してもかまいません。

## 実行する

```sh
cd tobira-weather
python3 kyoto_weather.py
```

- 天気をターミナルに表示したあと、対応する画像を epiphany で開きます。
- epiphany がすでに開いている場合は、新しいタブで開きます。
- Pi Zero W は動作が遅いため、画像が表示されるまでしばらくかかります。開発用 VM では、epiphany の起動から表示まで 30 秒ほどかかりました。
- SSH から実行した場合も、ラズパイの画面（`:0`）に表示します。

`kyoto_weather.py` と `images/` フォルダは、同じ場所に置いておく必要があります。スクリプトだけを別の場所にコピーすると、画像が見つからなくなります。

### うまくいかないとき

| 症状 | 原因と対処 |
| --- | --- |
| 「天気を取得できませんでした」と表示される | インターネットにつながっていません。ネットワークの接続を確認してください。 |
| ブラウザが開かない、または Chromium が開こうとする | epiphany が入っていません。「ラズパイでの準備」の 1 を実行してください。 |
| 画像の代わりに「既定のブラウザにしますか?」が出る | 「ラズパイでの準備」の 2 を実行してください。 |
| ブラウザに「ファイルが見つからない」と出る | `images/` フォルダがスクリプトと同じ場所にありません。 |

## 場所と時間を変える

`kyoto_weather.py` の次の部分を書き換えます。

| 変えたいもの | 書き換える場所 |
| --- | --- |
| 場所 | `KYOTO_LATITUDE` と `KYOTO_LONGITUDE`（緯度と経度） |
| 何日後か | `main()` の中の `timedelta(days=7)` |
| 時間帯 | `TIMEZONE`（初期値は `Asia/Tokyo`） |

- Open-Meteo は地名を受け付けないため、場所は緯度と経度で指定します。
- 予報を取れるのは 16 日後までです。
- 予報は 1 時間ごとなので、分は切り捨てて使います。

## ディレクトリ構成

```
.
├── kyoto_weather.py   天気を取得して画像を開くスクリプト
├── images/            天気ごとの画像（SVG）
├── docs/              ドキュメント
│   └── weather_codes.md   天気コードの一覧
└── vm/                Mac で動かす開発用 VM（UTM）の構築手順とスクリプト
```

## 開発用 VM

実機がなくても、Mac の UTM 上の VM で動作を確認できます。VM の作り方と使い方は [vm/README.md](vm/README.md) を見てください。

## 動作確認の状況

- 開発用 VM（Raspberry Pi OS Trixie、Python 3.13）で、天気の取得と画像の表示を確認しています。
- 実機の Pi Zero W では、まだ確認していません。VM の CPU は ARMv7 のため、ARMv6 の実機でしか起きない問題は VM では見つかりません。実機で動かして問題があれば知らせてください。
