"""Настройки проекта online-compiler. Всё, что зависит от окружения, берётся из .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

INSTALLED_APPS = [
    "daphne",  # runserver начинает обслуживать ASGI/WebSocket
    "channels",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "compiler",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "online_compiler"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        # Под ASGI каждый запрос идёт в своём потоке: «постоянные» соединения (CONN_MAX_AGE) там утекают
        # до исчерпания max_connections. Поэтому — пул psycopg и CONN_MAX_AGE = 0
        "CONN_MAX_AGE": 0,
        "OPTIONS": {"pool": {"min_size": 1, "max_size": int(os.getenv("DB_POOL_SIZE", "10")), "timeout": 10}},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# --- Движок исполнения кода ---
EXECUTOR = {
    # auto — docker, если демон доступен, иначе локальные тулчейны; docker; local
    "BACKEND": os.getenv("EXECUTOR_BACKEND", "auto"),
    "COMPILE_TIMEOUT": float(os.getenv("EXECUTOR_COMPILE_TIMEOUT", "30")),
    "RUN_TIMEOUT": float(os.getenv("EXECUTOR_RUN_TIMEOUT", "10")),
    "MEMORY_MB": int(os.getenv("EXECUTOR_MEMORY_MB", "512")),
    "MAX_OUTPUT_BYTES": int(os.getenv("EXECUTOR_MAX_OUTPUT_BYTES", str(64 * 1024))),
    "MAX_CODE_BYTES": int(os.getenv("EXECUTOR_MAX_CODE_BYTES", str(256 * 1024))),
    "MAX_STDIN_BYTES": int(os.getenv("EXECUTOR_MAX_STDIN_BYTES", str(64 * 1024))),
    "MAX_CONCURRENT": int(os.getenv("EXECUTOR_MAX_CONCURRENT", "4")),
    "RATE_LIMIT_PER_MINUTE": int(os.getenv("EXECUTOR_RATE_LIMIT_PER_MINUTE", "30")),
    "DOCKER_BIN": os.getenv("DOCKER_BIN", "docker"),
    # Интерактивная консоль: RUN_TIMEOUT там — лимит CPU-времени, а это — сколько сессия может жить вообще
    "INTERACTIVE_TIMEOUT": float(os.getenv("EXECUTOR_INTERACTIVE_TIMEOUT", "300")),
    "INTERACTIVE_MAX_OUTPUT_BYTES": int(os.getenv("EXECUTOR_INTERACTIVE_MAX_OUTPUT_BYTES", str(1024 * 1024))),
    "MAX_INTERACTIVE_SESSIONS": int(os.getenv("EXECUTOR_MAX_INTERACTIVE_SESSIONS", "8")),
    # Отладка: сессия живёт дольше, а CPU-лимит щедрее — отладчик сам по себе ест процессор
    "DEBUG_TIMEOUT": float(os.getenv("EXECUTOR_DEBUG_TIMEOUT", "900")),
    "DEBUG_CPU_SECONDS": float(os.getenv("EXECUTOR_DEBUG_CPU_SECONDS", "60")),
}

# --- Почта (сброс пароля) ---
# Без EMAIL_HOST письма печатаются в консоль сервера — для разработки этого хватает
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend" if EMAIL_HOST
    else "django.core.mail.backends.console.EmailBackend"
)
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Online Compiler <noreply@localhost>")
PASSWORD_RESET_TIMEOUT = 60 * 60 * 3  # ссылка из письма живёт 3 часа

# --- Вход через GitHub / Google (OAuth2) ---
# Кнопки появляются, только если заданы client id и secret. Callback-адреса для настройки приложения:
#   GitHub: <сайт>/auth/github/callback/      Google: <сайт>/auth/google/callback/
OAUTH_PROVIDERS = {
    "github": {
        "client_id": os.getenv("GITHUB_CLIENT_ID", ""),
        "client_secret": os.getenv("GITHUB_CLIENT_SECRET", ""),
    },
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
    },
}
