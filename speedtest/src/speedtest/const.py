"""Константы пакета. Только значения - без runtime-логики и настроек."""

DEFAULT_REQUEST_COUNT = 10
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_TIMEOUT_SECONDS = 3600.0

# Десятичный мегабайт (SI): так скорость сопоставима с цифрами провайдеров и speedtest-сервисов.
BYTES_PER_MEGABYTE = 1_000_000

ALLOWED_URL_SCHEMES = frozenset({"http", "https"})

# Часть CDN (например, Wikimedia) отклоняет запросы без осмысленного User-Agent.
USER_AGENT = "speedtest-cli (+https://github.com/gmoroz/speedtest)"
