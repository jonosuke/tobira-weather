#!/bin/sh
# UTM に VM を登録する (AppleScript のみで設定)。
#   - ディスク・カーネル・initrd を VM のバンドルへ取り込む
#     (カーネル・initrd は raw の VirtIO ドライブとして取り込む。AppleScript では
#      接続なしのドライブを作れないため。ゲストには /dev/vdb・vdc として見えるが起動には使わない)
#   - バンドル内のカーネル・initrd と起動引数を、QEMU の追加引数で指定する
#   - SHARE (既定はリポジトリのルート) を共有フォルダ (VirtFS) にする。ゲストでは /mnt/dev に見える
# UTM 内の QEMU はサンドボックスで動き、バンドル外のファイルは読めない。
# また UTM のデータフォルダは macOS に保護されていて config.plist を直接書き換えられない。
# 初回は「ターミナルが UTM を制御する」許可が必要
# (システム設定 → プライバシーとセキュリティ → オートメーション)。
set -eu

VM_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$VM_DIR/work/out"
VM_NAME="${VM_NAME:-RPi 3B+ Trixie 64-bit}"
SHARE="${SHARE:-$(cd "$VM_DIR/.." && pwd)}"
BUNDLE_DATA="$HOME/Library/Containers/com.utmapp.UTM/Data/Documents/$VM_NAME.utm/Data"
APPEND="$(cat "$OUT/cmdline.txt")"

open -a UTM
osascript - "$VM_NAME" "$OUT" "$BUNDLE_DATA" "$APPEND" "$SHARE" <<'EOF'
on run argv
  set vmName to item 1 of argv
  set outDir to item 2 of argv
  set bundleData to item 3 of argv
  set bootArgs to item 4 of argv
  set shareDir to item 5 of argv
  -- UTM は追加引数を空白で区切るため、空白を含む値はダブルクォートで囲む
  set q to quote
  tell application "UTM"
    -- ディスクのコピーに時間がかかることがあるため、タイムアウトを延ばす
    with timeout of 1800 seconds
      -- Pi 3B+ と同じ 4 コア・1GB。hypervisor:true で HVF を使う (CPU は Mac のもの)
      set vm to make new virtual machine with properties {backend:qemu, configuration:{name:vmName, architecture:"aarch64", machine:"virt", memory:1024, cpu cores:4, hypervisor:true, uefi:false, directory share mode:VirtFS, drives:{{interface:VirtIO, source:(POSIX file (outDir & "/rpi-trixie-arm64-virt.qcow2"))}, {interface:VirtIO, raw:true, source:(POSIX file (outDir & "/vmlinuz"))}, {interface:VirtIO, raw:true, source:(POSIX file (outDir & "/initrd.img"))}}, network interfaces:{{hardware:"virtio-net-pci", mode:shared}}, displays:{{hardware:"virtio-gpu-pci"}}, qemu additional arguments:{{argument string:"-kernel"}, {argument string:(q & bundleData & "/vmlinuz" & q)}, {argument string:"-initrd"}, {argument string:(q & bundleData & "/initrd.img" & q)}, {argument string:"-append"}, {argument string:(q & bootArgs & q)}}}}
    end timeout
    update registry vm with {POSIX file shareDir}
    return id of vm
  end tell
end run
EOF
echo "登録しました: $VM_NAME (共有フォルダ: $SHARE)"
