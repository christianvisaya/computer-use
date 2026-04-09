#!/usr/bin/env python3
"""
MetaTrader 4 Auto-Login Script (macOS)
Uses pyautogui for keyboard automation.

Steps:
1. Open MetaTrader 4 via Spotlight
2. Navigate to Login to Trade Account dialog
3. Fill login, password, server, and submit
"""

import argparse
import os
import subprocess
import sys
import time

import pyautogui

pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True

APP_NAME = "MetaTrader 4"


def _run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a subprocess command, optionally checking for errors."""
    result = subprocess.run(args, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(args)}\n{result.stderr}")
    return result


def _osatype(text: str) -> None:
    """Type text via osascript to avoid macOS emoji picker interference."""
    escaped = text.replace('"', '\\"')
    _run(
        ["osascript", "-e", f'tell application "System Events" to keystroke "{escaped}"'],
        check=False,
    )
    time.sleep(0.05 * len(text) + 0.1)


def check_accessibility() -> bool:
    """Check if Accessibility permissions are granted (required for keyboard automation)."""
    result = _run(
        ["osascript", "-e", "tell application \"System Events\" to return exists front window"],
        check=False,
    )
    if result.returncode != 0 or "error" in result.stdout.lower():
        print("ERROR: Accessibility permissions not granted.")
        print("  Go to System Settings > Privacy & Security > Accessibility")
        print("  and add + enable your terminal / Python runtime.")
        return False
    return True


def spotlight_open(app_name: str, timeout: float = 30) -> bool:
    """Open app via Spotlight, wait until it launches."""
    print(f"[1] Opening {app_name} via Spotlight...")
    _run(["osascript", "-e", 'tell application "System Events" to keystroke " " using command down'])
    time.sleep(0.5)
    _run(["osascript", "-e", f'tell application "System Events" to keystroke "{app_name}"'])
    time.sleep(0.5)
    _run(["osascript", "-e", 'tell application "System Events" to key code 36'])

    print(f"    Waiting up to {timeout}s for app to launch...")
    for i in range(int(timeout)):
        result = _run(["pgrep", "-x", app_name], check=False)
        if result.returncode == 0:
            print(f"    {app_name} is running.")
            return True
        time.sleep(1)

    print(f"    WARNING: {app_name} may not have started after {timeout}s.")
    return False


def open_login_dialog() -> None:
    """Open Login to Trade Account dialog using keyboard navigation."""
    print("[2] Opening Login to Trade Account dialog...")
    time.sleep(1)

    pyautogui.press("command")
    time.sleep(0.3)
    pyautogui.press("space")
    time.sleep(0.5)

    print("    Navigating... (Arrow Down 9x)")
    for _ in range(9):
        pyautogui.press("down")
        time.sleep(0.2)

    pyautogui.press("space")
    print("    Login dialog opened.")
    time.sleep(1)


def fill_login_dialog(login: str, password: str, server: str) -> None:
    """Fill the Login to Trade Account dialog with credentials."""
    print("[3] Filling login credentials...")
    time.sleep(1)

    print(f"    Login: {login}")
    _osatype(login)
    time.sleep(0.3)
    pyautogui.press("tab")
    time.sleep(0.3)

    print(f"    Password: {'*' * len(password)}")
    _osatype(password)
    time.sleep(0.3)
    pyautogui.press("tab")
    time.sleep(0.3)

    print(f"    Server: {server}")
    pyautogui.hotkey("command", "a")
    time.sleep(0.2)
    pyautogui.press("delete")
    time.sleep(0.2)
    _osatype(server)
    time.sleep(0.3)

    pyautogui.press("tab")
    time.sleep(0.2)
    pyautogui.press("tab")
    time.sleep(0.5)

    print("[4] Clicking Login...")
    pyautogui.press("return")


def main():
    parser = argparse.ArgumentParser(description="MetaTrader 4 Auto-Login (macOS)")
    parser.add_argument("--login", default=os.environ.get("MT4_LOGIN", "69773894"))
    parser.add_argument("--password", default=os.environ.get("MT4_PASSWORD", ""))
    parser.add_argument("--server", default=os.environ.get("MT4_SERVER", "Exness-Trial8"))
    parser.add_argument("--no-open", action="store_true", help="Skip opening MT4 (assume it's already running)")
    args = parser.parse_args()

    # Strip outer double-quotes if caller passed "password" (common in automation)
    password = args.password
    if password.startswith('"') and password.endswith('"') and len(password) >= 2:
        password = password[1:-1]

    if not password:
        print("ERROR: Password required. Set MT4_PASSWORD env var or pass --password.")
        sys.exit(1)

    print("=" * 50)
    print("MT4 Auto-Login Script (macOS)")
    print("=" * 50)

    if not check_accessibility():
        sys.exit(1)

    if not args.no_open:
        if not spotlight_open(APP_NAME):
            print("ERROR: Failed to open MetaTrader 4.")
            sys.exit(1)
        print("[1b] Waiting for MT4 to initialize...")
        time.sleep(5)

    open_login_dialog()
    fill_login_dialog(args.login, password, args.server)

    print("=" * 50)
    print("Done. Check MT4 for connection status.")
    print("=" * 50)


if __name__ == "__main__":
    main()
