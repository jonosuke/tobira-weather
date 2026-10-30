#!/bin/sh
# Raspberry Pi OS イメージを UTM (QEMU virt) 用に加工し、qcow2 を出力する。
#   - ルートパーティションを拡張
#   - 01-build-kernel.sh で作ったカーネルモジュールを追加
#   - customize-rootfs.sh を chroot で実行 (ARMv6 バイナリは binfmt の qemu-arm で動く)
# 出力: vm/work/out/rpi-trixie-virt.qcow2
set -eu

VM_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$VM_DIR/work"
SRC_IMG="${SRC_IMG:-2026-10-06-raspios-trixie-armhf.img}"
GROW="${GROW:-6G}"
# 加工中に使う Raspbian ミラー。空にするとイメージ既定 (raspbian.raspberrypi.com) を使う
RASPBIAN_MIRROR="${RASPBIAN_MIRROR-http://ftp.jaist.ac.jp/pub/Linux/raspbian-archive/raspbian}"
TMP_IMG="rpi-trixie-virt.img"

[ -f "$WORK/out/modules.tar" ] || { echo "先に 01-build-kernel.sh を実行してください" >&2; exit 1; }

cp "$WORK/$SRC_IMG" "$WORK/$TMP_IMG"
truncate -s "+$GROW" "$WORK/$TMP_IMG"

podman run --rm --privileged --platform linux/arm64 \
  -e RASPBIAN_MIRROR="$RASPBIAN_MIRROR" \
  -v /dev:/dev -v "$WORK":/work -v "$VM_DIR/scripts":/scripts:ro \
  docker.io/library/debian:trixie-slim sh -euc '
apt-get update -qq && apt-get install -y -qq fdisk e2fsprogs >/dev/null
IMG=/work/'"$TMP_IMG"'
echo ", +" | sfdisk -q -N 2 "$IMG"
L=$(losetup -fP --show "$IMG")
trap "umount -R /m 2>/dev/null || true; losetup -d $L" EXIT
e2fsck -fy "${L}p2" || [ $? -le 1 ]
resize2fs "${L}p2"

mkdir -p /m
mount "${L}p2" /m
mount "${L}p1" /m/boot/firmware
for d in proc sys dev dev/pts; do mount --bind /$d /m/$d; done
tar -C /m/usr/lib/modules -xf /work/out/modules.tar
mv /m/etc/resolv.conf /m/etc/resolv.conf.orig
cp /etc/resolv.conf /m/etc/resolv.conf
printf "#!/bin/sh\nexit 101\n" > /m/usr/sbin/policy-rc.d && chmod +x /m/usr/sbin/policy-rc.d
cp /scripts/customize-rootfs.sh /m/tmp/
chroot /m /bin/bash /tmp/customize-rootfs.sh
rm -f /m/tmp/customize-rootfs.sh /m/usr/sbin/policy-rc.d
mv -f /m/etc/resolv.conf.orig /m/etc/resolv.conf
'

qemu-img convert -p -O qcow2 "$WORK/$TMP_IMG" "$WORK/out/rpi-trixie-virt.qcow2"
rm "$WORK/$TMP_IMG"
ls -la "$WORK/out"
