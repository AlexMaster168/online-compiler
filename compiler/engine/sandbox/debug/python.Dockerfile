# Python + debugpy (DAP-сервер для Python)
FROM python:3.13-alpine
RUN pip install --no-cache-dir "debugpy>=1.8,<2"
