"""HTTP bridge to QEMU loopback; the container has no external network."""
import base64
import json
import secrets
import subprocess
import threading
import weakref

from django.http import HttpResponse
from django.views.decorators.http import require_GET

from .engine import docker

_sessions = weakref.WeakValueDictionary()
_lock = threading.Lock()
_bridge = '''import http.client,json,base64,sys
c=http.client.HTTPConnection('127.0.0.1',8080,timeout=5)
c.request('GET',sys.argv[1],headers={'Host':'esp32.local','Connection':'close'})
r=c.getresponse(); body=r.read(1048577)
if len(body)>1048576: raise ValueError('Response too large')
print(json.dumps({'status':r.status,'type':r.getheader('Content-Type','text/html'),'body':base64.b64encode(body).decode()}))
'''


def register(session):
    token = secrets.token_urlsafe(32)
    with _lock:
        _sessions[token] = session
    return f'/esp32-preview/{token}/'


@require_GET
def preview(request, token, path=''):
    with _lock:
        session = _sessions.get(token)
    if session is None or session.done.is_set() or not session._container:
        return HttpResponse('Сессия ESP32 завершена', status=404)
    target = '/' + path
    query = request.META.get('QUERY_STRING', '')
    if query:
        target += '?' + query
    if len(target) > 2048 or any(ord(char) < 32 for char in target):
        return HttpResponse('Недопустимый URL', status=400)
    try:
        process = subprocess.run([docker._docker(session.cfg), 'exec', session._container,
                                  '/usr/local/bin/oc-python', '-c', _bridge, target],
                                 capture_output=True, timeout=8)
        data = json.loads(process.stdout)
        response = HttpResponse(base64.b64decode(data['body']), status=data['status'],
                                content_type=data['type'])
    except (OSError, subprocess.SubprocessError, ValueError, KeyError):
        return HttpResponse('Веб-сервер ESP32 ещё не готов. Обнови страницу после получения IP в Serial.', status=502)
    response['Content-Security-Policy'] = (
        "sandbox allow-scripts allow-forms; default-src 'self' data: blob:; "
        "script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    )
    response['Cache-Control'] = 'no-store'
    response['Referrer-Policy'] = 'no-referrer'
    return response
