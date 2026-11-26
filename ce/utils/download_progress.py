"""Reusable terminal progress for streamed file transfers."""

from time import monotonic

from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)


def content_length(headers):
    """Return the byte total when the server provides a usable length."""
    try:
        length = int(headers.get("content-length", ""))
        return length if length >= 0 else None
    except (TypeError, ValueError):
        return None


class DownloadProgress:
    def __init__(self, name, total=None):
        self.name = name
        self.total = total
        self.completed = 0
        self.elapsed = 0.0
        self.console = Console(stderr=True)
        self.progress = Progress(
            TextColumn("{task.description}", markup=False),
            BarColumn(),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            disable=not self.console.is_terminal,
            transient=True,
        )

    def __enter__(self):
        self.started = monotonic()
        self.progress.start()
        self.task = self.progress.add_task(self.name, total=self.total)
        return self

    def advance(self, count):
        self.completed += count
        self.progress.update(self.task, advance=count)

    def __exit__(self, exc_type, exc, tb):
        self.elapsed = max(monotonic() - self.started, 1e-9)
        self.progress.stop()

    def summary(self):
        from rich.filesize import decimal

        return (
            f"{decimal(self.completed)} downloaded in {self.elapsed:.1f}s "
            f"({decimal(int(self.completed / max(self.elapsed, 1e-9)))}/s)"
        )
