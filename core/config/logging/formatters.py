import json
import logging

from .log_records import SimpleLogRecord

class FileJSONFormatter(logging.Formatter):
    """Форматер для логів у форматі JSON."""

    def format(self, record: SimpleLogRecord) -> str:
        log_data = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "username": getattr(record, "username", None),
            "exception": self.formatException(record.exc_info).splitlines() if record.exc_info is not None else None,
        }
        return json.dumps(log_data)