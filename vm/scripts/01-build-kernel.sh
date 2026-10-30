#!/bin/sh
# Debian Trixie の汎用 ARM32 カーネル (armmp-lpae) と、virtio ドライバ入り initrd を取り出す。
# Raspberry Pi OS 同梱のカーネルはラズパイ専用で QEMU virt マシンでは起動しないため。
# 出力: vm/work/out/{vmlinuz,initrd.img,modules.tar}
set -eu

VM_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$VM_DIR/work/out"
mkdir -p "$OUT"

podman run --rm --privileged --platform linux/arm/v7 \
  -v "$OUT":/out \
  docker.io/library/debian:trixie-slim sh -euc '
export DEBIAN_FRONTEND=noninteractive
mkdir -p /etc/initramfs-tools
printf "virtio_pci\nvirtio_mmio\nvirtio_blk\nvirtio_net\next4\n" >> /etc/initramfs-tools/modules
apt-get update -qq
apt-get install -y -qq --no-install-recommends linux-image-armmp-lpae initramfs-tools >/dev/null
KVER=$(ls /usr/lib/modules)
echo "kernel: $KVER"
cp "/boot/vmlinuz-$KVER" /out/vmlinuz
cp "/boot/initrd.img-$KVER" /out/initrd.img
tar -C /usr/lib/modules -cf /out/modules.tar "$KVER"
for m in virtio_blk virtio_net virtio-gpu virtio_input snd-hda-intel; do
  find "/usr/lib/modules/$KVER" -name "$m.ko*" | sed "s|.*/||"
done
'
ls -la "$OUT"
