"""Аккаунты и «Мои проекты»: регистрация, вход, сохранение проекта на месте, форки.

Всё — JSON API для одностраничного интерфейса; сессия и CSRF — стандартные джанговские.
"""
from __future__ import annotations

import re
from functools import wraps

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import Execution, Snippet
from .payload import BadRequest, api, args_field, files_field, json_body, language_field, no_nul, str_field

USERNAME_RE = re.compile(r"^[\w.-]{3,30}$")
MAX_PROJECTS_LISTED = 200
SNIPPETS = Snippet.objects.select_related("owner", "forked_from__owner")


def user_dict(user) -> dict | None:
    return {"username": user.get_username()} if user.is_authenticated else None


def login_required_json(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Сначала войди в аккаунт"}, status=401)
        return view(request, *args, **kwargs)
    return wrapper


def _auth_throttled(request) -> bool:
    """Защита от перебора паролей: попытки входа/регистрации с одного IP в минуту."""
    limit = getattr(settings, "AUTH_RATE_LIMIT_PER_MINUTE", 20)
    if limit <= 0:
        return False
    key = f"rl:auth:{request.META.get('REMOTE_ADDR')}"
    cache.add(key, 0, timeout=60)
    try:
        return cache.incr(key) > limit
    except ValueError:
        cache.set(key, 1, timeout=60)
        return False


def _login(request, user) -> None:
    """Вход с переносом анонимной истории: login() меняет ключ сессии, и без этого история бы пропала."""
    old_key = request.session.session_key
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    if old_key:
        Execution.objects.filter(session_key=old_key, user__isnull=True).update(user=user)


def _credentials(request) -> tuple[str, str]:
    data = json_body(request)
    return str_field(data, "username").strip(), str_field(data, "password")


# ---------- аккаунт ----------

@require_GET
def me(request):
    return JsonResponse({"user": user_dict(request.user)})


@require_POST
@api
def register(request):
    if _auth_throttled(request):
        return JsonResponse({"error": "Слишком много попыток, подожди минуту"}, status=429)
    username, password = _credentials(request)
    if not USERNAME_RE.match(username):
        raise BadRequest("Логин: 3–30 символов — буквы, цифры, точка, дефис, подчёркивание")
    User = get_user_model()
    if User.objects.filter(username__iexact=username).exists():
        raise BadRequest("Такой логин уже занят")
    try:
        validate_password(password, User(username=username))
    except ValidationError as exc:
        raise BadRequest(" ".join(exc.messages))
    user = User.objects.create_user(username=username, password=password)
    _login(request, user)
    return JsonResponse({"user": user_dict(user)}, status=201)


@require_POST
@api
def login_view(request):
    if _auth_throttled(request):
        return JsonResponse({"error": "Слишком много попыток, подожди минуту"}, status=429)
    username, password = _credentials(request)
    # Логин без учёта регистра: «Лёха» и «лёха» — один человек
    match = get_user_model().objects.filter(username__iexact=username).first()
    user = authenticate(request, username=match.get_username(), password=password) if match else None
    if user is None:
        return JsonResponse({"error": "Неверный логин или пароль"}, status=400)
    _login(request, user)
    return JsonResponse({"user": user_dict(user)})


@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({"user": None})


# ---------- проекты ----------

def update_snippet(snippet: Snippet, data: dict) -> None:
    """Сохранение на месте. Код и файлы приходят вместе (снимок проекта), название — отдельно (переименование)."""
    cfg = settings.EXECUTOR
    fields = []
    if "code" in data:
        slug = language_field(data) if "language" in data else snippet.language
        code = str_field(data, "code", required=True, max_bytes=cfg["MAX_CODE_BYTES"])
        snippet.language, snippet.code = slug, no_nul(code)
        snippet.files = files_field(data, slug, code)
        fields += ["language", "code", "files"]
    if "stdin" in data:
        snippet.stdin = no_nul(str_field(data, "stdin", max_bytes=cfg["MAX_STDIN_BYTES"]))
        fields.append("stdin")
    if "args" in data:
        snippet.args = args_field(data)[0]
        fields.append("args")
    if "title" in data:
        snippet.title = str_field(data, "title").strip()[:200]
        fields.append("title")
    if not fields:
        raise BadRequest("Нечего сохранять")
    snippet.save(update_fields=[*fields, "updated_at"])


def my_projects(user, query: str = "") -> list[dict]:
    qs = Snippet.objects.filter(owner=user).annotate(fork_count=Count("forks")).order_by("-updated_at")
    query = query.strip()
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(id=query) | Q(language__iexact=query))
    return [{**s.summary(), "forks": s.fork_count} for s in qs[:MAX_PROJECTS_LISTED]]


@require_GET
@login_required_json
def projects(request):
    return JsonResponse({"items": my_projects(request.user, request.GET.get("q", ""))})


@require_POST
@api
@login_required_json
def fork(request, snippet_id: str):
    source = get_object_or_404(Snippet, pk=snippet_id)
    copy = Snippet.objects.create(
        language=source.language, code=source.code, files=source.files, stdin=source.stdin, args=source.args,
        title=source.title, owner=request.user, forked_from=source,
    )
    return JsonResponse(SNIPPETS.get(pk=copy.pk).to_dict(request.user), status=201)


@require_http_methods(["GET", "PATCH", "DELETE"])
@api
def snippet_detail(request, snippet_id: str):
    """GET — любой по ссылке; PATCH (сохранить / переименовать) и DELETE — только владелец."""
    snippet = get_object_or_404(SNIPPETS, pk=snippet_id)
    if request.method == "GET":
        return JsonResponse(snippet.to_dict(request.user))
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Сначала войди в аккаунт"}, status=401)
    if snippet.owner_id != request.user.pk:
        return JsonResponse({"error": "Это чужой проект — сделай форк"}, status=403)
    if request.method == "DELETE":
        snippet.delete()
        return JsonResponse({"deleted": snippet_id})
    update_snippet(snippet, json_body(request))
    return JsonResponse(snippet.to_dict(request.user))
