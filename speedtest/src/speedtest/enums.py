"""Перечисление кода завершения командной строки."""

from enum import IntEnum


class ExitCode(IntEnum):
    """Коды завершения командной строки."""

    OK = 0
    ERROR = 1
    INTERRUPTED = 130
