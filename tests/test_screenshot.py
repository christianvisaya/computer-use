"""Tests for screenshot.py."""

import base64
import io
import platform
import pytest
from unittest.mock import patch, MagicMock

from computer_use.screenshot import capture_screen_base64, capture_screen


class TestCaptureScreen:
    def test_capture_screen_base64_returns_string(self):
        fake_jpeg = b"\xff\xd8\xff\xe0fake jpeg content"
        # Mock capture_screen directly so we don't need screen access
        with patch("computer_use.screenshot.capture_screen", return_value=fake_jpeg):
            result = capture_screen_base64()
            assert isinstance(result, str)
            assert len(result) > 0
            # Should be valid base64
            base64.b64decode(result)

    def test_capture_screen_darwin_uses_screencapture(self):
        # Must be >1000 bytes to trigger the early return path
        fake_jpeg = b"\xff\xd8\xff\xe0" + b"x" * 2000
        with patch.object(platform, "system", return_value="Darwin"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(stdout=fake_jpeg)
                result = capture_screen()
                assert result == fake_jpeg
                mock_run.assert_called_once()
