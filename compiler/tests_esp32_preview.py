import base64
import json
import threading
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from . import esp32_preview


class SessionStub:
    def __init__(self):
        self.done = threading.Event()
        self._container = 'oc-test'
        self.cfg = {}


class Esp32PreviewTests(SimpleTestCase):
    def test_unknown_and_expired_session(self):
        self.assertEqual(self.client.get('/esp32-preview/invalid/').status_code, 404)
        session = SessionStub()
        url = esp32_preview.register(session)
        session.done.set()
        self.assertEqual(self.client.get(url).status_code, 404)

    @patch('compiler.esp32_preview.subprocess.run')
    def test_bridge_has_fixed_destination_and_sandbox(self, run):
        run.return_value = SimpleNamespace(stdout=json.dumps({'body': base64.b64encode(b'<h1>ESP32</h1>').decode(),
                                                              'status': 200, 'type': 'text/html'}).encode())
        session = SessionStub()
        url = esp32_preview.register(session)
        response = self.client.get(url + 'hello?x=1')
        self.assertContains(response, '<h1>ESP32</h1>')
        self.assertIn('sandbox allow-scripts', response['Content-Security-Policy'])
        self.assertEqual(run.call_args.args[0][-1], '/hello?x=1')
        self.assertIn("HTTPConnection('127.0.0.1',8080", run.call_args.args[0][-2])

    @patch('compiler.esp32_preview.subprocess.run', side_effect=OSError)
    def test_not_ready(self, _run):
        session = SessionStub()
        self.assertEqual(self.client.get(esp32_preview.register(session)).status_code, 502)
