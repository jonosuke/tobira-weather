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

# Chromium の初回起動時に「新しいキーリングのパスワード」ダイアログが出て止まるため、
# キーリングを使わない (自動ログインではキーリングが開かない)
printf '%s\n' 'export CHROMIUM_FLAGS="$CHROMIUM_FLAGS --password-store=basic"' > /etc/chromium.d/90-password-store

# UTM の共有フォルダ (VirtFS、タグ share) を起動時に /mnt/dev へマウントする。
# 共有していないときも起動が止まらないよう nofail を付ける
mkdir -p /mnt/dev
grep -q "^share " /etc/fstab || echo "share  /mnt/dev  9p  trans=virtio,version=9p2000.L,nofail  0  0" >> /etc/fstab

# pyautogui の依存のうちネイティブ拡張を含むものは apt から入れる
apt-get -o Acquire::Retries=5 update
apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
  python3-venv python3-pil python3-xlib python3-tk scrot xdotool
apt-get clean

sudo -u "$VM_USER" python3 -m venv --system-site-packages "/home/$VM_USER/venv"
sudo -u "$VM_USER" "/home/$VM_USER/venv/bin/pip" install --no-cache-dir pyautogui

grep -E "^(autologin-user|autologin-session|user-session|greeter-session)=" /etc/lightdm/lightdm.conf
# pyautogui は import 時に X11 の DISPLAY を要求するため、ここではバージョンだけ確認する
"/home/$VM_USER/venv/bin/python" -c "import sys, importlib.metadata as m; print(sys.version.split()[0], 'pyautogui', m.version('pyautogui'))"
dpkg --print-architecture
dpkg-query -W -f '${Package} ${Version}\n' chromium firefox vlc 2>/dev/null || true
