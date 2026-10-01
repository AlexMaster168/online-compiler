"""WebSocket /ws/run/ — интерактивная консоль.

Клиент → сервер:
    {"type": "start", "language": ..., "code": ..., "files": [...]}
    {"type": "stdin", "data": "42\\n"}
    {"type": "eof"} | {"type": "interrupt"} | {"type": "kill"}
Сервер → клиент:
    {"type": "phase", "phase": "prepare" | "compile" | "run"}
    {"type": "output", "stream": "compile" | "stdout" | "stderr", "data": "..."}
    {"type": "exit", "id": <Execution.pk>, ...ExecutionResult}
    {"type": "error", "error": "..."}
"""
from __future__ import annotations

import asyncio

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .engine.dap import DapError
from .engine.debugger import DebugSession
from .engine.interactive import Session
from .payload import BadRequest, parse_breakpoints, parse_run, rate_limited, save_execution

MAX_STDIN_MESSAGE = 64 * 1024
DEBUG_COMMANDS = {"continue", "next", "stepIn", "stepOut", "pause", "setBreakpoints", "scopes", "variables",
                  "evaluate"}


class RunConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.session: Session | None = None
        self.request = None
        self.queue: asyncio.Queue = asyncio.Queue()
        self.loop = asyncio.get_running_loop()
        await self.accept()
        self.sender = asyncio.create_task(self._sender())

    async def disconnect(self, code):
        if self.session is not None:
            self.session.kill()
        self.sender.cancel()

    async def receive_json(self, content, **kwargs):
        if not isinstance(content, dict):
            return
        kind = content.get("type")
        session = self.session
        running = session is not None and not session.done.is_set()

        if kind in ("start", "debug_start"):
            await self._start(content, running, debug=kind == "debug_start")
        elif not running:
            return
        elif kind == "debug":
            await self._debug_request(content)
        elif kind == "stdin":
            data = content.get("data")
            if isinstance(data, str) and data:
                session.write(data[:MAX_STDIN_MESSAGE])
        elif kind == "eof":
            session.eof()
        elif kind == "interrupt":
            session.interrupt()
        elif kind == "kill":
            session.kill()

    async def _start(self, content: dict, running: bool, debug: bool = False) -> None:
        if running:
            await self.send_json({"type": "error", "error": "Программа уже запущена — останови её сначала"})
            return
        try:
            req = parse_run(content, with_stdin=False)
            breakpoints = parse_breakpoints(content, req) if debug else None
        except BadRequest as exc:
            await self.send_json({"type": "error", "error": str(exc)})
            return
        if await database_sync_to_async(rate_limited)(self._client_ip()):
            await self.send_json({"type": "error", "error": "Слишком много запусков, передохни минутку"})
            return
        self.request = req
        if debug:
            self.session = DebugSession(req.language, req.code, req.files_dict, emit=self._emit_threadsafe,
                                        breakpoints=breakpoints, args=req.argv)
        else:
            self.session = Session(req.language, req.code, req.files_dict, emit=self._emit_threadsafe, args=req.argv)
        self.session.start()
        if req.language == "esp32":
            from .esp32_preview import register
            await self.send_json({"type": "esp32_preview", "url": register(self.session)})

    async def _debug_request(self, content: dict) -> None:
        """Команда отладчику. DAP-запросы блокирующие — выполняем в потоке, ответ шлём с тем же id."""
        session = self.session
        request_id = content.get("id")
        command = content.get("command")
        args = content.get("args") if isinstance(content.get("args"), dict) else {}
        if not isinstance(session, DebugSession) or command not in DEBUG_COMMANDS:
            await self.send_json({"type": "debug_reply", "id": request_id, "error": "Команда недоступна"})
            return
        try:
            body = await asyncio.to_thread(session.request, command, args)
            await self.send_json({"type": "debug_reply", "id": request_id, "body": body})
        except (DapError, KeyError, ValueError, TypeError) as exc:
            await self.send_json({"type": "debug_reply", "id": request_id, "error": str(exc) or "Ошибка отладчика"})

    def _emit_threadsafe(self, event: dict) -> None:
        # Сессия живёт в своём потоке — в цикл событий передаём только через call_soon_threadsafe
        self.loop.call_soon_threadsafe(self.queue.put_nowait, (self.session, event))

    async def _sender(self) -> None:
        """Отправляет события по порядку; подряд идущий вывод склеивает, чтобы не заваливать сокет."""
        while True:
            session, event = await self.queue.get()
            batch = [event]
            while not self.queue.empty() and len(batch) < 256:
                batch.append(self.queue.get_nowait()[1])
            merged: list[dict] = []
            for ev in batch:
                prev = merged[-1] if merged else None
                if (prev and ev["type"] == "output" and prev["type"] == "output"
                        and prev["stream"] == ev["stream"]):
                    prev["data"] += ev["data"]
                else:
                    merged.append(dict(ev))
            for ev in merged:
                if ev["type"] == "exit":
                    ev["id"] = await self._save(session)
                await self.send_json(ev)

    async def _save(self, session: Session) -> int | None:
        if session is None or session.result is None or self.request is None:
            return None
        key = await self._session_key()
        execution = await database_sync_to_async(save_execution)(
            self.request, session.result, session_key=key, client_ip=self._client_ip(),
            stdin=session.stdin_text, user=self.scope.get("user"),
        )
        return execution.pk

    @database_sync_to_async
    def _session_key(self) -> str:
        http_session = self.scope.get("session")
        if http_session is None:
            return ""
        if not http_session.session_key:
            http_session.save()
        return http_session.session_key

    def _client_ip(self) -> str | None:
        client = self.scope.get("client")
        return client[0] if client else None
