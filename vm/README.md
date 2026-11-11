# Raspberry Pi 3B+ 開発用 VM（UTM / Raspberry Pi OS Trixie 64-bit）

Apple Silicon Mac の UTM 上で、Raspberry Pi 3B+ と同じ **Raspberry Pi OS Trixie 64-bit（デスクトップ版）** を動かします。用途は、Python（pyautogui）からブラウザや VLC を操作するスクリプトの動作確認です。

Mac も Pi 3B+ も 64-bit の ARM なので、VM はエミュレーションではなく仮想化（HVF）で動きます。そのため、実機とほぼ同じか、それより速く動きます。

## この VM で再現できること・できないこと

| 項目 | 実機（Pi 3B+） | この VM |
|---|---|---|
| OS / パッケージ | Raspberry Pi OS Trixie 64-bit（arm64） | **同じイメージ**（2026-10-06 版） |
| Python / VLC | 3.13.5 / 3.0.23 | **同じ** |
| ブラウザ | Chromium 154（標準）、Firefox 157 | **同じ** |
| デスクトップ | X11（openbox）に切り替えて使用 | 同じ（X11） |
| カーネル | Raspberry Pi カーネル | **Debian 汎用カーネル（6.12 arm64）**。ラズパイ用カーネルは QEMU の virt では起動しないため |
| CPU | Cortex-A53 4 コア（1.4GHz） | **Mac の CPU** 4 コア（HVF で仮想化） |
| メモリ | 1GB | 1GB |
| GPU | VideoCore IV（WebGL 1 まで） | virtio-gpu（3D なし。WebGL はソフトウェアで描画） |
| Wi-Fi / Bluetooth / GPIO / 音声 / 動画のハードウェアデコード | あり | **なし** |

注意:

- CPU は実機よりかなり速いです。待ち時間（`time.sleep`）などのタイミングは、実機で調整してください。
- GPU が違うため、ブラウザの描画の速さや WebGL の動作は、実機で確認してください。

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
        ├── cmdline.txt           カーネルの起動引数（03・04 が読む）
        └── rpi-trixie-arm64-virt.qcow2  VM のディスク
```

## 必要なもの

- Apple Silicon Mac
- Homebrew
- Podman（`podman machine` が起動していること。`docker` コマンドが Podman を指していても可）
- 空きディスク 30GB 程度

## 構築手順

全部で 10 分ほどかかります（ダウンロードを除く）。

### 1. UTM と QEMU をインストールする

```sh
brew install --cask utm
brew install qemu        # qemu-img と、コマンドでの起動確認に使う
```

### 2. Raspberry Pi OS のイメージをダウンロードする

```sh
mkdir -p vm/work && cd vm/work
F=2026-10-06-raspios-trixie-arm64.img.xz
P=raspios_arm64/images/raspios_arm64-2026-10-06/$F
curl -fLO "https://downloads.raspberrypi.com/$P.sha256"   # チェックサムは公式から取る
curl -fLO "https://ftp.jaist.ac.jp/pub/raspberrypi/$P"     # 本体は国内ミラー (JAIST) から取る
shasum -a 256 -c "$F.sha256"
xz -dk -T0 "$F"
cd ../..
```

公式（downloads.raspberrypi.com）からも取れますが、2026-11-11 には 1 秒あたり約 0.5MB しか出ず、45 分ほどかかる計算でした。JAIST は約 9.5MB/s でした。

最新版の URL は `curl -sIL https://downloads.raspberrypi.com/raspios_arm64_latest | grep -i location` で確認できます。別の版を使う場合は、手順 3 で `SRC_IMG=<ファイル名>` を指定します。

### 3. カーネルを用意し、イメージを加工する

```sh
vm/scripts/01-build-kernel.sh      # 1 分ほど。work/out に vmlinuz / initrd.img / modules.tar
vm/scripts/02-customize-image.sh   # 3 分ほど。work/out/rpi-trixie-arm64-virt.qcow2 と cmdline.txt
```

Podman の仮想マシンも arm64 なので、イメージ内のコマンドはエミュレーションなしでそのまま動きます。

`02-customize-image.sh` が行う加工（中身は `customize-rootfs.sh`）:

- ルートパーティションを 6GB 拡張（`GROW=10G` などで変更可）
- Debian カーネルのモジュールを追加
- ユーザー `pi`（パスワード `pizero`）を有効化し、初回起動ウィザードを無効化
  - 初期値の `raspberry` にすると、ログインのたびに SSH の警告ダイアログが出るため変えています
- デスクトップへの自動ログインと、X11（openbox）への切り替え
- 画面のブランク（10 分無操作で消灯）を無効化
- SSH を有効化し、cloud-init を無効化
- VNC（RealVNC / wayvnc）を停止（初期設定ダイアログが自動操作の邪魔になるため）
- Chromium がキーリングを使わないようにする（`/etc/chromium.d/90-password-store` で `--password-store=basic` を付ける）
  - 自動ログインではキーリングが開かないため、Chromium の初回起動時に「新しいキーリングのパスワードを決めてください」というダイアログが出て止まります
