"""Tests for reusable download progress."""

import pytest

from ce.utils.download_progress import DownloadProgress, content_length


@pytest.mark.parametrize(
    "headers, expected",
    [
        ({}, None),
        ({"content-length": "123"}, 123),
        ({"content-length": "-1"}, None),
        ({"content-length": "bad"}, None),
    ],
)
def test_content_length(headers, expected):
    assert content_length(headers) == expected


def test_progress_counts_bytes():
    with DownloadProgress("example.zip", total=12) as progress:
        progress.advance(5)
        progress.advance(7)
    assert progress.completed == 12
    assert "12 bytes downloaded" in progress.summary()
    assert "/s" in progress.summary()
