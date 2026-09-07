import logging


GREY = "\x1b[38;20m"
BLUE = "\x1b[34;20m"
YELLOW = "\x1b[33;20m"
RED = "\x1b[31;20m"
BOLD_RED = "\x1b[31;1m"
RESET = "\x1b[0m"

LVL_COLOR = {
    logging.DEBUG: BLUE,
    logging.INFO: GREY,
    logging.WARNING: YELLOW,
    logging.ERROR: RED,
    logging.CRITICAL: BOLD_RED,
}


class ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        color = LVL_COLOR.get(record.levelno)
        if color:
            return color + formatted + RESET
        else:
            return formatted
