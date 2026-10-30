"""pyautogui で VLC を起動・操作・終了できるかの簡単な確認。

ゲスト内のデスクトップ (X11) 上で実行する:
    DISPLAY=:0 ~/venv/bin/python smoke_vlc.py
"""
import os
import subprocess
import sys
import time

# pyscreeze は XDG_SESSION_TYPE で X11 か判定する。SSH 経由だと "tty" になり
# スクリーンショットが失敗するため、未設定・tty のときは x11 とみなす
if os.environ.get("XDG_SESSION_TYPE", "tty") == "tty":
    os.environ["XDG_SESSION_TYPE"] = "x11"

import pyautogui  # noqa: E402


def vlc_windows():
    result = subprocess.run(
        ["xdotool", "search", "--onlyvisible", "--class", "vlc"],
        capture_output=True, text=True,
    )
    return result.stdout.split()


def main():
    width, height = pyautogui.size()
    print(f"screen: {width}x{height}")

    vlc = subprocess.Popen(["vlc", "--no-qt-privacy-ask"])
    for _ in range(120):
        if vlc_windows():
            break
        time.sleep(1)
    else:
        sys.exit("VLC window did not appear")
    print("VLC window:", vlc_windows())
    time.sleep(3)

    window = vlc_windows()[0]
    subprocess.run(["xdotool", "windowactivate", "--sync", window], check=True)
    pyautogui.moveTo(width // 2, height // 2, duration=0.5)
    print("mouse:", pyautogui.position())
    shot = "/tmp/smoke_vlc.png"
    if os.path.exists(shot):
        os.remove(shot)  # scrot は既存ファイルを上書きせず別名で保存するため
    pyautogui.screenshot(shot)
    print("screenshot:", shot)

    pyautogui.hotkey("ctrl", "q")
    vlc.wait(timeout=60)
    print("VLC exited by Ctrl+Q, code", vlc.returncode)


if __name__ == "__main__":
    main()
