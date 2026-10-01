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