- 共有フォルダ（タグ `share`）を起動時に `/mnt/dev` へマウントする行を `/etc/fstab` に追加（`nofail` 付きなので、共有していなくても起動は止まらない）
- `python3-pil` `python3-xlib` `python3-tk` `scrot` `xdotool` を apt で導入
- `~/venv`（`--system-site-packages` 付き）を作り、pyautogui を pip で導入

### 4. （任意）QEMU コマンドで起動を確認する

```sh
vm/scripts/03-run-qemu.sh          # ウィンドウで起動。シリアルはターミナルに出力
ssh -p 5022 pi@127.0.0.1           # 別ターミナルから（パスワード pizero）
```

- `HEADLESS=1` を付けると画面なしで起動します。このとき、シリアル出力は `vm/work/serial.log` に、QEMU モニタは `vm/work/monitor.sock` に出ます。スクリーンショットは `printf 'screendump shot.png -f png\n' | nc -U vm/work/monitor.sock` で撮れます。
- `SHARE=<Mac のフォルダ>` を付けると、そのフォルダが VM の `/mnt/dev` に見えます。

### 5. UTM に登録する

```sh
vm/scripts/04-create-utm-vm.sh
```

事前に「システム設定 → プライバシーとセキュリティ → オートメーション」で、ターミナルに「UTM」の操作を許可してください（初回実行時に許可ダイアログが出ます）。UTM に「RPi 3B+ Trixie 64-bit」が追加されるので、▶ で起動します。

- `VM_NAME=<名前>` で VM の名前を変えられます。
- `SHARE=<Mac のフォルダ>` で共有フォルダを変えられます。既定はこのリポジトリのルートです。

作成される VM:

| 項目 | 値 |
|---|---|
| アーキテクチャ / システム | ARM64（aarch64） / `virt` |
| CPU / メモリ | 4 コア（HVF で仮想化） / 1024MB |
| ドライブ | `rpi-trixie-arm64-virt.qcow2`（VirtIO）。ほかに `vmlinuz` と `initrd.img` を raw の VirtIO ドライブとして取り込む |
| ネットワーク / ディスプレイ | 共有ネットワーク（`virtio-net-pci`） / `virtio-gpu-pci` |
| 共有フォルダ | VirtFS。`SHARE` のフォルダが VM の `/mnt/dev` に見える |
| QEMU の追加引数 | `-kernel` / `-initrd`（VM 内に取り込んだファイル）、`-append`（カーネル引数） |

この作り方にしている理由:

- UTM 内の QEMU はサンドボックスで動き、VM の外のファイルを読めません。そのため、カーネルと initrd をドライブとして VM 内に取り込み、そのパスを `-kernel` / `-initrd` に指定しています。
- AppleScript では「どこにも接続しないドライブ」を作れないため、カーネルと initrd は VirtIO ドライブになります。ゲストには `/dev/vdb`、`/dev/vdc` として見えますが、起動には使っていないので触らないでください。
- UTM は追加引数を空白で区切るため、空白を含む値（カーネル引数、VM のパス）はダブルクォートで囲んでいます。
- UTM のデータフォルダ（`~/Library/Containers/com.utmapp.UTM`）は macOS に保護されていて、ターミナルから設定ファイルを直接書き換えられません。そのため、設定はすべて AppleScript で行っています。共有フォルダも AppleScript（`update registry`）で指定しています。

作り直す場合は、UTM で VM を削除してから再実行してください。

## 使い方

起動すると、`pi` ユーザーのデスクトップ（X11）に自動ログインします。

### pyautogui を使う

```sh
# デスクトップ上のターミナルで
~/venv/bin/python your_script.py

# Mac から SSH で実行する場合（パスワード pizero）
ssh pi@192.168.64.3 'DISPLAY=:0 XDG_SESSION_TYPE=x11 ~/venv/bin/python /mnt/dev/vm/test/smoke_vlc.py'
```

共有フォルダのおかげで、Mac で編集したファイルを scp で送らずに、そのまま `/mnt/dev` から実行できます。

UTM の VM の IP アドレスは、Mac で `arp -a -i bridge100` を実行するか、ゲストで `hostname -I` を実行して確認します（2026-11-11 は `192.168.64.3` でした。ほかの VM が動いていると変わります）。`03-run-qemu.sh` で起動した場合は `ssh -p 5022 pi@127.0.0.1` です。

SSH から実行する場合の注意:

