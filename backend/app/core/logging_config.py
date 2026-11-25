"""
Structured Rotating Logging Configuration.
Features rotating file handlers, automated directory creation,
and sensitive credential & token scrubbing filters (CWE-532 protection).
"""
import logging
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from .config import settings

# Sensitive tokens and credential redaction patterns
REDACT_PATTERNS = [
    (re.compile(r'(bearer\s+)([a-zA-Z0-9_\-\.]+)', re.IGNORECASE), r'\1[REDACTED_BEARER_TOKEN]'),
    (re.compile(r'(password[\'\"]?\s*[:=]\s*[\'\"]?)([^\r\n\'\",&]+)', re.IGNORECASE), r'\1[REDACTED_PASSWORD]'),
    (re.compile(r'(token[\'\"]?\s*[:=]\s*[\'\"]?(?:bearer\s+)?)([^\r\n\'\",&]+)', re.IGNORECASE), r'\1[REDACTED_TOKEN]'),
    (re.compile(r'(cookie[\'\"]?\s*[:=]\s*[\'\"]?)([^\r\n\'\"]+)', re.IGNORECASE), r'\1[REDACTED_COOKIE]'),
    (re.compile(r'(secret[\'\"]?\s*[:=]\s*[\'\"]?)([^\r\n\'\",&]+)', re.IGNORECASE), r'\1[REDACTED_SECRET]'),
    (re.compile(r'(authorization[\'\"]?\s*[:=]\s*[\'\"]?)([^\r\n\'\"]+)', re.IGNORECASE), r'\1[REDACTED_AUTH]'),
]


class SensitiveDataFilter(logging.Filter):
    """
    Log filter that intercepts records and redacts passwords, tokens,
    session cookies, and authorization secrets before emission.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, repl in REDACT_PATTERNS:
                record.msg = pattern.sub(repl, record.msg)
        if record.args:
            if isinstance(record.args, dict):
                redacted_args = {}
                for k, v in record.args.items():
                    val_str = str(v)
                    for pattern, repl in REDACT_PATTERNS:
                        val_str = pattern.sub(repl, val_str)
                    redacted_args[k] = val_str
                record.args = redacted_args
            elif isinstance(record.args, tuple):
                redacted_list = []
                for item in record.args:
                    val_str = str(item)
                    for pattern, repl in REDACT_PATTERNS:
                        val_str = pattern.sub(repl, val_str)
                    redacted_list.append(val_str)
                record.args = tuple(redacted_list)
        return True


def setup_logging():
    """
    Configures structured, rotating logging for console output and local log files.
    Directs logs safely to logs/hav_scrap.log with credentials masked.
    Rotates at 10 MB per file, keeping up to 5 historical log backups.
    """
    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = settings.LOGS_DIR / "hav_scrap.log"

    log_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    sens_filter = SensitiveDataFilter()

    # 1. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    console_handler.setFormatter(log_format)
    console_handler.addFilter(sens_filter)

    # 2. Rotating File Handler (10 MB per file, 5 rotated backup archives)
    rotating_file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    rotating_file_handler.setLevel(logging.DEBUG)
    rotating_file_handler.setFormatter(log_format)
    rotating_file_handler.addFilter(sens_filter)

    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Avoid duplicate handlers if reloaded
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(rotating_file_handler)

    # Silence noisy third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logger = logging.getLogger("hav_scrap")
    logger.info(f"Rotating logging initialized. Telemetry directed to: {log_file}")
    return logger


logger = logging.getLogger("hav_scrap")
