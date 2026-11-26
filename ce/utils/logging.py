from __future__ import annotations

import logging
import os
import sys
from datetime import UTC, datetime

DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d %(funcName)s %(message)s"
DEFAULT_LOG_LEVEL = "WARNING"
VALID_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
DEFAULT_LOG_DESTINATIONS = "console"
DEFAULT_CLOUDWATCH_STREAM_NAME = "{logger_name}/{process_id}"
_CONFIGURED = False


class UtcFormatter(logging.Formatter):
    """Format log record timestamps as ISO-8601 UTC, including milliseconds."""

    def format(self, record: logging.LogRecord) -> str:
        """Prefix each log record once, leaving multiline content intact."""
        formatted = super().format(record)
        if "%(asctime)" not in self._style._fmt:
            return f"{self.formatTime(record, self.datefmt)} {formatted}"
        return formatted

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        utc_time = datetime.fromtimestamp(record.created, tz=UTC)
        if datefmt:
            return utc_time.strftime(datefmt)
        return utc_time.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def set_logging_level(log_level: str) -> None:
    """Apply the explicitly selected CLI threshold without rebuilding handlers.

    The top-level Click group sets up log handlers. A terminal command can
    override only the threshold after Click finishes parsing its own options.
    """
    selected_level = log_level.upper()
    if selected_level not in VALID_LOG_LEVELS:
        choices = ", ".join(VALID_LOG_LEVELS)
        raise ValueError(f"Invalid log level {log_level!r}. Choose one of: {choices}.")
    logging.getLogger().setLevel(selected_level)


def configure_logging(*, log_level: str = DEFAULT_LOG_LEVEL) -> None:
    """Configure logging once using an explicit, case-insensitive level."""
    global _CONFIGURED

    if _CONFIGURED:
        set_logging_level(log_level)
        return

    root_logger = logging.getLogger()
    selected_level = log_level.upper()
    if selected_level not in VALID_LOG_LEVELS:
        choices = ", ".join(VALID_LOG_LEVELS)
        raise ValueError(f"Invalid log level {log_level!r}. Choose one of: {choices}.")
    log_format = os.getenv("LOG_FORMAT", DEFAULT_LOG_FORMAT)
    destinations = _parse_destinations(
        os.getenv("LOG_DESTINATIONS", DEFAULT_LOG_DESTINATIONS),
    )

    formatter = UtcFormatter(log_format)
    handlers = [_build_handler(destination, formatter) for destination in destinations]

    root_logger.handlers.clear()
    root_logger.setLevel(selected_level)

    # Azure SDK request/response debugging can emit a header on every line.
    # Keep SDK logging separate from CE Ops verbosity unless explicitly enabled.
    azure_level = os.getenv("AZURE_SDK_LOG_LEVEL", "WARNING").upper()
    if azure_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError(f"Invalid AZURE_SDK_LOG_LEVEL: {azure_level}")
    logging.getLogger("azure").setLevel(azure_level)
    # Transport DEBUG logs can contain bearer credentials or signed download URLs.
    for name in (
        "httpx",
        "httpx2",
        "httpcore",
        "httpcore2",
        "authlib",
        "consumer_api_client",
        "publisher_client",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)
    for handler in handlers:
        root_logger.addHandler(handler)

    _CONFIGURED = True


def _parse_destinations(raw_value: str) -> list[str]:
    destinations = [
        item.strip().lower() for item in raw_value.split(",") if item.strip()
    ]
    if not destinations:
        raise ValueError("At least one log destination must be configured.")
    return destinations


def _build_handler(destination: str, formatter: logging.Formatter) -> logging.Handler:
    if destination == "console":
        handler = logging.StreamHandler(sys.stderr)
    elif destination == "cloudwatch":
        handler = _build_cloudwatch_handler()
    elif destination == "azure":
        handler = _build_azure_handler()
    else:
        raise ValueError(
            f"Unsupported log destination '{destination}'. "
            "Expected one of: console, cloudwatch, azure."
        )

    handler.setFormatter(formatter)
    return handler


def _build_cloudwatch_handler() -> logging.Handler:
    log_group_name = _require_env("CLOUDWATCH_LOG_GROUP")

    import boto3
    import watchtower

    stream_name = os.getenv(
        "CLOUDWATCH_LOG_STREAM_NAME", DEFAULT_CLOUDWATCH_STREAM_NAME
    )

    client_kwargs: dict[str, str] = {}
    region_name = os.getenv("AWS_REGION")
    if region_name:
        client_kwargs["region_name"] = region_name

    endpoint_url = os.getenv("CLOUDWATCH_ENDPOINT_URL")
    if endpoint_url:
        client_kwargs["endpoint_url"] = endpoint_url

    boto3_client = boto3.client("logs", **client_kwargs)
    return watchtower.CloudWatchLogHandler(
        boto3_client=boto3_client,
        log_group_name=log_group_name,
        stream_name=stream_name,
    )


def _build_azure_handler() -> logging.Handler:
    connection_string = _require_env("APPLICATIONINSIGHTS_CONNECTION_STRING")

    from opencensus.ext.azure.log_exporter import AzureLogHandler

    return AzureLogHandler(connection_string=connection_string)


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    raise ValueError(f"Missing required environment variable '{name}'.")


def summarize_exception(exc: Exception, *, max_length: int = 300) -> str:
    """Summarize exceptions without dumping multiline HTTP response headers.

    Full details can still be recorded in opt-in DEBUG traceback logs.
    """
    first_line = next(
        (line.strip() for line in str(exc).splitlines() if line.strip()),
        type(exc).__name__,
    )
    if len(first_line) > max_length:
        first_line = first_line[: max_length - 3] + "..."
    code = getattr(exc, "status_code", None)
    status = f" (HTTP {code})" if isinstance(code, int) else ""
    return f"{type(exc).__name__}{status}: {first_line}"


def format_status_line(message: str) -> str:
    """Format user-facing CLI status output like a timestamped log line."""
    record = logging.LogRecord("ce", logging.INFO, "", 0, message, (), None)
    formatter = UtcFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    return formatter.format(record)


def enable_debug() -> None:
    set_logging_level("DEBUG")


def is_debug() -> bool:
    return logging.getLogger().isEnabledFor(logging.DEBUG)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