- `DISPLAY=:0` が必要です。付けないと、ブラウザなどの画面を持つアプリは開きません（Python の `webbrowser.open` も、何も開かずに終わります）。
- `XDG_SESSION_TYPE=x11` も付けてください。pyscreeze（pyautogui のスクリーンショット機能）はこの変数で X11 かどうかを判断します。SSH では `tty` になるため、付けないと `pyautogui.screenshot()` が失敗します。

### 動作確認スクリプト

| スクリプト | 内容 |
|---|---|
| `vm/test/smoke_vlc.py` | VLC を起動 → ウィンドウ検出 → マウス移動 → スクリーンショット → Ctrl+Q で終了 |
| `vm/test/smoke_browser.py [chromium\|firefox] [URL]` | ブラウザを起動（既定は chromium） → Ctrl+L で URL を入力 → タイトルが変わるまで待つ → スクリーンショット → Alt+F4 で終了 |

## 検証結果（2026-11-11、UTM 5.0.8 / QEMU 11.1 / Apple Silicon）

UTM（`04-create-utm-vm.sh` で作成した VM）と、`03-run-qemu.sh` の両方で確認しました。

| 項目 | 結果 |
|---|---|
| アーキテクチャ | `uname -m` が `aarch64`、`dpkg --print-architecture` が `arm64` |
| 起動〜デスクトップ表示 | 約 4 秒（systemd の起動から）。X11 / openbox、ダイアログなし |
| 起動直後のメモリ | 使用 約 300MB / 967MB |
| 共有フォルダ | 起動時に `/mnt/dev` へ自動でマウントされる |
| `smoke_vlc.py` | 成功（6 秒） |
| `smoke_browser.py chromium` | 成功。ウィンドウ表示 1 秒、URL 入力後 3 秒以内にページ移動、Alt+F4 で正常終了 |
| `smoke_browser.py firefox` | 成功。同上 |

起動時の `systemctl --failed` には、次の 2 つが出ます。どちらもデスクトップと SSH には影響しません。

- `rpi-eeprom-update`: ラズパイの EEPROM がない VM では失敗します。
- `systemd-networkd-wait-online`: VM のネットワークは NetworkManager が管理しているため、2 分待って失敗します。待たされるのは `cups-browsed` など一部のサービスだけです。

### 自動操作のスクリプトを書くときの注意（検証中に起きたこと）

- **ブラウザの終了**: Chromium は Ctrl+Shift+Q で終了しませんでした。Firefox は Ctrl+Q だと、タブが複数あるとき確認ダイアログを出します。どちらも Alt+F4（ウィンドウを閉じる）で終了できます。
- **強制終了のあと**: ブラウザを強制終了（kill）すると、次の起動時に前回のタブを復元しようとします。Firefox では「前回のタブを開きますか?」のバーが出て、入力した URL が消えることがありました。終了は Alt+F4 で行ってください。
- **Chromium の吹き出し**: 初回起動時に「Make Chromium faster」（メモリセーバー）の吹き出しが出ます。キー入力は奪われませんでしたが、スクリーンショットには写ります。
- **キー入力の取りこぼし**: 32-bit 版のエミュレーションでは、URL 入力直後の Enter が無視されることがありました。この VM では起きていませんが、実機は VM より遅いので、操作のあとは結果（ウィンドウのタイトルなど）を確認する作りにしてください。

## 実機（Pi 3B+）に持っていくときの注意

この VM で設定したことのうち、次のものは実機でも同じ対応が必要です。

- X11 への切り替え: `sudo raspi-config nonint do_wayland W1`（pyautogui は Wayland では動かない）
- 画面のブランク無効化: `sudo raspi-config nonint do_blanking 1`
- 自動ログインにする場合は、Chromium のキーリングのダイアログを止める:
  ```sh
  echo 'export CHROMIUM_FLAGS="$CHROMIUM_FLAGS --password-store=basic"' | sudo tee /etc/chromium.d/90-password-store
  ```
- RealVNC を使わない場合は、初期設定ダイアログが出ないよう VNC を無効にする

## トラブルシューティング

| 症状 | 原因と対処 |
|---|---|
| `03-run-qemu.sh` が `UNIX socket path ... is too long` | ソケットのパスが 104 バイト以上。スクリプトは `vm/work` に移動して相対パスで指定するので、古いスクリプトなら更新する |
| `02-customize-image.sh` が exit 137 | Podman の仮想マシンのメモリ不足。ほかのコンテナを止めるか、`podman machine set --memory 4096` |
| `/mnt/dev` が空 | UTM の VM 設定の「共有」で、ディレクトリ共有モードが VirtFS になっていない、またはフォルダが選ばれていない |
| `pyautogui.screenshot()` が gnome-screenshot を要求する | `XDG_SESSION_TYPE=x11` を付けて実行する |
| Chromium が「新しいキーリングのパスワード」で止まる | `/etc/chromium.d/90-password-store` がない。上の「実機に持っていくときの注意」のコマンドで作る |
