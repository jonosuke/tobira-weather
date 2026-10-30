#!/bin/bash
# Raspberry Pi OS のルートファイルシステム内 (chroot) で実行する初期設定。
# 02-customize-image.sh から呼ばれる。実機の SD カードにも同じ設定を流用できる。
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive

VM_USER=pi
# 初期値の raspberry だと、ログインのたびに SSH の警告ダイアログ (pprompt) が出るため変える
VM_PASS=pizero

# 初回起動ウィザードの代わりに pi ユーザーを有効化 (Raspberry Pi OS 標準の userconf を使う)
/usr/lib/userconf-pi/userconf "$VM_USER" ""
echo "$VM_USER:$VM_PASS" | chpasswd

# デスクトップへ自動ログイン (B4) + X11 (W1)。pyautogui は Wayland では動かないため
SUDO_USER=$VM_USER raspi-config nonint do_boot_behaviour B4
SUDO_USER=$VM_USER raspi-config nonint do_wayland W1
# 画面のブランクを無効化 (既定は 10 分無操作で消灯し、スクリーンショットが真っ黒になる)
SUDO_USER=$VM_USER raspi-config nonint do_blanking 1

# SSH を有効化。cloud-init は無効化 (上で設定済みのため、初回起動の待ち時間を省く)
[ -e /etc/ssh/ssh_host_ed25519_key ] || ssh-keygen -A
systemctl enable ssh
touch /etc/cloud/cloud-init.disabled

# VNC は使わない (画面は UTM で見る)。RealVNC の初期設定ダイアログが自動操作の邪魔になるため止める。
# disable だと初回起動時の systemd プリセット適用で有効に戻るため mask する
systemctl mask vncserver-virtuald vncserver-x11-serviced wayvnc wayvnc-control
# userconf (上で実行済み) が無効化した初回設定サービスも、同じ理由で有効に戻り起動が遅くなるため mask する
systemctl mask userconfig

# 加工中だけ Raspbian のミラーを差し替える。既定の転送先 (地域ごとに自動選択) が
# Podman の仮想マシンからつながらないことがあったため。最後に元に戻す
SOURCES=$(grep -l "raspbian.raspberrypi.com/raspbian" /etc/apt/sources.list /etc/apt/sources.list.d/* 2>/dev/null | head -1)
if [ -n "${RASPBIAN_MIRROR:-}" ] && [ -n "$SOURCES" ]; then
  cp "$SOURCES" /tmp/sources.orig
  sed -i "s|http://raspbian.raspberrypi.com/raspbian|$RASPBIAN_MIRROR|" "$SOURCES"
fi

# pyautogui の依存のうちネイティブ拡張を含むものは apt (ARMv6 ビルド) から入れる
apt-get -o Acquire::Retries=5 update
apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
  python3-venv python3-pil python3-xlib python3-tk scrot xdotool
# epiphany-browser: Pi Zero W (ARMv6) で使えるブラウザ。標準の Firefox は armv6l を
# 起動スクリプトで拒否し、Chromium は ARMv7 ビルドのため Zero W では動かない。
# 依存が多く、まとめて入れるとエミュレーション下の apt がメモリ不足になるため分ける
apt-get -o Acquire::Retries=5 install -y --no-install-recommends epiphany-browser
# 初回起動時の「既定のブラウザにしますか?」ダイアログがキー入力を奪うため出さない
printf "[org.gnome.Epiphany]\nask-for-default=false\n" > /usr/share/glib-2.0/schemas/90-pizero-vm.gschema.override
glib-compile-schemas /usr/share/glib-2.0/schemas
apt-get clean
[ -f /tmp/sources.orig ] && mv /tmp/sources.orig "$SOURCES"

sudo -u "$VM_USER" python3 -m venv --system-site-packages "/home/$VM_USER/venv"
sudo -u "$VM_USER" "/home/$VM_USER/venv/bin/pip" install --no-cache-dir pyautogui

grep -E "^(autologin-user|autologin-session|user-session|greeter-session)=" /etc/lightdm/lightdm.conf
# pyautogui は import 時に X11 の DISPLAY を要求するため、ここではバージョンだけ確認する
"/home/$VM_USER/venv/bin/python" -c "import sys, importlib.metadata as m; print(sys.version.split()[0], 'pyautogui', m.version('pyautogui'))"
