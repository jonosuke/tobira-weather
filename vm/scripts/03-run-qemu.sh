#!/bin/sh
# UTM と同じ構成を QEMU コマンドで直接起動する (動作確認・自動テスト用)。
#   HEADLESS=1 で画面なし起動。シリアルは vm/work/serial.log、
#   QEMU モニタは vm/work/monitor.sock (screendump でスクリーンショット取得可)。
# SSH: ssh -p 5022 pi@127.0.0.1
set -eu

VM_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$VM_DIR/work/out"
APPEND="root=PARTUUID=99c03aa0-02 rootfstype=ext4 rw rootwait fsck.repair=yes console=ttyAMA0 console=tty1"

if [ "${HEADLESS:-0}" = 1 ]; then
  DISPLAY_OPTS="-display none -serial file:$VM_DIR/work/serial.log -monitor unix:$VM_DIR/work/monitor.sock,server,nowait"
else
  DISPLAY_OPTS="-display cocoa -serial stdio"
fi

# shellcheck disable=SC2086
exec qemu-system-arm \
  -M virt -cpu cortex-a7 -smp "${SMP:-1}" -m "${MEM:-512}" \
  -kernel "$OUT/vmlinuz" -initrd "$OUT/initrd.img" -append "$APPEND" \
  -drive if=none,id=hd0,format=qcow2,file="$OUT/rpi-trixie-virt.qcow2" \
  -device virtio-blk-pci,drive=hd0 \
  -netdev user,id=net0,hostfwd=tcp:127.0.0.1:5022-:22 -device virtio-net-pci,netdev=net0 \
  -device virtio-gpu-pci -device qemu-xhci -device usb-kbd -device usb-tablet \
  $DISPLAY_OPTS
