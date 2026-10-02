@echo off
rem Быстрый запуск Online Compiler: start.bat [порт]
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"
title Online Compiler

set "PORT=%~1"
if "%PORT%"=="" set "PORT=8000"
set "PY=.venv\Scripts\python.exe"

rem --- 1. Виртуальное окружение ---
if not exist "%PY%" (
    echo [*] Создаю виртуальное окружение .venv ...
    python -m venv .venv || goto :fail
)

rem --- 2. Зависимости: ставим только если requirements.txt поменялся ---
fc /b requirements.txt .venv\requirements.installed >nul 2>&1
if errorlevel 1 (
    echo [*] Ставлю зависимости ...
    "%PY%" -m pip install -q --disable-pip-version-check -r requirements.txt || goto :fail
    copy /y requirements.txt .venv\requirements.installed >nul
)

rem --- 3. Настройки ---
if not exist ".env" (
    copy .env.example .env >nul
    echo [!] Создан .env из .env.example — впиши DB_PASSWORD и перезапусти.
    notepad .env
    goto :end
)

rem --- 4. Docker: если демон спит — будим (движок подхватит его сам, когда поднимется) ---
docker info >nul 2>&1
if errorlevel 1 (
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        echo [*] Docker не запущен — стартую Docker Desktop в фоне. Пока он грузится, код идёт через локальные компиляторы.
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    ) else (
        echo [!] Docker не найден — языки будут работать только через локальные компиляторы.
    )
) else (
    echo [+] Docker работает
)

rem --- 4b. Redis (кеш, rate limit, сессии): если REDIS_URL локальный — поднимаем контейнер oc-redis ---
set "OC_LOCAL_REDIS="
findstr /b /c:"REDIS_URL=redis://127.0.0.1" .env >nul 2>&1 && set "OC_LOCAL_REDIS=1"
findstr /b /c:"REDIS_URL=redis://localhost" .env >nul 2>&1 && set "OC_LOCAL_REDIS=1"
if defined OC_LOCAL_REDIS (
    docker info >nul 2>&1
    if errorlevel 1 (
        echo [!] REDIS_URL задан, но Docker ещё не запущен — пока без кеша, сайт работает и так.
    ) else (
        docker start oc-redis >nul 2>&1 || docker run -d --name oc-redis --restart unless-stopped -p 127.0.0.1:6380:6379 redis:7-alpine >nul 2>&1
        echo [+] Redis: oc-redis на 127.0.0.1:6380
    )
)

rem --- 5. База ---
echo [*] Применяю миграции ...
"%PY%" manage.py migrate --noinput -v 0 || goto :fail

rem --- 6. Открыть браузер через пару секунд и запустить сервер ---
echo.
echo  ============================================
echo    Online Compiler: http://127.0.0.1:%PORT%
echo    Остановить: Ctrl+C
echo  ============================================
echo.
if not defined OC_NO_BROWSER start "" /b cmd /c "timeout /t 2 /nobreak >nul & start "" http://127.0.0.1:%PORT%/"
"%PY%" manage.py runserver 127.0.0.1:%PORT%
goto :end

:fail
echo.
echo [X] Что-то пошло не так — смотри ошибку выше.
pause
exit /b 1

:end
endlocal
