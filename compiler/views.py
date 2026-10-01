import io
import re
import zipfile

from django.conf import settings
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from . import engine
from .accounts import SNIPPETS, user_dict
from .engine.formatter import FormatError, server_formatter
from .engine.formatter import format_code as run_formatter
from .models import Execution, Snippet
from .payload import (
    api, args_field, files_field, json_body, language_field, no_nul, parse_run, rate_limited, save_execution, str_field,
)

HISTORY_SIZE = 30


def _session_key(request) -> str:
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _client_ip(request) -> str | None:
    return request.META.get("REMOTE_ADDR") or None


@ensure_csrf_cookie
def index(request, snippet_id: str | None = None):
    _session_key(request)  # сессия нужна до открытия WebSocket-консоли: по ней пишется история
    snippet = None
    if snippet_id:
        snippet = get_object_or_404(SNIPPETS, pk=snippet_id)
        Snippet.objects.filter(pk=snippet.pk).update(views=snippet.views + 1)
    return render(request, "compiler/index.html", {
        "snippet": snippet.to_dict(request.user) if snippet else None,
        "limits": _limits(),
        "user": user_dict(request.user),
    })


def snippet_raw(request, snippet_id: str):
    snippet = get_object_or_404(Snippet, pk=snippet_id)
    return HttpResponse(snippet.code, content_type="text/plain; charset=utf-8")


def _zip_response(slug: str, code: str, files: list[dict], title: str = "") -> HttpResponse:
    """Проект одним архивом: главный файл + все дополнительные, с путями."""
    lang = engine.get_language(slug)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(lang.filename, code)
        for item in files:
            zf.writestr(item["name"], item["content"])
    base = re.sub(r"[^\w.-]+", "-", title, flags=re.ASCII).strip("-.")[:60] or f"{slug}-project"
    response = HttpResponse(buf.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{base}.zip"'
    return response


def snippet_zip(request, snippet_id: str):
    snippet = get_object_or_404(Snippet, pk=snippet_id)
    return _zip_response(snippet.language, snippet.code, snippet.files, snippet.title or snippet.id)


@require_POST
@api
def project_zip(request):
    data = json_body(request)
    slug = language_field(data)
    code = str_field(data, "code", max_bytes=settings.EXECUTOR["MAX_CODE_BYTES"])
    return _zip_response(slug, code, files_field(data, slug, code), str_field(data, "title"))


@require_POST
@api
def format_code(request):
    """Beautify для языков без браузерного форматтера (Rust, Elixir)."""
    data = json_body(request)
    slug = language_field(data)
    code = str_field(data, "code", required=True, max_bytes=settings.EXECUTOR["MAX_CODE_BYTES"])
    if server_formatter(slug) is None:
        return JsonResponse({"error": "Этот язык форматируется в браузере или не форматируется вовсе"}, status=400)
    if rate_limited(_client_ip(request), "format"):
        return JsonResponse({"error": "Слишком много запросов, передохни минутку"}, status=429)
    try:
        return JsonResponse({"code": run_formatter(slug, code, settings.EXECUTOR)})
    except FormatError as exc:
        return JsonResponse({"error": str(exc)}, status=422)


def _limits() -> dict:
    cfg = settings.EXECUTOR
    return {
        "run_timeout": cfg["RUN_TIMEOUT"],
        "compile_timeout": cfg["COMPILE_TIMEOUT"],
        "memory_mb": cfg["MEMORY_MB"],
        "max_output_kb": cfg["MAX_OUTPUT_BYTES"] // 1024,
        "max_code_kb": cfg["MAX_CODE_BYTES"] // 1024,
        "interactive_timeout": cfg["INTERACTIVE_TIMEOUT"],
    }


@require_GET
def languages(request):
    return JsonResponse({"languages": engine.language_catalog(), "limits": _limits()})


@require_POST
@api
def run(request):
    req = parse_run(json_body(request))
    if rate_limited(_client_ip(request)):
        return JsonResponse({"error": "Слишком много запусков, передохни минутку"}, status=429)

    result = engine.execute(req.language, req.code, req.stdin, req.files_dict, req.argv)
    execution = save_execution(req, result, session_key=_session_key(request), client_ip=_client_ip(request),
                               user=request.user)
    return JsonResponse({"id": execution.pk, **result.to_dict()})


@require_POST
@api
def create_snippet(request):
    cfg = settings.EXECUTOR
    data = json_body(request)
    slug = language_field(data)
    code = str_field(data, "code", required=True, max_bytes=cfg["MAX_CODE_BYTES"])
    snippet = Snippet.objects.create(
        language=slug,
        code=no_nul(code),
        files=files_field(data, slug, code),
        stdin=no_nul(str_field(data, "stdin", max_bytes=cfg["MAX_STDIN_BYTES"])),
        args=args_field(data)[0],
        title=str_field(data, "title")[:200],
        session_key=_session_key(request),
        owner=request.user if request.user.is_authenticated else None,  # залогиненный — сразу в «Мои проекты»
    )
    return JsonResponse(SNIPPETS.get(pk=snippet.pk).to_dict(request.user), status=201)


def _own_executions(request):
    """История: у залогиненного — его запуски с любого устройства, у анонима — запуски этой сессии."""
    if request.user.is_authenticated:
        return Execution.objects.filter(user=request.user)
    key = request.session.session_key
    return Execution.objects.filter(session_key=key, user__isnull=True) if key else Execution.objects.none()


@require_GET
def history(request):
    qs = _own_executions(request).only(
        "id", "language", "status", "time_ms", "code", "files", "created_at")[:HISTORY_SIZE]
    return JsonResponse({"items": [e.summary() for e in qs]})


@require_GET
def execution_detail(request, execution_id: int):
    execution = _own_executions(request).filter(pk=execution_id).first()
    if execution is None:
        raise Http404
    return JsonResponse(execution.to_dict())
