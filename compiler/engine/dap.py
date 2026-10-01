"""Минимальный клиент Debug Adapter Protocol (https://microsoft.github.io/debug-adapter-protocol/).

Транспорт не важен: байты от адаптера подаются в feed(), отправка — через write-колбэк.
События обрабатываются в отдельном потоке, поэтому обработчик события может сам делать
синхронные запросы (stackTrace, variables…) — ответы разбираются в потоке чтения.
"""
from __future__ import annotations

import json
import logging
import queue
import threading

log = logging.getLogger(__name__)


class DapError(Exception):
    pass


class Pending:
    def __init__(self, command: str):
        self.command = command
        self._done = threading.Event()
        self._response: dict | None = None

    def resolve(self, response: dict) -> None:
        self._response = response
        self._done.set()

    def fail(self, message: str) -> None:
        self.resolve({"success": False, "message": message})

    def wait(self, timeout: float = 30) -> dict:
        if not self._done.wait(timeout):
            raise DapError(f"Отладчик не ответил на {self.command} за {timeout:g} с")
        response = self._response or {}
        if not response.get("success"):
            body = response.get("body") or {}
            error = (body.get("error") or {}).get("format") if isinstance(body, dict) else None
            raise DapError(error or response.get("message") or f"{self.command}: ошибка отладчика")
        return response.get("body") or {}


class DapClient:
    def __init__(self, write, on_event):
        self._write = write
        self._on_event = on_event
        self._seq = 0
        self._lock = threading.Lock()
        self._pending: dict[int, Pending] = {}
        self._buffer = b""
        self._events: queue.Queue = queue.Queue()
        self.closed = threading.Event()
        threading.Thread(target=self._dispatch, name="dap-events", daemon=True).start()

    # ---------- входящие байты ----------

    def feed(self, data: bytes) -> None:
        self._buffer += data
        while True:
            header_end = self._buffer.find(b"\r\n\r\n")
            if header_end < 0:
                return
            length = None
            for line in self._buffer[:header_end].split(b"\r\n"):
                name, _, value = line.partition(b":")
                if name.strip().lower() == b"content-length":
                    length = int(value.strip())
            if length is None:  # мусор до заголовка — выкидываем строку
                self._buffer = self._buffer[header_end + 4:]
                continue
            start = header_end + 4
            if len(self._buffer) < start + length:
                return
            body, self._buffer = self._buffer[start:start + length], self._buffer[start + length:]
            try:
                self._handle(json.loads(body))
            except (ValueError, UnicodeDecodeError):
                log.warning("Битое DAP-сообщение: %r", body[:200])

    def _handle(self, message: dict) -> None:
        kind = message.get("type")
        if kind == "response":
            with self._lock:
                pending = self._pending.pop(message.get("request_seq"), None)
            if pending:
                pending.resolve(message)
        elif kind == "event":
            self._events.put(message)
        elif kind == "request":
            # Обратные запросы (runInTerminal и т.п.) не поддерживаем — отвечаем отказом, чтобы адаптер не ждал
            self._send({"type": "response", "request_seq": message.get("seq"), "command": message.get("command"),
                        "success": False, "message": "not supported"})

    def _dispatch(self) -> None:
        while True:
            event = self._events.get()
            if event is None:
                return
            try:
                self._on_event(event)
            except Exception:
                log.exception("Ошибка в обработчике DAP-события %s", event.get("event"))

    # ---------- исходящие ----------

    def _send(self, message: dict) -> None:
        data = json.dumps(message, ensure_ascii=False).encode("utf-8")
        self._write(b"Content-Length: %d\r\n\r\n" % len(data) + data)

    def request_async(self, command: str, arguments: dict | None = None) -> Pending:
        pending = Pending(command)
        if self.closed.is_set():
            pending.fail("Отладчик отключился")
            return pending
        with self._lock:
            self._seq += 1
            seq = self._seq
            self._pending[seq] = pending
        message = {"seq": seq, "type": "request", "command": command}
        if arguments is not None:
            message["arguments"] = arguments
        try:
            self._send(message)
        except Exception as exc:
            with self._lock:
                self._pending.pop(seq, None)
            pending.fail(f"Не удалось отправить {command}: {exc}")
        return pending

    def request(self, command: str, arguments: dict | None = None, timeout: float = 30) -> dict:
        return self.request_async(command, arguments).wait(timeout)

    def close(self) -> None:
        if self.closed.is_set():
            return
        self.closed.set()
        with self._lock:
            pending, self._pending = list(self._pending.values()), {}
        for item in pending:
            item.fail("Отладчик отключился")
        self._events.put(None)
