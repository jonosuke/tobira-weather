#!/bin/sh
# UTM と同じ構成を QEMU コマンドで直接起動する (動作確認・自動テスト用)。
#   HEADLESS=1 で画面なし起動。シリアルは vm/work/serial.log、
#   QEMU モニタは vm/work/monitor.sock (screendump でスクリーンショット取得可)。
#   SHARE=<Mac のフォルダ> で、そのフォルダを共有フォルダ (ゲストの /mnt/dev) にする。
# SSH: ssh -p 5022 pi@127.0.0.1
set -eu

VM_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$VM_DIR/work/out"
APPEND="$(cat "$OUT/cmdline.txt")"

# UNIX ソケットのパスは 104 バイト未満に制限されるため、work に移動して相対パスで指定する
cd "$VM_DIR/work"
if [ "${HEADLESS:-0}" = 1 ]; then
  DISPLAY_OPTS="-display none -serial file:serial.log -monitor unix:monitor.sock,server,nowait"
else
  DISPLAY_OPTS="-display cocoa -serial stdio"
fi
SHARE_OPTS=""
if [ -n "${SHARE:-}" ]; then
  SHARE_OPTS="-virtfs local,path=$SHARE,mount_tag=share,security_model=mapped-xattr"
fi

# Pi 3B+ と同じ 4 コア・1GB。Mac と同じ arm64 なので HVF で仮想化する (CPU は Mac のもの)
# shellcheck disable=SC2086
exec qemu-system-aarch64 \
  -M virt -accel hvf -cpu host -smp "${SMP:-4}" -m "${MEM:-1024}" \
  -kernel "$OUT/vmlinuz" -initrd "$OUT/initrd.img" -append "$APPEND" \
  -drive if=none,id=hd0,format=qcow2,file="$OUT/rpi-trixie-arm64-virt.qcow2" \
  -device virtio-blk-pci,drive=hd0 \
  -netdev user,id=net0,hostfwd=tcp:127.0.0.1:5022-:22 -device virtio-net-pci,netdev=net0 \
  -device virtio-gpu-pci -device qemu-xhci -device usb-kbd -device usb-tablet \
  $SHARE_OPTS $DISPLAY_OPTS
