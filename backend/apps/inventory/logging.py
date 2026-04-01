from __future__ import annotations

import logging


class AuditContextFilter(logging.Filter):
    """Ensure audit formatter always has user/action placeholders."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "user"):
            record.user = "system"
        if not hasattr(record, "action"):
            record.action = "unknown"
        return True
