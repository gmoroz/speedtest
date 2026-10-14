"""Фейки HTTP-транспортов для модульных тестов."""

import httpx


class CloseTrackingTransport(httpx.MockTransport):
    """Запоминает вызов закрытия MockTransport."""

    closed = False

    def close(self) -> None:
        """Закрывает транспорт и фиксирует это для теста."""
        self.closed = True
        super().close()
