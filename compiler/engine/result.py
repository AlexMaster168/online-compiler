from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum


class Status(StrEnum):
    OK = "ok"
    COMPILE_ERROR = "compile_error"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    MEMORY_LIMIT = "memory_limit"
    OUTPUT_LIMIT = "output_limit"
    STOPPED = "stopped"
    UNAVAILABLE = "unavailable"
    INTERNAL_ERROR = "internal_error"


@dataclass
class ExecutionResult:
    status: Status
    stdout: str = ""
    stderr: str = ""
    compile_output: str = ""
    exit_code: int | None = None
    time_ms: int | None = None
    memory_kb: int | None = None
    backend: str = ""
    message: str = ""
    truncated: bool = False
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["status"] = str(self.status)
        data.pop("extra")
        return data
