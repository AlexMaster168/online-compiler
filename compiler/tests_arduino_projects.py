import json

from django.contrib.auth import get_user_model
from django.test import TestCase


class ArduinoProjectTests(TestCase):
    def save_project(self, **data):
        return self.client.post('/api/arduino/save/', json.dumps({'code': 'void setup(){} void loop(){}', **data}),
                                content_type='application/json')

    def test_anonymous_share_and_redirect(self):
        response = self.save_project(title='Blink')
        self.assertEqual(response.status_code, 201)
        project = response.json()
        self.assertContains(self.client.get(project['url']), 'Arduino Uno')
        self.assertRedirects(self.client.get('/s/' + project['id'] + '/'), project['url'])
        self.assertEqual(self.save_project(id=project['id']).status_code, 403)

    def test_owner_update_and_private_access(self):
        user = get_user_model().objects.create_user(username='uno', password='something-long')
        self.client.force_login(user)
        project = self.save_project(title='One').json()
        response = self.save_project(id=project['id'], title='Two')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Two')
        self.client.patch('/api/snippets/' + project['id'] + '/', json.dumps({'visibility': 'private'}),
                          content_type='application/json')
        self.client.logout()
        self.assertEqual(self.client.get(project['url']).status_code, 404)

    def test_circuit_saved_with_project(self):
        led = {'id': 'led1', 'type': 'led', 'x': 10, 'y': 20, 'pins': {'A': 'D13'},
               'props': {'color': 'red'}, 'state': {}}
        diagram = {'version': 1, 'board': 'uno', 'parts': [led]}
        project = self.save_project(title='Схема', diagram=json.dumps(diagram)).json()
        self.assertEqual(json.loads(project['files'][0]['content']), diagram)
        page = self.client.get(project['url'])
        self.assertContains(page, 'diagram.json')  # схема приходит на страницу вместе со скетчем
        self.assertContains(page, 'compiler/arduino.js')

    def test_broken_circuit_rejected(self):
        for diagram in ('{not json', '[1, 2]', '{"parts": "led"}'):
            response = self.save_project(diagram=diagram)
            self.assertEqual(response.status_code, 400, diagram)
        self.assertEqual(self.save_project(diagram='x' * (64 * 1024 + 1)).status_code, 400)


class Esp32BridgeTests(TestCase):
    """Мост к схеме ESP32 попадает в каждый проект и перехватывает ножки линкером."""

    def test_bridge_files_and_wraps(self):
        from compiler.engine import get_language
        lang = get_language('esp32')
        files = dict(lang.extra_files)
        self.assertIn('main/oc_hw.c', files)
        self.assertIn('oc_hw.h', lang.template)
        component = files['main/CMakeLists.txt']
        for symbol in ('gpio_set_level', 'gpio_get_level', 'ledc_update_duty', 'adc_oneshot_read'):
            self.assertIn(f'--wrap={symbol}', component)
            self.assertIn(f'__wrap_{symbol}', files['main/oc_hw.c'])
        self.assertIn('/opt/oc/esp32-cache/build', lang.docker.compile)  # сборка с кешем из образа
