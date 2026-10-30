# Raspberry Pi Zero W 開発用 VM（UTM / Raspberry Pi OS Trixie）

Apple Silicon Mac の UTM 上で、Raspberry Pi Zero W と同じ **Raspberry Pi OS Trixie 32-bit（デスクトップ版）** を動かします。用途は、Python（pyautogui）からブラウザや VLC を操作するスクリプトの動作確認です。

## この VM で再現できること・できないこと

| 項目 | 実機（Pi Zero W） | この VM |
|---|---|---|
| OS / パッケージ | Raspberry Pi OS Trixie 32-bit（ARMv6 ビルド） | **同じイメージ**（2026-10-06 版） |
| Python / VLC | 3.13.5 / 3.0.23 | **同じ** |
| ブラウザ | **Epiphany（WebKitGTK）のみ使える**（下記） | Epiphany のほか、Firefox / Chromium も動く |
| デスクトップ | X11（openbox）に切り替えて使用 | 同じ（X11） |
| カーネル | Raspberry Pi カーネル | **Debian 汎用カーネル（6.12 armmp-lpae）**。ラズパイ用カーネルは QEMU の virt では起動しないため |
| CPU | ARM1176（ARMv6）1 コア | Cortex-A7（ARMv7）1 コアのエミュレーション |
| メモリ | 512MB | 512MB |
| Wi-Fi / Bluetooth / GPIO / 音声 / 動画のハードウェアデコード | あり | **なし** |

注意:

- CPU が ARMv7 のため、「実機では動かないが VM では動く」ことがあります。使うバイナリは `readelf -A <ファイル> | grep Tag_CPU_arch` が `v6` であることを確認してください。
- 実行速度は実機と異なります。待ち時間（`time.sleep`）などのタイミングは、実機で調整してください。

### Pi Zero W で使えるブラウザ（重要）

イメージ内で確認した結果です。

| ブラウザ | ビルド | Pi Zero W（armv6l）での動作 |
|---|---|---|
| Chromium 154 | ARMv7 | **動かない**。起動スクリプト `/usr/bin/chromium` が NEON のない CPU を拒否し、バイナリ自体も ARMv7 向け |
| Firefox 157 | ARMv6 | **動かない**。起動スクリプト `/usr/bin/firefox` が `armv6l` だと「Firefox is not supported」と表示して終了する |
| Epiphany 48.5（WebKitGTK 2.48 `+rpi1`） | ARMv6 | 動く想定（Raspbian が ARMv6 向けにビルドしたもの） |

VM では 3 つとも動いてしまうため、Zero W 向けのスクリプトは **Epiphany で作成・確認してください**。このイメージには Epiphany を入れてあります。実機には次のコマンドで入れられます。

```sh
sudo apt install --no-install-recommends epiphany-browser
# 初回起動時の「既定のブラウザにしますか?」ダイアログがキー入力を奪うので止める
gsettings set org.gnome.Epiphany ask-for-default false
```

また、Firefox と Chromium は、RAM が 1GB 未満だと「It is not recommended to run ... on devices with less than 1GB of RAM」という確認ダイアログを出して止まります。VM で使う場合は、Firefox は `FF_SKIP_MEMCHECK=1`、Chromium は `--no-memcheck` で回避できます。

## 構成

```
vm/
├── README.md                     この手順書
├── .gitignore                    work/ を除外
├── scripts/
│   ├── 01-build-kernel.sh        Debian 汎用カーネルと initrd を取り出す
│   ├── 02-customize-image.sh     イメージを拡張・加工して qcow2 にする
│   ├── customize-rootfs.sh       イメージ内（chroot）で実行する初期設定
│   ├── 03-run-qemu.sh            QEMU コマンドで直接起動（確認用）
│   └── 04-create-utm-vm.sh       UTM に VM を登録
├── test/
│   ├── smoke_vlc.py              pyautogui で VLC を操作する確認スクリプト
│   └── smoke_browser.py          pyautogui でブラウザを操作する確認スクリプト
└── work/                         ダウンロードしたイメージと生成物（大容量、git 管理外）
    └── out/
        ├── vmlinuz / initrd.img  カーネル / initrd
        ├── modules.tar           カーネルモジュール
        └── rpi-trixie-virt.qcow2 VM のディスク
```

