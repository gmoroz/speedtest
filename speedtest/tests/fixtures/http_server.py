"""Локальный HTTP-сервер для интеграционных тестов."""

from collections.abc import Iterator
from contextlib import suppress
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread
from time import sleep
from urllib.parse import urlsplit

import pytest

IMAGE_PAYLOAD = bytes(range(256)) * 1024


@dataclass(slots=True)
class _ServerState:
    served_paths: list[str]
    in_flight: int = 0
    max_concurrent_requests: int = 0


@dataclass(frozen=True, slots=True)
class HttpServer:
    """Состояние локального HTTP-сервера и статистика его запросов."""

    base_url: str
    _state: _ServerState

    @property
    def served_paths(self) -> list[str]:
        """Возвращает пути обслуженных запросов."""
        return self._state.served_paths

    @property
    def max_concurrent_requests(self) -> int:
        """Возвращает максимум одновременно обрабатывавшихся запросов."""
        return self._state.max_concurrent_requests


@pytest.fixture
def http_server() -> Iterator[HttpServer]:
    """Запускает локальный HTTP-сервер и останавливает его после теста."""
    state = _ServerState(served_paths=[])
    state_lock = Lock()

    class RequestHandler(BaseHTTPRequestHandler):
        # Keep-alive: запросы одного соединения обслуживает один поток строго по очереди. При HTTP/1.0 каждый
        # запрос шёл в новом потоке, и предыдущий ещё не снимал счётчик in-flight, когда клиент уже слал следующий.
        protocol_version = "HTTP/1.1"

        def _send_body(self, status_code: int, body: bytes, content_type: str) -> None:
            with suppress(ConnectionError):
                self.send_response(status_code)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            with state_lock:
                state.served_paths.append(path)
                state.in_flight += 1
                state.max_concurrent_requests = max(state.max_concurrent_requests, state.in_flight)

            try:
                if path == "/redirect":
                    with suppress(ConnectionError):
                        self.send_response(302)
                        self.send_header("Location", "/image.bin")
                        self.send_header("Content-Length", "0")
                        self.end_headers()
                    return

                if path == "/slow":
                    sleep(1)
                    self._send_body(200, IMAGE_PAYLOAD, "image/jpeg")
                    return

                if path == "/image.bin":
                    self._send_body(200, IMAGE_PAYLOAD, "image/jpeg")
                    return

                if path == "/empty":
                    self._send_body(200, b"", "image/jpeg")
                    return

                if path == "/missing":
                    self._send_body(404, b"missing", "text/plain")
                    return

                self._send_body(404, b"not found", "text/plain")
            finally:
                with state_lock:
                    state.in_flight -= 1

        def log_message(self, _format: str, *_args: object) -> None:
            """Не выводит журналы HTTP-запросов в stderr."""

    server = ThreadingHTTPServer(("127.0.0.1", 0), RequestHandler)
    server.daemon_threads = True
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    server_info = HttpServer(base_url=f"http://127.0.0.1:{server.server_port}", _state=state)

    try:
        yield server_info
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
