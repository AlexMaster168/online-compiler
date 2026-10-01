"""Scratch 3: страница редактора и хранение проектов.

Проект Scratch — это файл .sb3 (zip с project.json, костюмами и звуками). Храним его в обычном Snippet
с языком "scratch" (код — .sb3 в base64), поэтому «Мои проекты», ссылки, форки и видимость работают как у кода.
Сам редактор — собранный из исходников scratch-gui (manage.py build_scratch) в static/scratch/.
"""
from __future__ import annotations

import base64
import binascii

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST

from .accounts import SNIPPETS, update_snippet, user_dict, visible_snippet_or_404
from .models import Snippet
from .payload import BadRequest, api, json_body, str_field

SCRATCH = "scratch"
MAX_SB3_BYTES = getattr(settings, "SCRATCH_MAX_BYTES", 10 * 1024 * 1024)


def editor_available() -> bool:
    from django.contrib.staticfiles import finders
    return finders.find("scratch/index.html") is not None


def sb3_field(data: dict) -> str:
    """base64 .sb3 -> проверенная строка base64 (zip, не больше лимита)."""
    encoded = str_field(data, "sb3", required=True)
    if len(encoded) > MAX_SB3_BYTES * 4 // 3 + 4:
        raise BadRequest(f"Проект больше {MAX_SB3_BYTES // (1024 * 1024)} МБ")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise BadRequest("sb3 должен быть в base64")
    if not raw.startswith(b"PK"):
        raise BadRequest("Это не файл .sb3 (ожидается zip-архив)")
    return encoded


def scratch_dict(snippet: Snippet, user) -> dict:
    data = snippet.to_dict(user)
    data["sb3"] = data.pop("code")
    for key in ("files", "stdin", "args"):
        data.pop(key, None)
    return data


@ensure_csrf_cookie
def page(request, snippet_id: str | None = None):
    project = None
    if snippet_id:
        snippet = visible_snippet_or_404(request, snippet_id)
        if snippet.language != SCRATCH:
            return redirect(f"/s/{snippet.pk}/")
        Snippet.objects.filter(pk=snippet.pk).update(views=snippet.views + 1)
        project = {k: v for k, v in scratch_dict(snippet, request.user).items() if k != "sb3"}
    return render(request, "compiler/scratch.html", {
        "project": project,
        "user": user_dict(request.user),
        # locale=ru: иначе scratch-gui берёт язык браузера (у кого-то окажется украинский или английский)
        "editor_url": static("scratch/index.html") + "?locale=ru" if editor_available() else "",
    })


@require_POST
@api
def create(request):
    data = json_body(request)
    snippet = Snippet.objects.create(
        language=SCRATCH, code=sb3_field(data), title=str_field(data, "title").strip()[:200],
        session_key=request.session.session_key or "",
        owner=request.user if request.user.is_authenticated else None,
    )
    return JsonResponse(scratch_dict(SNIPPETS.get(pk=snippet.pk), request.user), status=201)


@require_http_methods(["GET", "PATCH"])
@api
def detail(request, snippet_id: str):
    snippet = visible_snippet_or_404(request, snippet_id)
    if snippet.language != SCRATCH:
        raise BadRequest("Это не проект Scratch")
    if request.method == "GET":
        return JsonResponse(scratch_dict(snippet, request.user))
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Сначала войди в аккаунт"}, status=401)
    if snippet.owner_id != request.user.pk:
        return JsonResponse({"error": "Это чужой проект — сделай форк"}, status=403)
    data = json_body(request)
    if "sb3" in data:
        snippet.code = sb3_field(data)
        snippet.save(update_fields=["code", "updated_at"])
    rest = {k: v for k, v in data.items() if k in ("title", "visibility")}
    if rest:
        update_snippet(snippet, rest)
    return JsonResponse(scratch_dict(snippet, request.user))