## 必要なもの

- Apple Silicon Mac
- Homebrew
- Podman（`podman machine` が起動していること。`docker` コマンドが Podman を指していても可）
- 空きディスク 30GB 程度

## 構築手順

### 1. UTM と QEMU をインストールする

```sh
brew install --cask utm
brew install qemu        # qemu-img と、コマンドでの起動確認に使う
```

### 2. Raspberry Pi OS のイメージをダウンロードする

```sh
mkdir -p vm/work && cd vm/work
B=https://downloads.raspberrypi.com/raspios_armhf/images/raspios_armhf-2026-10-06/2026-10-06-raspios-trixie-armhf.img.xz
curl -LO "$B.sha256" && curl -LO "$B"
shasum -a 256 -c 2026-10-06-raspios-trixie-armhf.img.xz.sha256
xz -dk 2026-10-06-raspios-trixie-armhf.img.xz
cd ../..
```

最新版の URL は `curl -sIL https://downloads.raspberrypi.com/raspios_armhf_latest | grep -i location` で確認できます。別の版を使う場合は、手順 4 で `SRC_IMG=<ファイル名>` を指定します。

### 3. Podman で ARM32 のエミュレーションを有効にする

イメージ内（ARMv6 のバイナリ）でコマンドを実行するために必要です。Podman の仮想マシンを再起動すると消えるので、手順 4 の前に毎回実行してください。

```sh
podman run --rm --privileged --platform linux/arm64 docker.io/library/debian:trixie-slim sh -c '
apt-get update -qq && apt-get install -y -qq qemu-user >/dev/null
B=/proc/sys/fs/binfmt_misc
[ -e $B/qemu-arm ] && echo -1 > $B/qemu-arm
printf ":qemu-arm:M::\\x7f\\x45\\x4c\\x46\\x01\\x01\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x02\\x00\\x28\\x00:\\xff\\xff\\xff\\xff\\xff\\xff\\xff\\x00\\xff\\xff\\xff\\xff\\xff\\xff\\xff\\xff\\xfe\\xff\\xff\\xff:/usr/bin/qemu-arm:POCF\n" > $B/register'

# 確認 (armv7l と表示されれば OK)
podman run --rm --privileged --platform linux/arm/v7 docker.io/library/debian:trixie-slim uname -m
```

注意:

- `tonistiigi/binfmt` で登録した `qemu-arm` は、この環境（Podman 6 / libkrun）ではセグメンテーションフォールトで落ちました。そのため Debian の `qemu-user` を使っています。
- `--privileged` を付けないコンテナでは、32bit ARM のバイナリが動きません（seccomp の制限）。

### 4. カーネルを用意し、イメージを加工する

```sh
vm/scripts/01-build-kernel.sh      # 数分。work/out に vmlinuz / initrd.img / modules.tar
vm/scripts/02-customize-image.sh   # 10〜20 分。work/out/rpi-trixie-virt.qcow2
```

`02-customize-image.sh` が行う加工（中身は `customize-rootfs.sh`）:

- ルートパーティションを 6GB 拡張（`GROW=10G` などで変更可）
- Debian カーネルのモジュールを追加
- ユーザー `pi`（パスワード `pizero`）を有効化し、初回起動ウィザードを無効化
  - 初期値の `raspberry` にすると、ログインのたびに SSH の警告ダイアログが出るため変えています
- デスクトップへの自動ログインと、X11（openbox）への切り替え
- 画面のブランク（10 分無操作で消灯）を無効化
- SSH を有効化し、cloud-init を無効化
- VNC（RealVNC / wayvnc）を停止（初期設定ダイアログが自動操作の邪魔になるため）
- `python3-pil` `python3-xlib` `python3-tk` `scrot` `xdotool` `epiphany-browser` を apt で導入
- Epiphany の「既定のブラウザにしますか?」ダイアログを無効化（GSettings の既定値を上書き）
- `~/venv`（`--system-site-packages` 付き）を作り、pyautogui を pip で導入
  - ARMv6 向けのホイールは PyPI にほとんどないため、Pillow などのネイティブ拡張は apt の版を使います

