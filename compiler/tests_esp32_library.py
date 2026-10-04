import json

from django.test import TestCase

from .library import esp32


class Esp32LibraryTests(TestCase):
    def test_catalog_and_project_payloads(self):
        index = self.client.get('/api/library/?language=esp32').json()
        self.assertEqual(len(index['items']), 15)
        self.assertEqual(len({p['id'] for p in index['items']}), 15)
        self.assertEqual(set(index['categories']), {p['category'] for p in index['items']})
        for item in index['items']:
            data = self.client.get(f"/api/library/esp32/{item['id']}/").json()
            self.assertIn('void app_main(', data['code'])
            diagram = json.loads(data['files'][0]['content'])
            ids = [p['id'] for p in diagram['parts']]
            self.assertEqual(len(ids), len(set(ids)), item['id'])
            for resistor in (p for p in diagram['parts'] if p['type'] == 'resistor'):
                self.assertIn(resistor['series']['part'], ids)
        self.assertEqual(self.client.get('/api/library/esp32/unknown/').status_code, 404)

    def test_original_demo_is_complete(self):
        item = esp32.get_project('demo_stand')
        parts = json.loads(item['files'][0]['content'])['parts']
        self.assertTrue({'led', 'button', 'servo', 'buzzer', 'neopixel', 'lcd_i2c', 'pot', 'ir', 'resistor'}
                        <= {p['type'] for p in parts})
        self.assertIn('ESP32 LCD ok', item['code'])
        self.assertIn('TICK %u BTN=%d POT=%d', item['code'])
