import io
import re
import zipfile

from django.conf import settings
from django.db.models import F
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from . import cache as oc_cache
from . import engine, library
from .accounts import SNIPPETS, snippet_view, user_dict, visible_snippet_or_404
from .oauth import enabled_providers
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
def index(request, snippet_id: str | None = None, uidb64: str | None = None, token: str | None = None):
    _session_key(request)  # сессия нужна до открытия WebSocket-консоли: по ней пишется история
    snippet = None
    if snippet_id:
        snippet = snippet_view(request, snippet_id)  # из кеша: ссылки на проекты — самые частые запросы
        if snippet["language"] in ("scratch", "arduino"):
            return redirect(f"/{snippet['language']}/{snippet_id}/")
        Snippet.objects.filter(pk=snippet_id).update(views=F("views") + 1)  # без сигнала: кеш не сбрасывается
    return render(request, "compiler/index.html", {
        "snippet": snippet,
        "limits": _limits(),
        "user": user_dict(request.user),
        # Фронтенд сам открывает нужный диалог: «новый пароль» по ссылке из письма, ошибка входа через OAuth
        "auth": {
            "providers": enabled_providers(),
            "reset": {"uid": uidb64, "token": token} if uidb64 else None,
            "error": request.GET.get("auth_error", "")[:300],
        },
    })


def snippet_raw(request, snippet_id: str):
    snippet = visible_snippet_or_404(request, snippet_id)
    return HttpResponse(snippet.code, content_type="text/plain; charset=utf-8")


def _zip_response(slug: str, code: str, files: list[dict], title: str = "") -> HttpResponse:
    """Проект одним архивом: главный файл + все дополнительные, с путями."""
    lang = engine.get_language(slug)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(lang.filename if lang else "sketch.ino", code)
        for item in files:
            zf.writestr(item["name"], item["content"])
    base = re.sub(r"[^\w.-]+", "-", title, flags=re.ASCII).strip("-.")[:60] or f"{slug}-project"
    response = HttpResponse(buf.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{base}.zip"'
    return response


def snippet_zip(request, snippet_id: str):
    snippet = visible_snippet_or_404(request, snippet_id)
    if snippet.language == "scratch":
        import base64
        response = HttpResponse(base64.b64decode(snippet.code), content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="project.sb3"'
        return response
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


@require_GET
def library_index(request):
    """Библиотека алгоритмов для языка: категории и задачи, для которых есть код."""
    slug = request.GET.get("language", "")
    if slug == "esp32":
        from .library import esp32
        return JsonResponse({"categories": list(esp32.CATEGORIES), "items": esp32.catalog()})
    if engine.get_language(slug) is None:
        return JsonResponse({"error": "Неизвестный язык"}, status=400)
    items = oc_cache.cached(f"library:{library.version()}:index:{slug}", oc_cache.LIBRARY_TTL,
                            lambda: library.catalog(slug))
    return JsonResponse({"categories": list(library.CATEGORIES), "items": items})


@require_GET
def library_item(request, slug: str, algorithm_id: str):
    if slug == "esp32":
        from .library import esp32
        item = esp32.get_project(algorithm_id)
        if item is None:
            raise Http404
        return JsonResponse(item)
    code = oc_cache.cached(f"library:{library.version()}:code:{slug}:{algorithm_id}", oc_cache.LIBRARY_TTL,
                           lambda: library.get_code(slug, algorithm_id))
    if code is None:
        raise Http404
    algorithm = library.BY_ID[algorithm_id]
    return JsonResponse({"id": algorithm.id, "title": algorithm.title, "category": algorithm.category,
                         "description": algorithm.description, "language": slug, "code": code})


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
    # Каталог на каждый запрос опрашивает Docker о наличии образов — кешируем ненадолго
    # В ключе — бэкенд исполнения: при смене docker/local каталог другой (и в тестах настройки подменяются)
    cfg = settings.EXECUTOR
    key = f"languages:catalog:{cfg['BACKEND']}:{cfg['DOCKER_BIN']}"
    catalog = oc_cache.cached(key, oc_cache.LANGUAGES_TTL, engine.language_catalog)
    return JsonResponse({"languages": catalog, "limits": _limits()})


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
