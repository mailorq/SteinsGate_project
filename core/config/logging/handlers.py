import logging
from .log_records import SimpleLogRecord

class JSONFileHandler(logging.FileHandler):
    """Хендлер для запису логів у файл у форматі JSON."""

    def __init__(self, filename: str, level:int|str = 0) -> None:
        super().__init__(level)
        self.filename = filename

    def emit(self, record: SimpleLogRecord) -> None:
        try:
            msg = self.format(record)
            with open(self.filename, "a", encoding="utf-8") as log_file:
                log_file.write(msg + "\n")
        except Exception:
            self.handleError(record)