加工中だけ、Raspbian のミラーを JAIST（`RASPBIAN_MIRROR` で変更可）に差し替えます。既定の転送先（mirror.ossplanet.net）に Podman の仮想マシンからつながらないことがあったためです。最後に元の設定に戻します。

Podman の仮想マシンのメモリが少ないと、apt がメモリ不足で強制終了（exit 137）されることがあります。今回は 2GB の仮想マシンに、ほかのコンテナが動いている状態でも完了しました。

### 5. （任意）QEMU コマンドで起動を確認する

```sh
vm/scripts/03-run-qemu.sh          # ウィンドウで起動。シリアルはターミナルに出力
ssh -p 5022 pi@127.0.0.1           # 別ターミナルから（パスワード pizero）
```

`HEADLESS=1` を付けると画面なしで起動します。このとき、シリアル出力は `vm/work/serial.log` に、QEMU モニタは `vm/work/monitor.sock` に出ます。スクリーンショットは `printf 'screendump shot.png -f png\n' | nc -U vm/work/monitor.sock` で撮れます。

### 6. UTM に登録する

```sh
vm/scripts/04-create-utm-vm.sh
```

事前に「システム設定 → プライバシーとセキュリティ → オートメーション」で、ターミナルに「UTM」の操作を許可してください（初回実行時に許可ダイアログが出ます）。UTM に「RPi Zero W Trixie」が追加されるので、▶ で起動します。`VM_NAME=<名前>` で名前を変えられます。

作成される VM:

| 項目 | 値 |
|---|---|
| アーキテクチャ / システム | ARM (32-bit) / `virt` |
| CPU / メモリ | cortex-a7 1 コア / 512MB |
| ドライブ | `rpi-trixie-virt.qcow2`（VirtIO）。ほかに `vmlinuz` と `initrd.img` を raw の VirtIO ドライブとして取り込む |
| ネットワーク / ディスプレイ | 共有ネットワーク（`virtio-net-pci`） / `virtio-gpu-pci` |
| QEMU の追加引数 | `-cpu cortex-a7`、`-kernel` / `-initrd`（VM 内に取り込んだファイル）、`-append`（カーネル引数） |

この作り方にしている理由:

- UTM 内の QEMU はサンドボックスで動き、VM の外のファイルを読めません。そのため、カーネルと initrd をドライブとして VM 内に取り込み、そのパスを `-kernel` / `-initrd` に指定しています。
- AppleScript では「どこにも接続しないドライブ」を作れないため、カーネルと initrd は VirtIO ドライブになります。ゲストには `/dev/vdb`、`/dev/vdc` として見えますが、起動には使っていないので触らないでください。
- UTM は追加引数を空白で区切るため、空白を含む値（カーネル引数、VM のパス）はダブルクォートで囲んでいます。
- UTM のデータフォルダ（`~/Library/Containers/com.utmapp.UTM`）は macOS に保護されていて、ターミナルから設定ファイルを直接書き換えられません。そのため、設定はすべて AppleScript で行っています。

作り直す場合は、UTM で VM を削除してから再実行してください。

## 使い方

起動すると、約 2 分で `pi` ユーザーのデスクトップ（X11）に自動ログインします。

### pyautogui を使う

```sh
# デスクトップ上のターミナルで
~/venv/bin/python your_script.py

# Mac から SSH で実行する場合（UTM の VM。パスワード pizero）
scp vm/test/smoke_vlc.py pi@192.168.64.2:
ssh pi@192.168.64.2 'DISPLAY=:0 XDG_SESSION_TYPE=x11 ~/venv/bin/python smoke_vlc.py'
```

UTM の VM の IP アドレスは、Mac で `arp -a -i bridge100` を実行するか、ゲストで `hostname -I` を実行して確認します（今回は `192.168.64.2` でした）。`03-run-qemu.sh` で起動した場合は `ssh -p 5022 pi@127.0.0.1` です。

SSH から実行する場合の注意:

