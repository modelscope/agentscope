# -*- coding: utf-8 -*-
"""Local ``file://`` sources must decode percent-escapes before ``open()``.

``URLSource`` stores its URL as a pydantic ``AnyUrl``, so a local file passed
as ``Path(...).as_uri()`` arrives percent-encoded, e.g.
``file:///tmp/my%20file.png``. A formatter that strips the scheme without
decoding looks for a file that does not exist and fails before any request
is sent.
"""

import base64
import tempfile
import unittest
from pathlib import Path
from unittest import IsolatedAsyncioTestCase

from agentscope.formatter import (
    AnthropicChatFormatter,
    DashScopeChatFormatter,
    GeminiChatFormatter,
    MoonshotChatFormatter,
    OpenAIChatFormatter,
    XAIChatFormatter,
    local_path_from_file_url,
)
from agentscope.message import DataBlock, UserMsg, URLSource

try:
    import xai_sdk  # noqa: F401

    _HAS_XAI_SDK = True
except ImportError:
    _HAS_XAI_SDK = False


# A 1x1 transparent PNG
_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452"
    "000000010000000108060000001f15c489"
    "0000000d49444154789c63600000020001"
    "54a24f5d0000000049454e44ae426082"
)


class TestLocalPathFromFileUrl(unittest.TestCase):
    """Unit tests for the shared file-URL decoder."""

    def test_remote_urls_return_none(self) -> None:
        """A remote URL is not a local path, so callers keep their branch."""
        for url in (
            "https://example.com/image.png",
            "http://example.com/image.png",
            "",
        ):
            with self.subTest(url=url):
                self.assertIsNone(local_path_from_file_url(url))

    def test_percent_escapes_are_decoded(self) -> None:
        """Spaces, ``#`` and ``%`` are escapes, not part of the file name."""
        cases = {
            "file:///tmp/my%20file.png": "/tmp/my file.png",
            "file:///tmp/a%23b.png": "/tmp/a#b.png",
            "file:///tmp/100%25.png": "/tmp/100%.png",
            "file:///tmp/plain.png": "/tmp/plain.png",
        }
        for url, expected in cases.items():
            with self.subTest(url=url):
                self.assertEqual(local_path_from_file_url(url), expected)

    def test_windows_drive_leading_slash_is_dropped(self) -> None:
        """``file:///C:/dir`` strips to ``C:/dir``; the slash is authority."""
        self.assertEqual(
            local_path_from_file_url("file:///C:/dir/my%20file.png"),
            "C:/dir/my file.png",
        )


class TestFormattersReadEncodedLocalFiles(IsolatedAsyncioTestCase):
    """Every formatter that inlines local files must read the real file."""

    async def test_formatters_format_local_files_with_special_names(
        self,
    ) -> None:
        """An escaped local file name formats instead of raising."""
        formatters = {
            "openai": OpenAIChatFormatter,
            "anthropic": AnthropicChatFormatter,
            "gemini": GeminiChatFormatter,
            "xai": XAIChatFormatter,
            "moonshot": MoonshotChatFormatter,
            "dashscope": DashScopeChatFormatter,
        }
        for name, factory in formatters.items():
            if name == "xai" and not _HAS_XAI_SDK:
                # Optional dependency absent (CI installs agentscope[full]).
                continue
            for filename in ("my file.png", "a#b.png", "100%.png"):
                with self.subTest(formatter=name, filename=filename):
                    with tempfile.TemporaryDirectory() as tmp:
                        path = Path(tmp) / filename
                        path.write_bytes(_PNG)
                        msg = UserMsg(
                            name="user",
                            content=[
                                DataBlock(
                                    source=URLSource(
                                        url=path.as_uri(),
                                        media_type="image/png",
                                    ),
                                ),
                            ],
                        )
                        # Before the fix this raised FileNotFoundError for the
                        # still-encoded path; now the file is read and encoded.
                        await factory().format([msg])

    async def test_local_file_becomes_base64_data_uri(self) -> None:
        """The decoded file's bytes — not the encoded path — reach the API."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "my file.png"
            path.write_bytes(_PNG)
            msg = UserMsg(
                name="user",
                content=[
                    DataBlock(
                        source=URLSource(
                            url=path.as_uri(),
                            media_type="image/png",
                        ),
                    ),
                ],
            )
            formatted = await OpenAIChatFormatter().format([msg])
            url = formatted[0]["content"][0]["image_url"]["url"]

        expected = base64.b64encode(_PNG).decode("utf-8")
        self.assertEqual(url, f"data:image/png;base64,{expected}")
