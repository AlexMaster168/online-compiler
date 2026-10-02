"""Local Arduino toolchain; only compiled firmware is sent to the browser."""
import json
import threading
import uuid

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .engine import docker
from .engine.workspace import Workspace
from .engine.process import run_limited
from .payload import BadRequest, api, json_body, no_nul, str_field
from .accounts import visible_snippet_or_404, user_dict, update_snippet
from .models import Snippet

BUILD_SLOTS = threading.BoundedSemaphore(2)
DIAGRAM_MAX_BYTES = 64 * 1024


def diagram_files(text: str) -> list[dict]:
    """Схема с деталями хранится файлом diagram.json рядом со скетчем; пустая строка — схемы нет."""
    if not text:
        return []
    try:
        diagram = json.loads(text)
    except ValueError:
        raise BadRequest("Схема повреждена: это не JSON")
    if not isinstance(diagram, dict) or not isinstance(diagram.get("parts", []), list):
        raise BadRequest("Схема повреждена: нет списка деталей")
    return [{"name": "diagram.json", "content": text}]


@ensure_csrf_cookie
def page(request, snippet_id=None):
    project = visible_snippet_or_404(request, snippet_id) if snippet_id else None
    if project and project.language != "arduino":
        from django.http import Http404
        raise Http404
    return render(request, "compiler/arduino.html", {
        "project": project.to_dict(request.user) if project else None,
        "user": user_dict(request.user),
    })


@require_POST
@api
def save(request):
    data = json_body(request)
    code = no_nul(str_field(data, "code", required=True, max_bytes=128 * 1024))
    files = diagram_files(str_field(data, "diagram", max_bytes=DIAGRAM_MAX_BYTES))
    identifier = str_field(data, "id")
    if identifier:
        project = visible_snippet_or_404(request, identifier)
        if project.language != "arduino" or not request.user.is_authenticated or project.owner_id != request.user.pk:
            return JsonResponse({"error": "Сохранять этот проект может только владелец"}, status=403)
        update_snippet(project, {"title": str_field(data, "title")})
        project.code = code
        project.files = files
        project.save(update_fields=["code", "files", "updated_at"])
    else:
        project = Snippet.objects.create(
            language="arduino", code=code, files=files, title=str_field(data, "title")[:200],
            owner=request.user if request.user.is_authenticated else None,
        )
    return JsonResponse(project.to_dict(request.user), status=200 if identifier else 201)


@require_POST
@api
def compile_uno(request):
    code = str_field(json_body(request), "code", required=True, max_bytes=128 * 1024)
    cfg = settings.EXECUTOR
    if not docker.daemon_available(cfg) or not docker.image_present("oc-lang-arduino:1", cfg):
        return JsonResponse({"error": "Сборщик Arduino недоступен. Собери образ Arduino."}, status=503)
    if not BUILD_SLOTS.acquire(blocking=False):
        return JsonResponse({"error": "Сборщики заняты, попробуй через несколько секунд"}, status=429)
    name = "oc-uno-" + uuid.uuid4().hex
    try:
        with Workspace(prefix="oc-uno-") as ws:
            ws.write("sketch/sketch.ino", code)
            argv = [docker._docker(cfg), "run", "--rm", "--name", name,
                    "--network", "none", "--read-only", "--cap-drop", "ALL",
                    "--security-opt", "no-new-privileges", "--user", "65534:65534",
                    "--memory", "768m", "--cpus", "2", "--pids-limit", "96",
                    "--tmpfs", "/tmp:rw,nosuid,size=256m", "-v", f"{ws.path}:/code:rw",
                    "-e", "HOME=/tmp", "oc-lang-arduino:1", "arduino-cli", "compile",
                    "--fqbn", "arduino:avr:uno", "--build-path", "/tmp/build",
                    "--output-dir", "/code/out", "/code/sketch"]
            try:
                result = run_limited(argv, cwd=str(ws.path), timeout=90, max_output=256 * 1024)
            except OSError:
                return JsonResponse({"error": "Не удалось запустить сборщик Arduino"}, status=503)
            if result.timed_out or result.output_exceeded:
                docker.kill_container(name, cfg)
                return JsonResponse({"error": "Сборка превысила лимит времени или вывода"}, status=408)
            log = ws.clean((result.stdout + result.stderr).decode("utf-8", errors="replace"), "/code")[-24000:]
            firmware = ws.path / "out/sketch.ino.hex"
            if result.exit_code or not firmware.exists():
                return JsonResponse({"error": "Ошибка компиляции", "log": log}, status=422)
            return JsonResponse({"hex": firmware.read_text(encoding="ascii"), "log": log})
    finally:
        docker.kill_container(name, cfg)
        BUILD_SLOTS.release()
