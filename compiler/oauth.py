"""Вход через GitHub и Google: OAuth2 authorization code flow на стандартной библиотеке.

1. /auth/<provider>/login/    — кладём в сессию случайный state и уводим пользователя к провайдеру.
2. /auth/<provider>/callback/ — сверяем state (защита от CSRF), меняем code на токен, читаем профиль,
                                находим или создаём пользователя и логиним.

Ключи приложений — в settings.OAUTH_PROVIDERS (из .env); без них провайдер выключен и кнопки не показываются.
"""
from __future__ import annotations

import json
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404, HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme

from .accounts import USERNAME_RE, login_with_history
from .models import SocialAccount

PROVIDERS = {
    "github": {
        "title": "GitHub",
        "authorize": "https://github.com/login/oauth/authorize",
        "token": "https://github.com/login/oauth/access_token",
        "scope": "read:user user:email",
    },
    "google": {
        "title": "Google",
        "authorize": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "scope": "openid email profile",
    },
}


class OAuthError(Exception):
    pass


def enabled_providers() -> list[dict]:
    return [
        {"id": name, "title": PROVIDERS[name]["title"]}
        for name, cfg in settings.OAUTH_PROVIDERS.items()
        if name in PROVIDERS and cfg.get("client_id") and cfg.get("client_secret")
    ]


def _config(provider: str) -> dict:
    if provider not in {p["id"] for p in enabled_providers()}:
        raise Http404
    return settings.OAUTH_PROVIDERS[provider]


def _redirect_uri(request, provider: str) -> str:
    return request.build_absolute_uri(f"/auth/{provider}/callback/")


def http_json(url: str, data: dict | None = None, token: str | None = None) -> dict | list:
    """GET (или POST формы, если есть data) с JSON-ответом. Вынесено отдельно — тесты подменяют сеть здесь."""
    headers = {"Accept": "application/json", "User-Agent": "online-compiler"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    request = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, ValueError) as exc:
        raise OAuthError(f"провайдер не ответил: {exc}") from exc


def fetch_profile(provider: str, code: str, redirect_uri: str) -> dict:
    """Меняет code на токен и возвращает {uid, login, email, email_verified}."""
    cfg = settings.OAUTH_PROVIDERS[provider]
    form = {"client_id": cfg["client_id"], "client_secret": cfg["client_secret"], "code": code,
            "redirect_uri": redirect_uri}
    if provider == "google":
        form["grant_type"] = "authorization_code"
    token = http_json(PROVIDERS[provider]["token"], form).get("access_token")
    if not token:
        raise OAuthError("провайдер не выдал токен")

    if provider == "github":
        user = http_json("https://api.github.com/user", token=token)
        emails = http_json("https://api.github.com/user/emails", token=token)
        primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
        return {"uid": str(user["id"]), "login": user.get("login", ""),
                "email": primary["email"] if primary else "", "email_verified": primary is not None}

    info = http_json("https://openidconnect.googleapis.com/v1/userinfo", token=token)
    return {"uid": str(info["sub"]), "login": info.get("email", ""), "email": info.get("email", ""),
            "email_verified": bool(info.get("email_verified"))}


def _free_username(base: str) -> str:
    User = get_user_model()
    base = re.sub(r"[^\w.-]", "", base)[:26] or "user"
    if len(base) < 3:
        base = f"{base}_user"
    candidate, n = base, 1
    while not USERNAME_RE.match(candidate) or User.objects.filter(username__iexact=candidate).exists():
        n += 1
        candidate = f"{base[:26]}{n}"
    return candidate


def user_for_profile(request, provider: str, profile: dict):
    """Уже привязанный аккаунт -> его пользователь; вошёл — привязываем к нему; подтверждённая почта
    совпала с одним пользователем — к нему; иначе создаём нового (без пароля, его можно задать сбросом)."""
    User = get_user_model()
    linked = SocialAccount.objects.select_related("user").filter(provider=provider, uid=profile["uid"]).first()
    if linked:
        return linked.user
    user = request.user if request.user.is_authenticated else None
    if user is None and profile["email_verified"] and profile["email"]:
        same_email = list(User.objects.filter(email__iexact=profile["email"])[:2])
        user = same_email[0] if len(same_email) == 1 else None
    if user is None:
        login = profile["login"].split("@")[0] if provider == "google" else profile["login"]
        email = profile["email"] if profile["email_verified"] and not User.objects.filter(
            email__iexact=profile["email"]).exists() else ""
        user = User(username=_free_username(login), email=email)
        user.set_unusable_password()
        user.save()
    SocialAccount.objects.create(user=user, provider=provider, uid=profile["uid"], login=profile["login"])
    return user


def _safe_next(request, url: str | None) -> str:
    if url and url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()}, require_https=False):
        return url
    return "/"


def start(request, provider: str):
    cfg = _config(provider)
    state = secrets.token_urlsafe(24)
    request.session[f"oauth_state_{provider}"] = state
    request.session["oauth_next"] = _safe_next(request, request.GET.get("next"))
    params = {"client_id": cfg["client_id"], "redirect_uri": _redirect_uri(request, provider),
              "scope": PROVIDERS[provider]["scope"], "state": state}
    if provider == "google":
        params.update(response_type="code", prompt="select_account")
    return HttpResponseRedirect(f"{PROVIDERS[provider]['authorize']}?{urllib.parse.urlencode(params)}")


def callback(request, provider: str):
    _config(provider)
    expected_state = request.session.pop(f"oauth_state_{provider}", None)
    next_url = request.session.pop("oauth_next", "/")
    fail = lambda reason: HttpResponseRedirect("/?auth_error=" + urllib.parse.quote(reason))  # noqa: E731
    if not expected_state or not secrets.compare_digest(expected_state, request.GET.get("state", "")):
        return fail("Вход не удался: устаревшая или поддельная ссылка, попробуй ещё раз")
    if "code" not in request.GET:
        return fail("Вход отменён")
    try:
        profile = fetch_profile(provider, request.GET["code"], _redirect_uri(request, provider))
    except (OAuthError, KeyError, TypeError) as exc:
        return fail(f"Не удалось войти через {PROVIDERS[provider]['title']}: {exc}")
    user = user_for_profile(request, provider, profile)
    login_with_history(request, user)
    return HttpResponseRedirect(_safe_next(request, next_url))
