"""pyautogui でブラウザを起動し、URL を入力して開けるかの簡単な確認。

ゲスト内のデスクトップ (X11) 上で実行する:
    DISPLAY=:0 ~/venv/bin/python smoke_browser.py [epiphany|firefox|chromium] [URL]

Pi Zero W (ARMv6) で使えるのは epiphany (WebKitGTK の ARMv6 ビルド)。
firefox は起動スクリプトが armv6l を拒否し、chromium は ARMv7 ビルドのため、
この 2 つは VM でしか動かない。
"""
import os
import subprocess
import sys
import time

# smoke_vlc.py と同じ理由 (SSH 経由でのスクリーンショット対策)
if os.environ.get("XDG_SESSION_TYPE", "tty") == "tty":
    os.environ["XDG_SESSION_TYPE"] = "x11"

import pyautogui  # noqa: E402

# 起動コマンドとウィンドウクラス。firefox / chromium は RAM 1GB 未満だと
# 確認ダイアログで止まるため、それを飛ばす指定を付ける
BROWSERS = {
    "epiphany": (["epiphany"], "epiphany"),
    "firefox": (["env", "FF_SKIP_MEMCHECK=1", "firefox"], "firefox"),
    "chromium": (["chromium", "--no-memcheck"], "chromium"),
}
# エミュレーションでは起動・読み込みとも数十秒〜数分かかるため長めに待つ
WINDOW_TIMEOUT = 300
PAGE_LOAD_TIMEOUT = 300
# この秒数たってもタイトルが変わらなければ、Enter が取りこぼされたとみなして押し直す
ENTER_RETRY_AFTER = 60


def windows(window_class):
    result = subprocess.run(
        ["xdotool", "search", "--onlyvisible", "--class", window_class],
        capture_output=True, text=True,
    )
    return result.stdout.split()


def active_title():
    result = subprocess.run(["xdotool", "getactivewindow", "getwindowname"],
                            capture_output=True, text=True)
    return result.stdout.strip()


def main():
    browser = sys.argv[1] if len(sys.argv) > 1 else "epiphany"
    url = sys.argv[2] if len(sys.argv) > 2 else "https://example.com"
    command, window_class = BROWSERS[browser]

    started = time.monotonic()
    proc = subprocess.Popen([*command, "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    while not windows(window_class):
        if time.monotonic() - started > WINDOW_TIMEOUT:
            sys.exit(f"{browser} window did not appear in {WINDOW_TIMEOUT}s")
        time.sleep(1)
    print(f"{browser} window after {time.monotonic() - started:.0f}s")
    time.sleep(10)

    subprocess.run(["xdotool", "windowactivate", "--sync", windows(window_class)[-1]], check=True)
    before = active_title()
    print("title before:", before)
    # 負荷が高いと入力の反映が遅れ、続けて送ったキーが取りこぼされるため間を空ける
    pyautogui.hotkey("ctrl", "l")
    time.sleep(3)
    pyautogui.write(url, interval=0.1)
    time.sleep(2)
    pyautogui.press("enter")

    sent = last_enter = time.monotonic()
    while active_title() in ("", before):
        now = time.monotonic()
        if now - sent > PAGE_LOAD_TIMEOUT:
            sys.exit(f"page title did not change in {PAGE_LOAD_TIMEOUT}s")
        # URL 入力直後の Enter は、入力候補の処理中だと無視されることがある
        if now - last_enter > ENTER_RETRY_AFTER:
            print("title unchanged, pressing Enter again")
            pyautogui.hotkey("ctrl", "l")
            time.sleep(2)
            pyautogui.press("enter")
            last_enter = time.monotonic()
        time.sleep(3)
    print(f"title after {time.monotonic() - sent:.0f}s:", active_title())
    time.sleep(20)  # タイトルは本文の描画より先に変わるため、描画を待つ
    shot = f"/tmp/smoke_{browser}.png"
    if os.path.exists(shot):
        os.remove(shot)  # scrot は既存ファイルを上書きせず別名で保存するため
    pyautogui.screenshot(shot)
    print("screenshot:", shot)

    pyautogui.hotkey("ctrl", "q")
    try:
        proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.terminate()
    print(f"{browser} exited, code", proc.returncode)


if __name__ == "__main__":
    main()
