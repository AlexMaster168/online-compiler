"""Аккаунты и проекты: регистрация, вход, сброс пароля по почте, настройки аккаунта, профиль,
сохранение проекта на месте, видимость и форки.

Всё — JSON API для одностраничного интерфейса (плюс страница профиля); сессия и CSRF — стандартные джанговские.
Вход через GitHub / Google — в oauth.py.
"""
from __future__ import annotations

import re
from functools import wraps

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from . import cache as oc_cache
from .models import Execution, Snippet, Visibility
from .payload import BadRequest, api, args_field, files_field, json_body, language_field, no_nul, str_field

USERNAME_RE = re.compile(r"^[\w.-]{3,30}$")
MAX_PROJECTS_LISTED = 200
SNIPPETS = Snippet.objects.select_related("owner", "forked_from__owner")


def user_dict(user) -> dict | None:
    if not user.is_authenticated:
        return None
    return {
        "username": user.get_username(),
        "email": user.email,
        "has_password": user.has_usable_password(),  # без пароля — вошёл через GitHub / Google
        "providers": sorted(user.social_accounts.values_list("provider", flat=True)),
    }


def login_required_json(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Сначала войди в аккаунт"}, status=401)
        return view(request, *args, **kwargs)
    return wrapper


def _auth_throttled(request) -> bool:
    """Защита от перебора: попытки входа, регистрации и сброса пароля с одного IP в минуту."""
    return oc_cache.rate_hit(f"rl:auth:{request.META.get('REMOTE_ADDR')}",
                             getattr(settings, "AUTH_RATE_LIMIT_PER_MINUTE", 20))


def _throttled_response():
    return JsonResponse({"error": "Слишком много попыток, подожди минуту"}, status=429)


def login_with_history(request, user) -> None:
    """Вход с переносом анонимной истории: login() меняет ключ сессии, и без этого история бы пропала."""
    old_key = request.session.session_key
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    if old_key:
        Execution.objects.filter(session_key=old_key, user__isnull=True).update(user=user)


def _clean_email(value: str, user=None) -> str:
    """Пустая строка — почты нет; иначе проверяем формат и что она не занята другим аккаунтом."""
    email = value.strip()
    if not email:
        return ""
    try:
        validate_email(email)
    except ValidationError:
        raise BadRequest("Это не похоже на адрес почты")
    taken = get_user_model().objects.filter(email__iexact=email)
    if user is not None:
        taken = taken.exclude(pk=user.pk)
    if taken.exists():
        raise BadRequest("Эта почта уже привязана к другому аккаунту")
    return email


def _check_password(password: str, user) -> None:
    try:
        validate_password(password, user)
    except ValidationError as exc:
        raise BadRequest(" ".join(exc.messages))


# ---------- вход и регистрация ----------

@require_http_methods(["GET", "PATCH"])
@api
def me(request):
    """GET — текущий пользователь; PATCH {email, password} — сменить почту (с паролем, если он задан)."""
    if request.method == "GET":
        return JsonResponse({"user": user_dict(request.user)})
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Сначала войди в аккаунт"}, status=401)
    data = json_body(request)
    user = request.user
    # Почту меняем только зная пароль: иначе украденная сессия = украденный аккаунт через сброс пароля
    if user.has_usable_password() and not user.check_password(str_field(data, "password")):
        raise BadRequest("Неверный текущий пароль")
    user.email = _clean_email(str_field(data, "email"), user)
    user.save(update_fields=["email"])
    return JsonResponse({"user": user_dict(user)})


@require_POST
@api
def register(request):
    if _auth_throttled(request):
        return _throttled_response()
    data = json_body(request)
    username, password = str_field(data, "username").strip(), str_field(data, "password")
    if not USERNAME_RE.match(username):
        raise BadRequest("Логин: 3–30 символов — буквы, цифры, точка, дефис, подчёркивание")
    User = get_user_model()
    if User.objects.filter(username__iexact=username).exists():
        raise BadRequest("Такой логин уже занят")
    email = _clean_email(str_field(data, "email"))
    _check_password(password, User(username=username, email=email))
    user = User.objects.create_user(username=username, password=password, email=email)
    login_with_history(request, user)
    return JsonResponse({"user": user_dict(user)}, status=201)


@require_POST
@api
def login_view(request):
    if _auth_throttled(request):
        return _throttled_response()
    data = json_body(request)
    username, password = str_field(data, "username").strip(), str_field(data, "password")
    # Логин без учёта регистра: «Лёха» и «лёха» — один человек
    match = get_user_model().objects.filter(username__iexact=username).first()
    user = authenticate(request, username=match.get_username(), password=password) if match else None
    if user is None:
        return JsonResponse({"error": "Неверный логин или пароль"}, status=400)
    login_with_history(request, user)
    return JsonResponse({"user": user_dict(user)})


@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({"user": None})


@require_POST
@api
@login_required_json
def change_password(request):
    """Смена пароля. Аккаунту из GitHub / Google без пароля — задать первый, старый не нужен."""
    data = json_body(request)
    user = request.user
    if user.has_usable_password() and not user.check_password(str_field(data, "old_password")):
        raise BadRequest("Неверный текущий пароль")
    new_password = str_field(data, "new_password")
    _check_password(new_password, user)
    user.set_password(new_password)
    user.save(update_fields=["password"])
    update_session_auth_hash(request, user)  # иначе смена пароля разлогинит и эту сессию
    return JsonResponse({"user": user_dict(user)})


# ---------- сброс пароля по почте ----------

RESET_SUBJECT = "Сброс пароля — Online Compiler"
RESET_BODY = """Привет, {username}!

Кто-то (надеемся, ты) попросил сбросить пароль на Online Compiler. Новый пароль задаётся по ссылке:

{link}

Ссылка одноразовая и действует {hours} ч. Если это был не ты — просто не обращай внимания на письмо.
"""


@require_POST
@api
def password_reset(request):
    """Письмо со ссылкой сброса. Ответ одинаковый, есть такая почта или нет, — чтобы нельзя было перебирать адреса."""
    if _auth_throttled(request):
        return _throttled_response()
    email = str_field(json_body(request), "email").strip()
    if email:
        for user in get_user_model().objects.filter(email__iexact=email, is_active=True):
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            send_mail(
                RESET_SUBJECT,
                RESET_BODY.format(username=user.get_username(),
                                  link=request.build_absolute_uri(f"/reset/{uid}/{token}/"),
                                  hours=settings.PASSWORD_RESET_TIMEOUT // 3600),
                None, [user.email],
            )
    return JsonResponse({"ok": True})


def _user_from_uid(uid: str):
    try:
        pk = force_str(urlsafe_base64_decode(uid))
        return get_user_model().objects.get(pk=pk, is_active=True)
    except (ValueError, TypeError, OverflowError, get_user_model().DoesNotExist):
        return None


@require_POST
@api
def password_reset_confirm(request):
    if _auth_throttled(request):
        return _throttled_response()
    data = json_body(request)
    user = _user_from_uid(str_field(data, "uid"))
    if user is None or not default_token_generator.check_token(user, str_field(data, "token")):
        raise BadRequest("Ссылка устарела или уже использована — запроси сброс ещё раз")
    password = str_field(data, "password")
    _check_password(password, user)
    user.set_password(password)  # меняется хеш пароля — токен из письма перестаёт работать
    user.save(update_fields=["password"])
    login_with_history(request, user)
    return JsonResponse({"user": user_dict(user)})


# ---------- профиль ----------

def _public_projects(user) -> list[dict]:
    """Публичные проекты автора; кешируются, сбрасываются сигналом при сохранении/удалении/форке."""
    def load():
        qs = (Snippet.objects.filter(owner=user, visibility=Visibility.PUBLIC)
              .annotate(fork_count=Count("forks")).order_by("-updated_at"))
        return [{**s.summary(), "forks": s.fork_count} for s in qs[:MAX_PROJECTS_LISTED]]
    return oc_cache.cached(oc_cache.profile_key(user.pk), oc_cache.PROFILE_TTL, load)


def _profile_user(username: str):
    user = get_user_model().objects.filter(username__iexact=username, is_active=True).first()
    if user is None:
        raise Http404
    return user


@require_GET
def profile_api(request, username: str):
    user = _profile_user(username)
    return JsonResponse({"username": user.get_username(), "joined": user.date_joined.isoformat(),
                         "projects": _public_projects(user)})


@require_GET
def profile_page(request, username: str):
    user = _profile_user(username)
    from .engine.languages import BY_SLUG  # имена языков для карточек
    projects = [{**p, "language_name": BY_SLUG[p["language"]].name if p["language"] in BY_SLUG else p["language"]}
                for p in _public_projects(user)]
    return render(request, "compiler/profile.html", {
        "profile": user, "projects": projects,
        "is_me": request.user.is_authenticated and request.user.pk == user.pk,
    })


# ---------- проекты ----------

def snippet_view(request, snippet_id: str) -> dict:
    """Проект для чтения по ссылке — из кеша. В кеше лежит представление без привязки к пользователю,
    а «мой ли это проект» и доступ к приватному проверяются здесь, на каждый запрос."""
    def load():
        snippet = SNIPPETS.filter(pk=snippet_id).first()
        if snippet is None:
            return None
        return {"data": snippet.to_dict(None), "owner_id": snippet.owner_id, "visibility": snippet.visibility}

    entry = oc_cache.cached(oc_cache.snippet_key(snippet_id), oc_cache.SNIPPET_TTL, load)
    if entry is None:
        raise Http404
    user = request.user
    is_owner = bool(entry["owner_id"]) and user.is_authenticated and user.pk == entry["owner_id"]
    if entry["visibility"] == Visibility.PRIVATE and not is_owner:
        raise Http404
    return {**entry["data"], "is_owner": is_owner}


def visible_snippet_or_404(request, snippet_id: str) -> Snippet:
    """Проект по ссылке; приватный — только владельцу (остальным он «не существует»)."""
    snippet = get_object_or_404(SNIPPETS, pk=snippet_id)
    if not snippet.visible_to(request.user):
        raise Http404
    return snippet


def update_snippet(snippet: Snippet, data: dict) -> None:
    """Сохранение на месте. Код и файлы приходят вместе (снимок проекта), название и видимость — отдельно."""
    cfg = settings.EXECUTOR
    fields = []
    if "code" in data:
        slug = language_field(data) if "language" in data else snippet.language
        if slug == "scratch":
            raise BadRequest("Проекты Scratch сохраняются через редактор Scratch")
        code = str_field(data, "code", required=True, max_bytes=cfg["MAX_CODE_BYTES"])
        snippet.language, snippet.code = slug, no_nul(code)
        snippet.files = [] if slug == "arduino" else files_field(data, slug, code)
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
    if "visibility" in data:
        visibility = str_field(data, "visibility")
        if visibility not in Visibility.values:
            raise BadRequest("Видимость: public, unlisted или private")
        snippet.visibility = visibility
        fields.append("visibility")
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
    source = visible_snippet_or_404(request, snippet_id)
    copy = Snippet.objects.create(
        language=source.language, code=source.code, files=source.files, stdin=source.stdin, args=source.args,
        title=source.title, owner=request.user, forked_from=source,
    )
    return JsonResponse(SNIPPETS.get(pk=copy.pk).to_dict(request.user), status=201)


@require_http_methods(["GET", "PATCH", "DELETE"])
@api
def snippet_detail(request, snippet_id: str):
    """GET — любой по ссылке (приватный — только владелец); PATCH и DELETE — только владелец."""
    if request.method == "GET":
        return JsonResponse(snippet_view(request, snippet_id))
    snippet = visible_snippet_or_404(request, snippet_id)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Сначала войди в аккаунт"}, status=401)
    if snippet.owner_id != request.user.pk:
        return JsonResponse({"error": "Это чужой проект — сделай форк"}, status=403)
    if request.method == "DELETE":
        snippet.delete()
        return JsonResponse({"deleted": snippet_id})
    update_snippet(snippet, json_body(request))
    return JsonResponse(snippet.to_dict(request.user))
