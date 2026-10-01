"""Запуск процесса с лимитами: время, память, объём вывода, число процессов.

На Windows процесс стартует приостановленным, попадает в Job Object (лимит памяти,
лимит процессов, убийство всего дерева при закрытии) и только потом возобновляется —
так ни один дочерний процесс не ускользнёт из-под лимитов.
На POSIX — отдельная сессия (для kill всей группы) и rlimit на CPU/размер файлов.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass

IS_WINDOWS = sys.platform == "win32"


@dataclass
class ProcOutcome:
    stdout: bytes
    stderr: bytes
    exit_code: int | None
    time_ms: int
    timed_out: bool = False
    output_exceeded: bool = False
    memory_exceeded: bool = False
    peak_memory_bytes: int | None = None


if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _ntdll = ctypes.WinDLL("ntdll")

    class _IoCounters(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ulonglong) for name in (
            "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
            "ReadTransferCount", "WriteTransferCount", "OtherTransferCount",
        )]

    class _BasicLimits(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class _ExtendedLimits(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _BasicLimits),
            ("IoInfo", _IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    class _BasicAccounting(ctypes.Structure):
        _fields_ = [
            ("TotalUserTime", ctypes.c_int64),
            ("TotalKernelTime", ctypes.c_int64),
            ("ThisPeriodTotalUserTime", ctypes.c_int64),
            ("ThisPeriodTotalKernelTime", ctypes.c_int64),
            ("TotalPageFaultCount", wintypes.DWORD),
            ("TotalProcesses", wintypes.DWORD),
            ("ActiveProcesses", wintypes.DWORD),
            ("TotalTerminatedProcesses", wintypes.DWORD),
        ]

    _JobObjectBasicAccountingInformation = 1
    _JobObjectExtendedLimitInformation = 9
    _LIMIT_JOB_TIME = 0x00000004
    _LIMIT_ACTIVE_PROCESS = 0x00000008
    _LIMIT_JOB_MEMORY = 0x00000200
    _LIMIT_DIE_ON_UNHANDLED_EXCEPTION = 0x00000400
    _LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
    _CREATE_SUSPENDED = 0x00000004
    _CREATE_NO_WINDOW = 0x08000000

    _kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    _kernel32.CreateJobObjectW.argtypes = (wintypes.LPVOID, wintypes.LPCWSTR)
    _kernel32.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD)
    _kernel32.QueryInformationJobObject.argtypes = (
        wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD, wintypes.LPVOID)
    _kernel32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    _kernel32.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
    _kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _ntdll.NtResumeProcess.argtypes = (wintypes.HANDLE,)

    class _Job:
        def __init__(self, memory_bytes: int | None, max_processes: int | None, cpu_seconds: float | None = None):
            self.handle = _kernel32.CreateJobObjectW(None, None)
            if not self.handle:
                raise ctypes.WinError(ctypes.get_last_error())
            info = _ExtendedLimits()
            flags = _LIMIT_KILL_ON_JOB_CLOSE | _LIMIT_DIE_ON_UNHANDLED_EXCEPTION
            if memory_bytes:
                flags |= _LIMIT_JOB_MEMORY
                info.JobMemoryLimit = memory_bytes
            if cpu_seconds:
                # Лимит процессорного времени на всю job: ожидание ввода его не тратит, бесконечный цикл — тратит
                flags |= _LIMIT_JOB_TIME
                info.BasicLimitInformation.PerJobUserTimeLimit = int(cpu_seconds * 10_000_000)
            if max_processes:
                flags |= _LIMIT_ACTIVE_PROCESS
                info.BasicLimitInformation.ActiveProcessLimit = max_processes
            info.BasicLimitInformation.LimitFlags = flags
            if not _kernel32.SetInformationJobObject(
                    self.handle, _JobObjectExtendedLimitInformation, ctypes.byref(info), ctypes.sizeof(info)):
                err = ctypes.get_last_error()
                self.close()
                raise ctypes.WinError(err)

        def attach_and_resume(self, proc: subprocess.Popen) -> None:
            handle = int(proc._handle)  # noqa: SLF001 — Popen не даёт публичного доступа к хэндлу
            if not _kernel32.AssignProcessToJobObject(self.handle, handle):
                err = ctypes.get_last_error()
                proc.kill()
                raise ctypes.WinError(err)
            _ntdll.NtResumeProcess(handle)

        def peak_memory(self) -> int | None:
            info = _ExtendedLimits()
            ok = _kernel32.QueryInformationJobObject(
                self.handle, _JobObjectExtendedLimitInformation, ctypes.byref(info), ctypes.sizeof(info), None)
            return int(info.PeakJobMemoryUsed) if ok else None

        def cpu_seconds(self) -> float | None:
            info = _BasicAccounting()
            ok = _kernel32.QueryInformationJobObject(
                self.handle, _JobObjectBasicAccountingInformation, ctypes.byref(info), ctypes.sizeof(info), None)
            return info.TotalUserTime / 10_000_000 if ok else None

        def kill(self) -> None:
            if self.handle:
                _kernel32.TerminateJobObject(self.handle, 1)

        def close(self) -> None:
            if self.handle:
                _kernel32.CloseHandle(self.handle)
                self.handle = None


class _CappedReader(threading.Thread):
    """Читает поток в фоне; при превышении общего бюджета сигналит и дальше только сливает данные."""

    def __init__(self, stream, budget: dict, lock: threading.Lock, on_overflow):
        super().__init__(daemon=True)
        self.stream = stream
        self.budget = budget
        self.lock = lock
        self.on_overflow = on_overflow
        self.chunks: list[bytes] = []

    def run(self) -> None:
        read = getattr(self.stream, "read1", self.stream.read)
        try:
            while chunk := read(65536):
                with self.lock:
                    left = self.budget["left"]
                    if left <= 0:
                        continue
                    self.chunks.append(chunk[:left])
                    self.budget["left"] = left - len(chunk)
                    overflow = self.budget["left"] < 0
                if overflow:
                    self.on_overflow()
        except (OSError, ValueError):
            pass

    @property
    def data(self) -> bytes:
        return b"".join(self.chunks)


def _feed_stdin(stream, data: bytes) -> None:
    try:
        if data:
            stream.write(data)
    except (BrokenPipeError, OSError, ValueError):
        pass
    finally:
        try:
            stream.close()
        except OSError:
            pass


def run_limited(
    argv: list[str],
    *,
    cwd: str,
    stdin: bytes = b"",
    timeout: float,
    memory_mb: int | None = None,
    max_output: int = 64 * 1024,
    max_processes: int | None = None,
    env: dict[str, str] | None = None,
) -> ProcOutcome:
    job = None
    popen_kwargs: dict = {}
    if IS_WINDOWS:
        popen_kwargs["creationflags"] = _CREATE_SUSPENDED | _CREATE_NO_WINDOW
        job = _Job(memory_mb * 1024 * 1024 if memory_mb else None, max_processes)
    else:
        popen_kwargs["start_new_session"] = True
        popen_kwargs["preexec_fn"] = _posix_limits(timeout, max_output)

    started = time.perf_counter()
    try:
        proc = subprocess.Popen(
            argv, cwd=cwd, env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            **popen_kwargs,
        )
    except OSError:
        if job:
            job.close()
        raise

    overflow = threading.Event()

    def kill() -> None:
        if job:
            job.kill()
        else:
            _posix_killpg(proc)

    def on_overflow() -> None:
        overflow.set()
        kill()

    try:
        if job:
            job.attach_and_resume(proc)
        started = time.perf_counter()

        budget = {"left": max_output}
        lock = threading.Lock()
        readers = [_CappedReader(proc.stdout, budget, lock, on_overflow),
                   _CappedReader(proc.stderr, budget, lock, on_overflow)]
        for reader in readers:
            reader.start()
        feeder = threading.Thread(target=_feed_stdin, args=(proc.stdin, stdin), daemon=True)
        feeder.start()

        timed_out = False
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            kill()
            proc.wait()
        elapsed = int((time.perf_counter() - started) * 1000)

        # Главный процесс завершился — потомки не должны его пережить и держать пайпы открытыми
        peak = job.peak_memory() if job else None
        kill()
        for reader in readers:
            reader.join(timeout=2)
    finally:
        if job:
            job.kill()
            job.close()
        else:
            _posix_killpg(proc)
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            try:
                stream.close()
            except OSError:
                pass

    memory_exceeded = bool(
        memory_mb and peak and not timed_out and proc.returncode != 0
        and peak >= memory_mb * 1024 * 1024 * 0.9
    )
    return ProcOutcome(
        stdout=readers[0].data,
        stderr=readers[1].data,
        exit_code=proc.returncode,
        time_ms=elapsed,
        timed_out=timed_out,
        output_exceeded=overflow.is_set(),
        memory_exceeded=memory_exceeded,
        peak_memory_bytes=peak,
    )


def _posix_limits(timeout: float, max_output: int):
    def apply() -> None:
        import resource
        cpu = int(timeout) + 1
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
        size = max(max_output * 16, 64 * 1024 * 1024)
        resource.setrlimit(resource.RLIMIT_FSIZE, (size, size))
    return apply


def _posix_killpg(proc: subprocess.Popen) -> None:
    if IS_WINDOWS:
        return
    import signal
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        pass


class StreamProcess:
    """Процесс для интерактивного режима: вывод отдаётся колбэками по мере появления, ввод пишется на лету.

    Лимиты: память, число процессов и CPU-время (Windows — Job Object, POSIX — rlimit).
    Wall-таймаут — забота вызывающего (программа может законно ждать ввод).
    """

    def __init__(self, argv: list[str], *, cwd: str, env: dict[str, str] | None,
                 on_stdout, on_stderr, memory_mb: int | None = None,
                 max_processes: int | None = None, cpu_seconds: float | None = None):
        self.cpu_limit = cpu_seconds
        self.memory_mb = memory_mb
        self._job = None
        self._write_lock = threading.Lock()
        popen_kwargs: dict = {}
        if IS_WINDOWS:
            popen_kwargs["creationflags"] = _CREATE_SUSPENDED | _CREATE_NO_WINDOW
            self._job = _Job(memory_mb * 1024 * 1024 if memory_mb else None, max_processes, cpu_seconds)
        else:
            popen_kwargs["start_new_session"] = True
            popen_kwargs["preexec_fn"] = _posix_limits(cpu_seconds or 10, 64 * 1024 * 1024)
        try:
            self.proc = subprocess.Popen(
                argv, cwd=cwd, env=env, bufsize=0,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **popen_kwargs,
            )
            if self._job:
                self._job.attach_and_resume(self.proc)
        except Exception:
            if self._job:
                self._job.kill()
                self._job.close()
            raise
        self.started = time.perf_counter()
        self._readers = [
            threading.Thread(target=self._pump, args=(self.proc.stdout, on_stdout), daemon=True),
            threading.Thread(target=self._pump, args=(self.proc.stderr, on_stderr), daemon=True),
        ]
        for reader in self._readers:
            reader.start()

    @staticmethod
    def _pump(stream, callback) -> None:
        read = getattr(stream, "read1", stream.read)
        try:
            while chunk := read(65536):
                callback(chunk)
        except (OSError, ValueError):
            pass

    def write(self, data: bytes) -> bool:
        with self._write_lock:
            try:
                self.proc.stdin.write(data)
                self.proc.stdin.flush()
                return True
            except (BrokenPipeError, OSError, ValueError):
                return False

    def close_stdin(self) -> None:
        with self._write_lock:
            try:
                self.proc.stdin.close()
            except OSError:
                pass

    def kill(self) -> None:
        if self._job:
            self._job.kill()
        else:
            _posix_killpg(self.proc)
            try:
                self.proc.kill()
            except OSError:
                pass

    def wait(self, timeout: float | None = None) -> int | None:
        """Ждёт главный процесс; потомков добивает, чтобы они не держали пайпы. None — не дождались."""
        try:
            code = self.proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            return None
        self.elapsed_ms = int((time.perf_counter() - self.started) * 1000)
        self.peak_memory = self._job.peak_memory() if self._job else None
        self.cpu_used = self._job.cpu_seconds() if self._job else None
        self.kill()
        for reader in self._readers:
            reader.join(timeout=2)
        return code

    def cpu_now(self) -> float | None:
        """Сколько CPU уже съедено. Windows сам проверяет лимит job лениво (с опозданием на секунды),
        поэтому сессия опрашивает это и убивает процесс сама — ровно по лимиту."""
        return self._job.cpu_seconds() if self._job else None

    @property
    def cpu_exceeded(self) -> bool:
        used = getattr(self, "cpu_used", None)
        return bool(self.cpu_limit and used is not None and used >= self.cpu_limit * 0.97)

    @property
    def memory_exceeded(self) -> bool:
        peak = getattr(self, "peak_memory", None)
        return bool(self.memory_mb and peak and self.proc.returncode != 0
                    and peak >= self.memory_mb * 1024 * 1024 * 0.9)

    def close(self) -> None:
        self.kill()
        if self._job:
            self._job.close()
            self._job = None
        for stream in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
            try:
                stream.close()
            except OSError:
                pass