- `DISPLAY=:0` が必要です。
- `XDG_SESSION_TYPE=x11` も付けてください。pyscreeze（pyautogui のスクリーンショット機能）はこの変数で X11 かどうかを判断します。SSH では `tty` になるため、付けないと `pyautogui.screenshot()` が失敗します。

### 動作確認スクリプト

| スクリプト | 内容 |
|---|---|
| `vm/test/smoke_vlc.py` | VLC を起動 → ウィンドウ検出 → マウス移動 → スクリーンショット → Ctrl+Q で終了 |
| `vm/test/smoke_browser.py [epiphany\|firefox\|chromium] [URL]` | ブラウザを起動 → Ctrl+L で URL を入力 → タイトルが変わるまで待つ → スクリーンショット → Ctrl+Q で終了 |

## 検証結果（2026-10-30、QEMU 11.1 / Apple Silicon）

UTM 5.0.8（`04-create-utm-vm.sh` で作成した VM）と、`03-run-qemu.sh` の両方で確認しました。

| 項目 | 結果 |
|---|---|
| 起動〜デスクトップ表示 | 約 2 分（UTM で 108 秒）。X11 / openbox、ダイアログなし |
| 起動直後のメモリ | 使用 約 200MB / 483MB |
| `smoke_vlc.py` | 成功（起動・ウィンドウ検出・マウス移動・スクリーンショット・Ctrl+Q で終了） |
| `smoke_browser.py epiphany` | 成功（ウィンドウ表示 約 11〜17 秒、URL 入力後 約 20〜40 秒でページ移動） |
| Epiphany 使用中のメモリ | スワップを 150〜290MB 使用。動くが反応は遅い |

### 自動操作のスクリプトを書くときの注意（検証中に起きたこと）

- **キー入力の取りこぼし**: 負荷が高いと、URL 入力直後の Enter が無視されることがありました（UTM で 1 回発生）。操作のあとは結果（ウィンドウのタイトルなど）を確認し、変わらなければやり直す作りにしてください。`smoke_browser.py` は 60 秒たっても変わらなければ Enter を押し直します。
- **操作の間隔**: 続けて送ったキーが反映されないことがあるため、Ctrl+L のあと 3 秒、URL 入力のあと 2 秒待っています。
- **タブの復元**: Epiphany を強制終了すると、次の起動時に前回のタブが復元されます。終了は Ctrl+Q で行ってください。

## 実機（Pi Zero W）に持っていくときの注意

この VM で設定したことのうち、次のものは実機でも同じ対応が必要です。

- X11 への切り替え: `sudo raspi-config nonint do_wayland W1`（pyautogui は Wayland では動かない）
- 画面のブランク無効化: `sudo raspi-config nonint do_blanking 1`
- ブラウザは Epiphany を使い、`ask-for-default` を `false` にする
- pip で入れるパッケージのうち、ネイティブ拡張を含むものは apt の版を使う（例: Pillow は `python3-pil`）
- RealVNC を使わない場合は、初期設定ダイアログが出ないよう VNC を無効にする

## トラブルシューティング

| 症状 | 原因と対処 |
|---|---|
| カーネルが `pci-host-generic ... error -75` で止まる | LPAE なしのカーネル（armmp）を使っている。`01-build-kernel.sh` は armmp-lpae を使うので、作り直す |
| コンテナで 32bit ARM のバイナリが `Exit 139` | binfmt の qemu-arm が合っていない、または `--privileged` がない。手順 3 をやり直す |
| `02-customize-image.sh` が exit 137 | Podman の仮想マシンのメモリ不足。ほかのコンテナを止めるか、`podman machine set --memory 4096` |
| apt が `Unable to connect` | ミラーにつながらない。`RASPBIAN_MIRROR` で別のミラーを指定する |
| `pyautogui.screenshot()` が gnome-screenshot を要求する | `XDG_SESSION_TYPE=x11` を付けて実行する |
| ブラウザが起動しない（ダイアログで止まる） | RAM 1GB 未満の警告。Firefox は `FF_SKIP_MEMCHECK=1`、Chromium は `--no-memcheck` |
