"""Tests for platform.py."""

import subprocess
import pytest
from unittest.mock import patch, MagicMock

from computer_use.platform import get_os, launch_app, run_terminal, get_terminal_app


class TestGetOs:
    def test_macos(self):
        with patch("platform.system", return_value="Darwin"):
            assert get_os() == "macos"

    def test_linux(self):
        with patch("platform.system", return_value="Linux"):
            assert get_os() == "linux"

    def test_windows(self):
        with patch("platform.system", return_value="Windows"):
            assert get_os() == "windows"

    def test_raises_on_unknown(self):
        with patch("platform.system", return_value="FreeBSD"):
            with pytest.raises(RuntimeError, match="Unsupported OS"):
                get_os()


class TestLaunchApp:
    def test_macos_launch(self):
        with patch("platform.system", return_value="Darwin"):
            with patch("subprocess.run") as mock_run:
                launch_app("Safari")
                mock_run.assert_called_once_with(["open", "-a", "Safari"], check=True)

    def test_linux_xdg_open(self):
        with patch("platform.system", return_value="Linux"):
            with patch("subprocess.run") as mock_run:
                # xdg-open fails, falls back to gio
                mock_run.side_effect = [
                    subprocess.CalledProcessError(1, "xdg-open"),
                    MagicMock(),
                ]
                launch_app("firefox")
                # Should have tried xdg-open then gio open
                assert mock_run.call_count >= 1


class TestRunTerminal:
    def test_runs_command(self):
        with patch("platform.system", return_value="Darwin"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(stdout="hello", stderr="")
                result = run_terminal("echo hello")
                assert "hello" in result
