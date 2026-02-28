import logging


class SimpleLogRecord(logging.LogRecord):
    """Додає не стандартні поля до запису логу."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.username: int | None = None



logging.setLogRecordFactory(SimpleLogRecord)