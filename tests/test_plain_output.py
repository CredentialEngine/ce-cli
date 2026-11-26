from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


CE_SOURCE = Path(__file__).resolve().parent.parent / "ce"


FORBIDDEN = (
    "rich.panel",
    "rich.syntax",
    "rich.box",
    "box.SIMPLE",
    "border_style",
    'header_style="bold"',
)


@pytest.mark.parametrize("forbidden", FORBIDDEN)
def test_the_source_has_no_boxes_or_bold_headers(forbidden: str) -> None:
    offenders = [
        path.relative_to(CE_SOURCE).as_posix()
        for path in CE_SOURCE.rglob("*.py")
        if "iir/api" not in path.as_posix()
        and forbidden in path.read_text(encoding="utf-8")
    ]
    assert offenders == [], f"{forbidden!r} found in {offenders}"
