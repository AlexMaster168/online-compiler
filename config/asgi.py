"""ASGI: HTTP — обычный Django, WebSocket — интерактивная консоль."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402 — после инициализации Django
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402
from channels.auth import AuthMiddlewareStack  # noqa: E402
from django.urls import path  # noqa: E402

from compiler.consumers import RunConsumer  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # Проверка Origin: чужой сайт не сможет открыть консоль с куками пользователя
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter([path("ws/run/", RunConsumer.as_asgi())]))
    ),
})
