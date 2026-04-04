"""OS detection and platform-specific helpers."""

import platform
import subprocess
import shutil


def get_os() -> str:
    """Return 'macos', 'linux', or 'windows'."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "linux":
        return "linux"
    if system == "windows":
        return "windows"
    raise RuntimeError(f"Unsupported OS: {system}")


# Normalize common app name aliases to macOS app bundle names
_MAC_APP_ALIASES: dict[str, str] = {
    "chrome": "Google Chrome",
    "google-chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "chromium": "Chromium",
    "firefox": "Firefox",
    "safari": "Safari",
    "terminal": "Terminal",
    "finder": "Finder",
    "spotlight": "Spotlight",
    "messages": "Messages",
    "mail": "Mail",
    "slack": "Slack",
    "discord": "Discord",
    "zoom": "zoom.us",
    "vscode": "Visual Studio Code",
    "code": "Visual Studio Code",
    "obsidian": "Obsidian",
    "notion": "Notion",
    "1password": "1Password",
    "bitwarden": "Bitwarden",
}


def launch_app(app: str, linux_window_class: str | None = None, win_program: str | None = None) -> None:
    """Open an application by name."""
    os = get_os()

    if os == "macos":
        # Normalize common aliases to actual macOS app names
        normalized = _MAC_APP_ALIASES.get(app.lower(), app)
        subprocess.run(["open", "-a", normalized], check=True)
    elif os == "linux":
        # Try xdg-open first (works for most apps)
        try:
            subprocess.run(["xdg-open", app], check=True)
        except subprocess.CalledProcessError:
            # Fallback to gio for GTK apps
            subprocess.run(["gio", "open", app], check=True)
    elif os == "windows":
        prog = win_program or app
        subprocess.run(["start", "", prog], shell=True, check=True)


def run_terminal(command: str, timeout: int = 10) -> str:
    """Run a shell command and return stdout."""
    os = get_os()

    if os == "macos":
        shell = "/bin/zsh"
    elif os == "linux":
        shell = "/bin/bash"
    else:
        shell = "cmd /c"

    result = subprocess.run(
        command,
        shell=True,
        executable=shell,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout + result.stderr


def get_terminal_app() -> str:
    """Return the default terminal app name for the current OS."""
    os = get_os()
    if os == "macos":
        return "Terminal"
    if os == "linux":
        # Try to detect available terminal
        for term in ["gnome-terminal", "konsole", "xfce4-terminal", "xterm"]:
            if shutil.which(term):
                return term
        return "xterm"
    return "cmd"
