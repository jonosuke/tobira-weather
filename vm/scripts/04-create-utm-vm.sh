#!/bin/sh
# UTM に VM を登録する (AppleScript のみで設定)。
#   - ディスク・カーネル・initrd を VM のバンドルへ取り込む
#     (カーネル・initrd は raw の VirtIO ドライブとして取り込む。AppleScript では
#      接続なしのドライブを作れないため。ゲストには /dev/vdb・vdc として見えるが起動には使わない)
#   - バンドル内のカーネル・initrd と起動引数を、QEMU の追加引数で指定する
# UTM 内の QEMU はサンドボックスで動き、バンドル外のファイルは読めない。
# また UTM のデータフォルダは macOS に保護されていて config.plist を直接書き換えられない。
# 初回は「ターミナルが UTM を制御する」許可が必要
# (システム設定 → プライバシーとセキュリティ → オートメーション)。
set -eu

VM_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$VM_DIR/work/out"
VM_NAME="${VM_NAME:-RPi Zero W Trixie}"
BUNDLE_DATA="$HOME/Library/Containers/com.utmapp.UTM/Data/Documents/$VM_NAME.utm/Data"
APPEND="root=PARTUUID=99c03aa0-02 rootfstype=ext4 rw rootwait fsck.repair=yes console=ttyAMA0 console=tty1"

open -a UTM
osascript - "$VM_NAME" "$OUT" "$BUNDLE_DATA" "$APPEND" <<'EOF'
on run argv
  set vmName to item 1 of argv
  set outDir to item 2 of argv
  set bundleData to item 3 of argv
  set bootArgs to item 4 of argv
  -- UTM は追加引数を空白で区切るため、空白を含む値はダブルクォートで囲む
  set q to quote
  tell application "UTM"
    -- ディスクのコピーに時間がかかることがあるため、タイムアウトを延ばす
    with timeout of 1800 seconds
      set vm to make new virtual machine with properties {backend:qemu, configuration:{name:vmName, architecture:"arm", machine:"virt", memory:512, cpu cores:1, hypervisor:false, uefi:false, drives:{{interface:VirtIO, source:(POSIX file (outDir & "/rpi-trixie-virt.qcow2"))}, {interface:VirtIO, raw:true, source:(POSIX file (outDir & "/vmlinuz"))}, {interface:VirtIO, raw:true, source:(POSIX file (outDir & "/initrd.img"))}}, network interfaces:{{hardware:"virtio-net-pci", mode:shared}}, displays:{{hardware:"virtio-gpu-pci"}}, qemu additional arguments:{{argument string:"-cpu"}, {argument string:"cortex-a7"}, {argument string:"-kernel"}, {argument string:(q & bundleData & "/vmlinuz" & q)}, {argument string:"-initrd"}, {argument string:(q & bundleData & "/initrd.img" & q)}, {argument string:"-append"}, {argument string:(q & bootArgs & q)}}}}
    end timeout
    return id of vm
  end tell
end run
EOF
echo "登録しました: $VM_NAME"
