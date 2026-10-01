import json
import base64
import io
import zipfile
from unittest.mock import patch

from django.test import SimpleTestCase


class ArduinoTests(SimpleTestCase):
    def test_page(self):
        response = self.client.get('/arduino/')
        self.assertContains(response, 'ATmega328P')

    def test_input_validation(self):
        for body in ({}, {'code': 42}, {'code': 'x' * (128 * 1024 + 1)}):
            response = self.client.post('/api/arduino/compile/', json.dumps(body), content_type='application/json')
            self.assertEqual(response.status_code, 400)

    @patch('compiler.microcontrollers.docker.daemon_available', return_value=False)
    def test_unavailable(self, _probe):
        response = self.client.post('/api/arduino/compile/', '{"code":"void setup(){}"}',
                                    content_type='application/json')
        self.assertEqual(response.status_code, 503)

    def test_csrf_required(self):
        from django.test import Client
        response = Client(enforce_csrf_checks=True).post(
            '/api/arduino/compile/', '{"code":"void setup(){}"}', content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)


class SpecialProjectTests(SimpleTestCase):
    def test_scratch_download_is_sb3(self):
        from types import SimpleNamespace
        from django.test import RequestFactory
        from .views import snippet_zip
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w') as bundle:
            bundle.writestr('project.json', '{}')
        snippet = SimpleNamespace(language='scratch', code=base64.b64encode(archive.getvalue()).decode())
        with patch('compiler.views.visible_snippet_or_404', return_value=snippet):
            response = snippet_zip(RequestFactory().get('/'), 'example')
        with zipfile.ZipFile(io.BytesIO(response.content)) as bundle:
            self.assertEqual(bundle.read('project.json'), b'{}')
        self.assertIn('project.sb3', response['Content-Disposition'])

    def test_generic_code_update_rejects_scratch(self):
        from .accounts import update_snippet
        from .models import Snippet
        from .payload import BadRequest
        with self.assertRaises(BadRequest):
            update_snippet(Snippet(language='scratch'), {'code': 'plain text'})
